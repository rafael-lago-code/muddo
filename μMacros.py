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
from PyQt6.QtWidgets import (QAbstractItemView, QTextEdit, QVBoxLayout,
                              QListWidgetItem, QListWidget, QSplitter, QHeaderView, QLineEdit,
                              QTableWidget, QTableWidgetItem, QLabel, QDialog)
from helpers.μPrint import μPrint
from helpers.μImageFactory import *
from helpers.μStrings import *
from helpers.μAliases import μAliases
from μSettings import μSettings
from μSettingsProfile import μSettingsProfile
from widgets.μFloating import μToggler
from widgets.μOrb import μOrbSmall
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtCore import QSize, Qt
import glob, re, os, random
from typing import TYPE_CHECKING
from μMacrosDaemon import μMacrosDaemon
from widgets.μIconSelectDialog import μIconSelectDialog
if TYPE_CHECKING:
   from μMainWindow import μMainWindow


#---------------------------------------------------------------------------------------------------------------
#
#
#                                            T A B L E   R O W
#
#---------------------------------------------------------------------------------------------------------------
class cTableRow(QTableWidgetItem):
  def __init__(self, text=None):
    super().__init__(text)
    self.setFlags(Qt.ItemFlag.ItemIsDragEnabled)
    self.setFlags(~Qt.ItemFlag.ItemIsDropEnabled)


#---------------------------------------------------------------------------------------------------------------
#
#
#                                            M A C R O   I T E M
#
#---------------------------------------------------------------------------------------------------------------
class cMacroSet(QListWidgetItem):
  def __init__(self, parent : μMacros, name : str):
    super().__init__()
    self.parent = parent
    self.setText(name)
    self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
    self.setCheckState(Qt.CheckState.Unchecked)
    self.data = [["", "", "", ""]]

  #----------------------------------------------------------------------------------------------------------
  def setActive(self, val : bool):
    if val:
      self.setCheckState(Qt.CheckState.Checked)
    else:
      self.setCheckState(Qt.CheckState.Unchecked)

  #----------------------------------------------------------------------------------------------------------
  def sync(self, row, column):
    while row >= len(self.data):
      self.data.append([None, None, None, None])
    modifiedCell = self.parent.table.item(row, column)
    if modifiedCell is None: return
    if column == 0:
      self.data[row][0] = modifiedCell.data(Qt.ItemDataRole.UserRole) or ""
    else:
      self.data[row][column] = modifiedCell.text()

  #----------------------------------------------------------------------------------------------------------
  def display(self):
    table : QTableWidget = self.parent.table
    for row in self.data:
      pos = table.rowCount()
      table.insertRow(pos)
      icon_item = cTableRow()
      icon_item.setData(Qt.ItemDataRole.UserRole, row[0] or "")
      icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
      if row[0]:
        icon_item.setIcon(getIcon(row[0]))
      else:
        icon_item.setIcon(getIcon(P_ICON_PLACEHOLDER)) #TODO
      table.setItem(pos, 0, icon_item)
      table.setItem(pos, 1, cTableRow(str(row[1])))
      table.setItem(pos, 2, cTableRow(str(row[2])))
      table.setItem(pos, 3, cTableRow(str(row[3])))

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    filename = P_DEFAULT_MACRODIR + os.sep + self.text() + P_DEFAULT_MACROEXT
    json.dump(self.data, open(filename,'w'), cls=muJSONEncoder)

  #----------------------------------------------------------------------------------------------------------
  def removeRow(self, row : int):
    if row < len(self.data):
      self.data = self.data[:row] + self.data[row+1:]

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    filename = P_DEFAULT_MACRODIR + os.sep + self.text() + P_DEFAULT_MACROEXT
    try:
      with open(filename,"r") as f:
        self.data = json.load(f)
    except Exception as e:
      μPrint.error(f"{C_RED}WARNING:</font> error loading macro set from \"{filename}\"",e)
      self.data = []

  #----------------------------------------------------------------------------------------------------------
  def consolidate(self, consolidated = {}, aliases = {}, meta = {}) -> tuple:
    # Macros format:
    #     [<icon>, <name>, <hotkey>, <scripts>]
    # Scripts are of the form:
    #     <script1>; <script2>; <script3>;
    # Each script should be formatted as:
    #     <target1>, <target2>, <target3>: <action1>, <action2>, <action3>
    # If <target> is missing, "self" is assumed (useful for macros)
    # A special target "all" is provided for firing the macro to all running DDO processes
    # Actions:
    #   - sleep_X: wait for X seconds
    #   - anything else: interpreted as key presses
    # Scripts are all started at the same time whenever their shortcut is pressed

    # Discard aliases whose translation references a $N that the alias key doesn't capture.
    validAliases = {}
    for k, a in aliases.items():
      keyIds   = set(re.findall(r'\$(\d)', k))
      transIds = set(re.findall(r'\$(\d)', a))
      if not transIds.issubset(keyIds):
        μPrint.error(f"{C_RED}WARNING:</font> discarding alias \"{k}\" -> \"{a}\" (translation references $N not captured by the key)")
        continue
      validAliases[k] = a

    for row in self.data:
      icon, name = row[0], row[1]
      hotkey  = row[2]
      for k,a in validAliases.items():
        hotkey = replaceAlias(hotkey, k, a)
      hotkey  = (hotkey.replace(" ", "")).lower()
      if not hotkey or hotkey == 'none': continue
      entry = meta.setdefault(hotkey, {'icon': None, 'names': set()})
      if icon: entry['icon'] = icon
      if name: entry['names'].add(name)
      scripts = [e.strip() for e in row[3].split(";") if e.strip()]

      if hotkey in consolidated.keys():
        cs = consolidated[hotkey]
      else:
        cs = {}

      for s in scripts:
        s = s.split(':')
        if len(s) == 1:
          actors = ["self"]
        else:
          actors = (s.pop(0)).split(',')
          actors = [a.strip().lower() for a in actors]
          translated = []
          for a in actors:
            for k, v in validAliases.items():
              a = replaceAlias(a, k, v)
            translated.append(a)
          actors = translated
        commands = [s[0].replace("\n", "").strip()]

        for a in actors: cs[a] = cs.get(a, []) + commands

    # todo: check if "all" is scripting the same action; if yes, then the individual characters don't need to do it by themselves
      consolidated[hotkey] = cs
    return consolidated, meta


#---------------------------------------------------------------------------------------------------------------
#
#
#                                                M A C R O S
#
#---------------------------------------------------------------------------------------------------------------
class μMacros(μToggler):
  def __init__(self, main : μMainWindow):
    self.widgetID = "Macros"
    super().__init__("Macros", P_ICON_GEARHIER)
    self.toggler.setToolTip("Toggle Macros UI<br><b><i>Requires Milvian plugin installed and running in Dungeon Helper!</i></b>")
    v = QVBoxLayout()
    self.initialized = False
    self.toActivate = None
    self.main = main

    self.daemon = μMacrosDaemon(self.main)

    self.btnNewSet      = μOrbSmall(icon=P_ICON_NEWDOC, tooltip="Create a new set of shortcuts")
    self.btnDeleteSet   = μOrbSmall(icon=P_ICON_TRASH, tooltip="Delete currently selected set - this action cannot be undone!")
    self.btnAddEntry    = μOrbSmall(icon=P_ICON_ADD, tooltip="Add a new macro to the currently selected set")
    self.btnRemoveEntry = μOrbSmall(icon=P_ICON_REMOVE, tooltip="Remove the currently selected macro from the currently selected set")
    self.btnEditIcon    = μOrbSmall(icon=P_ICON_IMAGE, tooltip="Set icon for the selected macro")
    self.btnHelp        = μOrbSmall(icon=P_ICON_QUESTION, tooltip="Show a comprehensive help on how macros work here (lol)")
    self.btnPlay        = μOrbSmall(icon=P_ICON_PLAY, tooltip="Executes current text as-is, if Milvian is running already. <b><i>Ctrl+Enter</i></b> is a shortcut for that.")

    self.btnAddAlias    = μOrbSmall(icon=P_ICON_ADD, tooltip="Add a new alias")
    self.btnRemoveAlias = μOrbSmall(icon=P_ICON_REMOVE, tooltip="Remove the currently selected alias")

    self.btnNewSet.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
    self.btnDeleteSet.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)

    self.setListWidget = QListWidget()
    self.setListWidget.setWordWrap(True)
    self.setListWidget.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)

    self.aliasTable = QTableWidget(0, 2)
    self.aliasTable.setHorizontalHeaderLabels(["Alias", "Translation"])
    self.aliasTable.setColumnWidth(0, 120)
    self.aliasTable.horizontalHeader().setStretchLastSection(True)
    self.aliasTable.setSortingEnabled(True)
    self.aliasTable.setWordWrap(True)
    self.aliasTable.verticalHeader().setVisible(False)
    self.aliasTable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    self.aliasTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.aliasTable.setAcceptDrops(True)
    self.aliasTable.setDragEnabled(True)
    self.aliasTable.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
    self.aliasTable.setDropIndicatorShown(True)
    self.aliasTable.setDragDropOverwriteMode(False)

    self.aliasFilter = QLineEdit()

    self.allMacroItems = {}
    self.activeSetLabel = QLabel("Macros in selected set:")
    self._loading = False
    self._aliasLoading = False
    self._actionLoading = False

    self.table = QTableWidget(0, 4)
    self.table.setIconSize(QSize(32, 32))
    self.table.setHorizontalHeaderLabels(["Icon", "Name", "Trigger", "Action"])
    self.table.setColumnWidth(0, 32)
    self.table.horizontalHeader().setStretchLastSection(True)
    self.table.verticalHeader().setVisible(False)
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.table.setAcceptDrops(True)
    self.table.setDragEnabled(True)
    self.table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
    self.table.setDropIndicatorShown(True)
    self.table.setDragDropOverwriteMode(False)
    self.table.setColumnHidden(3, True)

    self.actionEditor = QTextEdit()
    _asplitter = QSplitter(Qt.Orientation.Horizontal)
    _asplitter.addWidget(self.table)
    _asplitter.addWidget(self.actionEditor)

    _vsplitter = QSplitter(Qt.Orientation.Vertical)
    _topSplitter = QSplitter()
    _topSplitter.addWidget(newVFrame([ "Sets:",
                              newHLayout([self.setListWidget,
                                newVLayout(["__stretch__",self.btnNewSet, self.btnDeleteSet, self.btnHelp, "__stretch__"])])]))
    _topSplitter.addWidget(newHFrame([newVLayout([self.aliasTable, newHLayout(["Filter by:", self.aliasFilter])]),
                           newVLayout(["__stretch__",self.btnAddAlias, self.btnRemoveAlias, "__stretch__"])]))

    _topSplitter.setSizes([100,400])

    _vsplitter.addWidget(_topSplitter)
    _vsplitter.addWidget(newVFrame([self.activeSetLabel,
                         newHLayout([_asplitter, newVLayout(["__stretch__", self.btnAddEntry,
                                     self.btnRemoveEntry, self.btnEditIcon, "__stretch__", self.btnPlay])])]))
    _vsplitter.setSizes([100,300])

    self.setLayout(newVLayout([_vsplitter]))

    self.table.dropEvent = lambda x : self._saveWhenDropped(x)      

    self.btnNewSet.clicked.connect(self.newMacroSet)
    self.btnDeleteSet.clicked.connect(self.deleteMacroSet)
    self.btnHelp.clicked.connect(self.showHelpWindow)
    self.btnPlay.clicked.connect(self.playMacro)
    self.setListWidget.itemChanged.connect(self.renameMacroSetFile)
    self.setListWidget.itemSelectionChanged.connect(self.updateTable)
    self.setListWidget.itemSelectionChanged.connect(self._ensureSetListSelection)
    self.table.cellChanged.connect(self.syncTable2Data)
    self.table.cellDoubleClicked.connect(self._onCellDoubleClicked)
    self.table.itemSelectionChanged.connect(self._onSelectionChanged)
    self.actionEditor.textChanged.connect(self._saveAction)
    QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._saveAction)
    QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.playMacro)
    QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self.playMacro)
    self.aliasTable.cellChanged.connect(self._onAliasCellChanged)

    self.btnAddAlias.clicked.connect(self.addAlias)
    self.btnRemoveAlias.clicked.connect(self.removeAlias)
    self.aliasFilter.textChanged.connect(self.filterAlias)

    self.btnAddEntry.clicked.connect(self.addMacroEntry)
    self.btnRemoveEntry.clicked.connect(self.removeMacroEntry)
    self.btnEditIcon.clicked.connect(self.editMacroIcon)

    self.reloadAlias()
  
  #----------------------------------------------------------------------------------------------------------
  def _saveWhenDropped(self, event):
    QTableWidget.dropEvent(self.table, event)
    cset : cMacroSet = self.setListWidget.currentItem()
    for row in range(self.table.rowCount()):
      for col in range(4):
        cset.sync(row,col)
    self.setListWidget.currentItem().save()


  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    super().initialize()
    allFiles = glob.glob(os.path.join(P_DEFAULT_MACRODIR, "*"+P_DEFAULT_MACROEXT))
    for n in allFiles:
      name = os.path.splitext(os.path.basename(n))[0]
      self.appendMacroSet(name)
    self.initialized = True
    self.setListWidget.itemChanged.connect(lambda a, x = μSettings: x.session.setMacroSets(self.getActiveSets()))
    μSettings.widget.sigProfileChanged.connect(self.updateProfile)
    self.updateProfile(μSettings.profile, μSettings.lastProfile)
    if self.toActivate:
      self.setActiveSets(self.toActivate)
      self.toActivate = None
    self._ensureSetListSelection()

  #----------------------------------------------------------------------------------------------------------
  def updateProfile(self, prof : μSettingsProfile, last : str):
    if prof.session.macroSets: self.setActiveSets(prof.session.macroSets)

  #----------------------------------------------------------------------------------------------------------
  def _ensureSetListSelection(self):
    if not self.setListWidget.selectedItems() and self.setListWidget.count() > 0:
      self.setListWidget.setCurrentRow(0)

  #----------------------------------------------------------------------------------------------------------
  def updateTable(self):
    sset = self.setListWidget.selectedItems()
    if not sset:
      return
    self._loading = True
    self._actionLoading = True
    self.table.clearContents()
    self.table.setRowCount(0)
    sset[0].display()
    self._loading = False
    self._actionLoading = False
    self.actionEditor.setEnabled(False)
    self.actionEditor.setPlainText("")
    if self.table.rowCount() > 0:
      self.table.selectRow(0)

  #----------------------------------------------------------------------------------------------------------
  def addMacroEntry(self):
    pos = self.table.rowCount()
    self.table.insertRow(pos)
    icon = cTableRow()
    icon.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
    icon.setIcon(getIcon(P_ICON_PLACEHOLDER))
    self.table.setItem(pos, 0, icon)
    self.table.setItem(pos, 1, cTableRow(""))
    self.table.setItem(pos, 2, cTableRow(""))
    self.table.setItem(pos, 3, cTableRow(""))

  #----------------------------------------------------------------------------------------------------------
  def syncTable2Data(self, row, column):
    if self._loading: return
    sset = self.setListWidget.selectedItems()
    if not sset: return
    sset[0].sync(row, column)
    self.activeSetLabel.setText(f"Shortcuts in \"{sset[0].text()}\":")
    sset[0].save()

  #----------------------------------------------------------------------------------------------------------
  def addAlias(self, alias="", action=""):
    pos = self.aliasTable.rowCount()
    self.aliasTable.insertRow(pos)
    self.aliasTable.setItem(pos, 0, cTableRow(alias))
    self.aliasTable.setItem(pos, 1, cTableRow(action))

  #----------------------------------------------------------------------------------------------------------
  def removeAlias(self):
    crow = self.aliasTable.currentRow()
    if crow >= 0:
      self.aliasTable.removeRow(crow)
      self.saveAlias()

  #----------------------------------------------------------------------------------------------------------
  def _onAliasCellChanged(self, row, column):
    if self._aliasLoading: return
    self.saveAlias()

  #----------------------------------------------------------------------------------------------------------
  def reloadAlias(self):
    self._aliasLoading = True
    self.aliasTable.clearContents()
    self.aliasTable.setRowCount(0)
    filename = P_DEFAULT_MACRODIR + os.sep + "aliases.json"
    with open(filename, "r") as f:
      data = json.load(f)
    for k in data.keys():
      self.addAlias(k, data[k])
    self._aliasLoading = False
    μAliases.set(data)

  #----------------------------------------------------------------------------------------------------------
  def saveAlias(self):
    d = self.getAliases()
    filename = P_DEFAULT_MACRODIR + os.sep + "aliases.json"
    json.dump(d, open(filename,'w'), cls=muJSONEncoder)
    μAliases.set(d)

  #----------------------------------------------------------------------------------------------------------
  def getAliases(self):
    d = {}
    for row in range(self.aliasTable.rowCount()):
      k = self.aliasTable.item(row, 0)
      v = self.aliasTable.item(row, 1)
      if k and v:
        d[k.text()] = v.text()
    return d

  #----------------------------------------------------------------------------------------------------------
  def filterAlias(self, text: str):
    text = text.lower()
    for row in range(self.aliasTable.rowCount()):
      alias       = self.aliasTable.item(row, 0)
      translation = self.aliasTable.item(row, 1)
      match = (text in (alias.text().lower() if alias else "")) or (text in (translation.text().lower() if translation else ""))
      self.aliasTable.setRowHidden(row, bool(text) and not match)

  #----------------------------------------------------------------------------------------------------------
  def newMacroSet(self):
    i = 1
    while f"NewSet{i}" in self.allMacroItems:
      i += 1
    self.appendMacroSet(f"NewSet{i}")

  #----------------------------------------------------------------------------------------------------------
  def appendMacroSet(self, name : str):
    if name in self.allMacroItems: return

    self.allMacroItems[name] = cMacroSet(self,name)
    self.setListWidget.addItem(self.allMacroItems[name])

    filename = P_DEFAULT_MACRODIR+os.sep+name+P_DEFAULT_MACROEXT
    if os.path.exists(filename):
      self.allMacroItems[name].load()
    else:
      μPrint.info(f"New macro set being created in \"{C_SILVER}{P_DEFAULT_MACRODIR}</font>\"...")
      self.allMacroItems[name].save()

  #----------------------------------------------------------------------------------------------------------
  def getActiveSets(self):
    allActive = []
    sset : cMacroSet
    for sset in self.allMacroItems.values():
      if sset.checkState() == Qt.CheckState.Checked:
        allActive.append(sset.text())
    return allActive

  #----------------------------------------------------------------------------------------------------------
  def setActiveSets(self, toActivate : list):
    if not self.initialized:
      self.toActivate = toActivate
      return

    sset : cMacroSet
    for sset in self.allMacroItems.values():
      if sset.text() in toActivate:
        sset.setActive(True)
      else:
        sset.setActive(False)

  #----------------------------------------------------------------------------------------------------------
  def playMacro(self):
    action = self.actionEditor.toPlainText().strip()
    if not action: return
    bridges = self.daemon.getBridges(returnMeta=True)
    if not bridges: return

    for script in action.split(';'):
      script = script.strip()
      if not script or ':' not in script: continue
      actors_str, _, actions_str = script.partition(':')
      actions = splitGroups(actions_str.strip())
      if not actions: continue
      actors = [a.strip().lower() for a in actors_str.split(',') if a.strip()]
      real_keys = [k for k in bridges.keys() if k != 'self']
      if 'all' in actors:
        targets = real_keys
      elif 'any' in actors:
        targets = [random.choice(real_keys)] if real_keys else []
      else:
        targets = [a for a in actors if a in bridges]
      for t in targets:
        bridges[t].execute(actions)

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
    <br> 1. <b>Create a Set:</b> click the \"New Set\" button ("Document" icon). A new line will appear in the list with a placeholder name, like NewSet1. The list is modifiable, just double click any entry to rename it. The new set will be inactive by default. Click the checkmark box on the left of NewSet1 name to toggle it on/off
    <br> 2. <b>Select NewSet1</b>: click your NewSet1, then the table display will show an empty set of shortcuts
    <br> 3. <b>Add Shortcuts:</b> click "+" button to define a new shortcut. A new, empty row will be added to the table. Edit this new row as needed (currently you have to enter shortcuts as text, e.g. "ctrl+m")
    <br> 4. <b>Launch Shortcuts Daemon:</b> press the "Play" button to enable all shortcuts from all active sets. If it is already running, press "Stop" and then "Play" again to refresh it

    <h2>Buttons</h2>
    <br> ● <b>Save set:</b> once you're satisfied with your configuration, select it from the list and press the "Save Set" button
    <br> ● <b>Delete sets</b>: to delete a full set, select it from the list and press the "Trash" icon button. This action cannot be undone!
    <br> ● <b>Active sets</b>: you can have many active sets at the same time, and there is no check if they have overlapping shortcuts. This is intentional. The daemon will execute ALL actions from ALL active sets whenever the shortcut is pressed. Be responsible!
    <br> ● <b>Sets configuration</b>: the "profile" saves the last active sets of shortcuts and reloads then when relaunching the application. It saves automatically if you exit the application normally, or you can manually go to "Settings" click "Save" to save the currently active profile
    <br> ● <b>Edit shortcuts</b>: just modify them directly in the table. The changes only take effect after you restart the shortcuts daemon
    <br> ● <b>Delete shortcuts</b>: to delete a single shortcut, select it from the table and press the "-" button. You can reload previously saved sets to undo this action.

    <h2>Tips</h2>
    <br> ● Changes take effect only after restarting the Daemon!!
    <br> ● It helps to have a "set" per class/character, e.g. a "healer" set. Toggle the set inactive/active if the healer account is online or not.
    <br> ● Right-click or Ctrl+Click "Save" or "Reload" to apply the action to all sets.
    <br> ● Use descriptive names for sets and shortcuts for easier management.
    <br> ● All sets are stored as text files in {P_DEFAULT_MACRODIR} and can be modified by any program. This is a security issue, if you believe in security issues, btw 🦄. Use at your own risk!

    <br>If you need further support, look for help.
    """
    text.setHtml(help_text)

    layout.addWidget(text)
    dlg.setLayout(layout)
    dlg.resize(400, 300)
    dlg.exec()

  #----------------------------------------------------------------------------------------------------------
  def deleteMacroSet(self):
    sset = self.setListWidget.selectedItems()
    if not sset: return
    μPrint.info(f"Removing macro set \"{C_SILVER}{sset[0].text()}</font>\"...")
    del self.allMacroItems[sset[0].text()]
    try:
      os.remove(P_DEFAULT_MACRODIR+os.sep+sset[0].text()+P_DEFAULT_MACROEXT)
    except:
      pass
    self.setListWidget.takeItem(self.setListWidget.row(sset[0]))
    del sset[0]

  #----------------------------------------------------------------------------------------------------------
  def consolidateActiveMacros(self) -> tuple:
    allActive = self.getActiveSets()
    aliases = self.getAliases()
    consolidated = {}
    meta = {}
    for name in allActive:
      consolidated, meta = self.allMacroItems[name].consolidate(consolidated, aliases, meta)

    μPrint.debug(f"--------------------------------------------------------")
    μPrint.debug(f"  Consolidated macros (all active sets)")
    μPrint.debug(f"--------------------------------------------------------")
    for hk in consolidated.keys():
      μPrint.debug(f"  {hk}:")
      for target in consolidated[hk].keys():
        μPrint.debug(f"     {target}: {consolidated[hk][target]}")
    return consolidated, meta

  #----------------------------------------------------------------------------------------------------------
  def removeMacroEntry(self):
    sset = self.setListWidget.selectedItems()
    if not sset: return
    crow = self.table.currentRow()
    if crow < 0: return
    sset[0].removeRow(crow)
    self._loading = True
    self.table.removeRow(crow)
    self._loading = False
    sset[0].save()

  #----------------------------------------------------------------------------------------------------------
  def _onCellDoubleClicked(self, row, column):
    if column == 0:
      self.editMacroIcon()

  #----------------------------------------------------------------------------------------------------------
  def editMacroIcon(self):
    sset = self.setListWidget.selectedItems()
    if not sset: return
    crow = self.table.currentRow()
    if crow < 0: return
    current_icon = sset[0].data[crow][0] if crow < len(sset[0].data) else None
    dlg = μIconSelectDialog(current=current_icon, parent=self)
    if dlg.exec():
      path = dlg.selectedPath()
      if path:
        icon_item = self.table.item(crow, 0)
        if not icon_item:
          icon_item = cTableRow()
          icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
          self.table.setItem(crow, 0, icon_item)
        icon_item.setData(Qt.ItemDataRole.UserRole, path)
        icon_item.setIcon(getIcon(path))
        sset[0].sync(crow, 0)
        sset[0].save()

  #----------------------------------------------------------------------------------------------------------
  def _onSelectionChanged(self):
    indexes = self.table.selectionModel().selectedRows()
    self._actionLoading = True
    if not indexes:
      self.actionEditor.setEnabled(False)
      self.actionEditor.setPlainText("")
    else:
      last_row = max(idx.row() for idx in indexes)
      item = self.table.item(last_row, 3)
      self.actionEditor.setPlainText(item.text() if item else "")
      self.actionEditor.setEnabled(len(indexes) == 1)
    self._actionLoading = False

  #----------------------------------------------------------------------------------------------------------
  def _saveAction(self):
    if self._actionLoading or self._loading: return
    indexes = self.table.selectionModel().selectedRows()
    if len(indexes) != 1: return
    row = indexes[0].row()
    item = self.table.item(row, 3)
    text = self.actionEditor.toPlainText()
    if item:
      if item.text() != text: item.setText(text)
    else:
      self.table.setItem(row, 3, cTableRow(text))

  #----------------------------------------------------------------------------------------------------------
  def swapTriggers(self, trigger_a: str, trigger_b: str):
    for cset in self.allMacroItems.values():
      modified = False
      for row in cset.data:
        if row[2] == trigger_a:
          row[2] = trigger_b
          modified = True
        elif row[2] == trigger_b:
          row[2] = trigger_a
          modified = True
      if modified:
        cset.save()
    self.updateTable()

  #----------------------------------------------------------------------------------------------------------
  def renameMacroSetFile(self, sset : cMacroSet):
    key = next((k for k, v in self.allMacroItems.items() if v is sset), None)
    if key != sset.text():
      μPrint.info(f"Renaming macro set from \"{C_SILVER}{key}</font>\" to \"{C_SILVER}{sset.text()}</font>\"...")
      os.rename(P_DEFAULT_MACRODIR+os.sep+key+P_DEFAULT_MACROEXT, P_DEFAULT_MACRODIR+os.sep+sset.text()+P_DEFAULT_MACROEXT)
      self.allMacroItems[sset.text()] = sset
      del self.allMacroItems[key]
