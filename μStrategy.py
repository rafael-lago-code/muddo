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
from PyQt6.QtWidgets import QComboBox, QSplitter, QLineEdit, QLabel, QWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QTextOption, QKeySequence, QShortcut
from helpers import μEffects
from helpers.μImageFactory import *
from helpers.μStrings import μString
from helpers.μDict import μDict
from widgets.μGrid import μGridLayout
from μMilvian import μMilvian, μMilvianMeta
from helpers.μPrint import μPrint
from helpers.μMilvianPacket import μMilvianPacket, cPacker, μPhonyPacket, packetCommand, packetStatus, packetSignal
from widgets.μNetwork import *
from widgets.μFloating import μToggler
from widgets.μOrb import μOrb, μBoxCheck, μOrbSmall, μOrbTask
from widgets.μCheckCombo import μCheckCombo
from widgets.μText import μDisplayLabel, μFontDisplay, μTextEdit, μFontMono
import glob
import yaml
import math
import shutil
import sys, time
from collections import Counter


P_DECORATION_PARTYLEADER    = "decorations/partyLeader"
P_DECORATION_SERGEANT       = "decorations/sergeant"
P_DECORATION_REMOTE         = "decorations/remote"
P_DECORATION_DISCONNECTED   = "decorations/disconnected"
P_DECORATION_CAPTAIN        = "decorations/captain"
P_DECORATION_PET            = "decorations/pet"
P_DECORATION_CONNECTED      = "decorations/connected"
P_DECORATION_COMMANDER      = "decorations/commander"
P_DECORATION_WARNING        = "decorations/warning"
P_DECORATION_ERROR          = "decorations/error"
P_DECORATION_MAJORCOMMANDER = "decorations/majorcommander"
P_DECORATION_PAUSED         = "decorations/paused"
P_DECORATION_RESUMED        = "decorations/resumed"


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def sortZigZag(members: list) -> list:
  n = len(members)
  if n == 0: return []
  result = [None] * n
  result[0] = members[0]
  lo, hi, i = 1, n - 1, 1
  while lo <= hi and i < n:
    result[lo] = members[i]; i += 1; lo += 1
    if lo <= hi and i < n:
      result[hi] = members[i]; i += 1; hi -= 1
  return result


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  N O D E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μPartyNode(μNode):

  _DIAG = 1.0 / math.sqrt(2)

  @staticmethod
  def dataGet(name: str) -> μDict:
    return μDict(μMilvianMeta.partyPreferences.get(name, {}))

  @staticmethod
  def dataSet(name: str, field: str, value):
    μMilvianMeta.partyPreferences.set(f"{name}/{field}", value)
    μMilvianMeta.partyPreferences.save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, key: str, parent=None, bg : QPixmap = None, allowOutgoing: bool = True):
    super().__init__(label="", parent=parent, bg=bg, allowOutgoing=allowOutgoing)
    self.key   = key
    self.owner = None
    self.setLabel()
    entry = μPartyNode.dataGet(self.key)
    self.label = entry['nickname'] or self.label
    icon = entry['icon_path']
    self.decorations: list[tuple[QPixmap, str]] = []
    if icon and os.path.exists(icon):
      self.setBg(QPixmap(icon))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setLabel(self):
    if ":" in self.key:  # pet — key is "owner:id"
      self.owner = self.key.split(':')[0].lower()
      self.label = self.key
      self.id    = '#' + self.key.split(':')[1].lower()
      self.key   = self.owner+":pet"
    else:
      self.id    = self.key.lower()
      self.owner = None
      self.label = self.key.capitalize()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addDecoration(self, image: QPixmap, position: str, size: int = 36):
    scaled = image.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    self.decorations.append((scaled, position))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clearDecorations(self):
    self.decorations.clear()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _decorationXY(self, dec: QPixmap, pos: str) -> tuple[int, int]:
    cx, cy, r = self.center.x(), self.center.y(), self._radius
    d = dec.width()
    h = dec.height()
    diag = r * μPartyNode._DIAG
    coords = {
      'N':  (cx - d/2,        cy - r),
      'S':  (cx - d/2,        cy + r - h),
      'W':  (cx - r,          cy - h/2),
      'E':  (cx + r - d,      cy - h/2),
      'NE': (cx + diag - d/2, cy - diag - h/2),
      'NW': (cx - diag - d/2, cy - diag - h/2),
      'SE': (cx + diag - d/2, cy + diag - h/2),
      'SW': (cx - diag - d/2, cy + diag - h/2),
    }
    x, y = coords.get(pos, (cx - d/2, cy - h/2))
    return int(x), int(y)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def draw(self, edges, is_dragging: bool, painter: QPainter):
    super().draw(edges, is_dragging, painter)
    for dec, pos in self.decorations:
      x, y = self._decorationXY(dec, pos)
      painter.drawPixmap(x, y, dec)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  N O D E   P A N E L
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μPartyNodePanel(QWidget):

  def __init__(self, parent=None):
    super().__init__(parent)
    self._node     = None
    self._iconPath = None

    self.imgLabel = QLabel()
    self.imgLabel.setFixedSize(80, 80)
    self.imgLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.imgLabel.setStyleSheet("background-color: black;")

    self.nameEdit  = QLineEdit()
    self.nameEdit.setEnabled(False)
    self.nickEdit  = QLineEdit()
    self.nickEdit.setMinimumWidth(120)
    self.nickEdit.setPlaceholderText("Nickname")

    self.btnSave     = μOrbSmall(icon=P_ICON_SAVE,  tooltip="Save")
    self.btnEditIcon = μOrbSmall(icon=P_ICON_IMAGE, tooltip="Edit Image")
    self.btnClose    = μOrbSmall(icon=P_ICON_CLOSE, tooltip="Close")

    self.btnSave.clicked.connect(self.save)
    self.btnEditIcon.clicked.connect(self.editIcon)
    self.btnClose.clicked.connect(self.close)

    self.nickEdit.editingFinished.connect(self.save)

    g = μGridLayout()
    g.appendRow(["Key:",      ">", self.nameEdit])
    g.appendRow(["Nickname:", ">", self.nickEdit])
    self.setLayout(newVLayout(["Image:", newHLayout(["__stretch__", self.imgLabel, "__stretch__"]), g,
                               newHLayout([self.btnSave, self.btnEditIcon, self.btnClose]), "__stretch__"]))
    # self.setFixedWidth(160)
    self.setVisible(False)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def openFor(self, node):
    self._node = node
    self.nameEdit.setText(node.key)
    self._iconPath = None
    nick = node.label or node.key
    self.nickEdit.setText(nick)
    self._originalNick = nick
    if node.bg:
      px = node.bg.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
      self.imgLabel.setPixmap(px)
    else:
      self.imgLabel.clear()
    self.setVisible(True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _updateImage(self):
    if self._iconPath and os.path.exists(self._iconPath):
      px = QPixmap(self._iconPath).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
    else:
      px = QPixmap(80, 80)
      px.fill(Qt.GlobalColor.transparent)
    self.imgLabel.setPixmap(px)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def editIcon(self):
    from widgets.μIconSelectDialog import μIconSelectDialog
    dlg = μIconSelectDialog(self)
    if dlg.exec():
      path = dlg.selectedPath()
      if path:
        self._iconPath = path
        self._updateImage()
        self.save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def save(self):
    if not self._node: return
    nickChanged = self.nickEdit.text().strip() != self._originalNick
    iconChanged = bool(self._iconPath)
    if not nickChanged and not iconChanged: return
    if nickChanged:
      nick = self.nickEdit.text().strip() or self._originalNick
      μPartyNode.dataSet(self._node.key, 'nickname', nick)
      self._node.label   = nick
      self._originalNick = nick
    if iconChanged:
      μPartyNode.dataSet(self._node.key, 'icon_path', self._iconPath)
      self._node.setBg(QPixmap(self._iconPath))
    if μStrategy._widget: μStrategy._widget.board.update()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def close(self):
    self._node = None
    self.setVisible(False)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  S T R A T E G Y
#
#   This is a hybrid class.
#   One instance lives in cMainWindow. __init__ creates the widgets, most of the rest is supposed to be done
#   via class methods
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μStrategy(μToggler):
  widgetID = "Strategy"
  converter = None
  _widget   = None
  sigNetworkUpdate = pyqtSignal()

  decorationsCache = {}

  directives: μDict = μDict()   # {actor: μDict{key: value}}
  consensus:  μDict = μDict()   # {key: value}  — majority across actors; written only by updateConsensus()
  nodes     : μDict = μDict()   # {name: μPartyNode}
  _defaults:  dict  = None      # loaded once from docs/default.directives

  # metaBridges = {}  # reserved for future meta-bridge support

  partyLeader = None
  partyMembers = None
  partyLocal = None
  partyCaptains = None
  partyCommander = None

  # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
  #   ❖  C O N S T R U C T O R
  # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  def __init__(self, filename : str):
    super().__init__("Strategy", "dm_deneith")
    μStrategy._widget = self
    self.isDebugging = True
    self.logFileName = filename
    self.btnToggle    = μOrb(icon=P_ICON_TOGGLE, title="Toggle", tooltip="Toggle selected Strategies on/off.<br><b><i>Ctrl+click</b></i> to pause all instead.")
    self.btnRefresh   = μOrbTask(icon=P_ICON_REFRESH, title="Refresh", tooltip="Refresh party info")
    self.btnOffensive = μOrb(icon="swords", title="Offensive", tooltip="Set selected party members to aggressive")
    self.btnDefensive = μOrb(icon="shield", title="Defensive",  tooltip="Set selected party members to defensive")
    self.btnPassive   = μOrb(icon="zen", title="Passive",    tooltip="Set selected party members to passive (follow only)")

    self.showPets = μBoxCheck(title="Show Pets")
    self.directiveList = QComboBox()
    self.directiveList.setEditable(True)
    self.directiveList.setMinimumWidth(150)
    self.board = μNetwork(self)
    self.board.setMinimumWidth(450)

    self.directivesEditor = μTextEdit(syntax='yaml')
    self.directivesEditor.setMinimumWidth(250)
    self.directivesEditor.setVisible(False)
    self.directivesEditor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    self.directivesEditor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    self.directivesEditor.setWordWrapMode(QTextOption.WrapMode.NoWrap)
    self.directivesEditor.setFont(μFontMono())
    self.directivesEditor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    self.btnEditDirectives      = μOrbSmall(icon=P_ICON_EDIT,   tooltip="Show/hide directives editor")
    self.btnDuplicateDirectives = μOrbSmall(icon=P_ICON_DUPDOC, tooltip="Duplicate current directive")
    self.btnRemoveDirectives    = μOrbSmall(icon=P_ICON_TRASH,  tooltip="Delete current directive")

    self.directiveList.currentTextChanged.connect(self._saveDirectiveToSession)
    self.directiveList.currentTextChanged.connect(self.load)

    self.btnOffensive.setEnabled(False) # Not yet implemented
    # self.btnOffensive.setFont(μFontDisplay(8))
    self.btnDefensive.setEnabled(False)  # Not yet implemented
    self.btnPassive.setEnabled(False)    # Not yet implemented

    self.board.setEdgeStyle(width=4, arrow_size=20, color=QColor(200, 60, 60))
    self.btnRefresh.execute = μStrategy.refreshPartyInfo
    self.sigNetworkUpdate.connect(self.updateNetwork)
    self.showPets.stateChanged.connect(self.updateNetwork)
    self.btnEditDirectives.clicked.connect(lambda : self.directivesEditor.setVisible(not self.directivesEditor.isVisible()))
    self.btnDuplicateDirectives.clicked.connect(self.duplicateDirective)
    self.btnRemoveDirectives.clicked.connect(self.removeDirective)
    self.directivesEditor.editingFinished.connect(self.saveDirective)
    self.directiveList.lineEdit().editingFinished.connect(self.renameDirective)
    QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.saveDirective)

    self.btnToggle.clicked.connect(μStrategy.toggleStrategy)
    self.btnToggle.ctrlClicked.connect(μStrategy.pauseStrategy)
    
    self.nodePanel = μPartyNodePanel(self)
    self.nodePanel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    _boardSplitter = QSplitter(Qt.Orientation.Horizontal)
    _boardSplitter.addWidget(self.board)
    _boardSplitter.addWidget(vFrame(self.nodePanel, self.directivesEditor))

    _toolbar = hLayout(self.btnOffensive, self.btnDefensive, self.btnPassive, self.btnToggle, self.btnRefresh, self.showPets, "__stretch__",
                  vLayout(hLayout(μDisplayLabel("Directives:"), self.directiveList),
                      hLayout(self.btnDuplicateDirectives, self.btnRemoveDirectives, self.btnEditDirectives)))

    self.setLayout(newVLayout([_boardSplitter,_toolbar]))
  
  # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
  #   🞋  W I D G E T / I N S T A N C E   M E T H O D S 
  # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def populateDirectivesCombo(self):
    d = self.strategyPath()
    files = glob.glob(os.path.join(d, "*.directives"))
    if not files:
      μPrint.warning(f"[μStrategy] No strategy found in {d}. Creating one from defaults...")
      os.makedirs(d, exist_ok=True)
      shutil.copy("docs/default.directives", d)
      files = glob.glob(os.path.join(d, "*.directives"))

    for f in files:
      self.directiveList.addItem(os.path.splitext(os.path.basename(f))[0].strip())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _saveDirectiveToSession(self, name: str):
    from μSettings import μSettings
    session = getattr(μSettings, 'session', None)
    if session: session.setStrategyDirective(name)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def load(self, name: str = None):
    path = self.directivePath(name)
    parsed = μStrategy.parseDirectives(path)
    if parsed:
      μStrategy.directives.clear()
      μStrategy.updateDirectives(filename=path)
      μStrategy.updateConsensus()
    try:
      with open(path, 'r') as f:
        self.directivesEditor.setText(f.read())
    except Exception:
      pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def directivePath(self, name: str = None) -> str:
    name = name or self.directiveList.currentText()
    return os.path.join(self.strategyPath(), f"{name}.directives")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveDirective(self):
    if not self.directivesEditor.isVisible(): return
    try:
      with open(self.directivePath(), 'w') as f:
        f.write(self.directivesEditor.toPlainText())
    except Exception as e:
      μPrint.error(f"[μStrategy] save failed: {e}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def renameDirective(self):
    new_name = self.directiveList.lineEdit().text().strip()
    idx = self.directiveList.currentIndex()
    old_name = self.directiveList.itemText(idx)
    if not new_name or new_name == old_name: return
    old_path = self.directivePath(old_name)
    new_path = self.directivePath(new_name)
    try:
      os.rename(old_path, new_path)
      self.directiveList.setItemText(idx, new_name)
    except Exception as e:
      μPrint.error(f"[μStrategy] rename failed: {e}")
      self.directiveList.setItemText(idx, old_name)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def duplicateDirective(self):
    src_name = self.directiveList.currentText().strip()
    if not src_name: return
    base = src_name + "_copy"
    new_name = base
    i = 2
    while os.path.exists(self.directivePath(new_name)):
      new_name = f"{base}{i}"
      i += 1
    try:
      shutil.copy(self.directivePath(src_name), self.directivePath(new_name))
      self.directiveList.addItem(new_name)
      self.directiveList.setCurrentIndex(self.directiveList.count() - 1)
    except Exception as e:
      μPrint.error(f"[μStrategy] duplicate failed: {e}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def removeDirective(self):
    idx = self.directiveList.currentIndex()
    name = self.directiveList.itemText(idx)
    if not name or self.directiveList.count() <= 1: return
    try:
      os.remove(self.directivePath(name))
      self.directiveList.removeItem(idx)
    except Exception as e:
      μPrint.error(f"[μStrategy] remove failed: {e}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def updateNode(self, node : μPartyNode):
    node.clearDecorations()
    self.board.clearEdges(node, outgoing=True, incoming=False)
    self.updateStyle()
    node.setStyle(self.board.nodeStyle)

    name = μString(node.key.lower())
    if name == μStrategy.partyLeader:  node.addDecoration(μStrategy.getDecoration('partyLeader'), 'NE')
    if μStrategy.isPet(name):          node.addDecoration(μStrategy.getDecoration('pet'),         'SW')
    elif name != μStrategy.partyLocal: node.addDecoration(μStrategy.getDecoration('remote'),      'SW')

    if μStrategy.partyCommander and name == μStrategy.partyCommander and name == μStrategy.partyCaptains:
      node.addDecoration(μStrategy.getDecoration('majorcommander'), 'NW')
    elif μStrategy.partyCommander and name == μStrategy.partyCommander:
      node.addDecoration(μStrategy.getDecoration('commander'),      'NW')
    elif name == μStrategy.partyCaptains and name == μStrategy.partyLocal:
      node.addDecoration(μStrategy.getDecoration('captain'),        'NW')
    elif name == μStrategy.partyCaptains:
      node.addDecoration(μStrategy.getDecoration('sergeant'),       'NW')

    running = μStrategy.directives.get(node.id, {}).get('strategyRunning', False)
    if not running and name != μStrategy.partyCommander and not μStrategy.isPet(name) and name == μStrategy.partyLocal:
      node.addDecoration(μStrategy.getDecoration('paused'), 'E')

    myCaptain = μStrategy.directives.get(name, {}).get('captain', '')
    if myCaptain and myCaptain in μStrategy.nodes:
      μStrategy._widget.board.connectNodes(node, μStrategy.nodes[myCaptain])

    if node.owner and node.owner in μStrategy.nodes:
      μStrategy._widget.board.connectNodes(node, μStrategy.nodes[node.owner], EdgeStyle(dashed=True))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def updateStyle(self):
    if not μStrategy.partyMembers: return
    from μSettings import μSettings
    plugins = getattr(μSettings, 'plugins', None)
    radius = plugins.strategyFrameSize() if plugins else 36
    self.board.setNodeStyle(fg=getPixmap("circular_frame_fg").scaledToWidth(80, Qt.TransformationMode.SmoothTransformation),
                            radius=radius, innerRadius=int(radius * 0.75),
                            color_receives=QColor(0,0,0,0), color_incomings=QColor(0,0,0,0),
                            label=LabelStyle(position='bottom', shadow=True, font=μFontDisplay()))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def updateNetwork(self):
    if not μStrategy.partyMembers: return
    self.updateStyle()

    sortedMembers = []
    members = list(μStrategy.partyMembers)
    petMembers = []
    for name in [μStrategy.consensus.get('commander')]: # might add some other later
      if name and name in members:
        members.remove(name)
        sortedMembers.append(name)
    for p in sorted(μStrategy.partyLocal):
      if p in members:
        members.remove(p)
        sortedMembers.append(p)
    petMembers    += [n for n in members if μStrategy.isPet(n)]
    sortedMembers += sorted(n for n in members if not μStrategy.isPet(n))
    if self.showPets.isChecked(): sortedMembers += sorted(petMembers)

    def toId(n): return ('#' + n.split(':')[1].lower()) if ':' in n else n.lower()
    sorted_ids = {toId(n) for n in sortedMembers}
    for nid in set(μStrategy.nodes.keys()) - sorted_ids:
      del μStrategy.nodes[nid]

    self.board.clear()

    for name in sortZigZag(sortedMembers):
      nid = toId(name)
      if nid not in μStrategy.nodes:
        node = μPartyNode(key=name, allowOutgoing=not μStrategy.isPet(name) and name in μStrategy.partyLocal)
        node.sigConnected.connect(lambda target, src=node: μStrategy.updateCaptain(src, target))
        node.sigDisconnected.connect(lambda src=node: μStrategy.updateCaptain(src, None))
        node.sigDoubleClicked.connect(lambda n=node: self.nodePanel.openFor(n))
        μStrategy.nodes[nid] = node
      n = μStrategy.nodes[nid]
      self.board.nodes.append(n)
    self.board._nodeCount = len(self.board.nodes)
    self.board.recomputePositions()

    for node in μStrategy.nodes.values(): self.updateNode(node)
    self.board.update()
    
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setVisible(self, value : bool):
    if value: self.btnRefresh._start()
    super().setVisible(value)

  # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
  #   🞋  C L A S S   M E T H O D S
  # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  @classmethod
  def strategyPath(cls) -> str:
    from μSettings import μSettings
    plugins = getattr(μSettings, 'plugins', None)
    if plugins: return plugins.strategyPath().rstrip("/\\")
    return P_DEFAULT_CONFIGDIR + os.sep + "strategy"

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def isPet(cls, name): return ":" in name or name.startswith("#")
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def restoreSession(cls):
    if cls._widget is None: return
    from μSettings import μSettings
    saved = getattr(getattr(μSettings, 'session', None), 'strategyDirective', "")
    if saved:
      μStrategy._widget.populateDirectivesCombo()
      idx = cls._widget.directiveList.findText(saved)
      if idx >= 0: cls._widget.directiveList.setCurrentIndex(idx)
    cls.refreshAllFromStatus()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def updateParty(cls, data) -> bool:
    match = True
    leader  = μString(data['leaderName'].lower()) if data['leaderName'] else None
    members = {μString(m.lower()) for m in data['members']}

    if cls.partyLeader is None: cls.partyLeader = leader
    if cls.partyLeader != leader:
      match = False

    if cls.partyMembers is None: cls.partyMembers = members
    if cls.partyMembers != members:
      cls.partyMembers = cls.partyMembers | members
      match = False

    if cls.partyLocal is None: cls.partyLocal = set()
    cls.partyLocal = cls.partyLocal | {μString(data['self'].lower())}
      
    return match

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getDecoration(cls, name):
    if name in cls.decorationsCache: return cls.decorationsCache[name]
    pmap = getPixmap("decorations/"+name)
    pmap = μEffects.dropShadow(pmap,3,3,3,opacity=0.7)
    cls.decorationsCache[name] = pmap
    return pmap

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def clearNetwork(cls):
    if cls.partyMembers: cls.partyMembers.clear()
    if cls.partyLocal: cls.partyLocal.clear()
    if cls.partyCaptains: cls.partyCaptains.clear()
    cls.partyMembers = None
    cls.partyLocal = None
    cls.partyCaptains = None
    cls.partyLeader = None
    cls.partyCommander = None
    cls._widget.board.clear()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _loadDefaults(cls) -> dict:
    if cls._defaults is None:
      path = os.path.join(P_MUDDO_DIR, 'docs', 'default.directives')
      with open(path, 'r') as f:
        cls._defaults = yaml.safe_load(f)
    return cls._defaults

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def refreshPartyInfo(cls):
    bridges = μMilvianMeta.getBridges()
    if not bridges: return
    cls.clearNetwork()

    packets = {}
    for name, bridge in bridges.items():
      packets[name] = bridge.query(packetCommand.queryparty)

    timeout = 0
    while packets:
      done = [name for name, pack in packets.items()
              if pack.status not in (packetStatus.unknown, packetStatus.waiting)]
      for name in done:
        data = μMilvian.unpackPartyInfo(packets.pop(name))
        if data is None: continue
        data['self'] = μString(name)
        match = μStrategy.updateParty(data)
        μPrint.info(f"[μStrategy] \"{C_SILVER}{name.capitalize()}</font>\" reported its party {"with mismatches!" if not match else ""}")
      time.sleep(0.05)
      timeout += 50
      if timeout > 2000:
        μPrint.warning(f"[μStrategy] refreshPartyInfo timeout — no response from: {list(packets.keys())}")
        break

    if cls._widget: cls._widget.sigNetworkUpdate.emit()
    cls.refreshAllFromStatus()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def refreshFromStatus(cls, char_name: str):
    from helpers.μStatusReader import μStatusReader
    with μStatusReader(char_name) as r:
      if not r.isOpen or not r.hasStrategyData: return
      cls.directives[char_name.lower()] = μDict({
        'captain':              r.captain.lower(),
        'commander':            r.commander.lower(),
        'followMount':          r.followMount,
        'followRecall':         r.followRecall,
        'acceptParty':          r.acceptParty,
        'acceptRess':           r.acceptRess,
        'acceptQuest':          r.acceptQuest,
        'closeExplorerJournal': r.closeExplorerJournal,
        'followJump':           r.followJump,
        'followSelect':         r.followSelect,
        'followAttack':         r.followAttack,
        'followPortal':         r.followPortal,
        'followDirection':      r.followDirection,
        'followDialogue':       r.followDialogue,
        'stopDistance':         r.stopDistance,
        'autonomyTime':         r.autonomyTime,
        'refreshInterval':      r.refreshInterval,
        'strategyRunning':      r.strategyRunning,
      })
    cls.updateConsensus()
    if cls._widget: cls._widget.sigNetworkUpdate.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def refreshAllFromStatus(cls):
    for name in μMilvianMeta.getBridges():
      cls.refreshFromStatus(name)

  # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
  #   🞋  U P D A T E   D I R E C T I V E S
  # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  @classmethod
  def updateDirectives(cls, filename: str):
    parsed = cls.parseDirectives(filename)
    if not parsed: return
    for a in μMilvianMeta.getBridges():
      if a not in cls.directives: cls.directives[a] = μDict()
      cls.directives[a].update(parsed)
      # μStrategy.printDirective(cls.directives[a], a)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def updateConsensus(cls):
    defaults = cls._loadDefaults()
    all_keys = set(defaults.keys())
    for actor_data in cls.directives.values():
      all_keys.update(actor_data.keys())

    cls.consensus = μDict()
    for key in all_keys:
      values = [data[key] for data in cls.directives.values() if key in data]
      if values:
        winner_str = Counter(str(v) for v in values).most_common(1)[0][0]
        for v in values:
          if str(v) == winner_str:
            cls.consensus[key] = v
            break
      else:
        cls.consensus[key] = defaults.get(key)
    
    cls.partyCaptains = set()
    for member, drv in cls.directives.items():
      if drv['captain']: cls.partyCaptains.add(drv['captain'])
    if cls.consensus['captain']: cls.partyCaptains.add(cls.consensus['captain'])
    if cls.consensus['commander']: cls.partyCommander = cls.consensus['commander']

    # μStrategy.printDirective(cls.consensus, "consensus")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def toggleStrategy(cls, value="resume|pause"):
    bridges = μMilvianMeta.getBridges()
    selected = {n.id for n in μStrategy._widget.board.getSelected()} or set(μStrategy.nodes.keys())
    cmd = f"strategy({cls._widget.directiveList.currentText()}, toggle, state={value})"
    for name, b in bridges.items():
      if name in selected: b.execute(cmd)

  @classmethod
  def resumeStrategy(cls): μStrategy.toggleStrategy("resume")
  @classmethod
  def pauseStrategy(cls):  μStrategy.toggleStrategy("pause")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def updateCaptain(cls, nodeFrom : μPartyNode, nodeTo : μPartyNode = None):
    targetCaptain = nodeTo.id if nodeTo is not None else "none"
    if cls.directives.get(nodeFrom.id, {}).get('captain') == targetCaptain: return
    bridges = μMilvianMeta.getBridges()
    if nodeFrom.id not in bridges: return
    cmd = f"strategy({cls._widget.directiveList.currentText()}, set, captain={targetCaptain})"
    bridges[nodeFrom.id].execute(cmd)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def parseDirectives(cls, filename: str) -> dict:
    result = μDict()
    try:
      with open(filename, 'r') as f:
        data = yaml.safe_load(f)
      result.update({k: v for k, v in data.items() if k != 'directives'})
    except Exception as e:
      μPrint.error(f"[μStrategy] parseDirectives failed: {e}")
    return result

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def printDirective(d: dict, label: str = ""):
    if not d:
      μPrint.debug(f"[μStrategy] {label or 'directive'}: (empty)")
      return
    μPrint.debug(f"[μStrategy] ┌─ {label or 'directive'}")
    for k, v in d.items():
      μPrint.debug(f"[μStrategy] │  {k:<24} = {v}")
    μPrint.debug(f"[μStrategy] └{'─'*40}")