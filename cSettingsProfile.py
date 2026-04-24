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
from PyQt6.QtWidgets import QComboBox, QDialog, QFileDialog, QCheckBox, QGroupBox, QLineEdit, QTabWidget, QWidget
from PyQt6.QtCore import QSettings
import cMilvian
from helpers.util import *
from helpers.cPrint import cPrint
from widgets.cFloating import cFloating
from widgets.cOrb import cOrbSmall
from widgets.cGridLayout import cGridLayout
from types import SimpleNamespace
import os, subprocess
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow


P_SERIALIZABLE = (QLineEdit, QCheckBox, QComboBox)


#---------------------------------------------------------------------------------------------------------------
#
#
#                                            P R O F I L E
#                                  
#   This is a static class. Don't instantiate it.
#---------------------------------------------------------------------------------------------------------------
class cProfile():
  previous = ""
  current = ""
  all = {}

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def switchProfile(cls, name):
    cls.launcher  = all[name].launcher
    cls.xsettings = all[name].xsettings
    cls.plugins   = all[name].plugins
    cls.session   = all[name].session

#----------------------------------------------------------------------------------------------------------
def _getValue(w):
  if isinstance(w, QLineEdit): return w.text()
  if isinstance(w, QCheckBox): return w.isChecked()
  if isinstance(w, QComboBox): return w.currentText()
  return None

#----------------------------------------------------------------------------------------------------------
def _setValue(w, v):
  if isinstance(w, QLineEdit):   w.setText(str(v) if v is not None else "")
  elif isinstance(w, QCheckBox):
    if isinstance(v, str): w.setChecked(v.lower() == "true")
    else: w.setChecked(bool(v))
  elif isinstance(w, QComboBox):
    idx = w.findText(str(v))
    if idx >= 0: w.setCurrentIndex(idx)

#---------------------------------------------------------------------------------------------------------------
class dSection():
  def __init__(self):
    allItems = dict(self.__dict__.items())
    for name, att in allItems.items():
      if isinstance(att, QLineEdit): setattr(self, name[1:], att.text)
      if isinstance(att, QCheckBox): setattr(self, name[1:], att.isChecked)
      if isinstance(att, QComboBox): setattr(self, name[1:], att.currentText)

#---------------------------------------------------------------------------------------------------------------
class dLauncher(dSection):
  def __init__(self):
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
    self._useHighRes    = QCheckBox("use HighRes")
    self._useDebug      = QCheckBox("enable debug")
    self._backend.addItems(["Steam Proton", "Wine64", "Wine32"])
    self._language.addItems(["English", "German", "French"])
    self.btnProtonExec = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select Steam Proton executable.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnCompatData = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select STEAM_COMPAT_DATA.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnWineExec   = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select Wine executable.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnWinePrefix = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select WINEPREFIX.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnSteamRoot  = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select STEAM_ROOT.<br><b>Ctrl+Click</b> for attempting to automatically find it.")
    self.btnGameExec   = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Select Dungeon Helper exec (usually in <b>x64/dndclient64.exe)</b><br><b>Ctrl+Click</b> for attempting to automatically find it.")

    self._backend.setEnabled(False)
    self.lblBackendPath.setFixedWidth(160)
    self._language.setEnabled(False)
    self._backend.currentIndexChanged.connect(self.toggleBackend)
    self.toggleBackend()
    super().__init__()

  #-------------------------------------------------------------------------------------------------------------  
  def gamePath(self):
    fullPath = self._gameFullExec.text()
    idx = fullPath.find("Dungeons & Dragons Online")
    return fullPath[:idx+len("Dungeons & Dragons Online")]
  
  #-------------------------------------------------------------------------------------------------------------  
  def gameExec(self):
    fullPath = self._gameFullExec.text()
    idx = fullPath.find("Dungeons & Dragons Online")
    return fullPath[idx+len("Dungeons & Dragons Online")+1:]
  
  #-------------------------------------------------------------------------------------------------------------  
  def command(self) -> str:
    #TODO implement Wine
    cmd  = f'STEAM_ROOT="{self.steamRoot()}" PROTON_LOG=1 '
    cmd += f'STEAM_COMPAT_DATA_PATH="{self.compatData()}" '
    cmd += f'STEAM_COMPAT_CLIENT_INSTALL_PATH="{self.compatData()}" '
    cmd += f'"{self.protonExec()}" run '
    return cmd
  
  #-------------------------------------------------------------------------------------------------------------  
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


#---------------------------------------------------------------------------------------------------------------
class dXSettings(dSection):
  def __init__(self):
    self._position    = QCheckBox("Position")                        
    self._size        = QCheckBox("Size")
    self._desktop     = QCheckBox("Virtual desktop")               
    self._blackscreenFix = QCheckBox("Fix blackscreen at startup") 
    self._MUDDOPos    = QCheckBox("Position")                      
    self._MUDDOSize   = QCheckBox("Size")                          
    self._MUDDODesktop= QCheckBox("Virtual desktop")               
    self._audio       = QComboBox()
    self._border      = QComboBox()
    self._logs        = QComboBox()
    self._MUDDOLog    = QComboBox()
    self._border.addItems(["Remember", "Always borderless", "Never borderless"])
    self._audio.addItems(["Remember", "Always muted", "Never muted"])
    self._logs.addItems(["Remember", "Always shown", "Never shown"])
    self._MUDDOLog.addItems(["Remember", "Always shown", "Never shown"])
    
    self._desktop.setEnabled(False)
    self._MUDDOPos.setChecked(True)
    self._MUDDOSize.setChecked(True)
    self._MUDDOPos.setEnabled(False)
    self._MUDDOSize.setEnabled(False)
    self._MUDDODesktop.setEnabled(False)
    self._MUDDOLog.setEnabled(False)
    self._audio.setEnabled(False)
    self._audio.setEnabled(False)
    self._border.setEnabled(False)
    self._logs.setEnabled(False)
    super().__init__()

#---------------------------------------------------------------------------------------------------------------
class dPlugins(dSection):
  def __init__(self):
    self._dhExec           = QLineEdit()
    self._milvianSHMPath   = QLineEdit()                          # not implemented
    self._useDH            = QCheckBox("enable Dungeon Helper")
    self._useMilvian       = QCheckBox("enable Milvian Bridge")   # not implemented
    self.btnDHExec         = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select DungeonHelper executable")
    self.btnMilvianSHMPath = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually set path for Milvian Bridges")

    self._useMilvian.setEnabled(False)
    self._milvianSHMPath.setEnabled(False)
    self.btnMilvianSHMPath.setEnabled(False)
    # self._useMilvian.stateChanged.connect(self._milvianSHMPath.setEnabled)
    # self._useMilvian.stateChanged.connect(self.btnMilvianSHMPath.setEnabled)
    self._useDH.stateChanged.connect(self._dhExec.setEnabled)
    self._useDH.stateChanged.connect(self.btnDHExec.setEnabled)
    super().__init__()

#---------------------------------------------------------------------------------------------------------------
class dSession(dSection):
  def __init__(self):
    self.world       = ""
    self.accounts    = []
    self.macroSets   = []
    self.windowsInfo = {}
    super().__init__()

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            P R O F I L E   D A T A
#
#
#---------------------------------------------------------------------------------------------------------------
class cSettingsProfile(QWidget):
  widgetID = "profile"

  def __init__(self, name : str, parent):
    super().__init__(parent)
    self.tab  = QTabWidget(self)
    self.name = name
    self.launcher = dLauncher()
    self.xsettings= dXSettings()
    self.plugins  = dPlugins()
    self.session  = dSession()
    self.state = QSettings(f"muDDO/newprofile_{self.name}")
    self.confFile = self.state.fileName()
    
    # Collects all saveable widgets (future-proof)
    self.sections = {}
    for sname, sobj in self.__dict__.items():
      if not isinstance(sobj, dSection): continue
      self.sections[sname] = {}
      for wname,wobj in sobj.__dict__.items():
        if not isinstance(wobj, P_SERIALIZABLE): continue
        name = wname[1:] if wname.startswith("_") else wname
        self.sections[sname][name] = wobj

    self.initializeLayout()
    self.load()
    self.wireInternal()

  #----------------------------------------------------------------------------------------------------------
  def initializeLayout(self):
    # self.setFixedSize(800,800)
    glauncher = cGridLayout()
    glauncher.appendRow([self.launcher._backend,    newVLayout([self.launcher.lblBackendExec]), newVLayout([self.launcher._protonExec, self.launcher._wineExec]),   newVLayout([self.launcher.btnProtonExec, self.launcher.btnWineExec])])
    glauncher.appendRow([self.launcher._language,   newVLayout([self.launcher.lblBackendPath]), newVLayout([self.launcher._compatData, self.launcher._winePrefix]), newVLayout([self.launcher.btnCompatData, self.launcher.btnWinePrefix])])
    glauncher.appendRow([self.launcher._useDebug,   self.launcher.lblBackendRoot, self.launcher._steamRoot,  self.launcher.btnSteamRoot])
    glauncher.appendRow([self.launcher._useHighRes, "Game executable:",   self.launcher._gameFullExec,   self.launcher.btnGameExec])

    gxl = cGridLayout()
    gxl.appendRow([self.xsettings._position, self.xsettings._size, self.xsettings._desktop])
    gxl.appendRow(["Border:", ">", self.xsettings._border])
    gxl.appendRow(["Audio:",  ">", self.xsettings._audio])
    gxl.appendRow(["Logs:",   ">", self.xsettings._logs])
    gxl.appendRow([">",   ">",     self.xsettings._blackscreenFix])
    gxr = cGridLayout()
    gxr.appendRow([self.xsettings._MUDDOPos, self.xsettings._MUDDOSize, self.xsettings._MUDDODesktop])
    gxr.appendRow([" "])
    gxr.appendRow([" "])
    gxr.appendRow(["Logs:",   ">", self.xsettings._MUDDOLog])
    gxr.appendRow([" "])

    gbxl = QGroupBox(title="Game Client")
    gbxr = QGroupBox(title="μDDO")
    gbxl.setLayout(gxl)
    gbxr.setLayout(gxr)

    gplugins = cGridLayout()
    gplugins.appendRow([self.plugins._useDH,      "Dungeon Helper executable:", self.plugins._dhExec,         self.plugins.btnDHExec])
    gplugins.appendRow([self.plugins._useMilvian, "Milvian SHM Path:",          self.plugins._milvianSHMPath, self.plugins.btnMilvianSHMPath])

    self.tab.addTab(newVFrame([glauncher, "__stretch__"]), "Launcher")
    self.tab.addTab(newVFrame([newHLayout([gbxl, gbxr]), "__stretch__"]), "X && Audio")
    self.tab.addTab(newVFrame([gplugins, "__stretch__"]), "Plugins")
    self.setLayout(newVLayout([self.tab]))

  #----------------------------------------------------------------------------------------------------------
  def wireInternal(self):
    self.launcher.btnProtonExec.clicked.connect(    lambda x : self.selectDialog(self.launcher._protonExec,    "Steam Proton executable", False))
    self.launcher.btnCompatData.clicked.connect(    lambda x : self.selectDialog(self.launcher._compatData,    "Steam Proton COMPAT_DATA path", True))
    self.launcher.btnWineExec.clicked.connect(      lambda x : self.selectDialog(self.launcher._wineExec,      "Wine executable", False))
    self.launcher.btnWinePrefix.clicked.connect(    lambda x : self.selectDialog(self.launcher._winePrefix,    "WINE_PREFIX path", True))
    self.launcher.btnSteamRoot.clicked.connect(     lambda x : self.selectDialog(self.launcher._steamRoot,     "STEAM_ROOT path", True))
    self.launcher.btnGameExec.clicked.connect(      lambda x : self.selectDialog(self.launcher._gameFullExec,      "DDO executable", False))
    self.plugins.btnDHExec.clicked.connect(         lambda x : self.selectDialog(self.plugins._dhExec,         "Dungeon Helper executable", False))
    self.plugins.btnMilvianSHMPath.clicked.connect( lambda x : self.selectDialog(self.plugins._milvianSHMPath, "Milvians SHM path", True))

    self.launcher.btnProtonExec.ctrlClicked.connect(    lambda x : self.autoDialog(self.launcher._protonExec,    "Steam Proton executable", False))
    self.launcher.btnCompatData.ctrlClicked.connect(    lambda x : self.autoDialog(self.launcher._compatData,    "Steam Proton COMPAT_DATA path", True))
    self.launcher.btnWineExec.ctrlClicked.connect(      lambda x : self.autoDialog(self.launcher._wineExec,      "Wine executable", False))
    self.launcher.btnWinePrefix.ctrlClicked.connect(    lambda x : self.autoDialog(self.launcher._winePrefix,    "WINE_PREFIX path", True))
    self.launcher.btnSteamRoot.ctrlClicked.connect(     lambda x : self.autoDialog(self.launcher._steamRoot,     "STEAM_ROOT path", True))
    self.launcher.btnGameExec.ctrlClicked.connect(      lambda x : self.autoDialog(self.launcher._gameFullExec,      "DDO executable", False))
    self.plugins.btnDHExec.ctrlClicked.connect(         lambda x : self.autoDialog(self.plugins._dhExec,         "Dungeon Helper executable", False))
    self.plugins.btnMilvianSHMPath.ctrlClicked.connect( lambda x : self.autoDialog(self.plugins._milvianSHMPath, "Milvians SHM path", True))

    for sname, sobj in self.sections.items():
      for wname, wobj in sobj.items():
        if isinstance(wobj, QLineEdit):   wobj.editingFinished.connect(self.onWidgetChanged)
        elif isinstance(wobj, QCheckBox): wobj.toggled.connect(self.onWidgetChanged)
        elif isinstance(wobj, QComboBox): wobj.currentIndexChanged.connect(self.onWidgetChanged)

  #----------------------------------------------------------------------------------------------------------
  def onWidgetChanged(self, *_):
    self.save()

  #----------------------------------------------------------------------------------------------------------
  def wire(self, main : cMainWindow):
    self.plugins._useDH.stateChanged.connect(main.dh.orb.setEnabled)
    self.plugins._useMilvian.stateChanged.connect(main.macros.toggler.setEnabled)
    self.plugins._useMilvian.stateChanged.connect(main.macros.daemon.orb.setEnabled)
    self.plugins._useMilvian.stateChanged.connect(main.storageManager.toggler.setEnabled)
    self.plugins._dhExec.editingFinished.connect( lambda : cMilvian.setup(self.plugins.dhExec(), self.plugins.milvianSHMPath()))

  #----------------------------------------------------------------------------------------------------------
  def unwire(self, main : cMainWindow):
    pass

  #----------------------------------------------------------------------------------------------------------
  def aggregate(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def propagate(self):
    pass

  # #----------------------------------------------------------------------------------------------------------
  # def getValue(self, w):
  #   if isinstance(w, str):
  #     names = w.split('.')
  #     try:
  #       return _getValue(self.sections[names[0][names[1]]])
  #     except:
  #       return None
  #   else: return _getValue(w)

  # #----------------------------------------------------------------------------------------------------------
  # def setValue(self, w, v):
  #   if isinstance(w, str):
  #     names = w.split('.')
  #     try:
  #       _setValue(self.sections[names[0][names[1]]], v)
  #     except:
  #       return None
  #   else: return _setValue(w, v)

  #==========================================================================================================
  #  Persistence
  #==========================================================================================================
  def load(self):
    if not self.state.allKeys():
      cPrint.info(f"cProfileNew.loadFromFile: no settings found in {self.confFile}. Creating with defaults...")
      self.loadFromDefaults()
      return

    try:
      for sname, sobj in self.sections.items():
        for wname, wobj in sobj.items():
          if self.state.contains(f"{sname}/{wname}"):
            _setValue(wobj, self.state.value(f"{sname}/{wname}"))
          else:
            cPrint.warning(f"[cProfile] key \"{wname}\" not found in settings. Using default.")

      self.session.world       = self.state.value("session/world",       "")
      self.session.accounts    = self.state.value("session/accounts",    [])
      self.session.macroSets   = self.state.value("session/macroSets",   [])
      self.session.windowsInfo = self.state.value("session/windowsInfo", {})
    except Exception as e:
      cPrint.error(f"cProfileNew.loadFromFile: error applying values from {self.confFile}", e)
    else:
      cPrint.info(f"Profile loaded from {self.confFile}")

  #----------------------------------------------------------------------------------------------------------
  def loadFromDefaults(self):
    # do stuff
    self.launcher._useHighRes.setChecked(True)
    self.launcher._useDebug.setChecked(True)
    cPrint.info(f"{C_RED}Load from defaults not yet implemented!!!</font>")
    self.save()

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    for sname, sobj in self.sections.items():
      for wname, wobj in sobj.items():
        self.state.setValue(f"{sname}/{wname}", _getValue(wobj))

    self.state.setValue("session/world",       self.session.world)
    self.state.setValue("session/accounts",    self.session.accounts)
    self.state.setValue("session/macroSets",   self.session.macroSets)
    self.state.setValue("session/windowsInfo", self.session.windowsInfo)

    self.state.sync()
    if self.state.status() != QSettings.Status.NoError:
      cPrint.error(f"cProfileNew.saveToFile: could not write {self.confFile}")
    else:
      cPrint.info(f"Profile saved to {self.confFile}")

  #----------------------------------------------------------------------------------------------------------
  def selectDialog(self, target : QLineEdit, title, dir = True):
    if dir: filename = QFileDialog.getExistingDirectory(self, f"Select {title}...", directory=target.text())
    else: filename = QFileDialog.getOpenFileName(self, f"Select {title}...", directory=target.text())
    if isinstance(filename,(list,tuple)): filename = filename[0]
    if filename:
      target.setText(filename)
      target.editingFinished.emit()
    else:
      cPrint.warning(f"[cProfile] invalid {title} selected, doing nothing...")
    
  #----------------------------------------------------------------------------------------------------------
  def autoDialog(self, target : QLineEdit, title, dir = True):
    cPrint.warning(f"[cProfile] auto finding {title} is not yet implemented. Enter it manually for now.")

  # #----------------------------------------------------------------------------------------------------------
  # def propagate(self):
  #   if self.lastWorld: self.main.credentials.selectWorld(self.lastWorld)
  #   if self.lastAccounts: self.main.credentials.selectAccounts(self.lastAccounts)
  #   self.main.patch.updateTimestamp()
  
  # #----------------------------------------------------------------------------------------------------------
  # def aggregate(self):
  #   self.lastWorld = self.main.credentials.getSelectedWorld()
  #   self.lastAccounts = self.main.credentials.getSelectedAccounts()