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
from PyQt6.QtWidgets import QCheckBox, QDialog, QLineEdit, QListWidgetItem, QMenu, QListWidget, QTextEdit
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.cOrb import cOrb, cOrbCheck, cOrbSmall
from helpers.util import *
from widgets.cToggler import cToggler
from widgets.cCheckCombo import cCheckCombo
from widgets.cItemsTable import *
from helpers.cMilvianPacket import cMilvianPacket, packetCommand, packetStatus, packetSignal
from helpers.cDispatcher import cDispatcher
from helpers.cPrint import cPrint
import time, struct, mmap
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMacrosDaemon import cMacrosDaemon
   from cMilvian import cMilvian


#---------------------------------------------------------------------------------------------------------------
#
#
#                                         F I L T E R   I T E M 
#
#                                  
#---------------------------------------------------------------------------------------------------------------
class cFilterItem(QListWidgetItem):
  def __init__(self, name : str, content : str):
    super().__init__()
    self.name = name
    self.setText(name)
    self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)
    self.content = content

  #----------------------------------------------------------------------------------------------------------
  def setActive(self, val : bool ):
    pass

  #----------------------------------------------------------------------------------------------------------
  def rename(self):
    oldFilename = P_DEFAULT_FILTERSDIR + os.sep + self.name + P_DEFAULT_FILTEREXT
    newFilename = P_DEFAULT_FILTERSDIR + os.sep + self.text() + P_DEFAULT_FILTEREXT
    os.rename(oldFilename, newFilename)
    self.name = self.text()
    
  #----------------------------------------------------------------------------------------------------------
  def sync(self, content):
    self.content = content

  #----------------------------------------------------------------------------------------------------------
  def display(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    filename = P_DEFAULT_FILTERSDIR + os.sep + self.text() + P_DEFAULT_FILTEREXT
    os.makedirs(P_DEFAULT_FILTERSDIR, exist_ok=True)
    with open(filename, 'w') as f:
      f.write(self.content)

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    filename = P_DEFAULT_FILTERSDIR + os.sep + self.text() + P_DEFAULT_FILTEREXT
    try:
      with open(filename,"r") as f:
        self.content = f.read()
    except Exception as e:
      cPrint.error(f"{C_RED}WARNING:</font> error loading filter from \"{filename}\"",e)
      self.content = ""


#---------------------------------------------------------------------------------------------------------------
#
#
#                                            S T O R A G E   M A N A G E R 
#
#                                  
#---------------------------------------------------------------------------------------------------------------
class cStorageManager(cToggler):
  sigAppendItem  = pyqtSignal(cItemData)
  sigPurgeStale  = pyqtSignal(str)
  sigSetStatus = pyqtSignal(object,int)
  widgetID = "StorageManager"
  daemon : cMacrosDaemon = None
  status : dict = {}
  allFilterScripts : dict = {}

  def __init__(self, main):
    self.main = main
    super().__init__("Storage\nManager", P_ICON_CHEST)
    self.toggler.setToolTip("Toggle StorageManager UI<br><b><i>NOT IMPLEMENTED</i></b>")
    self.table = cItemsTable(self)
    
    # self.btnLoad        = cOrb(icon=P_ICON_TRIANGLE_DOWN, tooltip="Load storage data from file")
    self.btnRefresh   = cOrb("Refresh",     icon=P_ICON_REFRESH, tooltip="Fetch data from running clients and display in the viewer.<br><b>Ctrl+Click</b> to examine items and get more detailed data.<br><i>Right-click for more options</i>")
    self.btnFeedJewel = cOrb("Feed\nJewel", icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_dissolve_lean.svg'),
                             tooltip="Feeds selected items into a sentient jewel. You must manually open the jewel UI.")
    self.btnDissolve  = cOrb("Dissolve",    icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_dissolve_lean.svg'),
                             tooltip="Dissolve all selected items. Item Deconstruction UI must be open. <br><b>Ctrl+Click</b> to skip confirmation<b>.")
    self.btnSell      = cOrb("Sell",        icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_vendor_lean.svg'),
                             tooltip="Sell all selected items to the currently open vendor UI. <br><b>Ctrl+Click</b> to repair equipment too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnTrade     = cOrb("Trade",       icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_trade_lean.svg'),
                             tooltip="Trade selected items with selected player. <br><b>Ctrl+Click</b> to add platinum too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnStore     = cOrb("Store",       icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_bank_lean.svg'),
                             tooltip="Store selected items in the currently open bank/chest UI. <br><b><i>Right-click for more options</i></b>")

    self.filterCB = SimpleNamespace()
    for f in ["Equipped", "Unequipped", "Unbound", "Bound", "Locked", "Unlocked", "Name", "Description"]:
      setattr(self.filterCB, f.lower(), cOrbCheck(f))
    self.filterCB.aug0  = cOrbCheck('0')
    self.filterCB.aug1  = cOrbCheck('1')
    self.filterCB.aug2  = cOrbCheck('2')
    self.filterCB.aug3p = cOrbCheck('3+')

    for cb in self.filterCB.__dict__.keys():
      getattr(self.filterCB, cb).setChecked(True)
      getattr(self.filterCB, cb).stateChanged.connect(self.applyFilters)
    
    self.filterQualifier = cCheckCombo("Qualifier")
    for q in ["Named", "Vendor", "Random", "Raid"]:
      self.filterQualifier.addCheckItem(q)

    self.filterAugments = cCheckCombo("Augments")
    for q in P_ITEM_AUGMENTS_NAME.values():
      self.filterAugments.addCheckItem(q)

    self.filterOwner = cCheckCombo("Owner")
    self.filterType  = cCheckCombo("Type")
    self.filterText = QLineEdit()
    
    advFilters = newVFrame([newHLayout(["Filter by...", self.filterText]),
                            newHLayout(["__stretch__", self.filterCB.name, self.filterCB.description, "__stretch__"]),
                            "__line__",
                            newHLayout([self.filterCB.equipped, self.filterCB.bound, self.filterCB.locked]), 
                            newHLayout([self.filterCB.unequipped, self.filterCB.unbound, self.filterCB.unlocked]),
                            newHFrame(["Augments Count:", self.filterCB.aug0, self.filterCB.aug1, self.filterCB.aug2, self.filterCB.aug3p]),
                            newHLayout([self.filterQualifier, self.filterAugments, self.filterOwner, self.filterType])])

    self.filterScriptList      = QListWidget()
    self.filterScriptLabel     = QLabel("Selected Filter Script:")
    self.filterBtnNewScript    = cOrbSmall(icon=P_ICON_NEWDOC, tooltip="Create a new filter script with the text currently in the editor")
    self.filterBtnSaveScript   = cOrbSmall(icon=P_ICON_SAVE, tooltip="Save currently selected filter script\nCtrl+Left click to save all")
    self.filterBtnDelScript    = cOrbSmall(icon=P_ICON_TRASH, tooltip="Delete currently selected filter script - this action cannot be undone!")
    self.filterBtnReloadScript = cOrbSmall(icon=P_ICON_REFRESH, tooltip="Reload currently selected script from file\nCtrl+Left click to reload all")
    self.filterBtnApplyScript  = cOrbSmall(icon=P_ICON_FILTER, tooltip="Apply current filter")
    self.filterBtnHelp         = cOrbSmall(icon=P_ICON_QUESTION, tooltip="Show a comprehensive help on how script work here (lol)")
    self.filterScriptEdit      = QTextEdit()
    filtersContainer = newHSplitter([newHFrame([newVLayout(["Saved Filters:", self.filterScriptList]),
                                  newVFrame(["__stretch__",self.filterBtnApplyScript, self.filterBtnNewScript, self.filterBtnSaveScript,self.filterBtnDelScript, self.filterBtnReloadScript, self.filterBtnHelp, "__stretch__"])]),
                                  newVFrame([self.filterScriptLabel, self.filterScriptEdit]), advFilters])
    filtersContainer.setSizes([300,700,100])


    self.filterQualifier.changed.connect(self.applyFilters)
    self.filterOwner.changed.connect(self.applyFilters)
    self.filterType.changed.connect(self.applyFilters)
    self.filterText.textEdited.connect(self.applyFilters)

    self.btnRefresh.clicked.connect(lambda : self.requestRefreshStorage(False))
    self.btnRefresh.ctrlClicked.connect(lambda : self.requestRefreshStorage(True))
    self.btnDissolve.clicked.connect(self.requestRefreshStorage)
    self.btnFeedJewel.clicked.connect(self.requestFeedJewel)
    self.btnFeedJewel.ctrlClicked.connect(lambda : self.requestFeedJewel(force=True))
    self.btnRefresh.ctrlClicked.connect(lambda : self.requestRefreshStorage(True))

    self.filterScriptList.itemChanged.connect(self.renameFilterScript)
    self.filterBtnApplyScript.clicked.connect(self.applyScriptFilters)
    self.filterBtnNewScript.clicked.connect(self.newFilterScript)
    self.filterBtnSaveScript.clicked.connect(self.saveFilterScript)
    self.filterBtnSaveScript.ctrlClicked.connect(self.saveAllFilterScripts)
    self.filterBtnReloadScript.clicked.connect(self.reloadFilterScript)
    self.filterBtnReloadScript.ctrlClicked.connect(self.reloadAllFilterScripts)
    self.filterBtnDelScript.clicked.connect(self.deleteFilterScript)
    self.filterBtnHelp.clicked.connect(self.showHelpWindow)

    self.filterScriptList.itemSelectionChanged.connect(self.setActiveFilterScript)
    self.filterScriptEdit.textChanged.connect(self.syncFilterScript)

    # self.setListWidget.itemChanged.connect(self.updateMacroSetFile)
    # self.setListWidget.itemSelectionChanged.connect(self.updateTable)

    self.sigAppendItem.connect(self.table.append)
    self.sigAppendItem.connect(self.applyFilters)
    self.sigAppendItem.connect(self.updateDynamicFilters)
    self.sigPurgeStale.connect(self.table.clearStale)
    self.sigSetStatus.connect(self.setStatus)
    allSplitters = newVSplitter([self.table, filtersContainer])
    allSplitters.setSizes([400,100])
   
    self.setLayout(newVLayout([allSplitters, newHLayout([self.btnRefresh, self.btnStore, self.btnTrade, self.btnSell, self.btnDissolve, self.btnFeedJewel])]))
  
  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, bridge, newStatus):
    if newStatus == P_STATUS_IDLE:
      if bridge in self.status: del self.status[bridge]
      if len(self.status)>0: newStatus=list(self.status.values())[0]
    else:
      self.status[bridge]=newStatus

    if newStatus == P_STATUS_BUSY_REFRESH:
      self.btnRefresh.setEnabled(True)
      self.btnDissolve.setEnabled(False)
      self.btnSell.setEnabled(False)
      self.btnTrade.setEnabled(False)
      self.btnStore.setEnabled(False)
    elif newStatus == P_STATUS_BUSY_DISSOLVE:
      self.btnRefresh.setEnabled(False)
      self.btnDissolve.setEnabled(True)
      self.btnSell.setEnabled(False)
      self.btnTrade.setEnabled(False)
      self.btnStore.setEnabled(False)
    elif newStatus == P_STATUS_BUSY_SELL:
      self.btnRefresh.setEnabled(False)
      self.btnDissolve.setEnabled(False)
      self.btnSell.setEnabled(True)
      self.btnTrade.setEnabled(False)
      self.btnStore.setEnabled(False)
    elif newStatus == P_STATUS_BUSY_TRADE:
      self.btnRefresh.setEnabled(False)
      self.btnDissolve.setEnabled(False)
      self.btnSell.setEnabled(False)
      self.btnTrade.setEnabled(True)
      self.btnStore.setEnabled(False)
    elif newStatus == P_STATUS_BUSY_STORE:
      self.btnRefresh.setEnabled(False)
      self.btnDissolve.setEnabled(False)
      self.btnSell.setEnabled(False)
      self.btnTrade.setEnabled(False)
      self.btnStore.setEnabled(False)
      self.btnStore.setEnabled(True)
    elif newStatus == P_STATUS_IDLE:
      self.btnRefresh.setEnabled(True)
      self.btnDissolve.setEnabled(True)
      self.btnSell.setEnabled(True)
      self.btnTrade.setEnabled(True)
      self.btnStore.setEnabled(True)
      self.btnStore.setEnabled(True)

  #----------------------------------------------------------------------------------------------------------
  def initialize(self, daemon : cMacrosDaemon):
    self.daemon = daemon
    self.table.staleData = {}

    allFiles = glob.glob(os.path.join(P_DEFAULT_FILTERSDIR, "*"+P_DEFAULT_FILTEREXT))
    for n in allFiles:
      name = os.path.splitext(os.path.basename(n))[0]
      self.appendFilterScript(cFilterItem(name, ""))

  #----------------------------------------------------------------------------------------------------------
  def newFilterScript(self):
    i = 1
    while f"NewSet{i}" in self.allFilterScripts:
      i += 1
    newFilter = cFilterItem(f"NewSet{i}", "")
    newFilter.save()
    self.appendFilterScript(newFilter)

  #----------------------------------------------------------------------------------------------------------
  def appendFilterScript(self, filter : cFilterItem):
    if filter.name in self.allFilterScripts: return
    filter.load()
    self.allFilterScripts[filter.name] = filter
    self.filterScriptList.addItem(filter)

  #----------------------------------------------------------------------------------------------------------
  def renameFilterScript(self, item : cFilterItem):
    oldName = item.name
    item.rename()
    self.allFilterScripts[item.name] = item
    del self.allFilterScripts[oldName]
    
  #----------------------------------------------------------------------------------------------------------
  def setActiveFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0:
      self.filterScriptEdit.setText(cfilter[0].content)
    else:
      self.filterScriptEdit.setText("")

  #----------------------------------------------------------------------------------------------------------
  def saveFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0: cfilter[0].save()

  #----------------------------------------------------------------------------------------------------------
  def saveAllFilterScripts(self):
    for f in self.allFilterScripts.values():
      f.save()

  #----------------------------------------------------------------------------------------------------------
  def syncFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0: cfilter[0].sync(self.filterScriptEdit.toPlainText())

  #----------------------------------------------------------------------------------------------------------
  def reloadFilterScript(self):
    cfilter = self.filterScriptList.selectedItems()
    if len(cfilter)>0:
      cfilter[0].load()
    self.setActiveFilterScript()

  #----------------------------------------------------------------------------------------------------------
  def reloadAllFilterScripts(self):
    for f in self.allFilterScripts.values():
      f.load()
    self.setActiveFilterScript()

  #----------------------------------------------------------------------------------------------------------
  def deleteFilterScript(self):
    filter = self.filterScriptList.selectedItems()
    if not filter: return
    cPrint.info(f"Removing filter script \"{C_SILVER}{filter[0].text()}</font>\"...")
    del self.allFilterScripts[filter[0].text()]
    try:
      os.remove(P_DEFAULT_MACRODIR+os.sep+filter[0].text()+P_DEFAULT_MACROEXT)
    except:
      pass
    self.filterScriptList.takeItem(self.filterScriptList.row(filter[0]))
    del filter[0]

  #----------------------------------------------------------------------------------------------------------
  def updateDynamicFilters(self, item: cItemData):
    if item._ownerName:
      self.filterOwner.addCheckItem(item._ownerName)
    if item._type:
      self.filterType.addCheckItem(item._type)
    # if item._qualifier:
    #   self.filterQualifier.addCheckItem(item._qualifier)
  
  #----------------------------------------------------------------------------------------------------------
  def requestRefreshStorage(self, detailed: bool = False):
    printStatus = True                        # for now always true 
    inData = struct.pack('?', detailed)       # provide detailed information
    inData += struct.pack('?', printStatus)   # provide status updates

    self.table.staleData = {}
    for bridge in self.daemon.getBridges().values():
      bridge : cMilvian
      try: os.remove(f'/dev/shm/Milvian/InventoryData{bridge.id}.bin')
      except: pass
      self.table.staleData[bridge.charName] = []
      p = cMilvianPacket(packetCommand.queryinventory, bridge, inData)
      cDispatcher.connect((bridge.id, p.id, packetSignal.gotResponse), lambda data, p=p: self.storageStatusUpdate(p, data))
      # cDispatcher.fate((bridge.id, p.id, packetSignal.running), self.loadStorageData)
      bridge.sendRequest(p)
      self.refreshStorage(bridge)

  #----------------------------------------------------------------------------------------------------------
  def storageStatusUpdate(self, packet : cMilvianPacket, rawData : bytes):
    packet.status = packetStatus(rawData[4:8])
    packet.outData = rawData[12:]
    if packet.status == packetStatus.success:
      cPrint.info(f"[cStorage] Finished refreshing storage for {C_SILVER}{packet.bridge.charName}</font>")
      cDispatcher.disconnect((packet.bridge.id, packet.id, packetSignal.gotResponse))
    else:
      cPrint.info(f"[cStorage] {C_ORANGE}{packet.outData.decode('utf-8')}</font>")
    # cDispatcher.fulfill((packet.bridge.id, packet.id, packetSignal.running), packet.bridge)

  #----------------------------------------------------------------------------------------------------------
  def requestDeconstruct(self, force=False):
    # force ignores checks if item is deconstructeable e.g. named items cannot be deconstructed
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestStore(self, force=False):
    # force ignores checks if item is storeable e.g. bound items
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestTrade(self, force=False):
    # force ignores checks if item is tradeable e.g. bound items
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestSell(self, sellGems : bool = True, repair : bool = False):
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestFeedJewel(self, force=False):
    # force ignores checks if item is feedable e.g. random loot
    pass
  
  #----------------------------------------------------------------------------------------------------------
  def applyScriptFilters(self, item : cItemData = None):
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
      "str": str,
      "int": int,
      "float": float,

      # String helpers (very useful for items)
      "startswith": lambda s, prefix: str(s).startswith(str(prefix)),
      "endswith":   lambda s, suffix: str(s).endswith(str(suffix)),
      "contains":   lambda s, sub: str(sub) in str(s),
      # "lower": lambda x: str(x).lower() if x is not None else "",
      # "upper": lambda x: str(x).upper() if x is not None else "",
      # "startswith": lambda s, prefix: str(s).lower().startswith(str(prefix).lower()),
      # "endswith":   lambda s, suffix: str(s).lower().endswith(str(suffix).lower()),
      # "contains":   lambda s, sub: str(sub).lower() in str(s).lower(),   # bonus: allows "contains"
    }

    def _filterItem(item : cItemData):
      if len(scriptText)==0: 
        self.table.setRowHidden(row, False)
        return
      
      try:
        itemContext = {
          "id"              : item._id               ,    
          "name"            : item._name.lower()     ,
          "ownerid"         : item._ownerID          ,
          "ownername"       : item._ownerName.lower(),
          "container"       : item._container      ,
          "weenieid"        : item._weenieID       ,
          "type"            : item._type.lower()   ,
          "quantity"        : item._quantity       ,
          "qualifier"       : item._qualifier.lower(),
          "valuecopper"     : item._valueCopper    ,
          "hardness"        : item._hardness       ,
          "durability"      : item._durability     ,
          "iconid"          : item._iconId         ,
          "icon"            : item._icon           ,
          "description"     : item._description.lower(),
          "minlevel"        : item._minLevel       ,
          "material"        : item._material       ,
          "istrash"         : item._isTrash        ,
          "islocked"        : item._isLocked       ,
          "isminorartifact" : item._isMinorArtifact,
          "setbonus1"       : item._setBonus1.lower(),
          "setbonus2"       : item._setBonus2.lower(),
          "currentslot"     : item._currentSlot    ,
          "binding"         : "unbound" if item._binding==0 else item.binding(),
          "equipsto"        : item._equipsTo.lower(),
          "augments"        : [a.lower() for a in item.augments()],
          "effects"         : {k.lower(): v.lower() for k, v in item._effects.items()},
          "slot"            : item.slot(),
          "effectname"      : [k.lower() for k in item._effects.keys()],
          "effectdesc"      : [v.lower() for v in item._effects.values()],
          "effectfull"      : " ".join([k.lower() + " " + v.lower() for k, v in item._effects.items()]),
          "text"            : item.toolTip().lower().replace("<br>","").replace("<b>","").replace("</b>","").replace("<i>","").replace("</i>","")
        }
        itemContext.update(safeContext)
        result = eval(scriptText, itemContext)
        self.table.setRowHidden(row, not result)
        return bool(result)
      except Exception as e: raise(e)
        
    try:
      if isinstance(item, cItemData):
        row = item.row()
        _filterItem(item)
      else:
        for row in range(self.table.rowCount()):
          _filterItem(self.table.item(row, 0))
    except Exception as e:
      cPrint.error("[cStorage]: error while evaluating filter script:",e)

  
  #----------------------------------------------------------------------------------------------------------
  def applyFilters(self, item : cItemData = None):
    filterText = self.filterText.text().lower().strip()
    checkedOwners = self.filterOwner.getChecked()
    checkedTypes  = self.filterType.getChecked()
    checkedQuals  = self.filterQualifier.getChecked()
    checkedAugs   = self.filterAugments.getChecked()

    def _filterItem(item : cItemData):
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

      itemAugs = item.augments(textOnly=True)
      for a in list(itemAugs):
        if a not in checkedAugs: itemAugs.pop(itemAugs.index(a))
      if len(itemAugs) == 0 and not self.filterCB.aug0.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) == 1 and not self.filterCB.aug1.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) == 2 and not self.filterCB.aug2.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) >= 3 and not self.filterCB.aug3p.isChecked(): return self.table.setRowHidden(row, True)

      if item._qualifier not in checkedQuals:  return self.table.setRowHidden(row, True)
      if item._ownerName not in checkedOwners: return self.table.setRowHidden(row, True)
      if item._type      not in checkedTypes:  return self.table.setRowHidden(row, True)
      hasAug = False
      for a in itemAugs:
        hasAug = hasAug or (a in checkedAugs)
      if not hasAug: self.table.setRowHidden(row, True)

      self.table.setRowHidden(row, False)

    if isinstance(item, cItemData):
      row = item.row()
      _filterItem(item)
    else:
      for row in range(self.table.rowCount()):
        _filterItem(self.table.item(row, 0))
        

  #----------------------------------------------------------------------------------------------------------
  def refreshStorage(self, bridge : cMilvian):
    self.table.staleData[bridge] = []
    for i in range(self.table.rowCount()):
      if self.table.item(i,P_ITEM_COLUMNS.index("Owner")).text() == bridge.charName:
        self.table.staleData[bridge.charName].append(self.table.item(i,P_ITEM_COLUMNS.index("Name")))
    
    def _refreshStorageThread(self : cStorageManager, bridge : cMilvian):
      filename = f'/dev/shm/Milvian/InventoryData{bridge.id}.bin'
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
            item = cItemData()
            item.readFromBin(f)
            itemsCount += 1
            item.digest()
            self.sigAppendItem.emit(item)
          else:
            time.sleep(0.05)
          if itemsCount>=nItems: break
      self.sigSetStatus.emit(bridge, P_STATUS_IDLE)
      self.table.clearStale(bridge.charName)

    self.setStatus(bridge, P_STATUS_BUSY_REFRESH)
    t = threading.Thread(target=_refreshStorageThread, args=(self, bridge), daemon=True)
    t.start()
  
  #----------------------------------------------------------------------------------------------------------
  def showRefreshMenu(self):
    menu = QMenu(self)
    actRefresh  = QAction("Refresh",           self)
    actDetailed = QAction("Refresh (Detailed)", self)
    actPurge    = QAction("Purge All",          self)
    actCancel   = QAction("Cancel",             self)
    actCancel.setEnabled(False) # TODO implement
    actRefresh.triggered.connect(lambda: self.requestRefreshStorage(False))
    actDetailed.triggered.connect(lambda: self.requestRefreshStorage(True))
    actPurge.triggered.connect(self.table.clearAll)
    menu.addAction(actRefresh)
    menu.addAction(actDetailed)
    menu.addSeparator()
    menu.addAction(actPurge)
    menu.addSeparator()
    menu.addAction(actCancel)
    menu.exec(QCursor.pos())
  
  #----------------------------------------------------------------------------------------------------------
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
    <br> ● ownername: str   
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