#
#
#    μDDO
#    Copyright (C) 2025  Rafael Lago
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
from __future__ import annotations
import os
import sqlite3
import struct
import threading
import time
import yaml
from types import SimpleNamespace

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLineEdit

from helpers.μImageFactory import *
from helpers.μMilvianPacket import μMilvianPacket, packetCommand, packetStatus
from helpers.μPrint import μPrint
from helpers.μStrings import *
from widgets.μCombo import μCheckCombo
from widgets.μFloating import μToggler
from widgets.μItemsTable import *
from widgets.μOrb import μOrb, μOrbSmall, μOrbTask
from widgets.μOrb import μBoxCheck
from μMilvian import *
from μWorlds import μWorldList

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from μMilvianBridge import μMilvianBridge

def _vaultDBPath() -> str:
    try:
        server = μWorldList.getServerName()
    except Exception:
        server = "default"
    return os.path.join(P_DEFAULT_CONFIGDIR, f"storage{server}.db")

# StorageType values must match C# enum
STORAGE_INVALID          = 0
STORAGE_INVENTORY        = 1
STORAGE_CHARACTER_BANK   = 2
STORAGE_SHARED_BANK      = 3
STORAGE_REINCARNATION    = 4
STORAGE_GUILD_GENERAL1   = 5
STORAGE_GUILD_GENERAL2   = 6
STORAGE_GUILD_OFFICER1   = 7
STORAGE_GUILD_OFFICER2   = 8
STORAGE_GUILD_CHEST_SM   = 9
STORAGE_GUILD_CHEST_LG   = 10

P_DEFAULT_EXAMINE_DELAY  = 100
P_EXTENDED_SETTINGS_FILE = os.path.join(P_DEFAULT_CONFIGDIR, "extendedSettings.yaml")

# Fields that only inventory can reliably provide — bank UPSERT must not overwrite these
_INVENTORY_ONLY_COLS = {"current_slot", "effects"}

def _loadExtendedSettings() -> dict:
    try:
        with open(P_EXTENDED_SETTINGS_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def resolveOwnerName(ownerName: str) -> str:
    """Map guild hex ID → guildName, else return ownerName as-is."""
    if not ownerName.startswith("0x"):
        return ownerName
    try:
        server = μWorldList.getServerName()
    except Exception:
        return ownerName
    settings = _loadExtendedSettings()
    server_data = settings.get(server, {})
    if not isinstance(server_data, dict):
        return ownerName
    # YAML parses hex literals as ints — normalize keys to uppercase hex strings
    normalized = {
        (f"0x{k:X}" if isinstance(k, int) else k): v
        for k, v in server_data.items()
    }
    entry = normalized.get(ownerName.upper(), normalized.get(ownerName, {}))
    if isinstance(entry, dict) and "guildName" in entry:
        return entry["guildName"]
    return ownerName

# ─────────────────────────────────────────────────────────────────────────────────────────────────
#   D B   H E L P E R S
# ─────────────────────────────────────────────────────────────────────────────────────────────────
def _openDB() -> sqlite3.Connection:
    os.makedirs(P_DEFAULT_CONFIGDIR, exist_ok=True)
    conn = sqlite3.connect(_vaultDBPath(), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id            INTEGER PRIMARY KEY,
            storage_type  INTEGER NOT NULL DEFAULT 0,
            name          TEXT    NOT NULL DEFAULT '',
            owner_id      INTEGER NOT NULL DEFAULT 0,
            owner_name    TEXT    NOT NULL DEFAULT '',
            weenie_id     INTEGER NOT NULL DEFAULT 0,
            type          TEXT    NOT NULL DEFAULT '',
            quantity      INTEGER NOT NULL DEFAULT 0,
            qualifier     TEXT    NOT NULL DEFAULT '',
            value_copper  INTEGER NOT NULL DEFAULT 0,
            hardness      INTEGER NOT NULL DEFAULT 0,
            durability    INTEGER NOT NULL DEFAULT 0,
            icon_id       INTEGER NOT NULL DEFAULT 0,
            description   TEXT    NOT NULL DEFAULT '',
            min_level     INTEGER NOT NULL DEFAULT 0,
            material      INTEGER NOT NULL DEFAULT 0,
            is_junk       INTEGER NOT NULL DEFAULT 0,
            is_locked     INTEGER NOT NULL DEFAULT 0,
            is_minor_artifact INTEGER NOT NULL DEFAULT 0,
            is_sellable   INTEGER NOT NULL DEFAULT 0,
            set_bonus_1   TEXT    NOT NULL DEFAULT '',
            set_bonus_2   TEXT    NOT NULL DEFAULT '',
            current_slot  INTEGER NOT NULL DEFAULT 0,
            binding       INTEGER NOT NULL DEFAULT 0,
            equips_to     TEXT    NOT NULL DEFAULT '',
            augments      TEXT    NOT NULL DEFAULT '',
            effects       TEXT    NOT NULL DEFAULT ''
        )
    """)
    conn.commit()
    return conn


def _upsertItem(conn: sqlite3.Connection, item: μItemData, storageType: int):
    """
    Upsert item into DB.
    Bank sources (non-inventory) do NOT overwrite inventory-only fields if a
    richer inventory row already exists.
    """
    is_bank = storageType != STORAGE_INVENTORY

    augments_str = ",".join(str(a) for a in item._augments)
    effects_str  = "|".join(f"{k}={v}" for k, v in item._effects.items())

    if is_bank:
        conn.execute("""
            INSERT INTO items
              (id, storage_type, name, owner_id, owner_name, weenie_id, type,
               quantity, qualifier, value_copper, hardness, icon_id,
               description, min_level, material, is_minor_artifact,
               set_bonus_1, set_bonus_2, binding, augments,
               durability, is_junk, is_locked, is_sellable, equips_to,
               current_slot, effects)
            VALUES (?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?, 0,0,0,0,'', 4294967295,'')
            ON CONFLICT(id) DO UPDATE SET
              storage_type  = excluded.storage_type,
              name          = excluded.name,
              owner_id      = excluded.owner_id,
              owner_name    = excluded.owner_name,
              weenie_id     = excluded.weenie_id,
              type          = excluded.type,
              quantity      = excluded.quantity,
              qualifier     = excluded.qualifier,
              value_copper  = excluded.value_copper,
              hardness      = excluded.hardness,
              icon_id       = excluded.icon_id,
              description   = excluded.description,
              min_level     = excluded.min_level,
              material      = excluded.material,
              is_minor_artifact = excluded.is_minor_artifact,
              set_bonus_1   = excluded.set_bonus_1,
              set_bonus_2   = excluded.set_bonus_2,
              binding       = excluded.binding,
              augments      = excluded.augments
        """, (item._id, storageType, item._name, item._ownerID, item._ownerName,
              item._weenieID, item._type, item._quantity, item._qualifier,
              item._valueCopper, item._hardness, item._iconId,
              item._description, item._minLevel, item._material, item._isMinorArtifact,
              item._setBonus1, item._setBonus2, item._binding, augments_str))
    else:
        conn.execute("""
            INSERT INTO items
              (id, storage_type, name, owner_id, owner_name, weenie_id, type,
               quantity, qualifier, value_copper, hardness, durability, icon_id,
               description, min_level, material, is_junk, is_locked, is_sellable,
               is_minor_artifact, set_bonus_1, set_bonus_2, current_slot,
               binding, equips_to, augments, effects)
            VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?,?, ?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              storage_type  = excluded.storage_type,
              name          = excluded.name,
              owner_id      = excluded.owner_id,
              owner_name    = excluded.owner_name,
              weenie_id     = excluded.weenie_id,
              type          = excluded.type,
              quantity      = excluded.quantity,
              qualifier     = excluded.qualifier,
              value_copper  = excluded.value_copper,
              hardness      = excluded.hardness,
              durability    = excluded.durability,
              icon_id       = excluded.icon_id,
              description   = excluded.description,
              min_level     = excluded.min_level,
              material      = excluded.material,
              is_junk       = excluded.is_junk,
              is_locked     = excluded.is_locked,
              is_sellable   = excluded.is_sellable,
              is_minor_artifact = excluded.is_minor_artifact,
              set_bonus_1   = excluded.set_bonus_1,
              set_bonus_2   = excluded.set_bonus_2,
              current_slot  = excluded.current_slot,
              binding       = excluded.binding,
              equips_to     = excluded.equips_to,
              augments      = excluded.augments,
              effects       = excluded.effects
        """, (item._id, storageType, item._name, item._ownerID, item._ownerName,
              item._weenieID, item._type, item._quantity, item._qualifier,
              item._valueCopper, item._hardness, item._durability, item._iconId,
              item._description, item._minLevel, item._material,
              item._isJunk, item._isLocked, item._isSellable, item._isMinorArtifact,
              item._setBonus1, item._setBonus2, item._currentSlot,
              item._binding, item._equipsTo, augments_str, effects_str))


def _purgeStale(conn: sqlite3.Connection, storageType: int, ownerName: str, freshIds: set):
    if not freshIds:
        return
    placeholders = ",".join("?" * len(freshIds))
    conn.execute(
        f"DELETE FROM items WHERE storage_type=? AND owner_name=? AND id NOT IN ({placeholders})",
        [storageType, ownerName] + list(freshIds)
    )


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#
#   ❖  V A U L T
#
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μVault(μToggler):
    sigAppendItem        = pyqtSignal(μItemData)
    sigPurgeStale        = pyqtSignal(int, str, set)  # (storageType, ownerName, freshIds)
    sigSetStatus         = pyqtSignal(str)
    sigVaultDone         = pyqtSignal()
    widgetID = "Vault"

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def __init__(self, main):
        self.main = main
        super().__init__("Vault", P_ICON_CHEST)
        self.toggler.setToolTip("Toggle Vault — cross-character item browser")
        self.table = μItemsTable(self, columns=P_VAULT_COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        setBGColour(self.table.viewport(), P_DEFAULT_BG)

        self.btnToggle = μOrb("Toggle", icon=P_ICON_REFRESH, checkable=True,
                              tooltip="Toggle bank event watching.<br>When active, opening any bank in-game captures its contents.")
        self.btnRefresh = μOrbTask("Refresh", icon=P_ICON_REFRESH,
                                   tooltip="Refresh inventory for all active characters.")
        self._pendingThreads = 0
        self._pendingLock    = threading.Lock()

        self.filterCB = SimpleNamespace()
        for f in ["Name", "Description"]:
            setattr(self.filterCB, f.lower(), μBoxCheck(f))
        self.filterCB.aug0  = μBoxCheck('0')
        self.filterCB.aug1  = μBoxCheck('1')
        self.filterCB.aug2  = μBoxCheck('2')
        self.filterCB.aug3p = μBoxCheck('3+')

        for cb in self.filterCB.__dict__.keys():
            getattr(self.filterCB, cb).setChecked(True)
            getattr(self.filterCB, cb).stateChanged.connect(self.applyFilters)

        self.filterQualifier = μCheckCombo("Qualifier")
        for q in ["<Empty>", "Named", "Vendor", "Random", "Raid"]:
            self.filterQualifier.addCheckItem(q)

        self.filterAugments  = μCheckCombo("Augments")
        for n, i in zip(P_ITEM_AUGMENTS_NAME.values(), P_ITEM_AUGMENTS_ICON.values()):
            self.filterAugments.addCheckItem(f"{n} {i}")

        self.filterOwner    = μCheckCombo("Owner")
        self.filterType     = μCheckCombo("Type")
        self.filterStorage  = μCheckCombo("Storage")
        for v in P_STORAGE_NAMES.values():
            if v: self.filterStorage.addCheckItem(v)

        self.filterText            = QLineEdit()
        self.filterClearSelection  = μOrbSmall(icon=P_ICON_CLEAR, tooltip="Clear whole selection")

        hline = QFrame()
        hline.setFixedHeight(2)
        hline.setFrameShape(QFrame.Shape.HLine)
        g1 = QGridLayout()
        g1.addWidget(self.filterCB.name,        0, 0)
        g1.addWidget(self.filterCB.description, 0, 1)
        g1.addWidget(newHFrame([self.filterClearSelection, "Clear selection"]), 0, 2, 1, 2, Qt.AlignmentFlag.AlignRight)
        g1.addWidget(hline, 1, 0, 1, 4)
        g1.addWidget(newHFrame(["Augments Count:", self.filterCB.aug0, self.filterCB.aug1,
                                self.filterCB.aug2, self.filterCB.aug3p]), 2, 0, 1, 4)

        advFilters = newVFrame([
            newHLayout(["Filter by...", self.filterText]), g1,
            newHLayout([self.filterQualifier, self.filterType]),
            newHLayout([self.filterAugments, self.filterOwner, self.filterStorage]),
        ])

        self.filterQualifier.changed.connect(self.applyFilters)
        self.filterOwner.changed.connect(self.applyFilters)
        self.filterType.changed.connect(self.applyFilters)
        self.filterStorage.changed.connect(self.applyFilters)
        self.filterAugments.changed.connect(self.applyFilters)
        self.filterText.textEdited.connect(self.applyFilters)
        self.filterClearSelection.clicked.connect(self.table.clearSelection)

        self.btnToggle.clicked.connect(self._onToggle)
        self.btnRefresh.execute = self._requestRefreshInventory
        self.btnRefresh.executeCtrl = lambda : self._requestRefreshInventory(True)

        self.sigAppendItem.connect(self.table.append)
        self.sigAppendItem.connect(self._updateDynamicFilters)
        self.sigAppendItem.connect(self.applyFilters)
        self.sigPurgeStale.connect(self._purgeStaleSlot)
        self.sigVaultDone.connect(lambda: self.btnToggle.setChecked(False))

        allSplitters = newVSplitter([self.table, advFilters])
        allSplitters.setSizes([800, 150])
        self.setLayout(newVLayout([allSplitters, newHLayout([self.btnRefresh, self.btnToggle])]))

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def initialize(self, daemon):
        super().initialize()
        self._loadFromDB()

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _loadFromDB(self):
        try:
            conn = _openDB()
            rows = conn.execute("SELECT * FROM items").fetchall()
            conn.close()
        except Exception as e:
            μPrint.error("[μVault] DB load failed:", e)
            return

        cols = ["id","storage_type","name","owner_id","owner_name","weenie_id","type",
                "quantity","qualifier","value_copper","hardness","durability","icon_id",
                "description","min_level","material","is_junk","is_locked","is_minor_artifact",
                "is_sellable","set_bonus_1","set_bonus_2","current_slot","binding","equips_to",
                "augments","effects"]

        for row in rows:
            d = dict(zip(cols, row))
            item = μItemData()
            item._id             = d["id"]
            item._storageType    = d["storage_type"]
            item._name           = d["name"]
            item._ownerID        = d["owner_id"]
            item._ownerName      = resolveOwnerName(d["owner_name"])
            item._weenieID       = d["weenie_id"]
            item._type           = d["type"]
            item._quantity       = d["quantity"]
            item._qualifier      = d["qualifier"]
            item._valueCopper    = d["value_copper"]
            item._hardness       = d["hardness"]
            item._durability     = d["durability"]
            item._iconId         = d["icon_id"]
            item._description    = d["description"]
            item._minLevel       = d["min_level"]
            item._material       = d["material"]
            item._isJunk         = d["is_junk"]
            item._isLocked       = d["is_locked"]
            item._isSellable     = d["is_sellable"]
            item._isMinorArtifact= d["is_minor_artifact"]
            item._setBonus1      = d["set_bonus_1"]
            item._setBonus2      = d["set_bonus_2"]
            item._currentSlot    = d["current_slot"]
            item._binding        = d["binding"]
            item._equipsTo       = d["equips_to"]
            item._augments       = [int(x) for x in d["augments"].split(",") if x] if d["augments"] else []
            item._effects        = dict(p.split("=",1) for p in d["effects"].split("|") if "=" in p) if d["effects"] else {}
            item.digest()
            self.sigAppendItem.emit(item)

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _onToggle(self, checked: bool):
        bridges = μMilvianMeta.getBridges()
        if not bridges:
            μPrint.warning("[μVault] No active bridges")
            self.btnToggle.setChecked(False)
            return
        inData = struct.pack('<I', 1 if checked else 0)
        if checked:
            with self._pendingLock:
                self._pendingThreads = len(bridges)
        for bridge in bridges.values():
            p = μMilvianPacket(packetCommand.queryvault, bridge, inData)
            bridge.send(p)
            if checked:
                charName = bridge.charName.lower()
                pathFile = f"/dev/shm/milvian/{charName}/vault.bin"
                try: os.remove(pathFile)
                except: pass
                μPrint.info(f"[μVault] Watching started for {bridge.charName} — open a bank in-game")
                t = threading.Thread(target=self._readVaultThread, args=(bridge,), daemon=True)
                t.start()
            else:
                μPrint.info(f"[μVault] Watching stopped for {bridge.charName}")

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _requestRefreshInventory(self, detailed: bool = False, delay: int = P_DEFAULT_EXAMINE_DELAY):
        bridges = μMilvianMeta.getBridges()
        if not bridges:
            μPrint.warning("[μVault] No active bridges")
            return
        inData  = struct.pack('?', detailed) # detailed=False
        inData += struct.pack('?', True)     # printStatus=True
        inData += struct.pack('<I', delay)   # delay (unused when not detailed)
        for bridge in bridges.values():
            charName = bridge.charName.lower()
            try: os.remove(f"/dev/shm/milvian/{charName}/inventory.bin")
            except: pass
            p = μMilvianPacket(packetCommand.queryinventory, bridge, inData)
            bridge.send(p)
            μPrint.info(f"[μVault] Inventory refresh requested for {bridge.charName}")
            t = threading.Thread(target=self._readInventoryThread, args=(bridge,), daemon=True)
            t.start()

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _readInventoryThread(self, bridge):
        import mmap as _mmap
        charName = bridge.charName.lower()
        pathFile = f"/dev/shm/milvian/{charName}/inventory.bin"

        while not os.path.exists(pathFile) or os.path.getsize(pathFile) < 13:
            time.sleep(0.1)

        freshIds = set()
        ownerName = bridge.charName

        with open(pathFile, 'rb') as f:
            _requestId = struct.unpack('<I', f.read(4))[0]
            nItems     = struct.unpack('<I', f.read(4))[0]
            _avail0    = struct.unpack('<I', f.read(4))[0]
            favail     = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)

            itemsCount = 0
            while True:
                avail = struct.unpack('<I', favail[8:12])[0]
                if avail > itemsCount:
                    item = μItemData()
                    try:
                        item.readFromBin(f)
                    except Exception as e:
                        μPrint.error(f"[μVault] inventory readFromBin failed at {itemsCount}/{nItems}:", e)
                        break
                    item._storageType = STORAGE_INVENTORY
                    item.digest()
                    freshIds.add(item._id)
                    try:
                        conn = _openDB()
                        _upsertItem(conn, item)
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        μPrint.error("[μVault] DB upsert failed:", e)
                    self.sigAppendItem.emit(item)
                    itemsCount += 1
                else:
                    time.sleep(0.05)
                if itemsCount >= nItems:
                    break

        try:
            conn = _openDB()
            _purgeStale(conn, STORAGE_INVENTORY, ownerName, freshIds)
            self.sigPurgeStale.emit(STORAGE_INVENTORY, ownerName, freshIds)
            conn.commit()
            conn.close()
        except Exception as e:
            μPrint.error("[μVault] DB purge failed:", e)

        μPrint.info(f"[μVault] Inventory refresh complete for {bridge.charName}")

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _readVaultThread(self, bridge):
        charName = bridge.charName.lower()
        pathFile = f"/dev/shm/milvian/{charName}/vault.bin"

        while not os.path.exists(pathFile) or os.path.getsize(pathFile) < 4:
            time.sleep(0.1)

        freshIds: dict[int, set] = {}
        ownerNames: dict[int, str] = {}

        def read_exactly(f, n) -> bytes:
            data = b''
            while len(data) < n:
                chunk = f.read(n - len(data))
                if chunk:
                    data += chunk
                else:
                    time.sleep(0.05)
            return data

        def read_uint32(f) -> int:
            return struct.unpack('<I', read_exactly(f, 4))[0]

        def poll_avail(f, avail_pos) -> int:
            cur = f.tell()
            f.seek(avail_pos)
            data = f.read(4)
            f.seek(cur)
            return struct.unpack('<I', data)[0] if len(data) == 4 else 0

        with open(pathFile, 'rb') as f:
            while True:
                storageType = read_uint32(f)
                if storageType == 0:
                    break

                nItems   = read_uint32(f)
                avail_pos = f.tell()      # position of the itemAvail counter in the file
                read_uint32(f)            # skip past it; we'll seek back to poll it

                if storageType not in freshIds:
                    freshIds[storageType] = set()

                itemsRead = 0
                while itemsRead < nItems:
                    if poll_avail(f, avail_pos) > itemsRead:
                        item = μItemData()
                        try:
                            item.readFromBin(f)
                        except Exception as e:
                            μPrint.error(f"[μVault] readFromBin failed at item {itemsRead}/{nItems}:", e)
                            break
                        item._storageType = storageType
                        item._ownerName   = resolveOwnerName(item._ownerName)
                        if storageType not in ownerNames:
                            ownerNames[storageType] = item._ownerName
                        freshIds[storageType].add(item._id)
                        item.digest()
                        self.sigAppendItem.emit(item)

                        try:
                            conn = _openDB()
                            _upsertItem(conn, item, storageType)
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            μPrint.error("[μVault] DB upsert failed:", e)

                        itemsRead += 1
                    else:
                        time.sleep(0.05)

        # purge stale per storageType
        try:
            conn = _openDB()
            for st, ids in freshIds.items():
                owner = ownerNames.get(st, "")
                _purgeStale(conn, st, owner, ids)
                self.sigPurgeStale.emit(st, owner, ids)
            conn.commit()
            conn.close()
        except Exception as e:
            μPrint.error("[μVault] DB purge failed:", e)

        μPrint.info(f"[μVault] Snapshot complete for {bridge.charName}")
        with self._pendingLock:
            self._pendingThreads -= 1
            done = self._pendingThreads <= 0
        if done:
            self.sigVaultDone.emit()

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _purgeStaleSlot(self, storageType: int, ownerName: str, freshIds: set):
        toRemove = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item._storageType == storageType and item._ownerName == ownerName and item._id not in freshIds:
                toRemove.append(row)
        for row in reversed(toRemove):
            col0 = self.table.item(row, 0)
            if col0:
                try: del self.table.itemsById[col0._id]
                except KeyError: pass
            self.table.removeRow(row)

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _updateDynamicFilters(self, item: μItemData):
        if item._ownerName:
            self.filterOwner.addCheckItem(item.owner())
        if item._type:
            self.filterType.addCheckItem(item._type)
        if item._qualifier:
            self.filterQualifier.addCheckItem(item._qualifier)

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    def applyFilters(self, item: μItemData = None):
        filterText    = self.filterText.text().lower().strip()
        checkedOwners = [q.lower() for q in self.filterOwner.getChecked()]
        checkedTypes  = [q.lower() for q in self.filterType.getChecked()]
        checkedQuals  = [q.lower() for q in self.filterQualifier.getChecked()]
        checkedAugs   = [q.lower() for q in self.filterAugments.getChecked()]
        checkedStorage= [q.lower() for q in self.filterStorage.getChecked()]

        def _filterItem(item: μItemData, row: int):
            textTarget = ""
            if self.filterCB.name.isChecked():        textTarget += item._name.lower() + " "
            if self.filterCB.description.isChecked(): textTarget += (item.toolTip() or "").lower() + " "
            if filterText and filterText not in textTarget:
                return self.table.setRowHidden(row, True)

            itemAugs = [a for a in item.augments(textOnly=True) if a.lower() in checkedAugs]
            if len(itemAugs) == 0 and not self.filterCB.aug0.isChecked():  return self.table.setRowHidden(row, True)
            if len(itemAugs) == 1 and not self.filterCB.aug1.isChecked():  return self.table.setRowHidden(row, True)
            if len(itemAugs) == 2 and not self.filterCB.aug2.isChecked():  return self.table.setRowHidden(row, True)
            if len(itemAugs) >= 3 and not self.filterCB.aug3p.isChecked(): return self.table.setRowHidden(row, True)

            qualKey = item._qualifier.lower() if item._qualifier else "<empty>"
            if qualKey not in checkedQuals:                   return self.table.setRowHidden(row, True)
            if item.owner().lower() not in checkedOwners:     return self.table.setRowHidden(row, True)
            if item._type.lower() not in checkedTypes:        return self.table.setRowHidden(row, True)

            storageName = P_STORAGE_NAMES.get(item._storageType, "").lower()
            if storageName not in checkedStorage:             return self.table.setRowHidden(row, True)

            self.table.setRowHidden(row, False)

        if isinstance(item, μItemData):
            try:
                _filterItem(item, item.row())
            except RuntimeError:
                pass
        else:
            for row in range(self.table.rowCount()):
                col0 = self.table.item(row, 0)
                if col0:
                    _filterItem(col0, row)
