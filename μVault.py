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
import struct
import threading
import time
from types import SimpleNamespace

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLineEdit

from helpers.χDB import *
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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from μMilvianBridge import μMilvianBridge

P_DEFAULT_EXAMINE_DELAY = 100

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
        self.table = μItemsTable(self, columns=P_STORAGE_COLUMNS)
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
            conn = openVaultDB()
            rows = conn.execute("SELECT * FROM items").fetchall()
            conn.close()
        except Exception as e:
            μPrint.error("[μVault] DB load failed:", e)
            return

        for row in rows:
            d = dict(zip(DB_ITEM_COLS, row))
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
                        conn = openVaultDB()
                        upsertVaultItem(conn, item, STORAGE_INVENTORY)
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
            conn = openVaultDB()
            purgeStaleVault(conn, STORAGE_INVENTORY, ownerName, freshIds)
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
                            conn = openVaultDB()
                            upsertVaultItem(conn, item, storageType)
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            μPrint.error("[μVault] DB upsert failed:", e)

                        itemsRead += 1
                    else:
                        time.sleep(0.05)

        # purge stale per storageType
        try:
            conn = openVaultDB()
            for st, ids in freshIds.items():
                owner = ownerNames.get(st, "")
                purgeStaleVault(conn, st, owner, ids)
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
