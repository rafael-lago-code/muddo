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
from PyQt6.QtWidgets import QTextEdit, QTabWidget, QComboBox, QSplitter
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QMetaObject, Qt
from PyQt6.QtGui import QColor, QTextOption, QKeySequence, QShortcut
from helpers import μEffects
from helpers.μImageFactory import *
from helpers.μStrings import splitGroups, guess, μString
from helpers.μDict import μDict
from μMilvian import μMilvian, μMilvianMeta
from helpers.μPrint import μPrint
from helpers.μMilvianPacket import μMilvianPacket, cPacker, μPhonyPacket, packetCommand, packetStatus, packetSignal
from widgets.μNetwork import μNetwork, μNode
from widgets.μFloating import μToggler
from widgets.μOrb import μOrb, μBoxCheck, μOrbSmall, μOrbTask
from widgets.μCheckCombo import μCheckCombo
from widgets.μTextEdit import μTextEdit, μFontMono
from datetime import datetime
import glob
import json
import shutil
import sys, time
from collections import Counter


P_DECORATION_PARTYLEADER    = "decoration_partyLeader"
P_DECORATION_SERGEANT       = "decoration_sergeant"
P_DECORATION_REMOTE         = "decoration_remote"
P_DECORATION_DISCONNECTED   = "decoration_disconnected"
P_DECORATION_CAPTAIN        = "decoration_captain"
P_DECORATION_PET            = "decoration_pet"
P_DECORATION_CONNECTED      = "decoration_connected"
P_DECORATION_COMMANDER      = "decoration_commander"
P_DECORATION_WARNING        = "decoration_warning"
P_DECORATION_ERROR          = "decoration_error"
P_DECORATION_MAJORCOMMANDER = "decoration_majorcommander"


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def guessValue(text: str):
  s = str(text).strip()
  if '|' in s: return s
  return guess(s)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def actorCommand(text: str) -> tuple[str, str]:
  s = str(text).strip()
  if ':' in s:
    actor, cmd = s.split(':', 1)
    return actor.strip(), cmd.strip()
  return 'all', s

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def strategyArgs(text: str) -> dict:
  out = {'_directive': '', '_action': 'toggle', '_state': None}
  for p in splitGroups(str(text), ','):
    p = str(p).strip()
    if not p: continue
    if '=' in p:
      k, v = p.split('=', 1)
      k, v = k.strip(), v.strip()
      if   k == 'directives': out['_directive'] = v
      elif k == 'action':     out['_action']    = v
      elif k == 'state':      out['_state']     = v
      else:                   out[k]            = guessValue(v)
    elif p.startswith('!'):   out[p[1:]]        = False
    elif p == 'toggle':       out['_action']    = 'toggle'
    elif p == 'set':          out['_action']    = 'set'
    elif p == 'resume':       out['_state']     = 'resume'
    elif p == 'pause':        out['_state']     = 'pause'
    elif not out['_directive']: out['_directive'] = p
    else:                       out[p]          = True
  return out


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  N O D E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μPartyNode(μNode):

  def __init__(self, name: str = None, parent=None, bg : QPixmap = None, allowOutgoing: bool = True):
    super().__init__(label=name, parent=parent, bg=bg, allowOutgoing=allowOutgoing)
    self.decorations: list[QPixmap] = []

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addDecoration(self, image: QPixmap):
    d = self._radius * 2
    self.decorations.append(image.scaled(d, d, Qt.AspectRatioMode.IgnoreAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clearDecorations(self):
    self.decorations.clear()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def draw(self, edges, is_dragging: bool, painter: QPainter):
    super().draw(edges, is_dragging, painter)
    for dec in self.decorations:
      dx = int(self.center.x() - dec.width()  / 2)
      dy = int(self.center.y() - dec.height() / 2)
      painter.drawPixmap(dx, dy, dec)


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
  sigPartyRefreshed = pyqtSignal()
  sigFromMacro      = pyqtSignal()

  decorationsCache = {}

  directives: μDict = μDict()   # {actor: μDict{key: value}}
  consensus:  μDict = μDict()   # {key: value}  — majority across actors; written only by updateConsensus()
  _defaults:  dict  = None      # loaded once from docs/default.directives

  # metaBridges = {}  # reserved for future meta-bridge support

  partyLeader = None
  partyMembers = None
  partyPets = None
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
    self.btnToggle = μOrb(icon=P_ICON_PLAY, title="Start", tooltip="Toggle Strategy on/off")
    self.btnRefresh = μOrbTask(icon=P_ICON_REFRESH, title="Refresh", tooltip="Refresh party info")

    self.showPets = μBoxCheck(title="Show Pets")
    self.directiveList = QComboBox()
    self.directiveList.setEditable(True)
    self.board = μNetwork(self)
    self.board.setMinimumWidth(450)

    self.directivesEditor = μTextEdit(syntax='json')
    self.directivesEditor.setMinimumWidth(250)
    self.directivesEditor.setVisible(False)
    self.directivesEditor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    self.directivesEditor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    self.directivesEditor.setWordWrapMode(QTextOption.WrapMode.NoWrap)
    self.directivesEditor.setFont(μFontMono())
    self.btnEditDirectives      = μOrb(icon=P_ICON_EDIT, title="Edit", tooltip="Show/hide directives editor")
    self.btnDuplicateDirectives = μOrbSmall(icon=P_ICON_DUPDOC, tooltip="Duplicate current directive")
    self.btnRemoveDirectives    = μOrbSmall(icon=P_ICON_TRASH,  tooltip="Delete current directive")


    self.directiveList.currentTextChanged.connect(self._saveDirectiveToSession)
    self.directiveList.currentTextChanged.connect(self.load)

    from μSettings import μSettings
    plugins = getattr(μSettings, 'plugins', None)
    radius = plugins.strategyFrameSize() if plugins else 36
    self.board.setNodeStyle(fg=getPixmap("circular_frame_fg").scaledToWidth(80, Qt.TransformationMode.SmoothTransformation),
                            radius=radius)
    self.board.setEdgeStyle(width=6, arrow_size=24)
    self.btnRefresh.execute = μStrategy.refreshPartyInfo
    self.sigPartyRefreshed.connect(self.updateNetwork, Qt.ConnectionType.QueuedConnection)
    self.sigFromMacro.connect(self.updateNetwork, Qt.ConnectionType.QueuedConnection)
    self.btnEditDirectives.clicked.connect(lambda : self.directivesEditor.setVisible(not self.directivesEditor.isVisible()))
    self.btnDuplicateDirectives.clicked.connect(self.duplicateDirective)
    self.btnRemoveDirectives.clicked.connect(self.removeDirective)
    self.directivesEditor.editingFinished.connect(self.saveDirective)
    self.directiveList.lineEdit().editingFinished.connect(self.renameDirective)
    QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.saveDirective)

    _boardSplitter = QSplitter(Qt.Orientation.Horizontal)
    _boardSplitter.addWidget(self.directivesEditor)
    _boardSplitter.addWidget(self.board)

    self.setLayout(newVLayout([newHLayout(["Directives:", self.directiveList, self.btnDuplicateDirectives, self.btnRemoveDirectives]), _boardSplitter,
                      newHLayout([self.btnEditDirectives,
                                  "__stretch__", self.btnToggle, self.btnRefresh, self.showPets])]))
  
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
    parsed = μStrategy.parseFromJson(path)
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
  @pyqtSlot()
  def updateNetwork(self):
    if not μStrategy.partyMembers: return
    captains  = μStrategy.partyCaptains or set()
    local     = μStrategy.partyLocal    or set()
    pets      = μStrategy.partyPets     or set()
    commander = μStrategy.partyCommander
    leader    = μStrategy.partyLeader

    P_CLASS_IMG="/home/holysword/.config/muDDO/icons/classes/45px-"
    sortedMembers = []
    members = list(μStrategy.partyMembers)
    petMembers = []
    for name in [μStrategy.consensus.get('commander'), μStrategy.partyLeader]:
      if name and name in members:
        members.remove(name)
        sortedMembers.append(name)
    for p in sorted(μStrategy.partyLocal):
      if p in members:
        members.remove(p)
        sortedMembers.append(p)
    for p in sorted(μStrategy.partyPets):
      if p in members:
        members.remove(p)
        petMembers.append(p)
    sortedMembers += sorted(members)
    if petMembers: sortedMembers += sorted(petMembers)

    self.board.clear()
    allNodes = {}
    for name in sortZigZag(sortedMembers):
      n = μPartyNode(name=name.capitalize(), allowOutgoing=name not in pets)
      allNodes[name] = n
      self.board.add(n)  # applies nodeStyle (sets _radius) before decorations are sized

      if name == leader:      n.addDecoration(μStrategy.getDecoration('partyLeader'))
      if name in pets:        n.addDecoration(μStrategy.getDecoration('pet'))
      elif name not in local: n.addDecoration(μStrategy.getDecoration('remote'))

      if   commander and name == commander and name in captains: n.addDecoration(μStrategy.getDecoration('majorcommander'))
      elif commander and name == commander:                      n.addDecoration(μStrategy.getDecoration('commander'))
      elif name in captains and name in local:                   n.addDecoration(μStrategy.getDecoration('captain'))
      elif name in captains:                                     n.addDecoration(μStrategy.getDecoration('sergeant'))
    
    for name, node in allNodes.items():
      captain = μStrategy.directives.get(name, {}).get('captain', '')
      if captain and captain in allNodes:
        μStrategy._widget.board.connectNodes(node, allNodes[captain])
  
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
    pets    = {μString(m.lower()) for m in data['pets']}

    if cls.partyLeader is None: cls.partyLeader = leader
    if cls.partyLeader != leader:
      match = False

    if cls.partyMembers is None: cls.partyMembers = members
    if cls.partyMembers != members:
      cls.partyMembers = cls.partyMembers | members
      match = False

    if cls.partyPets is None: cls.partyPets = pets
    if cls.partyPets != pets:
      cls.partyPets = cls.partyPets | pets
      match = False

    if cls.partyLocal is None: cls.partyLocal = set()
    cls.partyLocal = cls.partyLocal | {μString(data['self'].lower())}
      
    return match

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getDecoration(cls, name):
    if name in cls.decorationsCache: return cls.decorationsCache[name]
    pmap = getPixmap("decoration_"+name)
    pmap = μEffects.dropShadow(pmap,3,3,3,shadow_opacity=0.7)
    cls.decorationsCache[name] = pmap
    return pmap

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def clearNetwork(cls):
    if cls.partyMembers: cls.partyMembers.clear()
    if cls.partyPets: cls.partyPets.clear()
    if cls.partyLocal: cls.partyLocal.clear()
    if cls.partyCaptains: cls.partyCaptains.clear()
    cls.partyMembers = None
    cls.partyPets = None
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
        cls._defaults = json.load(f)
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
      if timeout > 1000:
        μPrint.warning(f"[μStrategy] refreshPartyInfo timeout — no response from: {list(packets.keys())}")
        break

    if cls._widget: cls._widget.sigPartyRefreshed.emit()
    cls.refreshAllFromStatus()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def refreshFromStatus(cls, char_name: str):
    from helpers.μStatusReader import μStatusReader
    print(f"[DEBUG] refreshFromStatus called for {char_name!r}, path={μStatusReader.filePath(char_name)!r}")
    with μStatusReader(char_name) as r:
      print(f"[DEBUG] isOpen={r.isOpen} hasStrategyData={r.hasStrategyData if r.isOpen else 'N/A'}")
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
      })
    cls.updateConsensus()
    if cls._widget:
      cls._widget.sigFromMacro.emit()
      QMetaObject.invokeMethod(cls._widget, 'updateNetwork', Qt.ConnectionType.QueuedConnection)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def refreshAllFromStatus(cls):
    for name in μMilvianMeta.getBridges():
      cls.refreshFromStatus(name)

  # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
  #   🞋  U P D A T E   D I R E C T I V E S
  #      
  #     Parse text (macro) or filename (JSON) and merge result into cls.directives.
  #     Toggle semantics: pipe-separated options cycle from current value; bare booleans flip
  # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  @classmethod
  def updateDirectives(cls, source: str = None, text: str = None, filename: str = None):
    if text is not None:
      parsed = cls.parseFromMacro(text)
    elif filename is not None:
      parsed = cls.parseFromJson(filename)
    else:
      return

    parsed.pop('_actor',     None)
    action = parsed.pop('_action',    'set')
    parsed.pop('_directive', None)
    parsed.pop('_state',     None)

    targets = [source] if source else list(μMilvianMeta.getBridges().keys())

    for a in targets:
      if a not in cls.directives: cls.directives[a] = μDict()
      current = cls.directives[a]

      for key, value in parsed.items():
        raw = str(value) if value is not None else ''
        has_pipe = '|' in raw

        if action == 'set':
          new_val = cls._coerce(raw.split('|')[0]) if has_pipe else value
          current[key] = new_val

        else:  # toggle
          if has_pipe:
            options  = [cls._coerce(x.strip()) for x in raw.split('|')]
            cur_val  = current.get(key)
            try:    idx = options.index(cur_val)
            except: idx = -1
            current[key] = options[(idx + 1) % len(options)]
          else:
            cur_val      = current.get(key, True)
            current[key] = not bool(cur_val)
      μStrategy.printDirective(current, a)

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

    μStrategy.printDirective(cls.consensus, "consensus")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def updateFromMacro(cls, source, text: str):
    cls.updateDirectives(source, text=text)
    cls.updateConsensus()   #  This is currently being called too many times, i.e. once per party member. Not critical but not elegant
    if cls._widget:
      cls._widget.updateNetwork()
      cls._widget.sigFromMacro.emit()

  
  # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
  #   🞋  P A R S E   F R O M   M A C R O   A N D   F R O M   J S O N
  #      
  #     Parse 'actor: strategy(directive, action, key=val, ...)' text.
  #     Returns {_actor, _action, _directive, [_state], key: value, ...}.
  #     Values may be pipe-separated strings ('a|b') — toggle semantics preserved."""
  # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  @classmethod
  def parseFromJson(cls, filename: str) -> dict:
    result = μDict()
    try:
      with open(filename, 'r') as f:
        data = json.load(f)
      result.update({k: v for k, v in data.items() if k != 'directives'})
    except Exception as e:
      μPrint.error(f"[μStrategy] parseFromJson failed: {e}")
    result['_actor']     = 'all'
    result['_action']    = 'set'
    result['_directive'] = filename
    return result

  # 🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
  @classmethod
  def parseFromMacro(cls, text: str) -> dict:
    text = text.strip()
    actor = 'all'
    if ':' in text:
      actor, text = text.split(':', 1)
      actor = actor.strip().lower()
      text  = text.strip()

    if text.lower().startswith('strategy(') and text.endswith(')'):
      content_str = text[9:-1].strip()
    else:
      content_str = text

    content_str = ' '.join(content_str.split())
    content = μString(content_str).dictionary()

    action = 'toggle'
    if 'toggle' in content: del content['toggle']; action = 'toggle'
    if 'set'    in content: del content['set'];    action = 'set'

    state = None
    if 'resume' in content: del content['resume']; state = 'resume'
    if 'pause'  in content: del content['pause'];  state = 'pause'

    directive = ''
    if 'directives' in content:
      directive = str(content.pop('directives'))
    else:
      tokens = μString(content_str).split(',')
      if tokens:
        first = str(tokens[0]).strip()
        if first and '=' not in first and first not in ('set', 'toggle', 'resume', 'pause'):
          directive = first
          content.pop(first, None)

    result = {'_actor': actor, '_action': action, '_directive': directive}
    if state: result['_state'] = state
    result.update(content)
    return result

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def _coerce(value):
    """Convert a string to int/float/bool if possible, else return as str."""
    if not isinstance(value, str): return value
    try:    return int(value)
    except: pass
    try:    return float(value)
    except: pass
    if value.lower() == 'true':  return True
    if value.lower() == 'false': return False
    return value

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def printDirective(d: dict, label: str = ""):
    if not d:
      μPrint.debug(f"[μStrategy] {label or 'directive'}: (empty)")
      return
    meta_keys = {'_actor', '_action', '_state', '_directive'}
    meta  = {k: v for k, v in d.items() if k in meta_keys}
    flags = {k: v for k, v in d.items() if k not in meta_keys}
    header = label or meta.get('_directive') or 'directive'
    actor  = meta.get('_actor', '')
    action = meta.get('_action', '')
    state  = meta.get('_state', '')
    tag    = ' | '.join(filter(None, [actor, action, state]))
    μPrint.debug(f"[μStrategy] ┌─ {header}{f'  [{tag}]' if tag else ''}")
    for k, v in flags.items():
      μPrint.debug(f"[μStrategy] │  {k:<24} = {v}")
    μPrint.debug(f"[μStrategy] └{'─'*40}")