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
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QListWidgetItem, QListWidget, QSplitter
from cWidgets.util import *
from cWidgets.cTab import cTab
from cWidgets.cButton import cButton, cLauncherButton
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import glob, re, os
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
from typing import TYPE_CHECKING
from cShortcutsDaemon import cShortcutsDaemon
from XHelper import XHelper
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

P_DEFAULT_SHORTCUTEXT = ".shortcut"

class cShortcutItem(QListWidgetItem):
  def __init__(self, parent : cShortcuts, name : str):
    super().__init__()
    self.parent = parent
    self.setText(name)
    self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
    self.setCheckState(Qt.CheckState.Unchecked)
    self.data = [["", "", "", ""]]

  #----------------------------------------------------------------------------------------------------------
  def setActive(self, val : bool ):
    if val:
      self.setCheckState(Qt.CheckState.Checked)
    else:
      self.setCheckState(Qt.CheckState.Unchecked)
    
  #----------------------------------------------------------------------------------------------------------
  def sync(self, row, column):
    while row >= len(self.data):
      self.data.append([None, None, None, None])
    modifiedCell = self.parent.table.item(row,column)
    self.data[row][column] = modifiedCell.text()

  #----------------------------------------------------------------------------------------------------------
  def display(self):
    table : QTableWidget = self.parent.table
    for row in self.data:
      pos = table.rowCount()
      table.insertRow(pos)
      icon_item = QTableWidgetItem()
      if row[0]:
        icon_item.setIcon(QIcon(row[0]))
      else:
        icon_item.setIcon(QIcon('/home/soul/share/μddo/images/ddo_themes/skill_icons/placeholder.png'))
      # table.setCellWidget(pos,0,QPushButton("D"))
      table.setItem(pos, 0, icon_item)
      table.setItem(pos, 1, QTableWidgetItem(str(row[1])))
      table.setItem(pos, 2, QTableWidgetItem(str(row[2])))
      table.setItem(pos, 3, QTableWidgetItem(str(row[3])))

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    filename = P_DEFAULT_SHORTCUTDIR + os.sep + self.text() + P_DEFAULT_SHORTCUTEXT
    json.dump(self.data, open(filename,'w'), cls=muJSONEncoder)

  #----------------------------------------------------------------------------------------------------------
  def removeRow(self, row : int):
    if row < len(self.data):
      self.data = self.data[:row] + self.data[row+1:]

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    filename = P_DEFAULT_SHORTCUTDIR + os.sep + self.text() + P_DEFAULT_SHORTCUTEXT
    try:
      with open(filename,"r") as f:
        self.data = json.load(f)
    except Exception as e:
      self.parent.main.console.error(f"{C_RED}WARNING:</font> error loading shortcut set from \"{filename}\"",e)
      self.data = []

  #----------------------------------------------------------------------------------------------------------
  def consolidate(self, consolidated = {}, aliases = {}) -> dict:
    # Shortcuts format:
    #     [<icon>, <name>, <hotkey>, <scripts>]
    # Scripts are of the form: 
    #     <script1>; <script2>; <script3>; 
    # Each script should be formatted as:
    #     <target1>, <target2>, <target3>: <action1>, <action2>, <action3>
    # If <target> is missing, "self" is assumed (useful for macros)
    # A special target "all" is provided for firing the shortcut to all running DDO processes
    # Actions:
    #   - sleep X: wait for X seconds
    #   - anything else: interpreted as key presses
    # Scripts are all started at the same time whenever their shortcut is pressed
    for row in self.data:
      hotkey  = row[2]
      for k,a in aliases.items():
        hotkey = hotkey.replace(k,a)
      hotkey  = (hotkey.replace(" ", "")).lower()
      scripts = row[3]
      for k,a in aliases.items():
        scripts = scripts.replace(k,a)
      scripts = [e.strip() for e in (scripts).split(";") if e.strip()]

      if hotkey in consolidated.keys():
        cs = consolidated[hotkey]
      else:
        cs = {}

      for s in scripts:
        s = s.split(':')
        if len(s) == 1:
          targets = ["self"]
        else:
          targets = (s.pop(0)).split(',')
          targets = [t.strip().lower() for t in targets]
        actions = s[0].split(',')
        actions = [a.strip() for a in actions]
        
        for t in targets:
          if t in cs.keys():
            cs[t] += actions
          else:
            cs[t] = actions
    
    # todo: check if "all" is scripting the same action; if yes, then the individual characters don't need to do it by themselves
      consolidated[hotkey] = cs
    return consolidated
  
#----------------------------------------------------------------------------------------------------------  
class cMacroLists(QListWidgetItem):
  def __init__(self, parent : cShortcuts):
    super().__init__()
    self.parent = parent

#----------------------------------------------------------------------------------------------------------
class cShortcuts(cTab):
  def __init__(self, main : cMainWindow):
    super().__init__("&Shortcuts")
    v = QVBoxLayout()
    self.initialized = False
    self.toActivate = None
    self.main = main

    self.btnDaemonToggle = cLauncherButton("&Shortcuts\nDaemon", tooltip="Toggle on/off all shortcuts from all active sets")
    self.btnDaemonToggle.setIcon(QIcon(QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/ShortcutDaemonIcon64.png')))

    self.btnNewSet      = cButton(icon=P_ICON_NEWDOC, tooltip="Create a new set of shortcuts")
    self.btnSaveSet     = cButton(icon=P_ICON_SAVE, tooltip="Save currently selected set to a file\nCtrl+Left click or Right click to save all")
    self.btnDeleteSet   = cButton(icon=P_ICON_TRASH, tooltip="Delete currently selected set - this action cannot be undone!")
    self.btnReloadSet   = cButton(icon=P_ICON_REFRESH, tooltip="Reload currently selected set from file\nCtrl+Left click or Right click to reload all")
    self.btnAddEntry    = cButton(icon=P_ICON_ADD, tooltip="Add a new shortcut to the currently selected set")
    self.btnRemoveEntry = cButton(icon=P_ICON_REMOVE, tooltip="Remove the currently selected shortcut from the currently selected set")
    self.btnHelp        = cButton(icon=P_ICON_QUESTION, tooltip="Show a comprehensive help on how shortcuts work here (lol)")

    self.btnAddAlias    = cButton(icon=P_ICON_ADD, tooltip="Add a new alias")
    self.btnRemoveAlias = cButton(icon=P_ICON_REMOVE, tooltip="Remove the currently selected alias")
    self.btnSaveAlias   = cButton(icon=P_ICON_SAVEALL, tooltip="Save all aliases to file")
    self.btnReloadAlias = cButton(icon=P_ICON_REFRESH, tooltip="Reload all aliases from file")
    
    self.btnDaemonToggle.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)

    self.btnNewSet.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
    self.btnSaveSet.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
    self.btnDeleteSet.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
    self.btnReloadSet.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
    
    self.shortcutListWidget = QListWidget()
    self.macroTable = QTableWidget(0, 2)
    self.macroTable.setHorizontalHeaderLabels(["Alias", "Translation"])
    self.macroTable.setColumnWidth(40, 40)
    self.macroTable.horizontalHeader().setStretchLastSection(True)
    self.macroTable.verticalHeader().setVisible(False)
    

    self.allShortcutItems = {}
    self.activeSetLabel = QLabel("Shortcut in selected set:")
    self.table = QTableWidget(0, 4)
    self.table.setHorizontalHeaderLabels(["Icon", "Name", "Trigger", "Action"])
    self.table.setColumnWidth(0, 40)
    self.table.horizontalHeader().setStretchLastSection(True)
    self.table.verticalHeader().setVisible(False)

    _topsplitter = QSplitter()
    _vsplitter = QSplitter(Qt.Orientation.Vertical)
    _topsplitter.addWidget(newVFrame([ "Shortcut Sets:", 
                              newHLayout([self.shortcutListWidget,
                                newVLayout(["__stretch__",self.btnNewSet, self.btnDeleteSet, 
                                  self.btnSaveSet, self.btnReloadSet, "__stretch__"])])]))
    
    _topsplitter.addWidget(newVFrame(["Aliases:", 
                              newHLayout([self.macroTable, 
                                  newVLayout(["__stretch__",self.btnAddAlias, self.btnRemoveAlias,
                                              self.btnSaveAlias, self.btnReloadAlias,"__stretch__"])])]))
    _vsplitter.addWidget(_topsplitter)
    _vsplitter.addWidget(newVFrame([self.activeSetLabel, 
                            newHLayout([self.table,newVLayout(["__stretch__", self.btnAddEntry, 
                                        self.btnRemoveEntry, "__stretch__", self.btnHelp])])]))
    self.setLayout(newVLayout([_vsplitter]))

    self.btnNewSet.clicked.connect(self.newShortcutSet)
    self.btnDeleteSet.clicked.connect(self.deleteShortcutSet)
    self.btnHelp.clicked.connect(self.showHelpWindow)
    self.shortcutListWidget.itemChanged.connect(self.updateShortcutSetFile)
    self.shortcutListWidget.itemSelectionChanged.connect(self.updateTable)
    self.table.cellChanged.connect(self.syncTable2Data)

    self.btnAddAlias.clicked.connect(self.addAlias)
    self.btnRemoveAlias.clicked.connect(self.removeAlias)
    self.btnSaveAlias.clicked.connect(self.saveAlias)
    self.btnReloadAlias.clicked.connect(self.reloadAlias)

    self.btnDaemonToggle.clicked.connect(self.launchDaemon)
    self.btnDaemonToggle.ctrlClicked.connect(lambda x=True : self.launchDaemon(x))
    self.btnDaemonToggle.rightClicked.connect(lambda x=True : self.launchDaemon(x))
    self.btnAddEntry.clicked.connect(self.addShortcutEntry)
    self.btnRemoveEntry.clicked.connect(self.removeShortcutEntry)
    self.btnSaveSet.clicked.connect(self.saveSelectedShortcutSet)
    self.btnSaveSet.ctrlClicked.connect(self.saveAllShortcutSet)
    self.btnSaveSet.rightClicked.connect(self.saveAllShortcutSet)
    self.btnReloadSet.clicked.connect(self.reloadSelectedShortcutSet)
    self.btnReloadSet.ctrlClicked.connect(self.reloadAllShortcutSet)
    self.btnReloadSet.rightClicked.connect(self.reloadAllShortcutSet)

    self.reloadAlias()

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    allFiles = glob.glob(os.path.join(P_DEFAULT_SHORTCUTDIR, "*.shortcut"))
    for n in allFiles:
      name = os.path.splitext(os.path.basename(n))[0]
      self.appendShortcutSet(name)
    self.initialized = True
    if self.toActivate: 
      self.setActiveSets(self.toActivate)
      self.toActivate = None
  
  #----------------------------------------------------------------------------------------------------------
  def updateTable(self):
    sset = self.shortcutListWidget.selectedItems()
    if not s: return

    self.table.clearContents()
    self.table.setRowCount(0)
    sset[0].display()

  #----------------------------------------------------------------------------------------------------------
  def addShortcutEntry(self):
    pos = self.table.rowCount()
    self.table.insertRow(pos)
    self.table.setItem(pos, 0, QTableWidgetItem(""))
    self.table.setItem(pos, 1, QTableWidgetItem(""))
    self.table.setItem(pos, 2, QTableWidgetItem(""))
    self.table.setItem(pos, 3, QTableWidgetItem(""))

  #----------------------------------------------------------------------------------------------------------
  def syncTable2Data(self, row, column):
    sset = self.shortcutListWidget.selectedItems()
    if not sset: return
    sset[0].sync(row, column)
    self.activeSetLabel.setText(f"Shortcuts in \"{sset[0].text()}\":")
  
  #----------------------------------------------------------------------------------------------------------
  def addAlias(self, alias="", action=""):
    pos = self.macroTable.rowCount()
    self.macroTable.insertRow(pos)
    self.macroTable.setItem(pos, 0, QTableWidgetItem(alias))
    self.macroTable.setItem(pos, 1, QTableWidgetItem(action))

  #----------------------------------------------------------------------------------------------------------
  def removeAlias(self):
    crow = self.macroTable.currentRow()
    if crow:
      self.macroTable.removeRow(crow)

  #----------------------------------------------------------------------------------------------------------
  def reloadAlias(self):
    self.macroTable.clearContents()
    self.macroTable.setRowCount(0)

    filename = P_DEFAULT_SHORTCUTDIR + os.sep + "aliases.json"
    with open(filename,"r") as f:
      data = json.load(f)
    for k in data.keys():
      self.addAlias(k,data[k])

  #----------------------------------------------------------------------------------------------------------
  def saveAlias(self):
    d = self.getAliases()
    filename = P_DEFAULT_SHORTCUTDIR + os.sep + "aliases.json"
    json.dump(d, open(filename,'w'), cls=muJSONEncoder)

  #----------------------------------------------------------------------------------------------------------
  def getAliases(self):
    d = {}
    for row in range(self.macroTable.rowCount()):
      d[self.macroTable.item(row,0).text()] = self.macroTable.item(row,1).text()
    return d


  #----------------------------------------------------------------------------------------------------------
  def newShortcutSet(self):
    i = 1
    while f"NewSet{i}" in self.allShortcutItems:
      i += 1
    self.appendShortcutSet(f"NewSet{i}")

  #----------------------------------------------------------------------------------------------------------
  def appendShortcutSet(self, name : str):
    if name in self.allShortcutItems: return

    self.allShortcutItems[name] = cShortcutItem(self,name)
    self.shortcutListWidget.addItem(self.allShortcutItems[name])
    
    filename = P_DEFAULT_SHORTCUTDIR+os.sep+name+P_DEFAULT_SHORTCUTEXT
    if os.path.exists(filename):
      self.allShortcutItems[name].load()
    else:
      self.main.console.info(f"New shortcut set being created in \"{C_SILVER}{P_DEFAULT_SHORTCUTDIR}</font>\"...")
      self.allShortcutItems[name].save()

  #----------------------------------------------------------------------------------------------------------
  def getActiveSets(self):
    allActive = []
    sset : cShortcutItem
    for sset in self.allShortcutItems.values():
      if sset.checkState() == Qt.CheckState.Checked:
        allActive.append(sset.text())
    return allActive
  
  #----------------------------------------------------------------------------------------------------------
  def setActiveSets(self, toActivate : list):
    if not self.initialized:
      self.toActivate = toActivate
      return

    sset : cShortcutItem
    for sset in self.allShortcutItems.values():
      if sset.text() in toActivate:
        sset.setActive(True)
      else:
        sset.setActive(False)

  #----------------------------------------------------------------------------------------------------------
  def showHelpWindow(self):
    dlg = QDialog(self)
    dlg.setWindowTitle("Shortcuts Help")
    layout = QVBoxLayout(dlg)
    text = QTextEdit()
    text.setReadOnly(True)
    help_text = f"""
    <h2>How to Use</h2>
    <br>You'll be working with "sets" of shorcuts. Each set can have its own collection of shortcuts and you can toggle each set on/off (inactive/active). Shortcuts between sets can overlap - this is intentional.
    <br>
    <br>1. <b>Create a Set:</b> click the \"New Set\" button ("Document" icon). A new line will appear in the list with a placeholder name, like NewSet1. The list is modifiable, just double click any entry to rename it. The new set will be inactive by default. Click the checkmark box on the left of NewSet1 name to toggle it on/off
    <br>2. <b>Select NewSet1</b>: click your NewSet1, then the table display will show an empty set of shortcuts
    <br>3. <b>Add Shortcuts:</b> click "+" button to define a new shortcut. A new, empty row will be added to the table. Edit this new row as needed (currently you have to enter shortcuts as text, e.g. "ctrl+m")
    <br>4. <b>Launch Shortcuts Daemon:</b> press the "Play" button to enable all shortcuts from all active sets. If it is already running, press "Stop" and then "Play" again to refresh it

    <h2>Features</h2>
    <br>● <b>Save set:</b> once you're satisfied with your configuration, select it from the list and press the "Save Set" button
    <br>● <b>Delete sets</b>: to delete a full set, select it from the list and press the "Trash" icon button. This action cannot be undone!
    <br>● <b>Active sets</b>: you can have many active sets at the same time, and there is no check if they have overlapping shortcuts. This is intentional. The daemon will execute ALL actions from ALL active sets whenever the shortcut is pressed. Be responsible!
    <br>● <b>Sets configuration</b>: the "profile" saves the last active sets of shortcuts and reloads then when relaunching the application. It saves automatically if you exit the application normally, or you can manually go to "Settings" click "Save" to save the currently active profile
    <br>● <b>Edit shortcuts</b>: just modify them directly in the table. The changes only take effect after you restart the shortcuts daemon
    <br>● <b>Delete shortcuts</b>: to delete a single shortcut, select it from the table and press the "-" button. You can reload previously saved sets to undo this action.

    <h2>Tips</h2>
    <br>● Changes take effect only after restarting the Daemon!!
    <br>● It helps to have a "set" per class/character, e.g. a "healer" set. Toggle the set inactive/active if the healer account is online or not.
    <br>● Right-click or Ctrl+Click "Save" or "Reload" to apply the action to all sets.
    <br>● Use descriptive names for sets and shortcuts for easier management.
    <br>● All sets are stored as text files in {P_DEFAULT_SHORTCUTDIR} and can be modified by any program. This is a security issue, if you believe in security issues, btw 🦄. Use at your own risk! 

    <br>If you need further support, look for help.
    """
    text.setHtml(help_text)

    layout.addWidget(text)
    dlg.setLayout(layout)
    dlg.resize(400, 300)
    dlg.exec()

  #----------------------------------------------------------------------------------------------------------
  def deleteShortcutSet(self):
    sset = self.shortcutListWidget.selectedItems()
    if not sset: return
    self.main.console.info(f"Removing shortcut set \"{C_SILVER}{sset[0].text()}</font>\"...")
    del self.allShortcutItems[sset[0].text()]
    try:
      os.remove(P_DEFAULT_SHORTCUTDIR+os.sep+sset[0].text()+P_DEFAULT_SHORTCUTEXT)
    except:
      pass
    self.shortcutListWidget.takeItem(self.shortcutListWidget.row(sset[0]))
    del sset[0]

  #----------------------------------------------------------------------------------------------------------
  def launchDaemon(self, purge=False):
    # self.main.processManager.setVisible(True)
    for key, proc in self.main.processManager.items.items():
      if key.startswith("scd_"):
        self.main.console.info("Restarting Shortcuts Daemon...")
        proc.toggle() # turns off
        if purge:
          self.main.console.info("Purging all possible shortcuts...")
          XHelper().forceCleanup()
        proc.toggle() # turns on again
        self.main.console.info("Shortcuts Daemon restarted!")
        return
    
    scd = cShortcutsDaemon(self.main)
    self.main.processManager.addItem(scd)
    scd.launch()

  #----------------------------------------------------------------------------------------------------------
  def consolidateActiveShortcuts(self) -> dict:
    allActive = self.getActiveSets()
    aliases = self.getAliases()
    consolidated = {}
    for name in allActive:
      consolidated = self.allShortcutItems[name].consolidate(consolidated, aliases)

    self.main.console.debugMessage(f"--------------------------------------------------------")
    self.main.console.debugMessage(f"  Consolidated shortcuts (all active sets)")
    self.main.console.debugMessage(f"--------------------------------------------------------")
    for hk in consolidated.keys():
      self.main.console.debugMessage(f"  {hk}:")
      for target in consolidated[hk].keys():
        self.main.console.debugMessage(f"     {target}: {consolidated[hk][target]}")
    return consolidated

  #----------------------------------------------------------------------------------------------------------
  def removeShortcutEntry(self):
    sset = self.shortcutListWidget.selectedItems()
    if not sset: return
    crow = self.table.currentRow()
    sset[0].removeRow(crow)
    self.table.removeRow(crow)

  #----------------------------------------------------------------------------------------------------------
  def saveSelectedShortcutSet(self):
    sset = self.shortcutListWidget.selectedItems()
    if not sset: return
    sset[0].save()

  #----------------------------------------------------------------------------------------------------------
  def saveAllShortcutSet(self):
    for sset in self.allShortcutItems.values():
      sset.save()

  #----------------------------------------------------------------------------------------------------------
  def reloadAllShortcutSet(self):
    for sset in self.allShortcutItems.values():
      sset.load()
    self.updateTable()

  #----------------------------------------------------------------------------------------------------------
  def reloadSelectedShortcutSet(self):
    sset = self.shortcutListWidget.selectedItems()
    if not sset: return
    sset[0].load()
    self.updateTable()

  #----------------------------------------------------------------------------------------------------------
  def updateShortcutSetFile(self, sset : cShortcutItem):
    key = next((k for k, v in self.allShortcutItems.items() if v is sset), None)
    if key != sset.text():
      self.main.console.info(f"Renaming shortcut set from \"{C_SILVER}{key}</font>\" to \"{C_SILVER}{sset.text()}</font>\"...")
      os.rename(P_DEFAULT_SHORTCUTDIR+os.sep+key+P_DEFAULT_SHORTCUTEXT, P_DEFAULT_SHORTCUTDIR+os.sep+sset.text()+P_DEFAULT_SHORTCUTEXT, )
      self.allShortcutItems[sset.text()] = sset
      del self.allShortcutItems[key]
    

    # from pynput import keyboard

    # def on_activate_h():
    #     print('++h pressed')

    # def on_activate_i():
    #     print('++i pressed')

    # with keyboard.GlobalHotKeys({
    #     '<ctrl>+h': on_activate_h,
    #     '<ctrl>+i': on_activate_i}) as h:
    #     h.join()


    


