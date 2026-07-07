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
from PyQt6.QtWidgets import QComboBox, QFileDialog, QGroupBox, QLineEdit, QSpinBox, QWidget, QSlider
from PyQt6.QtCore import QSettings
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
from widgets.μOrb import μOrbSmall
from widgets.μOrb import μBoxCheck
from widgets.μGrid import μGridLayout
import json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
P_SERIALIZABLE = (QLineEdit, μBoxCheck, QComboBox, QSpinBox, QSlider)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _getValue(w):
  if isinstance(w, QLineEdit): return w.text()
  if isinstance(w, μBoxCheck): return w.isChecked()
  if isinstance(w, QComboBox): return w.currentText()
  if isinstance(w, QSpinBox):  return w.value()
  if isinstance(w, QSlider):  return w.value()
  return None

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _setValue(w, v):
  if isinstance(w, QLineEdit):   w.setText(str(v) if v is not None else "")
  elif isinstance(w, μBoxCheck):
    if isinstance(v, str): w.setChecked(v.lower() == "true")
    else: w.setChecked(bool(v))
  elif isinstance(w, QComboBox):
    idx = w.findText(str(v))
    if idx >= 0: w.setCurrentIndex(idx)
  elif isinstance(w, QSpinBox):
    try: w.setValue(int(v))
    except (TypeError, ValueError): pass
  elif isinstance(w, QSlider):
    try: w.setValue(int(v))
    except (TypeError, ValueError): pass

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dSection():
  name = ""
  def __init__(self, state):
    self._state : QSettings = state
    allItems = dict(self.__dict__.items())
    # getter methods
    for wname, att in allItems.items():
      wname = wname[1:]
      if isinstance(att, QLineEdit): setattr(self, wname, att.text)
      if isinstance(att, μBoxCheck): setattr(self, wname, att.isChecked)
      if isinstance(att, QComboBox): setattr(self, wname, att.currentText)
      if isinstance(att, (QSpinBox, QSlider)): setattr(self, wname, att.value)

    # each modification saves to disk immediately
    for wname, att in allItems.items():
      wname = wname[1:]
      if isinstance(att, QLineEdit): att.editingFinished.connect(lambda a=att, w=wname: self.saveWidget(w, a.text()))
      if isinstance(att, μBoxCheck): att.stateChanged.connect(lambda a=False, w=wname: self.saveWidget(w, a))
      if isinstance(att, QComboBox): att.currentTextChanged.connect(lambda a="", w=wname: self.saveWidget(w, a))
      if isinstance(att, (QSpinBox, QSlider)): att.valueChanged.connect(lambda a=0, w=wname: self.saveWidget(w, a))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────---
  def saveWidget(self, key, value):
    self._state.setValue(f"{self.name}/{key}", value)
    self._state.sync()

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N   -   L A U N C H E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dLauncher(dSection):
  name = "launcher"
  def __init__(self, state):
    self.lblBackendExec = QLabel("Proton executable:")
    self.lblBackendPath = QLabel("STEAM_COMPAT_DATA:")
    self.lblBackendRoot = QLabel("STEAM_ROOT:")
    self._gameFullExec  = QLineEdit()
    self._protonExec    = QLineEdit()
    self._compatData    = QLineEdit()
    self._steamRoot     = QLineEdit()
    self._wineExec      = QLineEdit()  # not implemented
    self._winePrefix    = QLineEdit()  # not implemented
    self._backend       = QComboBox()  # not implemented
    self._language      = QComboBox()  # not implemented
    self._useHighRes    = μBoxCheck("use HighRes")
    self._useDebug      = μBoxCheck("enable debug")
    self._backend.addItems(["Steam Proton", "Wine64", "Wine32"])
    self._language.addItems(["English", "German", "French"])
    self.btnProtonExec = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select Steam Proton executable.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnCompatData = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select STEAM_COMPAT_DATA.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnWineExec   = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select Wine executable.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnWinePrefix = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select WINEPREFIX.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnSteamRoot  = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select STEAM_ROOT.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnGameExec   = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select Dungeon Helper exec (usually in <b>x64/dndclient64.exe)</b><br><b>Ctrl+Click</b> for attempting to automatically find it.")

    self._backend.setEnabled(False)
    self.lblBackendPath.setFixedWidth(160)
    self._language.setEnabled(False)
    self._backend.currentIndexChanged.connect(self.toggleBackend)
    self.toggleBackend()
    super().__init__(state)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────---  
  def gamePath(self):
    fullPath = self._gameFullExec.text()
    idx = fullPath.find("Dungeons & Dragons Online")
    return fullPath[:idx+len("Dungeons & Dragons Online")]
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────---  
  def gameExec(self):
    fullPath = self._gameFullExec.text()
    idx = fullPath.find("Dungeons & Dragons Online")
    return fullPath[idx+len("Dungeons & Dragons Online")+1:]
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────---  
  def command(self) -> str:
    #TODO implement Wine
    cmd  = f'STEAM_ROOT="{self.steamRoot()}" PROTON_LOG=1 '
    cmd += f'STEAM_COMPAT_DATA_PATH="{self.compatData()}" '
    cmd += f'STEAM_COMPAT_CLIENT_INSTALL_PATH="{self.compatData()}" '
    cmd += f'"{self.protonExec()}" run '
    return cmd
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────---  
  def toggleBackend(self):
    if self._backend.currentText() == "Steam Proton":
      self.lblBackendExec.setText("Proton executable:")
      self.lblBackendPath.setText("STEAM_COMPAT_DATA:")
      protonOn = True
    else:
      self.lblBackendExec.setText("Wine executable:")
      self.lblBackendPath.setText("WINEPREFIX:")
      protonOn = False

    for w in [self._protonExec, self._compatData, self._steamRoot, self.btnProtonExec, self.btnCompatData, self.btnSteamRoot, self.lblBackendRoot]:
      w.setEnabled(protonOn)
      w.setVisible(protonOn)
    for w in [self._wineExec, self._winePrefix, self.btnWineExec, self.btnWinePrefix]:
      w.setEnabled(not protonOn)
      w.setVisible(not protonOn)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N   -   X S E T T I N G S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dXSettings(dSection):
  name = "xsettings"
  def __init__(self, state):
    self._position    = μBoxCheck("Position")                        
    self._size        = μBoxCheck("Size")
    self._desktop     = μBoxCheck("Virtual desktop")               
    self._blackscreenFix = μBoxCheck("Fix blackscreen at startup") 
    self._MUDDOPos    = μBoxCheck("Position")                      
    self._MUDDOSize   = μBoxCheck("Size")                          
    self._MUDDODesktop= μBoxCheck("Virtual desktop")               
    self._audio       = QComboBox()
    self._border      = QComboBox()
    self._logs        = QComboBox()
    self._MUDDOLog    = QComboBox()
    self._border.addItems(["Remember", "Always borderless", "Never borderless"])
    self._audio.addItems(["Remember", "Always muted", "Never muted"])
    self._logs.addItems(["Remember", "Always shown", "Never shown"])
    self._MUDDOLog.addItems(["Remember", "Always shown", "Never shown"])
    
    self._MUDDOPos.setChecked(True)
    self._MUDDOSize.setChecked(True)
    self._MUDDOPos.setEnabled(False)
    self._MUDDOSize.setEnabled(False)
    self._MUDDODesktop.setEnabled(False)
    self._MUDDOLog.setEnabled(False)
    super().__init__(state)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N   -   P L U G I N
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dPlugins(dSection):
  name = "plugins"
  def __init__(self, state):
    self._dhExec           = QLineEdit()
    self._milvianSHMPath   = QLineEdit()                          # not implemented
    self._strategyPath     = QLineEdit()
    self._useDH            = μBoxCheck("enable Dungeon Helper")
    self._useMilvian       = μBoxCheck("enable Milvian Bridge")   # not implemented
    self._useStrategy      = μBoxCheck("enable Strategy")
    self.btnDHExec         = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select DungeonHelper executable")
    self.btnMilvianSHMPath = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually set path for Milvian Bridges")
    self.btnStrategyPath   = μOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually set path for Strategy (and directives)")
    self._strategyFrameSize = QSpinBox()
    self._strategyFrameSize.setValue(36) # default values
    self._strategyPath.setText(P_DEFAULT_CONFIGDIR+os.sep+"strategy/") # default values
    
    # This would be handy but very difficult to implement, specially the overlay part, since we cannot know
    # when they spawn and I will NOT create a daemon just for that
    # self._hideDHUI         = QComboBox()
    # self._hideDHOverlay    = QComboBox()
    # self._hideDHUI.addItems(["Remember", "Always borderless", "Never borderless"])
    # self._hideDHOverlay.addItems(["Remember", "Always borderless", "Never borderless"])

    self._useMilvian.setEnabled(False)
    self._milvianSHMPath.setEnabled(False)
    self.btnMilvianSHMPath.setEnabled(False)
    self._useDH.stateChanged.connect(self._dhExec.setEnabled)
    self._useDH.stateChanged.connect(self.btnDHExec.setEnabled)
    self._useStrategy.stateChanged.connect(self._strategyPath.setEnabled)
    self._useStrategy.stateChanged.connect(self.btnStrategyPath.setEnabled)
    self._useStrategy.stateChanged.connect(self._strategyFrameSize.setEnabled)
    super().__init__(state)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N   -   M A P
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dMap(dSection):
  name      = "map"
  _raw_keys = {'uiDetailsVisible', 'uiMapOpacity', 'uiPlayerOpacity', 'uiStaticOpacity', 'uiEntityOpacity'}
  def __init__(self, state):
    self._iconSize = QSpinBox()
    self._iconShadow = QLineEdit("")
    self._cartographers = QLineEdit("")
    self._mapZoom = QSpinBox()
    self._upscale = QSpinBox()

    self._refreshInterval = QSpinBox()
    self._mapZoom.setRange(25,500)
    self._mapZoom.setSingleStep(10)
    self._mapZoom.setValue(100)
    self._mapZoom.setSuffix("%")
    self._upscale.setRange(100,500)
    self._upscale.setSingleStep(50)
    self._upscale.setValue(400)
    self._upscale.setSuffix("%")
    self._iconSize.setValue(16)
    self._iconShadow.setEnabled(False)
    self._refreshInterval.setRange(100, 10000)
    self._refreshInterval.setSingleStep(100)
    self._refreshInterval.setValue(500)
    self._refreshInterval.setSuffix("ms")
    super().__init__(state)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N   -   T O O L B A R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dToolbar(dSection):
  name      = "toolbar"
  _raw_keys = {'x', 'y', 'w', 'h', 'geometry'}
  def __init__(self, state):
    self._macroNRows        = QSpinBox()
    self._macroNCols        = QSpinBox()
    self._macroNRows.setMinimum(1)
    self._macroNCols.setMinimum(1)
    self._macroFloating     = μBoxCheck("floating macros bar")
    self._macroFillRowFirst = μBoxCheck("fill rows first")
    self._macroFillMissing  = μBoxCheck("fill missing/inactive macros")
    self._transparentIcon   = μBoxCheck("enable transparent icons (magenta mask)")
    self._macroFloating.setVisible(False)   # Not implemented
    self._transparentIcon.setVisible(False) # Not implemented
    super().__init__(state)

  def saveWidgetGeometry(self, widget):
    p = widget.pos()
    s = widget.size()
    self._state.setValue("toolbar/x", p.x())
    self._state.setValue("toolbar/y", p.y())
    self._state.setValue("toolbar/w", s.width())
    self._state.setValue("toolbar/h", s.height())
    self._state.sync()

  def loadWidgetGeometry(self, widget):
    x = self._state.value("toolbar/x", None)
    y = self._state.value("toolbar/y", None)
    w = self._state.value("toolbar/w", None)
    h = self._state.value("toolbar/h", None)
    if x is None: return
    try:
      widget.move(int(x), int(y))
      widget.resize(int(w), int(h))
    except (TypeError, ValueError): pass

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E C T I O N   -   S E S S I O N
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class dSession(dSection):
  name = "session"
  def __init__(self, state):
    self.world              = ""
    self.accounts           = []
    self.macroSets          = []
    self.windowsPreferences = {}
    self.strategyDirective  = ""
    super().__init__(state)
  
  # ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setAccounts(self, selectedAccounts : list):
    self.accounts = selectedAccounts
    self._state.setValue("session/accounts", ", ".join(selectedAccounts))
    self._state.sync()

  # ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setWorld(self, world : str):
    self.world = world
    self._state.setValue("session/world", world)
    self._state.sync()

  # ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setMacroSets(self, macroSets : list):
    self.macroSets = macroSets
    self._state.setValue("session/macroSets", ", ".join(macroSets))
    self._state.sync()

  # ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  # ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setStrategyDirective(self, name : str):
    self.strategyDirective = name
    self._state.setValue("session/strategyDirective", name)
    self._state.sync()

  # ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setWindowsPreference(self, windowsPreferences : dict):
    self.windowsPreferences = windowsPreferences
    lines = [f'  {json.dumps(k)}: {json.dumps(list(v))}' for k, v in windowsPreferences.items()]
    self._state.setValue("session/windowsPreferences", "{\n" + ",\n".join(lines) + "\n}")
    self._state.sync()


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S E T T I N G S   P R O F I L E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μSettingsProfile(QWidget):
  widgetID = "profile"
  
  def __init__(self, name : str, parent = None):
    super().__init__(parent)
    self.name = name
    self._state   = QSettings(P_DEFAULT_CONFIGDIR + f"/profile_{self.name}.conf", QSettings.Format.IniFormat)
    self.launcher = dLauncher(self._state)
    self.xsettings= dXSettings(self._state)
    self.plugins  = dPlugins(self._state)
    self.session  = dSession(self._state)
    self.toolbar  = dToolbar(self._state)
    self.map      = dMap(self._state)
    self.confFile = self._state.fileName()
    
    self.initializeLayout()
    self.load()
    self.wireInternal()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def initializeLayout(self):
    # self.setFixedSize(800,800)
    glauncher = μGridLayout()
    glauncher.appendRow([self.launcher._backend,    newVLayout([self.launcher.lblBackendExec]), newVLayout([self.launcher._protonExec, self.launcher._wineExec]),   newVLayout([self.launcher.btnProtonExec, self.launcher.btnWineExec])])
    glauncher.appendRow([self.launcher._language,   newVLayout([self.launcher.lblBackendPath]), newVLayout([self.launcher._compatData, self.launcher._winePrefix]), newVLayout([self.launcher.btnCompatData, self.launcher.btnWinePrefix])])
    glauncher.appendRow([self.launcher._useDebug,   self.launcher.lblBackendRoot, self.launcher._steamRoot,  self.launcher.btnSteamRoot])
    glauncher.appendRow([self.launcher._useHighRes, "Game executable:",   self.launcher._gameFullExec,   self.launcher.btnGameExec])

    gxl = μGridLayout()
    gxl.appendRow([self.xsettings._position, self.xsettings._size, self.xsettings._desktop])
    gxl.appendRow(["Border:", ">", self.xsettings._border])
    gxl.appendRow(["Audio:",  ">", self.xsettings._audio])
    gxl.appendRow(["Logs:",   ">", self.xsettings._logs])
    gxl.appendRow([">",   ">",     self.xsettings._blackscreenFix])
    gxr = μGridLayout()
    gxr.appendRow([self.xsettings._MUDDOPos, self.xsettings._MUDDOSize, self.xsettings._MUDDODesktop])
    gxr.appendRow([" "])
    gxr.appendRow([" "])
    gxr.appendRow(["Logs:",   ">", self.xsettings._MUDDOLog])
    gxr.appendRow([" "])

    gbxl = QGroupBox(title="Game Client")
    gbxr = QGroupBox(title="μDDO")
    gbxl.setLayout(gxl)
    gbxr.setLayout(gxr)

    gplugins = μGridLayout()
    gplugins.appendRow([self.plugins._useDH,       "Dungeon Helper executable:", self.plugins._dhExec,         self.plugins.btnDHExec])
    gplugins.appendRow([self.plugins._useMilvian,  "Milvian SHM Path:",          self.plugins._milvianSHMPath, self.plugins.btnMilvianSHMPath])
    gplugins.appendRow([self.plugins._useStrategy, "Strategy Path:",             self.plugins._strategyPath,   self.plugins.btnStrategyPath])
    gplugins.appendRow(["Party frame radius:", self.plugins._strategyFrameSize])

    gtoolbar = μGridLayout()
    gtoolbar.appendRow(["Number of Rows:", self.toolbar._macroNRows, "Number of Columns:", self.toolbar._macroNCols])
    gtoolbar.appendRow([self.toolbar._macroFillRowFirst, ">", self.toolbar._macroFillMissing])

    gmap = μGridLayout()
    gmap.appendRow(["Icon Size:", self.map._iconSize, "Icon Shadow Colour:", self.map._iconShadow])
    gmap.appendRow(["Map Zoom:", self.map._mapZoom, "Defautl Cartographers:", self.map._cartographers])
    gmap.appendRow(["Upscale:", self.map._upscale, "Refresh Interval:", self.map._refreshInterval])

    self.wLauncher  = newVFrame([glauncher, "__stretch__"])
    self.wXAudio    = newVFrame([newHLayout([gbxl, gbxr]), "__stretch__"])
    self.wPlugins   = newVFrame([gplugins, "__stretch__"])
    self.wToolbar   = newVFrame([gtoolbar, "__stretch__"])
    self.wMap       = newVFrame([gmap, "__stretch__"])

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def sectionWidgets(self):
    return [self.wLauncher, self.wXAudio, self.wPlugins, self.wToolbar, self.wMap]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def wireInternal(self):
    self.launcher.btnProtonExec.clicked.connect(   lambda x : self.selectDialog(self.launcher._protonExec,    "Steam Proton executable", False))
    self.launcher.btnCompatData.clicked.connect(   lambda x : self.selectDialog(self.launcher._compatData,    "Steam Proton COMPAT_DATA path", True))
    self.launcher.btnWineExec.clicked.connect(     lambda x : self.selectDialog(self.launcher._wineExec,      "Wine executable", False))
    self.launcher.btnWinePrefix.clicked.connect(   lambda x : self.selectDialog(self.launcher._winePrefix,    "WINE_PREFIX path", True))
    self.launcher.btnSteamRoot.clicked.connect(    lambda x : self.selectDialog(self.launcher._steamRoot,     "STEAM_ROOT path", True))
    self.launcher.btnGameExec.clicked.connect(     lambda x : self.selectDialog(self.launcher._gameFullExec,  "DDO executable", False))
    self.plugins.btnDHExec.clicked.connect(        lambda x : self.selectDialog(self.plugins._dhExec,         "Dungeon Helper executable", False))
    self.plugins.btnMilvianSHMPath.clicked.connect(lambda x : self.selectDialog(self.plugins._milvianSHMPath, "Milvians SHM path", True))
    self.plugins.btnStrategyPath.clicked.connect(  lambda x : self.selectDialog(self.plugins._strategyPath,   "Strategy directives path", True))

    self.launcher.btnProtonExec.ctrlClicked.connect(   lambda x : self.autoDialog(self.launcher._protonExec,    "Steam Proton executable", False))
    self.launcher.btnCompatData.ctrlClicked.connect(   lambda x : self.autoDialog(self.launcher._compatData,    "Steam Proton COMPAT_DATA path", True))
    self.launcher.btnWineExec.ctrlClicked.connect(     lambda x : self.autoDialog(self.launcher._wineExec,      "Wine executable", False))
    self.launcher.btnWinePrefix.ctrlClicked.connect(   lambda x : self.autoDialog(self.launcher._winePrefix,    "WINE_PREFIX path", True))
    self.launcher.btnSteamRoot.ctrlClicked.connect(    lambda x : self.autoDialog(self.launcher._steamRoot,     "STEAM_ROOT path", True))
    self.launcher.btnGameExec.ctrlClicked.connect(     lambda x : self.autoDialog(self.launcher._gameFullExec,  "DDO executable", False))
    self.plugins.btnDHExec.ctrlClicked.connect(        lambda x : self.autoDialog(self.plugins._dhExec,         "Dungeon Helper executable", False))
    self.plugins.btnMilvianSHMPath.ctrlClicked.connect(lambda x : self.autoDialog(self.plugins._milvianSHMPath, "Milvians SHM path", True))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def load(self):
    if not self._state.allKeys():
      μPrint.info(f"[cSettingsProfile] no settings found in {self.confFile}. Creating with defaults...")
      self.loadFromDefaults()
      return

    try:
      for key in self._state.allKeys():
        parts = key.split("/", 1)
        if len(parts) != 2: continue
        sname, wname = parts
        if sname == "session": continue
        sobj = getattr(self, sname, None)
        if not isinstance(sobj, dSection): continue
        if wname in getattr(sobj, '_raw_keys', set()): continue
        wobj = getattr(sobj, f"_{wname}", None) or getattr(sobj, wname, None)
        if isinstance(wobj, P_SERIALIZABLE):
          _setValue(wobj, self._state.value(key))
        else:
          μPrint.error(f"[cProfile] widget \"{wname}\" (section \"{sname}\") does not exist.")

      self.session.world             = self._state.value("session/world",             "")
      self.session.strategyDirective = self._state.value("session/strategyDirective", "")
      accounts  = self._state.value("session/accounts",  "")
      macroSets = self._state.value("session/macroSets", "")
      self.session.accounts  = [a.strip() for a in accounts.split(",")  if a.strip()] if isinstance(accounts,  str) else accounts
      self.session.macroSets = [m.strip() for m in macroSets.split(",") if m.strip()] if isinstance(macroSets, str) else macroSets
      raw = self._state.value("session/windowsPreferences", "{}")
      try:
        parsed = json.loads(raw) if isinstance(raw, str) else {}
        self.session.windowsPreferences = {k: tuple(v) for k, v in parsed.items()}
      except Exception:
        self.session.windowsPreferences = {}
    except Exception as e:
      μPrint.error(f"[cSettingsProfile] error loading values from {self.confFile}", e)
    else:
      μPrint.info(f"Profile loaded from {self.confFile}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def loadFromDefaults(self):
    # do stuff
    self.launcher._useHighRes.setChecked(True)
    self.launcher._useDebug.setChecked(True)
    μPrint.info(f"{C_RED}Load from defaults not yet implemented!!!</font>")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def selectDialog(self, target : QLineEdit, title, dir = True):
    if dir: filename = QFileDialog.getExistingDirectory(self, f"Select {title}...", directory=target.text())
    else: filename = QFileDialog.getOpenFileName(self, f"Select {title}...", directory=target.text())
    if isinstance(filename,(list,tuple)): filename = filename[0]
    if filename:
      target.setText(filename)
      target.editingFinished.emit()
    else:
      μPrint.warning(f"[cSettingsProfile] invalid {title} selected, doing nothing...")
    
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def autoDialog(self, target : QLineEdit, title, dir = True):
    μPrint.warning(f"[cSettingsProfile] auto finding {title} is not yet implemented. Enter it manually for now.")

