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
import threading
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QCursor, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.μOrb import μOrb, μOrbSmall, μOrbTask
from helpers.μImageFactory import *
from widgets.μFloating import μToggler
from widgets.μItemsTable import *
from widgets.μItemFilter import μItemFilter
from helpers.μMilvianPacket import μMilvianPacket, packetCommand, packetStatus, packetSignal
from helpers.μPrint import μPrint
from helpers.μStrings import *
from μMilvian import *
import os, time, struct, mmap
from helpers import χDB
from helpers.χDB import P_STORAGE_INVENTORY
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMilvianBridge import μMilvianBridge
   

P_DEFAULT_EXAMINE_DELAY=100

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#
#   ❖  S T O R A G E   M A N A G E R
#
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μStorage(μToggler):
  sigAppendItem  = pyqtSignal(μItemData)
  sigPurgeStale  = pyqtSignal(int, str, set)  # (storageType, ownerName, freshIds)
  sigSetStatus = pyqtSignal(object,int)
  vaultMode = False
  widgetID = "StorageManager"
  daemon : μMilvianBridge = None
  status : dict = {}

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, main):
    self.main = main
    super().__init__("Storage\nManager", P_ICON_CHEST)
    self.toggler.setToolTip("Toggle Storage Manager UI")
    self.table = μItemsTable(self, columns=P_STORAGE_COLUMNS)
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    setBGColour(self.table.viewport(), P_DEFAULT_BG)

    # self.btnLoad        = cOrb(icon=P_ICON_TRIANGLE_DOWN, tooltip="Load storage data from file")
    self.btnRefresh   = μOrbTask("Refresh\nInventory",  icon=getIcon('backpack'), tooltip="Fetch inventory data from running clients and display in the viewer.<br><b>Ctrl+Click</b> to examine items and get more detailed data.")
    self.btnDissolve  = μOrbTask("Dissolve", icon=getIcon('cannith_dissolve_lean'),
                             tooltip="Dissolve all selected items. Item Deconstruction UI must be open.")
    self.btnSell      = μOrbTask("Sell",     icon=getIcon('cannith_vendor_lean'),
                             tooltip="Sell all selected items to the currently open vendor UI. <br><b>Ctrl+Click</b> to repair equipment too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnUse       = μOrbTask("Use",      icon=getIcon('use_gears'),
                             tooltip="Use selected items. Shortcut: <b><i>enter</i></b>. <b><i>Ctrl+Click</i></b> for auto-accepting confirmation dialogues. Shortcut: <b><i>Ctrl+Enter</i></b>")
    self.btnStore     = μOrbTask("Store",    icon=getIcon('cannith_bank_lean'),
                             tooltip="Store selected items in the currently open bank/chest. <br><b><i>Ctrl+click</i></b> to send to character bank (guild or shared banks preferred otherwise)")
    self.btnSort      = μOrbTask("Sort",     icon=getIcon('sort'),
                             tooltip="<b><i>Not Implemented Yet</b></i><br>Sort selected items by type. <br><i><b>Ctrl+Click</b></i> to sort by name<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnTrade     = μOrbTask("Trade",    icon=getIcon('cannith_trade_lean'),
                             tooltip="<b><i>Not Implemented Yet</b></i><br>Trade selected items with selected player. <br><b>Ctrl+Click</b> to add platinum too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnFeedJewel = μOrbTask("Feed\nJewel", icon=getIcon('cannith_feed_jewel'),
                             tooltip="<b><i>Not Implemented Yet</b></i><br>Feeds selected items into a sentient jewel. You must manually open the jewel UI.")
    self.btnToggleVault = μOrb("Vault\nMode", icon=getIcon('vault'),
                             tooltip="Toggles between inventory (managing current inventory) and vault mode (tracking banks and guild chests).")
    self.btnToggleRecord = μOrbTask("Record\nVault", icon=getIcon('camera'),
                             tooltip="Toggles data collection on/off")
    self.btnToggleVault.setCheckable(True)
    self.btnToggleRecord.setCheckable(True)
    self.lblExplanation = QLabel("Some explanation")
    self._pendingThreads = 0
    self._pendingLock    = threading.Lock()

    self.itemFilter = μItemFilter(self, self.table, lambda: self.modeFilter)


    self.btnRefresh.execute = lambda : self.refreshInventory(False)
    self.btnRefresh.executeCtrl = lambda : self.refreshInventory(True)
    self.btnUse.execute = self.requestUse
    self.btnUse.executeCtrl = lambda : self.requestUse(True)
    self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.btnSell.execute = self.requestSell
    self.btnSell.executeCtrl = lambda : self.requestSell(True, True)
    self.btnDissolve.execute = self.requestDissolve
    self.btnStore.execute = self.requestStore
    self.btnStore.executeCtrl = lambda : self.requestStore(destUI=3)
    self.btnFeedJewel.execute = self.requestFeedJewel
    self.btnFeedJewel.executeCtrl = lambda : self.requestFeedJewel(force=True)
    self.btnToggleVault.clicked.connect(self.toggleVaultMode)
    self.btnToggleRecord.clicked.connect(self.toggleRecord)

    self.btnSort.setEnabled(False)
    self.btnFeedJewel.setEnabled(False)
    self.btnTrade.setEnabled(False)

    for seq, slot in [("Esc",    self.table.clearSelection),
                      ("Return", self.requestUse),
                      ("Enter",  self.requestUse),
                      ("Ctrl+Return", lambda : self.requestUse(True)),
                      ("Ctrl+Enter",  lambda : self.requestUse(True))]:
      sc = QShortcut(QKeySequence(seq), self.table)
      sc.setContext(Qt.ShortcutContext.WidgetShortcut)
      sc.activated.connect(slot)
    self.table.itemDoubleClicked.connect(self.requestUseViaDoubleClick)

    self.sigAppendItem.connect(self.table.append)
    self.sigAppendItem.connect(self.itemFilter.updateDynamicFilters)
    self.sigAppendItem.connect(self.itemFilter.applyFilters)
    self.sigPurgeStale.connect(self.purgeStale)
    self.sigSetStatus.connect(self.setStatus)
    allSplitters = newVSplitter([self.table, self.itemFilter])
    allSplitters.setSizes([800, 100])
   
    self.setLayout(newVLayout([allSplitters, newHLayout([self.btnRefresh, self.btnToggleRecord, self.lblExplanation, self.btnUse, self.btnStore, self.btnSell,
                                                         self.btnDissolve, self.btnTrade, self.btnSort, self.btnFeedJewel, self.btnToggleVault])]))
    self.setInventoryMode()
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setStatus(self, bridge, newStatus):
    if newStatus != P_STATUS_IDLE:
      self.status[bridge]=newStatus
      if len(self.status.keys())>1:
        return  # assume that status was already set before by some other bridge
    else:
      if bridge in self.status: del self.status[bridge]
      if len(self.status)>0:
        # someone is still doing something; set newStatus to the first one found
        newStatus=list(self.status.values())[0]

    # This is easily bugged if we don't get a proper response from the bridge. 
    # Commenting for now, so the UI will basically act as a request-sender
    # Status is merely figurative and you can send many overlapping requests
    # They overwrite each other. That's fine for now, I guess
    # if newStatus == P_STATUS_BUSY_REFRESH:
    #   self.btnRefresh.setEnabled(True)
    #   self.btnDissolve.setEnabled(False)
    #   self.btnSell.setEnabled(False)
    #   self.btnTrade.setEnabled(False)
    #   self.btnStore.setEnabled(False)
    #   self.btnFeedJewel.setEnabled(False)
    #   self.btnSort.setEnabled(False)
    # elif newStatus == P_STATUS_BUSY_DISSOLVE:
    #   self.btnRefresh.setEnabled(False)
    #   self.btnDissolve.setEnabled(True)
    #   self.btnSell.setEnabled(False)
    #   self.btnTrade.setEnabled(False)
    #   self.btnStore.setEnabled(False)
    #   self.btnFeedJewel.setEnabled(False)
    #   self.btnSort.setEnabled(False)
    # elif newStatus == P_STATUS_BUSY_SELL:
    #   self.btnRefresh.setEnabled(False)
    #   self.btnDissolve.setEnabled(False)
    #   self.btnSell.setEnabled(True)
    #   self.btnTrade.setEnabled(False)
    #   self.btnStore.setEnabled(False)
    #   self.btnFeedJewel.setEnabled(False)
    #   self.btnSort.setEnabled(False)
    # elif newStatus == P_STATUS_BUSY_TRADE:
    #   self.btnRefresh.setEnabled(False)
    #   self.btnDissolve.setEnabled(False)
    #   self.btnSell.setEnabled(False)
    #   self.btnTrade.setEnabled(True)
    #   self.btnStore.setEnabled(False)
    #   self.btnFeedJewel.setEnabled(False)
    #   self.btnSort.setEnabled(False)
    # elif newStatus == P_STATUS_BUSY_STORE:
    #   self.btnRefresh.setEnabled(False)
    #   self.btnDissolve.setEnabled(False)
    #   self.btnSell.setEnabled(False)
    #   self.btnTrade.setEnabled(False)
    #   self.btnStore.setEnabled(True)
    #   self.btnFeedJewel.setEnabled(False)
    #   self.btnSort.setEnabled(False)
    # elif newStatus == P_STATUS_BUSY_FEEDJEWEL:
    #   self.btnRefresh.setEnabled(False)
    #   self.btnDissolve.setEnabled(False)
    #   self.btnSell.setEnabled(False)
    #   self.btnTrade.setEnabled(False)
    #   self.btnStore.setEnabled(False)
    #   self.btnFeedJewel.setEnabled(True)
    #   self.btnSort.setEnabled(False)
    # elif newStatus == P_STATUS_IDLE:
    if True:
      self.btnRefresh.setEnabled(True)
      self.btnDissolve.setEnabled(True)
      self.btnUse.setEnabled(True)
      self.btnSell.setEnabled(True)
      self.btnTrade.setEnabled(False)
      self.btnStore.setEnabled(True)
      self.btnFeedJewel.setEnabled(False)
      self.btnSort.setEnabled(False)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def initialize(self, daemon : μMilvianBridge):
    super().initialize()
    self.daemon = daemon
    self.itemFilter.initialize()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def toggleVaultMode(self):
    if self.vaultMode: self.setInventoryMode()
    else: self.setVaultMode()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _inventoryModeFilter(self, item: μItemData) -> bool:
    if item._storageType != P_STORAGE_INVENTORY:
      return True
    liveNames = {b.charName for b in μMilvianMeta.getBridges().values()}
    return item._ownerName not in liveNames

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setVaultMode(self):
    self.vaultMode = True
    self.modeFilter = lambda x : False
    self.itemFilter.setVaultMode(True)
    self.itemFilter.applyFilters()
    self.btnDissolve.setVisible(False)
    self.btnFeedJewel.setVisible(False)
    self.btnSell.setVisible(False)
    self.btnSort.setVisible(False)
    self.btnStore.setVisible(False)
    self.btnTrade.setVisible(False)
    self.btnUse.setVisible(False)
    self.lblExplanation.setVisible(True)
    self.btnToggleRecord.setVisible(True)
    self.btnToggleVault.setChecked(True)
    self.table.customContextMenuRequested.disconnect()
    self.loadDBData()
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def show(self):
    super().show()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def hide(self):
    super().hide()
    # if it is recording, stop

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setInventoryMode(self):
    self.vaultMode = False
    self.modeFilter = self._inventoryModeFilter
    self.itemFilter.setVaultMode(False)
    self.itemFilter.applyFilters()
    # if is recording, stop recording
    self.btnDissolve.setVisible(True)
    self.btnFeedJewel.setVisible(True)
    self.btnSell.setVisible(True)
    self.btnSort.setVisible(True)
    self.btnTrade.setVisible(True)
    self.btnStore.setVisible(True)
    self.btnUse.setVisible(True)
    self.lblExplanation.setVisible(False)
    self.btnToggleRecord.setVisible(False)
    self.btnToggleVault.setChecked(False)
    self.table.customContextMenuRequested.connect(self._showTableContextMenu)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _showTableContextMenu(self, pos):
    menu = QMenu(self)
    menu.addAction("In-Game Select",         self.requestSelectItem)
    menu.addAction("Examine",                self.requestExamine)
    menu.addSeparator()
    menu.addAction("Cleanup selected items", self._contextMenuCleanupSelected)
    menu.addAction("Clear selection",        self.table.clearSelection)
    menu.exec(QCursor.pos())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def requestSelectItem(self):
    selectedItems = self.getSelectedIDs()
    bridges = μMilvianMeta.getBridges()
    for c, items in selectedItems.items():
      if not items or c not in bridges: continue
      bridges[c].selectItem(items[0]._id)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _contextMenuCleanupSelected(self):
    rows = sorted(
      {item.row() for item in self.table.selectedItems() if not self.table.isRowHidden(item.row())},
      reverse=True)
    for row in rows:
      col0 = self.table.item(row, 0)
      if col0 is not None:
        try: del self.table.itemsById[col0._id]
        except KeyError: pass
      self.table.removeRow(row)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getSelectedIDs(self) -> dict:
    selectedItems = {b : [] for b in μMilvianMeta.getBridges().keys()}
    for item in self.table.selectedItems():
      if item.column()==0:
        item : μItemData
        if item.isSelected() and not self.table.isRowHidden(item.row()):
          selectedItems[item._ownerName.lower()].append(item)
    return selectedItems
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  L O A D   D B   D A T A 
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def loadDBData(self):
    def _thread():
      try:
        conn = χDB.openVaultDB()
        rows = conn.execute("SELECT * FROM items").fetchall()
        conn.close()
      except Exception as e:
        μPrint.error("[μStorage] DB load failed:", e)
        return
      for row in rows:
        d = dict(zip(χDB.DB_ITEM_COLS, row))
        item = μItemData()
        item._id              = d["id"]
        item._storageType     = d["storage_type"]
        item._name            = d["name"]
        item._ownerID         = d["owner_id"]
        item._ownerName       = χDB.resolveOwnerName(d["owner_name"])
        item._weenieID        = d["weenie_id"]
        item._type            = d["type"]
        item._quantity        = d["quantity"]
        item._qualifier       = d["qualifier"]
        item._valueCopper     = d["value_copper"]
        item._hardness        = d["hardness"]
        item._durability      = d["durability"]
        item._iconId          = d["icon_id"]
        item._description     = d["description"]
        item._minLevel        = d["min_level"]
        item._material        = d["material"]
        item._isJunk          = d["is_junk"]
        item._isLocked        = d["is_locked"]
        item._isSellable      = d["is_sellable"]
        item._isMinorArtifact = d["is_minor_artifact"]
        item._setBonus1       = d["set_bonus_1"]
        item._setBonus2       = d["set_bonus_2"]
        item._currentSlot     = d["current_slot"]
        item._binding         = d["binding"]
        item._equipsTo        = d["equips_to"]
        item._augments        = [int(x) for x in d["augments"].split(",") if x] if d["augments"] else []
        item._effects         = dict(p.split("=", 1) for p in d["effects"].split("|") if "=" in p) if d["effects"] else {}
        item.digest()
        self.sigAppendItem.emit(item)
    threading.Thread(target=_thread, daemon=True).start()

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E C O R D   V A U L T
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def toggleRecord(self, checked: bool):
    bridges = μMilvianMeta.getBridges()
    if not bridges:
      μPrint.warning("[μStorage] No active bridges")
      self.btnToggleRecord.setChecked(False)
      return
    inData = struct.pack('<I', 1 if checked else 0)
    if checked:
      with self._pendingLock:
        self._pendingThreads = len(bridges)
    for bridge in bridges.values():
      p = μMilvianPacket(packetCommand.queryvault, bridge, inData)
      p.χigResponse.connect(lambda data, p=p: self._vaultStatusUpdate(p, data))
      bridge.send(p)
      if checked:
        pathFile = f"/dev/shm/milvian/{bridge.charName.lower()}/vault.bin"
        try: os.remove(pathFile)
        except: pass
        μPrint.info(f"[μStorage] Vault recording started for {bridge.charName} — interact with a bank in-game")
        threading.Thread(target=self._readVaultThread, args=(bridge, p), daemon=True).start()
      else:
        μPrint.info(f"[μStorage] Vault recording stopped for {bridge.charName}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _vaultStatusUpdate(self, packet: μMilvianPacket, rawData: bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[μStorage] Vault recording done for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
    else:
      μPrint.info(f"[μStorage] {C_ORANGE}{packet.outData.decode('utf-8', errors='replace')}</font>")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _readVaultThread(self, bridge, packet: μMilvianPacket):
    charName = bridge.charName.lower()
    pathFile = f"/dev/shm/milvian/{charName}/vault.bin"

    while not os.path.exists(pathFile) or os.path.getsize(pathFile) < 4:
      time.sleep(0.1)

    freshIds   : dict[int, set] = {}
    ownerNames : dict[int, str] = {}

    def read_exactly(f, n) -> bytes:
      data = b''
      while len(data) < n:
        chunk = f.read(n - len(data))
        if chunk: data += chunk
        else: time.sleep(0.05)
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
        nItems    = read_uint32(f)
        avail_pos = f.tell()
        read_uint32(f)
        if storageType not in freshIds:
          freshIds[storageType] = set()
        itemsRead = 0
        while itemsRead < nItems:
          if poll_avail(f, avail_pos) > itemsRead:
            item = μItemData()
            try:
              item.readFromBin(f)
            except Exception as e:
              μPrint.error(f"[μStorage] _readVaultThread readFromBin failed at {itemsRead}/{nItems}:", e)
              break
            item._storageType = storageType
            item._ownerName   = χDB.resolveOwnerName(item._ownerName)
            if storageType not in ownerNames:
              ownerNames[storageType] = item._ownerName
            freshIds[storageType].add(item._id)
            item.digest()
            self.sigAppendItem.emit(item)
            try:
              conn = χDB.openVaultDB()
              χDB.upsertVaultItem(conn, item, storageType)
              conn.commit()
              conn.close()
            except Exception as e:
              μPrint.error("[μStorage] _readVaultThread DB upsert failed:", e)
            itemsRead += 1
          else:
            time.sleep(0.05)

    try:
      conn = χDB.openVaultDB()
      for st, ids in freshIds.items():
        owner = ownerNames.get(st, "")
        χDB.purgeStaleVault(conn, st, owner, ids)
        self.sigPurgeStale.emit(st, owner, ids)
      conn.commit()
      conn.close()
    except Exception as e:
      μPrint.error("[μStorage] _readVaultThread DB purge failed:", e)

    μPrint.info(f"[μStorage] Vault snapshot complete for {bridge.charName}")
    with self._pendingLock:
      self._pendingThreads -= 1
      if self._pendingThreads <= 0:
        self.btnToggleRecord.setChecked(False)

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   U S E
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestUse(self, confirm=False):
    self._requestUse(self.getSelectedIDs(), confirm)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def requestUseViaDoubleClick(self, item: μItemData):
    if item.column() != 0: return
    selectedItems = {b: [] for b in μMilvianMeta.getBridges().keys()}
    selectedItems[item._ownerName.lower()].append(item)
    self._requestUse(selectedItems)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _requestUse(self, selectedItems: dict, confirm=False):
    if not selectedItems: return
    packets = {}
    bridges : μMilvian = μMilvianMeta.getBridges()
    for c in selectedItems.keys():
      inData  = struct.pack('<?',True)  # sendStatus flag, requests frequent status update always for now
      inData += struct.pack('<?',confirm)
      inData += struct.pack('<I',1)     # number of retries
      inData += struct.pack('<I',len(selectedItems[c]))
      for item in list(selectedItems[c]):
        inData += struct.pack('<Q',item._id)
      p = μMilvianPacket(packetCommand.useItems, bridges[c], inData)
      packets[c] = p
      self.setStatus(bridges[c], P_STATUS_BUSY_USE)
      bridges[c].send(packets[c])
      p.χigResponse.connect(lambda data, p=p: self.useItemUpdate(p, data))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def useItemUpdate(self, packet : μMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[μStorage] Finished using requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[μStorage] Error using items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      used = packet.outData[0]
      iID = struct.unpack('<Q', packet.outData[1:9])[0]
      μPrint.info(f"[μStorage] {"used" if used else "failed to use"} {C_ORANGE}{iID}</font>")

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   D I S S O L V E
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestDissolve(self, force=False):
    # TO IMPLEMENT: force ignores checks if item is deconstructeable e.g. named items cannot be deconstructed
    selectedItems = self.getSelectedIDs()
    if not selectedItems: return
    packets = {}
    bridges : μMilvian = μMilvianMeta.getBridges()
    for c in selectedItems.keys():
      inData = struct.pack('<?',True)  # sendStatus flag, requests frequent status update always for now
      inData += struct.pack('<I',3)    # number of retries
      inData += struct.pack('<I',len(selectedItems[c]))
      for item in list(selectedItems[c]):
        inData += struct.pack('<Q',item._id)
      p = μMilvianPacket(packetCommand.dissolveItems, bridges[c], inData)
      packets[c] = p
      self.setStatus(bridges[c], P_STATUS_BUSY_DISSOLVE)
      bridges[c].send(packets[c])
      p.χigResponse.connect(lambda data, p=p: self.storageDissolveUpdate(p, data))
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def storageDissolveUpdate(self, packet : μMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[μStorage] Finished dissolving requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[μStorage] Error dissolving items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      dissolved = packet.outData[0]
      iID = struct.unpack('<Q',packet.outData[1:9])[0]
      μPrint.info(f"[μStorage] {"dissolved" if dissolved else "failed dissolving"} {C_ORANGE}{iID}</font>")

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   S T O R E
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestStore(self, destUI : int = 0, force=False):
    # TO IMPLEMENT: force ignores checks if item is no bankeable
    selectedItems = self.getSelectedIDs()
    if not selectedItems: return
    packets = {}
    bridges : μMilvian = μMilvianMeta.getBridges()
    for c in selectedItems.keys():
      inData = struct.pack('<?',True)     # sendStatus flag, requests frequent status update always for now
      inData += struct.pack('<I',3)       # number of retries
      inData += struct.pack('<I',destUI)  # which UI to store to (0=auto, 1=guild bank, 2=shared bank, 3=personal bank)
      inData += struct.pack('<I',len(selectedItems[c]))
      for item in list(selectedItems[c]):
        inData += struct.pack('<Q',item._id)
      p = μMilvianPacket(packetCommand.storeItems, bridges[c], inData)
      packets[c] = p
      self.setStatus(bridges[c], P_STATUS_BUSY_STORE)
      bridges[c].send(packets[c])
      p.χigResponse.connect(lambda data, p=p: self.storageStoreUpdate(p, data))
 
   # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def storageStoreUpdate(self, packet : μMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[μStorage] Finished storing requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[μStorage] Error storing items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      stored = packet.outData[0]
      iID = struct.unpack('<Q',packet.outData[1:9])[0]
      μPrint.info(f"[μStorage] {"stored" if stored else "failed to store"} {C_ORANGE}{iID}</font>")

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   T R A D E
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestTrade(self, force=False):
    # force ignores checks if item is tradeable e.g. bound items
    pass

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   S E L L
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestSell(self, sellGems : bool = True, repair : bool = False):
    selectedItems = self.getSelectedIDs()
    if not selectedItems: return
    packets = {}
    bridges : μMilvian = μMilvianMeta.getBridges()
    for c in selectedItems.keys():
      inData  = struct.pack('<?',True)     # sendStatus flag, requests frequent status update always for now
      inData += struct.pack('<?',repair)   # repair
      inData += struct.pack('<?',sellGems) # sellGems
      inData += struct.pack('<I',len(selectedItems[c]))
      for item in list(selectedItems[c]):
        inData += struct.pack('<Q',item._id)
      p = μMilvianPacket(packetCommand.sellItems, bridges[c], inData)
      packets[c] = p
      self.setStatus(bridges[c], P_STATUS_BUSY_SELL)
      bridges[c].send(packets[c])
      p.χigResponse.connect(lambda data, p=p: self.storageSellUpdate(p, data))
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def storageSellUpdate(self, packet : μMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[μStorage] Finished selling requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[μStorage] Error selling items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      iID = struct.unpack('<Q',packet.outData[0:8])[0]
      μPrint.info(f"[μStorage] sold {C_ORANGE}{iID}</font>")

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   F E E D   J E W E L
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestFeedJewel(self, force=False):
    # force ignores checks if item is feedable e.g. random loot
    pass

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   E X A M I N E
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestExamine(self, delay : int = P_DEFAULT_EXAMINE_DELAY):
    selectedItems = self.getSelectedIDs()
    if not selectedItems: return
    bridges : μMilvian = μMilvianMeta.getBridges()
    for c in selectedItems.keys():
      if not selectedItems[c]: continue
      bridge = bridges[c]
      inData  = struct.pack('<?', True)              # sendStatus flag
      inData += struct.pack('<I', delay)             # ms delay between examines
      inData += struct.pack('<I', len(selectedItems[c]))
      for item in list(selectedItems[c]):
        inData += struct.pack('<Q', item._id)
      try: os.remove(f'/dev/shm/milvian/{bridge.charName.lower()}/inventory.bin')
      except: pass
      p = μMilvianPacket(packetCommand.examineItems, bridge, inData)
      p.χigResponse.connect(lambda data, p=p: self.inventoryStatusUpdate(p, data))
      bridge.send(p)
      self.readInventoryBin(bridge)


  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E F R E S H   S T U F F
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def refreshInventory(self, detailed: bool = False, delay: int = P_DEFAULT_EXAMINE_DELAY):
    printStatus = True                        # for now always true
    inData  = struct.pack('?', detailed)      # provide detailed information
    inData += struct.pack('?', printStatus)   # provide status updates
    inData += struct.pack('<I', delay)        # ms delay between examines (only used when detailed=True)

    for bridge in μMilvianMeta.getBridges().values():
      bridge : μMilvian
      try: os.remove(f'/dev/shm/milvian/{bridge.charName.lower()}/inventory.bin')
      except: pass
      p = μMilvianPacket(packetCommand.queryinventory, bridge, inData)
      p.χigResponse.connect(lambda data, p=p: self.inventoryStatusUpdate(p, data))
      bridge.send(p)
      μPrint.info(f"[μStorage] Inventory refresh requested for {C_ORANGE}{bridge.charName}</font>")
      self.readInventoryBin(bridge)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def inventoryStatusUpdate(self, packet : μMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[μStorage] Finished refreshing storage for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
    else:
      μPrint.info(f"[μStorage] {C_ORANGE}{packet.outData.decode('utf-8', errors='replace')}</font>")
    # cDispatcher.fulfill((packet.bridge.id, packet.id, packetSignal.running), packet.bridge)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def readInventoryBin(self, bridge : μMilvian):
    def _refreshStorageThread(self : μStorage, bridge : μMilvian):
      filename  = f'/dev/shm/milvian/{bridge.charName.lower()}/inventory.bin'
      ownerName = bridge.charName
      freshIds  = set()

      while not os.path.exists(filename) or os.path.getsize(filename) < 13:
        time.sleep(0.1)

      with open(filename, 'rb') as f:
        _requestId = struct.unpack('<I', f.read(4))[0]
        nItems     = struct.unpack('<I', f.read(4))[0]
        _avail0    = struct.unpack('<I', f.read(4))[0]
        favail     = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        itemsCount = 0
        while True:
          if struct.unpack('<I', favail[8:12])[0] > itemsCount:
            item = μItemData()
            try:
              item.readFromBin(f)
            except Exception as e:
              μPrint.error(f"[μStorage] readFromBin failed at item {itemsCount}/{nItems}:", e)
              break
            item._storageType = P_STORAGE_INVENTORY
            item._ownerName   = ownerName
            item.digest()
            freshIds.add(item._id)
            try:
              conn = χDB.openVaultDB()
              χDB.upsertVaultItem(conn, item, P_STORAGE_INVENTORY)
              conn.commit()
              conn.close()
            except Exception as e:
              μPrint.error(f"[μStorage] DB upsert failed:", e)
            self.sigAppendItem.emit(item)
            itemsCount += 1
          else:
            time.sleep(0.05)
          if itemsCount >= nItems: break

      try:
        conn = χDB.openVaultDB()
        χDB.purgeStaleVault(conn, P_STORAGE_INVENTORY, ownerName, freshIds)
        conn.commit()
        conn.close()
      except Exception as e:
        μPrint.error(f"[μStorage] DB purge failed:", e)

      self.sigSetStatus.emit(bridge, P_STATUS_IDLE)
      self.sigPurgeStale.emit(P_STORAGE_INVENTORY, ownerName, freshIds)

    self.setStatus(bridge, P_STATUS_BUSY_REFRESH)
    t = threading.Thread(target=_refreshStorageThread, args=(self, bridge), daemon=True)
    t.start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def purgeStale(self, storageType: int, ownerName: str, freshIds: set):
    toRemove = []
    for row in range(self.table.rowCount()):
      item = self.table.item(row, 0)
      if item and item._storageType == storageType and item._ownerName == ownerName and item._id not in freshIds:
        toRemove.append(row)
    npurged = len(toRemove)
    for row in reversed(toRemove):
      col0 = self.table.item(row, 0)
      if col0:
        try: del self.table.itemsById[col0._id]
        except: pass
      self.table.removeRow(row)
    if npurged:
      μPrint.info(f"[μStorage] cleaned {npurged} stale items from {C_ORANGE}{ownerName}</font>")
  
