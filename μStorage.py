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
#    This software is heavily based on PyLotRO (credits to AJackson
#    <ajackson@bcs.org.uk>), which in turn is based on a lotrolauncher 
#    script by SNy (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
import glob
import threading
from types import SimpleNamespace
from PyQt6.QtWidgets import QDialog, QGridLayout, QLineEdit, QListWidgetItem, QMenu, QListWidget, QTextEdit
from PyQt6.QtGui import QAction, QCursor, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.μOrb import μOrb, μOrbSmall, μOrbTask
from widgets.μOrb import μBoxCheck
from helpers.μImageFactory import *
from widgets.μFloating import μToggler
from widgets.μCombo import μCheckCombo
from widgets.μItemsTable import *
from helpers.μMilvianPacket import μMilvianPacket, packetCommand, packetStatus, packetSignal
from helpers.μPrint import μPrint
from helpers.μStrings import *
from widgets.μText import μTextEdit
from μMilvian import *
import time, struct, mmap
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
  sigPurgeStale  = pyqtSignal(str)
  sigSetStatus = pyqtSignal(object,int)
  widgetID = "StorageManager"
  daemon : μMilvianBridge = None
  status : dict = {}
  allFilterScripts : dict = {}

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, main):
    self.main = main
    super().__init__("Storage\nManager", P_ICON_CHEST)
    self.toggler.setToolTip("Toggle Storage Manager UI")
    self.table = μItemsTable(self)
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    setBGColour(self.table.viewport(), P_DEFAULT_BG)
    
    # self.btnLoad        = cOrb(icon=P_ICON_TRIANGLE_DOWN, tooltip="Load storage data from file")
    self.btnRefresh   = μOrbTask("Refresh",     icon=P_ICON_REFRESH, tooltip="Fetch data from running clients and display in the viewer.<br><b>Ctrl+Click</b> to examine items and get more detailed data.<br><i>Right-click for more options</i>")
    self.btnDissolve  = μOrbTask("Dissolve",    icon=getIcon('cannith_dissolve_lean'),
                             tooltip="Dissolve all selected items. Item Deconstruction UI must be open.")
    self.btnSell      = μOrbTask("Sell",        icon=getIcon('cannith_vendor_lean'),
                             tooltip="Sell all selected items to the currently open vendor UI. <br><b>Ctrl+Click</b> to repair equipment too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnUse       = μOrbTask("Use",        icon=getIcon('use_gears'),
                             tooltip="Use selected items. Shortcut: <b><i>enter</i></b>. <b><i>Ctrl+Click</i></b> for auto-accepting confirmation dialogues. Shortcut: <b><i>Ctrl+Enter</i></b>")
    self.btnStore     = μOrbTask("Store",       icon=getIcon('cannith_bank_lean'),
                             tooltip="Store selected items in the currently open bank/chest. <br><b><i>Ctrl+click</i></b> to send to character bank (guild or shared banks preferred otherwise)")
    self.btnSort      = μOrbTask("Sort",       icon=getIcon('sort'),
                             tooltip="<b><i>Not Implemented Yet</b></i><br>Sort selected items by type. <br><i><b>Ctrl+Click</b></i> to sort by name<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnFeedJewel = μOrbTask("Feed\nJewel", icon=getIcon('cannith_feed_jewel'),
                             tooltip="<b><i>Not Implemented Yet</b></i><br>Feeds selected items into a sentient jewel. You must manually open the jewel UI.")
    self.btnTrade     = μOrbTask("Trade",       icon=getIcon('cannith_trade_lean'),
                             tooltip="<b><i>Not Implemented Yet</b></i><br>Trade selected items with selected player. <br><b>Ctrl+Click</b> to add platinum too<b>.<br><b><i>Right-click for more options</i></b>")

    self.filterCB = SimpleNamespace()
    for f in ["Equipped", "Unequipped", "Unbound", "Bound", "Locked", "Unlocked", "Sellable", "Unsellable", "Name", "Description"]:
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

    self.filterAugments = μCheckCombo("Augments")
    for n,i in zip(P_ITEM_AUGMENTS_NAME.values(), P_ITEM_AUGMENTS_ICON.values()):
      self.filterAugments.addCheckItem(f"{n} {i}")

    self.filterOwner = μCheckCombo("Owner")
    self.filterType  = μCheckCombo("Type")
    self.filterText = QLineEdit()
    self.filterClearSelection  = μOrbSmall(icon=P_ICON_CLEAR, tooltip="Clear whole selection")

    hline = QFrame()
    hline.setFixedHeight(2)
    hline.setFrameShape(QFrame.Shape.HLine)
    g1 = QGridLayout()
    g1.addWidget(self.filterCB.name,        0, 0, 1, 1)
    g1.addWidget(self.filterCB.description, 0, 1, 1, 1)
    g1.addWidget(newHFrame([self.filterClearSelection,"Clear selection"]), 0, 2, 1, 2, Qt.AlignmentFlag.AlignRight)
    g1.addWidget(hline,    1, 0, 1, 4)
    g1.addWidget(self.filterCB.equipped,   2, 0, 1, 1)
    g1.addWidget(self.filterCB.locked,     2, 1, 1, 1)
    g1.addWidget(self.filterCB.sellable,   2, 2, 1, 1)
    g1.addWidget(self.filterCB.bound,      2, 3, 1, 1)
    g1.addWidget(self.filterCB.unequipped, 3, 0, 1, 1)
    g1.addWidget(self.filterCB.unlocked,   3, 1, 1, 1)
    g1.addWidget(self.filterCB.unsellable, 3, 2, 1, 1)
    g1.addWidget(self.filterCB.unbound,    3, 3, 1, 1)
    
    
    advFilters = newVFrame([newHLayout(["Filter by...", self.filterText]), g1,
                            # newHLayout(["__stretch__", self.filterCB.name, self.filterCB.description, "__stretch__", self.filterClearSelection, "Clear selection"]),
                            # "__line__",
                            # newHLayout([self.filterCB.equipped,   self.filterCB.locked  , self.filterCB.sellable,   self.filterCB.bound  ]), 
                            # newHLayout([self.filterCB.unequipped, self.filterCB.unlocked, self.filterCB.unsellable, self.filterCB.unbound]),
                            newHFrame(["Augments Count:", self.filterCB.aug0, self.filterCB.aug1, self.filterCB.aug2, self.filterCB.aug3p]),
                            newHLayout([self.filterQualifier, self.filterType]),
                            newHLayout([self.filterAugments, self.filterOwner, ])])

    self.filterScriptList      = QListWidget()
    self.filterScriptLabel     = QLabel("Selected Filter Script:")
    self.filterBtnNewScript    = μOrbSmall(icon=P_ICON_NEWDOC, tooltip="Create a new filter script with the text currently in the editor")
    self.filterBtnSaveScript   = μOrbSmall(icon=P_ICON_SAVE, tooltip="Save currently selected filter script.<br><b><i>Shortcut: Ctrl+S</b></i>.<br><b><i>Ctrl+Left</b></i> click to save all")
    self.filterBtnDelScript    = μOrbSmall(icon=P_ICON_TRASH, tooltip="Delete currently selected filter script - this action cannot be undone!")
    self.filterBtnReloadScript = μOrbSmall(icon=P_ICON_REFRESH, tooltip="Reload currently selected script from file\nCtrl+Left click to reload all")
    self.filterBtnApplyScript  = μOrbSmall(icon=P_ICON_FILTER, tooltip="Apply current filter.<br><b><i>Shortcut: Ctrl+Enter</b></i>.")
    self.filterBtnHelp         = μOrbSmall(icon=P_ICON_QUESTION, tooltip="Show a comprehensive help on how script work here (lol)")
    self.filterScriptEdit      = μTextEdit(syntax="filter")
    filtersContainer = newHSplitter([newHFrame([newVLayout(["Saved Filters:", self.filterScriptList]),
                                  newVFrame(["__stretch__",self.filterBtnApplyScript, self.filterBtnNewScript, self.filterBtnSaveScript,self.filterBtnDelScript, self.filterBtnReloadScript, self.filterBtnHelp, "__stretch__"])]),
                                  newVFrame([self.filterScriptLabel, self.filterScriptEdit]), advFilters])
    filtersContainer.setSizes([300,700,100])

    self.filterClearSelection.clicked.connect(self.table.clearSelection)
    self.filterQualifier.changed.connect(self.applyFilters)
    self.filterOwner.changed.connect(self.applyFilters)
    self.filterType.changed.connect(self.applyFilters)
    self.filterAugments.changed.connect(self.applyFilters)
    self.filterText.textEdited.connect(self.applyFilters)


    self.btnRefresh.execute = lambda : self.requestRefreshStorage(False)
    self.btnRefresh.executeCtrl = lambda : self.requestRefreshStorage(True)
    self.btnUse.execute = self.requestUse
    self.btnUse.executeCtrl = lambda : self.requestUse(True)
    self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.table.customContextMenuRequested.connect(self._showTableContextMenu)
    self.btnSell.execute = self.requestSell
    self.btnSell.executeCtrl = lambda : self.requestSell(True, True)
    self.btnDissolve.execute = self.requestDissolve
    self.btnStore.execute = self.requestStore
    self.btnStore.executeCtrl = lambda : self.requestStore(destUI=3)
    self.btnFeedJewel.execute = self.requestFeedJewel
    self.btnFeedJewel.executeCtrl = lambda : self.requestFeedJewel(force=True)

    self.btnSort.setEnabled(False)
    self.btnFeedJewel.setEnabled(False)
    self.btnTrade.setEnabled(False)

    self.filterScriptList.itemChanged.connect(self.renameFilterScript)
    self.filterBtnApplyScript.clicked.connect(self.applyFilters)
    self.filterBtnNewScript.clicked.connect(self.newFilterScript)
    self.filterBtnSaveScript.clicked.connect(self.saveFilterScript)
    self.filterBtnSaveScript.ctrlClicked.connect(self.saveAllFilterScripts)
    self.filterBtnReloadScript.clicked.connect(self.reloadFilterScript)
    self.filterBtnReloadScript.ctrlClicked.connect(self.reloadAllFilterScripts)
    self.filterBtnDelScript.clicked.connect(self.deleteFilterScript)
    self.filterBtnHelp.clicked.connect(self.showHelpWindow)

    self.filterScriptList.itemSelectionChanged.connect(self.setActiveFilterScript)
    self.filterScriptEdit.textChanged.connect(self.syncFilterScript)

    for seq, slot in [("Ctrl+S",      self.saveFilterScript),
                      ("Ctrl+Return", self.applyFilters),
                      ("Ctrl+Enter",  self.applyFilters)]:
      sc = QShortcut(QKeySequence(seq), self.filterScriptEdit)
      sc.setContext(Qt.ShortcutContext.WidgetShortcut)
      sc.activated.connect(slot)

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
    self.sigAppendItem.connect(self.updateDynamicFilters)
    self.sigAppendItem.connect(self.applyFilters)
    self.sigPurgeStale.connect(self.table.clearStale)
    self.sigSetStatus.connect(self.setStatus)
    allSplitters = newVSplitter([self.table, filtersContainer])
    allSplitters.setSizes([800,100])
   
    self.setLayout(newVLayout([allSplitters, newHLayout([self.btnRefresh, self.btnUse, self.btnStore, self.btnSell, self.btnDissolve, self.btnTrade, self.btnSort])]))
  
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
    self.table.staleData = {}

    noneItem = μFilterItem("<None>", "")
    noneItem.setFlags(noneItem.flags() & ~Qt.ItemFlag.ItemIsEditable)
    self.filterScriptList.addItem(noneItem)

    allFiles = glob.glob(os.path.join(P_DEFAULT_FILTERSDIR, "*"+P_DEFAULT_FILTEREXT))
    for n in allFiles:
      name = os.path.splitext(os.path.basename(n))[0]
      if name == "<None>": continue
      self.appendFilterScript(μFilterItem(name, ""))

    self.filterScriptList.setCurrentItem(noneItem)

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
          selectedItems[item.owner().lower()].append(item)
    return selectedItems
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E Q U E S T   U S E 
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestUse(self, confirm=False):
    self._requestUse(self.getSelectedIDs(), confirm)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def requestUseViaDoubleClick(self, item: μItemData):
    if item.column() != 0: return
    selectedItems = {b: [] for b in μMilvianMeta.getBridges().keys()}
    selectedItems[item.owner().lower()].append(item)
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
      μPrint.info(f"[cStorage] Finished using requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[cStorage] Error using items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      used = packet.outData[0]
      iID = struct.unpack('<Q', packet.outData[1:9])[0]
      μPrint.info(f"[cStorage] {"used" if used else "failed to use"} {C_ORANGE}{iID}</font>")

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
      μPrint.info(f"[cStorage] Finished dissolving requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[cStorage] Error dissolving items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      dissolved = packet.outData[0]
      iID = struct.unpack('<Q',packet.outData[1:9])[0]
      μPrint.info(f"[cStorage] {"dissolved" if dissolved else "failed dissolving"} {C_ORANGE}{iID}</font>")

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
      μPrint.info(f"[cStorage] Finished storing requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[cStorage] Error storing items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      stored = packet.outData[0]
      iID = struct.unpack('<Q',packet.outData[1:9])[0]
      μPrint.info(f"[cStorage] {"stored" if stored else "failed to store"} {C_ORANGE}{iID}</font>")

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
      μPrint.info(f"[cStorage] Finished selling requested items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    elif packet.status == packetStatus.error:
      μPrint.error(f"[cStorage] Error selling items for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
      self.sigSetStatus.emit(packet.bridge, P_STATUS_IDLE)
    else:
      iID = struct.unpack('<Q',packet.outData[0:8])[0]
      μPrint.info(f"[cStorage] sold {C_ORANGE}{iID}</font>")

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
      self.table.staleData[bridge.charName] = []
      p = μMilvianPacket(packetCommand.examineItems, bridge, inData)
      p.χigResponse.connect(lambda data, p=p: self.storageStatusUpdate(p, data))
      bridge.send(p)
      self.refreshStorage(bridge)
  

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  R E F R E S H   S T U F F
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def requestRefreshStorage(self, detailed: bool = False, delay: int = P_DEFAULT_EXAMINE_DELAY):
    printStatus = True                        # for now always true
    inData  = struct.pack('?', detailed)      # provide detailed information
    inData += struct.pack('?', printStatus)   # provide status updates
    inData += struct.pack('<I', delay)        # ms delay between examines (only used when detailed=True)

    self.table.staleData = {}
    for bridge in μMilvianMeta.getBridges().values():
      bridge : μMilvian
      try: os.remove(f'/dev/shm/milvian/{bridge.charName.lower()}/inventory.bin')
      except: pass
      self.table.staleData[bridge.charName] = []
      p = μMilvianPacket(packetCommand.queryinventory, bridge, inData)
      p.χigResponse.connect(lambda data, p=p: self.storageStatusUpdate(p, data))
      bridge.send(p)
      self.refreshStorage(bridge)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def storageStatusUpdate(self, packet : μMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      μPrint.info(f"[cStorage] Finished refreshing storage for {C_SILVER}{packet.bridge.charName}</font>")
      packet.χigResponse.disconnect()
    else:
      μPrint.info(f"[cStorage] {C_ORANGE}{packet.outData.decode('utf-8', errors='replace')}</font>")
    # cDispatcher.fulfill((packet.bridge.id, packet.id, packetSignal.running), packet.bridge)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def refreshStorage(self, bridge : μMilvian):
    self.table.staleData[bridge.charName] = []
    for i in range(self.table.rowCount()):
      if self.table.item(i,P_ITEM_COLUMNS.index("Owner")).text() == bridge.charName:
        self.table.staleData[bridge.charName].append(self.table.item(i,P_ITEM_COLUMNS.index("Name")))
    
    def _refreshStorageThread(self : μStorage, bridge : μMilvian):
      filename = f'/dev/shm/milvian/{bridge.charName.lower()}/inventory.bin'
      while not os.path.exists(filename) or os.path.getsize(filename) < 13:
        time.sleep(0.1)

      with open(filename, 'rb') as f:
        requestId  = struct.unpack('<I', f.read(4))[0]
        nItems     = struct.unpack('<I', f.read(4))[0]
        itemAvail  = struct.unpack('<I', f.read(4))[0]
        favail     = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        itemsCount = 0
        while True:
          itemAvail = struct.unpack('<I', favail[8:12])[0]
          if itemAvail > itemsCount:
            item = μItemData()
            try:
              item.readFromBin(f)
            except Exception as e:
              μPrint.error(f"[cStorage] readFromBin failed at item {itemsCount}/{nItems}:", e)
              break
            itemsCount += 1
            item.digest()
            self.sigAppendItem.emit(item)
          else:
            time.sleep(0.05)
          if itemsCount>=nItems: break
      self.sigSetStatus.emit(bridge, P_STATUS_IDLE)
      self.sigPurgeStale.emit(bridge.charName)

    self.setStatus(bridge, P_STATUS_BUSY_REFRESH)
    t = threading.Thread(target=_refreshStorageThread, args=(self, bridge), daemon=True)
    t.start()
  
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  F I L T E R   S T U F F
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def applyFilters(self, item : μItemData = None):
    scriptText = self.filterScriptEdit.toPlainText().lower()
    scriptText = " ".join(scriptText.strip().split())

    safeContext = {
      "__builtins__": {},
      # Common functions
      "len": len,
      "any": any,
      "all": all,
      "true": True,
      "false": False,
      "str": μString,
      "int": int,
      "float": float,

      # String helpers (very useful for items)
      "file":    lambda name: fileContents(P_DEFAULT_FILTERSDIR+"/"+name+".list"),
    }

    filterText = self.filterText.text().lower().strip()
    checkedOwners = [q.lower() for q in self.filterOwner.getChecked()]
    checkedTypes  = [q.lower() for q in self.filterType.getChecked()]
    checkedQuals  = [q.lower() for q in self.filterQualifier.getChecked()]
    checkedAugs   = [q.lower() for q in self.filterAugments.getChecked()]

    def _filterItem(item : μItemData):
      # --- script filter (runs first)
      if len(scriptText) > 0:
        try:
          S = μString
          itemContext = {
            "id"              : item._id               ,
            "name"            : S(item._name.lower())  ,
            "ownerid"         : item._ownerID          ,
            "owner"           : S(item.owner().lower()),
            # "container"       : item._container      ,
            "weenieid"        : item._weenieID       ,
            "type"            : S(item._type.lower())  ,
            "quantity"        : item._quantity       ,
            "qualifier"       : S(item._qualifier.lower()),
            "valuecopper"     : item._valueCopper    ,
            "hardness"        : item._hardness       ,
            "durability"      : item._durability     ,
            "iconid"          : item._iconId         ,
            "icon"            : item._icon           ,
            "description"     : S(item._description.lower()),
            "minlevel"        : item._minLevel       ,
            "material"        : item._material       ,
            "isJunk"          : item._isJunk        ,
            "islocked"        : item._isLocked       ,
            "issellable"      : item._isSellable     ,
            "isminorartifact" : item._isMinorArtifact,
            "setbonus1"       : S(item._setBonus1.lower()),
            "setbonus2"       : S(item._setBonus2.lower()),
            "currentslot"     : item._currentSlot    ,
            "isequipped"      : isinstance(item.slot(), str),
            "binding"         : S("unbound" if item._binding==0 else item.binding()),
            "equipsto"        : S(item._equipsTo.lower()),
            "augments"        : [S(a.lower()) for a in item.augments()],
            "effects"         : {k.lower(): S(v.lower()) for k, v in item._effects.items()},
            "slot"            : item.slot(),
            "effectname"      : [S(k.lower()) for k in item._effects.keys()],
            "effectdesc"      : [S(v.lower()) for v in item._effects.values()],
            "effectfull"      : S(" ".join([k.lower() + " " + v.lower() for k, v in item._effects.items()])),
            "text"            : S(item.toolTip().lower().replace("<br>","").replace("<b>","").replace("</b>","").replace("<i>","").replace("</i>",""))
          }
          itemContext.update(safeContext)
          if not bool(eval(scriptText, itemContext)):
            return self.table.setRowHidden(row, True)
        except Exception as e:
          μPrint.error("[cStorage]: error while evaluating filter script:",e)
          return

      # --- checkbox filter (runs after script passes)
      textTarget = ""
      if self.filterCB.name.isChecked(): textTarget += item._name.lower() + " "
      if self.filterCB.description.isChecked(): textTarget += item.toolTip().lower() + " "

      if not (filterText=="" or filterText in textTarget): return self.table.setRowHidden(row, True)

      isEquipped = isinstance(item.slot(), str)
      if not self.filterCB.equipped.isChecked()   and     isEquipped: return self.table.setRowHidden(row, True)
      if not self.filterCB.unequipped.isChecked() and not isEquipped: return self.table.setRowHidden(row, True)

      if not self.filterCB.bound.isChecked()   and item._binding>0:  return self.table.setRowHidden(row, True)
      if not self.filterCB.unbound.isChecked() and item._binding==0: return self.table.setRowHidden(row, True)

      if not self.filterCB.locked.isChecked()   and item._isLocked==1: return self.table.setRowHidden(row, True)
      if not self.filterCB.unlocked.isChecked() and item._isLocked==0: return self.table.setRowHidden(row, True)

      if not self.filterCB.sellable.isChecked()   and item._isSellable==1: return self.table.setRowHidden(row, True)
      if not self.filterCB.unsellable.isChecked() and item._isSellable==0: return self.table.setRowHidden(row, True)

      itemAugs = [a for a in item.augments(textOnly=True) if a.lower() in checkedAugs]
      if len(itemAugs) == 0 and not self.filterCB.aug0.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) == 1 and not self.filterCB.aug1.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) == 2 and not self.filterCB.aug2.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) >= 3 and not self.filterCB.aug3p.isChecked(): return self.table.setRowHidden(row, True)

      qualKey = item._qualifier.lower() if item._qualifier else "<empty>"
      if qualKey not in checkedQuals: return self.table.setRowHidden(row, True)
      if item.owner().lower()    not in checkedOwners: return self.table.setRowHidden(row, True)
      if item._type.lower()      not in checkedTypes:  return self.table.setRowHidden(row, True)

      self.table.setRowHidden(row, False)

    if isinstance(item, μItemData):
      try:
        row = item.row()
      except RuntimeError:
        return  # Qt object was deleted before we could use it
      _filterItem(item)
    else:
      for row in range(self.table.rowCount()):
        _filterItem(self.table.item(row, 0))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def newFilterScript(self):
    i = 1
    while f"NewSet{i}" in self.allFilterScripts:
      i += 1
    newFilter = μFilterItem(f"NewSet{i}", "")
    newFilter.save()
    self.appendFilterScript(newFilter)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def appendFilterScript(self, filter : μFilterItem):
    if filter.name in self.allFilterScripts: return
    filter.load()
    self.allFilterScripts[filter.name] = filter
    self.filterScriptList.addItem(filter)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def renameFilterScript(self, item : μFilterItem):
    if item.name == "<None>": return
    oldName = item.name
    item.rename()
    self.allFilterScripts[item.name] = item
    del self.allFilterScripts[oldName]
    
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setActiveFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    isEditable = bool(cfilter) and cfilter[0].name != "<None>"
    self.filterScriptEdit.setEnabled(isEditable)
    self.filterBtnApplyScript.setEnabled(isEditable)
    self.filterBtnDelScript.setEnabled(isEditable)
    self.filterScriptEdit.setText(cfilter[0].content if isEditable else "")
    self.applyFilters()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0 and cfilter[0].name != "<None>": cfilter[0].save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveAllFilterScripts(self):
    for f in self.allFilterScripts.values():
      f.save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def syncFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0 and cfilter[0].name != "<None>":
      cfilter[0].sync(self.filterScriptEdit.toPlainText())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def reloadFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0 and cfilter[0].name != "<None>":
      cfilter[0].load()
    self.setActiveFilterScript()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def reloadAllFilterScripts(self):
    for f in self.allFilterScripts.values():
      f.load()
    self.setActiveFilterScript()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def deleteFilterScript(self):
    selected = self.filterScriptList.selectedItems()
    if not selected: return
    filter : μFilterItem = selected[0]
    μPrint.info(f"Removing filter script \"{C_SILVER}{filter.name}</font>\"...")
    self.allFilterScripts.pop(filter.name, None)
    filename = P_DEFAULT_FILTERSDIR + os.sep + filter.name + P_DEFAULT_FILTEREXT
    try:
      os.remove(filename)
    except FileNotFoundError:
      pass
    except OSError as e:
      μPrint.error(f"[cStorage] failed to remove filter file \"{filename}\":", e)
    self.filterScriptList.takeItem(self.filterScriptList.row(filter))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def updateDynamicFilters(self, item: μItemData):
    if item.owner():
      self.filterOwner.addCheckItem(item.owner())
    if item._type:
      self.filterType.addCheckItem(item._type)
    if item._qualifier:
      self.filterQualifier.addCheckItem(item._qualifier)

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  O T H E R
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def showHelpWindow(self):
    dlg = QDialog(self)
    dlg.setWindowTitle("Shortcuts Help")
    layout = QVBoxLayout(dlg)
    text = QTextEdit()
    text.setReadOnly(True)
    help_text = f"""
    <h2>How to Use</h2>
    <br>You can save useful scripts and recall them again later. This is only available for text filters, not for the checkboxes.
    <br>
    <br> Filter scripts are evaluated as basic Python scripts. They must return a bool (True or False). 
    Everything is case insenstitive for the sake of simplicity. Example:
    <br>        (name.startswith("potion") and qualifier == "vendor")
    <br><h2>Valid identifiers:</h2>
    <br> ● id: int             
    <br> ● name: str
    <br> ● ownerid: int
    <br> ● owner: str   
    <br> ● container: str 
    <br> ● weenieid: id
    <br> ● type: str   
    <br> ● quantity: int      
    <br> ● qualifier: str  
    <br> ● valuecopper: int 
    <br> ● hardness: str
    <br> ● durability: int  
    <br> ● iconid: int
    <br> ● icon: an image, don't use this    
    <br> ● description: str
    <br> ● minlevel: int
    <br> ● material: str  
    <br> ● istrash: bool  
    <br> ● islocked: bool  
    <br> ● isminorartifact: bool
    <br> ● setbonus1: str
    <br> ● setbonus2: str 
    <br> ● currentslot: int
    <br> ● binding: str ("unbound", "BtC", "BtCoE", etc)
    <br> ● equipsto: str   
    <br> ● augments: list
    <br> ● effects: dictionary[effectName] = effectDesc
    <br> ● slot: str
    <br> ● effectname: list
    <br> ● effectdesc: list
    <br> ● effectfull: [effectName + effectDesc]
    <br> ● text: the full text displayed in the tooltip - includes name, descritpion, material, qualifier, effects  
    <br><h2>Valid Python functions:</h2>
    <br> ● len()
    <br> ● any()
    <br> ● all()
    <br> ● str()
    <br> ● int()
    <br> ● float()
    <br> ● startswith()
    <br> ● endswith()
    <br> ● contains: (an alias; A contains B translates to B in A)
    <h2>Buttons</h2>
    <br> ● <b>Apply filter:</b> click this to apply the filter whose text is being displayed (regardless if it is saved or not)
    <br> ● <b>New filter:</b> creates a new filter with the text currently being displayed in the text box
    <br> ● <b>Save filter:</b> filters are not saved automatically by construction. Click this to save the current filter into a file
    <br> ● <b>Delete filter:</b> removes the filter and its file from the disk. This action cannot be undone!
    <br> ● <b>Reload filter:</b> discard changes and reload the last saved values for this filter
    <h2>Tips</h2>
    <br> ● To disable filtering, just clear the text box (ctrl+a, del) and click "apply"
    <br> ● It helps to have a filter for dissolving, one for selling, one for feeding, etc
    <br> ● Right-click or Ctrl+Click "Save" or "Reload" to apply the action to all filters
    <br> ● Use descriptive names for filters for easier management.
    <br> ● All filters are stored as text files in {P_DEFAULT_FILTERSDIR} and can be modified by any program. This is a security issue, if you believe in security issues, btw 🦄. Use at your own risk! 
    <br> ● Scripts execution use some "safe context", so security issues should not be an issue™

    <br>If you need further support, good luck.
    """
    text.setHtml(help_text)

    layout.addWidget(text)
    dlg.setLayout(layout)
    dlg.resize(400, 300)
    dlg.exec()

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  F I L T E R   I T E M
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μFilterItem(QListWidgetItem):
  def __init__(self, name : str, content : str):
    super().__init__()
    self.name = name
    self.setText(name)
    self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)
    self.content = content

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setActive(self, val : bool ):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def rename(self):
    oldFilename = P_DEFAULT_FILTERSDIR + os.sep + self.name + P_DEFAULT_FILTEREXT
    newFilename = P_DEFAULT_FILTERSDIR + os.sep + self.text() + P_DEFAULT_FILTEREXT
    os.rename(oldFilename, newFilename)
    self.name = self.text()
    
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def sync(self, content):
    self.content = content

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def display(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def save(self):
    filename = P_DEFAULT_FILTERSDIR + os.sep + self.text() + P_DEFAULT_FILTEREXT
    os.makedirs(P_DEFAULT_FILTERSDIR, exist_ok=True)
    with open(filename, 'w') as f:
      f.write(self.content)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def load(self):
    filename = P_DEFAULT_FILTERSDIR + os.sep + self.text() + P_DEFAULT_FILTEREXT
    try:
      with open(filename,"r") as f:
        self.content = f.read()
    except Exception as e:
      μPrint.error(f"{C_RED}WARNING:</font> error loading filter from \"{filename}\"",e)
      self.content = ""