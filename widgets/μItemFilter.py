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
import glob
from types import SimpleNamespace
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QGridLayout, QLineEdit, QListWidgetItem, QListWidget, QTextEdit, QLabel, QFrame
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from widgets.μOrb import μOrbSmall
from widgets.μOrb import μBoxCheck
from helpers.μImageFactory import *
from widgets.μCombo import μCheckCombo, μAdvancedCombo
from widgets.μItemsTable import *
from helpers.μPrint import μPrint
from helpers.χDB import getAccountCharacters
from helpers.μStrings import *
from widgets.μText import μTextEdit
from μMilvian import *


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#
#   ❖  I T E M   F I L T E R
#
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μItemFilter(QWidget):
  allFilterScripts : dict = {}

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, parent, table: μItemsTable, getModeFilter):
    super().__init__(parent)
    self.table         = table
    self.getModeFilter = getModeFilter
    self.allFilterScripts = {}
    self.accountMap    = {}

    self.cb = SimpleNamespace()
    for f in ["Equipped", "Unequipped", "Unbound", "Bound", "Locked", "Unlocked", "Sellable", "Unsellable", "Name", "Description"]:
      setattr(self.cb, f.lower(), μBoxCheck(f))
    self.cb.aug0  = μBoxCheck('0')
    self.cb.aug1  = μBoxCheck('1')
    self.cb.aug2  = μBoxCheck('2')
    self.cb.aug3p = μBoxCheck('3+')

    for cb in self.cb.__dict__.keys():
      getattr(self.cb, cb).setChecked(True)
      getattr(self.cb, cb).stateChanged.connect(self.applyFilters)

    self.qualifier = μCheckCombo("Qualifier")
    for q in ["<Empty>", "Named", "Vendor", "Random", "Raid"]:
      self.qualifier.addCheckItem(q)

    self.augments = μCheckCombo("Augments")
    for n,i in zip(P_ITEM_AUGMENTS_NAME.values(), P_ITEM_AUGMENTS_ICON.values()):
      self.augments.addCheckItem(f"{n} {i}")

    self.storage = μCheckCombo("Storage")
    for n in P_STORAGE_NAMES.values():
      if n: self.storage.addCheckItem(f"{n}")

    self.accountSet = μBoxCheck('Accounts as sets')
    self.accountSet.setToolTip("Controls behaviour when filtering by an account in the \"Owners\" dropdown menu.<br><b>✓</b> includes all known characters in that account. <br><b>✗</b> only show items in this account's shared bank.<br>Update $HOME/.config/muDDO/extendedPreferences.yaml with accounts info.")

    self.owner     = μAdvancedCombo("Owner")
    self.itemType  = μAdvancedCombo("Type")
    self.text  = QLineEdit()
    self.btnClearSelection = μOrbSmall(icon=P_ICON_CLEAR, tooltip="Clear whole selection")

    hline = QFrame()
    hline.setFixedHeight(2)
    hline.setFrameShape(QFrame.Shape.HLine)
    g1 = QGridLayout()
    g1.addWidget(self.cb.name,        0, 0, 1, 1)
    g1.addWidget(self.cb.description, 0, 1, 1, 1)
    g1.addWidget(newHFrame([self.btnClearSelection,"Clear selection"]), 0, 2, 1, 2, Qt.AlignmentFlag.AlignRight)
    g1.addWidget(hline,    1, 0, 1, 4)
    g1.addWidget(self.cb.equipped,   2, 0, 1, 1)
    g1.addWidget(self.cb.locked,     2, 1, 1, 1)
    g1.addWidget(self.cb.sellable,   2, 2, 1, 1)
    g1.addWidget(self.cb.bound,      2, 3, 1, 1)
    g1.addWidget(self.cb.unequipped, 3, 0, 1, 1)
    g1.addWidget(self.cb.unlocked,   3, 1, 1, 1)
    g1.addWidget(self.cb.unsellable, 3, 2, 1, 1)
    g1.addWidget(self.cb.unbound,    3, 3, 1, 1)

    advFilters = newVFrame([newHLayout(["Filter by...", self.text]), g1,
                            newHFrame(["Augments Count:", self.cb.aug0, self.cb.aug1, self.cb.aug2, self.cb.aug3p]),
                            newHLayout([self.qualifier, self.itemType, self.storage]),
                            newHLayout([self.augments, self.owner, self.accountSet])])

    self.scriptList      = QListWidget()
    self.scriptLabel     = QLabel("Selected Filter Script:")
    self.btnNew    = μOrbSmall(icon=P_ICON_NEWDOC,    tooltip="Create a new filter script with the text currently in the editor")
    self.btnSave   = μOrbSmall(icon=P_ICON_SAVE,      tooltip="Save currently selected filter script.<br><b><i>Shortcut: Ctrl+S</b></i>.<br><b><i>Ctrl+Left</b></i> click to save all")
    self.btnDel    = μOrbSmall(icon=P_ICON_TRASH,     tooltip="Delete currently selected filter script - this action cannot be undone!")
    self.btnReload = μOrbSmall(icon=P_ICON_REFRESH,   tooltip="Reload currently selected script from file\nCtrl+Left click to reload all")
    self.btnApply  = μOrbSmall(icon=P_ICON_FILTER,    tooltip="Apply current filter.<br><b><i>Shortcut: Ctrl+Enter</b></i>.")
    self.btnHelp         = μOrbSmall(icon=P_ICON_QUESTION,  tooltip="Show a comprehensive help on how script work here (lol)")
    self.scriptEdit      = μTextEdit(syntax="filter")

    filtersContainer = newHSplitter([
      newHFrame([newVLayout(["Saved Filters:", self.scriptList]),
                 newVFrame(["__stretch__", self.btnApply, self.btnNew, self.btnSave,
                            self.btnDel, self.btnReload, self.btnHelp, "__stretch__"])]),
      newVFrame([self.scriptLabel, self.scriptEdit]),
      advFilters])
    filtersContainer.setSizes([300, 700, 100])

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(filtersContainer)
    self.setLayout(layout)

    self.btnClearSelection.clicked.connect(self.table.clearSelection)
    self.qualifier.changed.connect(self.applyFilters)
    self.owner.changed.connect(self.applyFilters)
    self.storage.changed.connect(self.applyFilters)
    self.itemType.changed.connect(self.applyFilters)
    self.augments.changed.connect(self.applyFilters)
    self.text.textEdited.connect(self.applyFilters)

    self.scriptList.itemChanged.connect(self.renameFilterScript)
    self.btnApply.clicked.connect(self.applyFilters)
    self.btnNew.clicked.connect(self.newFilterScript)
    self.btnSave.clicked.connect(self.saveFilterScript)
    self.btnSave.ctrlClicked.connect(self.saveAllFilterScripts)
    self.btnReload.clicked.connect(self.reloadFilterScript)
    self.btnReload.ctrlClicked.connect(self.reloadAllFilterScripts)
    self.btnDel.clicked.connect(self.deleteFilterScript)
    self.btnHelp.clicked.connect(self.showHelpWindow)
    self.scriptList.itemSelectionChanged.connect(self.setActiveFilterScript)
    self.scriptEdit.textChanged.connect(self.syncFilterScript)

    for seq, slot in [("Ctrl+S",      self.saveFilterScript),
                      ("Ctrl+Return", self.applyFilters),
                      ("Ctrl+Enter",  self.applyFilters)]:
      sc = QShortcut(QKeySequence(seq), self.scriptEdit)
      sc.setContext(Qt.ShortcutContext.WidgetShortcut)
      sc.activated.connect(slot)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def initialize(self):
    noneItem = μFilterItem("<None>", "")
    noneItem.setFlags(noneItem.flags() & ~Qt.ItemFlag.ItemIsEditable)
    self.scriptList.addItem(noneItem)

    allFiles = glob.glob(os.path.join(P_DEFAULT_FILTERSDIR, "*"+P_DEFAULT_FILTEREXT))
    for n in allFiles:
      name = os.path.splitext(os.path.basename(n))[0]
      if name == "<None>": continue
      self.appendFilterScript(μFilterItem(name, ""))

    self.scriptList.setCurrentItem(noneItem)

    try:
      from μWorlds import μWorldList
      self.accountMap = getAccountCharacters(μWorldList.getServerName())
    except Exception:
      self.accountMap = {}
    for accountName in self.accountMap:
      self.owner.addCheckItem(accountName)
      self.accountMap[accountName].add(accountName)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setVaultMode(self, enabled: bool):
    self.storage.setEnabled(enabled)
    self.accountSet.setEnabled(enabled)

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  F I L T E R
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def applyFilters(self, item: μItemData = None):
    scriptText = self.scriptEdit.toPlainText().lower()
    scriptText = " ".join(scriptText.strip().split())

    modeFilter = self.getModeFilter()
    safeContext = {
      "__builtins__": {},
      "len": len,
      "any": any,
      "all": all,
      "true": True,
      "false": False,
      "str": μString,
      "int": int,
      "float": float,
      "file": lambda name: fileContents(P_DEFAULT_FILTERSDIR+"/"+name+".list"),
    }

    filterText      = self.text.text().lower().strip()
    rawOwners       = [q.lower() for q in self.owner.getChecked()]
    if self.accountSet.isChecked():
      checkedOwners = set()
      for o in rawOwners:
        checkedOwners.update(self.accountMap.get(o, {o}))
    else:
      checkedOwners = set(rawOwners)
    checkedTypes    = [q.lower() for q in self.itemType.getChecked()]
    checkedQuals    = [q.lower() for q in self.qualifier.getChecked()]
    checkedAugs     = [q.lower() for q in self.augments.getChecked()]
    checkedStorage  = [q.lower() for q in self.storage.getChecked()] if self.storage.isEnabled() else "inventory"

    def _filterItem(item: μItemData):
      if modeFilter(item): return self.table.setRowHidden(row, True)

      if len(scriptText) > 0:
        try:
          S = μString
          itemContext = {
            "id"              : item._id,
            "name"            : S(item._name.lower()),
            "ownerid"         : item._ownerID,
            "owner"           : S(item._ownerName.lower()),
            "storage"         : S(P_STORAGE_NAMES[item._storageType].lower()),
            "weenieid"        : item._weenieID,
            "type"            : S(item._type.lower()),
            "quantity"        : item._quantity,
            "qualifier"       : S(item._qualifier.lower()),
            "valuecopper"     : item._valueCopper,
            "hardness"        : item._hardness,
            "durability"      : item._durability,
            "iconid"          : item._iconId,
            "icon"            : item._icon,
            "description"     : S(item._description.lower()),
            "minlevel"        : item._minLevel,
            "material"        : item._material,
            "isJunk"          : item._isJunk,
            "islocked"        : item._isLocked,
            "issellable"      : item._isSellable,
            "isminorartifact" : item._isMinorArtifact,
            "setbonus1"       : S(item._setBonus1.lower()),
            "setbonus2"       : S(item._setBonus2.lower()),
            "currentslot"     : item._currentSlot,
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
          μPrint.error("[μItemFilter]: error while evaluating filter script:", e)
          return

      textTarget = ""
      if self.cb.name.isChecked():        textTarget += item._name.lower() + " "
      if self.cb.description.isChecked(): textTarget += item.toolTip().lower() + " "

      if not (filterText=="" or filterText in textTarget): return self.table.setRowHidden(row, True)

      isEquipped = isinstance(item.slot(), str)
      if not self.cb.equipped.isChecked()   and     isEquipped: return self.table.setRowHidden(row, True)
      if not self.cb.unequipped.isChecked() and not isEquipped: return self.table.setRowHidden(row, True)

      if not self.cb.bound.isChecked()   and item._binding>0:  return self.table.setRowHidden(row, True)
      if not self.cb.unbound.isChecked() and item._binding==0: return self.table.setRowHidden(row, True)

      if not self.cb.locked.isChecked()   and item._isLocked==1: return self.table.setRowHidden(row, True)
      if not self.cb.unlocked.isChecked() and item._isLocked==0: return self.table.setRowHidden(row, True)

      if not self.cb.sellable.isChecked()   and item._isSellable==1: return self.table.setRowHidden(row, True)
      if not self.cb.unsellable.isChecked() and item._isSellable==0: return self.table.setRowHidden(row, True)

      itemAugs = [a for a in item.augments(textOnly=True) if a.lower() in checkedAugs]
      if len(itemAugs) == 0 and not self.cb.aug0.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) == 1 and not self.cb.aug1.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) == 2 and not self.cb.aug2.isChecked():  return self.table.setRowHidden(row, True)
      if len(itemAugs) >= 3 and not self.cb.aug3p.isChecked(): return self.table.setRowHidden(row, True)

      qualKey = item._qualifier.lower() if item._qualifier else "<empty>"
      if qualKey                   not in checkedQuals:  return self.table.setRowHidden(row, True)
      if item._ownerName.lower()   not in checkedOwners: return self.table.setRowHidden(row, True)
      if item._type.lower()        not in checkedTypes:  return self.table.setRowHidden(row, True)
      if checkedStorage is not None and P_STORAGE_NAMES.get(item._storageType, "").lower() not in checkedStorage:
        return self.table.setRowHidden(row, True)

      self.table.setRowHidden(row, False)

    if isinstance(item, μItemData):
      try:
        row = item.row()
      except RuntimeError:
        return
      _filterItem(item)
    else:
      for row in range(self.table.rowCount()):
        _filterItem(self.table.item(row, 0))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def updateDynamicFilters(self, item: μItemData):
    if item._ownerName: self.owner.addCheckItem(item._ownerName)
    if item._type:      self.itemType.addCheckItem(item._type)
    if item._qualifier: self.qualifier.addCheckItem(item._qualifier)

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  F I L T E R   S C R I P T S
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def newFilterScript(self):
    i = 1
    while f"NewSet{i}" in self.allFilterScripts:
      i += 1
    newFilter = μFilterItem(f"NewSet{i}", "")
    newFilter.save()
    self.appendFilterScript(newFilter)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def appendFilterScript(self, filter: μFilterItem):
    if filter.name in self.allFilterScripts: return
    filter.load()
    self.allFilterScripts[filter.name] = filter
    self.scriptList.addItem(filter)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def renameFilterScript(self, item: μFilterItem):
    if item.name == "<None>": return
    oldName = item.name
    item.rename()
    self.allFilterScripts[item.name] = item
    del self.allFilterScripts[oldName]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setActiveFilterScript(self):
    cfilter = self.scriptList.selectedItems()
    isEditable = bool(cfilter) and cfilter[0].name != "<None>"
    self.scriptEdit.setEnabled(isEditable)
    self.btnApply.setEnabled(isEditable)
    self.btnDel.setEnabled(isEditable)
    self.scriptEdit.setText(cfilter[0].content if isEditable else "")
    self.applyFilters()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveFilterScript(self):
    cfilter = self.scriptList.selectedItems()
    if len(cfilter)>0 and cfilter[0].name != "<None>": cfilter[0].save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveAllFilterScripts(self):
    for f in self.allFilterScripts.values():
      f.save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def syncFilterScript(self):
    cfilter = self.scriptList.selectedItems()
    if len(cfilter)>0 and cfilter[0].name != "<None>":
      cfilter[0].sync(self.scriptEdit.toPlainText())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def reloadFilterScript(self):
    cfilter = self.scriptList.selectedItems()
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
    selected = self.scriptList.selectedItems()
    if not selected: return
    filter: μFilterItem = selected[0]
    μPrint.info(f"Removing filter script \"{C_SILVER}{filter.name}</font>\"...")
    self.allFilterScripts.pop(filter.name, None)
    filename = P_DEFAULT_FILTERSDIR + os.sep + filter.name + P_DEFAULT_FILTEREXT
    try:
      os.remove(filename)
    except FileNotFoundError:
      pass
    except OSError as e:
      μPrint.error(f"[μItemFilter] failed to remove filter file \"{filename}\":", e)
    self.scriptList.takeItem(self.scriptList.row(filter))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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
    <br> ● storage: str
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
    <br> ● isJunk: bool
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
  def __init__(self, name: str, content: str):
    super().__init__()
    self.name = name
    self.setText(name)
    self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)
    self.content = content

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setActive(self, val: bool):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def rename(self):
    oldFilename = P_DEFAULT_FILTERSDIR + os.sep + self.name    + P_DEFAULT_FILTEREXT
    newFilename = P_DEFAULT_FILTERSDIR + os.sep + self.text()  + P_DEFAULT_FILTEREXT
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
      with open(filename, "r") as f:
        self.content = f.read()
    except Exception as e:
      μPrint.error(f"{C_RED}WARNING:</font> error loading filter from \"{filename}\"", e)
      self.content = ""
