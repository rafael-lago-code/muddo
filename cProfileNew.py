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
from dataclasses import dataclass
from helpers.util import *
from helpers.cPrint import cPrint
from widgets.cOrb import cOrbSmall
from widgets.cGridLayout import cGridLayout
from types import SimpleNamespace
import os, subprocess, json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow


# {
#   "lastActiveShortcutSet": ["global", "asiaSet", "raritySet", "flutterSet", "hoitySet", "xenoSet", "appleSet"]
# }

@dataclass
class dLauncher:
  _gameExec   = QLineEdit()
  _protonExec = QLineEdit()
  _wineExec   = QLineEdit()
  _winePrefix = QLineEdit()
  _compatData = QLineEdit()
  _steamRoot  = QLineEdit()
  _backend    = QComboBox()
  _language   = QComboBox()
  _useHighRes = QCheckBox("use HighRes")
  _useDebug   = QCheckBox("enable debug")
  _backend.addItems(["Steam Proton", "Wine64", "Wine32"])
  _language.addItems(["English", "German", "French"])
  _btnProtonExec = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select Steam Proton executable")
  _btnCompatData = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select STEAM_COMPAT_DATA")
  _btnWineExec   = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select Wine executable") 
  _btnWinePrefix = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select WINEPREFIX")
  _btnSteamRoot  = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select STEAM_ROOT")
  _btnGameExec   = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select Dungeon Helper exec")

  gameExec   = _gameExec.text
  protonExec = _protonExec.text
  wineExec   = _wineExec.text
  winePrefix = _winePrefix.text
  compatData = _compatData.text
  steamRoot  = _steamRoot.text
  backend    = _backend.currentText
  language   = _language.currentText
  usesHighRes= _useHighRes.isChecked
  isDebugging= _useDebug.isChecked

#---------------------------------------------------------------------------------------------------------------
@dataclass
class dXSettings:
  _lastPreferences = {}
  _rememberPos=QCheckBox("Position")
  _rememberSize=QCheckBox("Size")
  _rememberDesktop=QCheckBox("Virtual desktop")
  _blackscreenFix=QCheckBox("Fix blackscreen at startup")
  _rememberMUDDOPos=QCheckBox("Position")
  _rememberMUDDOSize=QCheckBox("Size")
  _rememberMUDDODesktop=QCheckBox("Virtual desktop")
  _audioOptions=QComboBox()
  _borderOptions=QComboBox()
  _logOptions=QComboBox()
  _MUDDOLog=QComboBox()
  _borderOptions.addItems(["Remember", "Always borderless", "Never borderless"])
  _audioOptions.addItems(["Remember", "Always muted", "Never muted"])
  _logOptions.addItems(["Remember", "Always shown", "Never shown"])
  _MUDDOLog.addItems(["Remember", "Always shown", "Never shown"])

  remembersPos          = _rememberPos.isChecked
  remembersSize         = _rememberSize.isChecked
  remembersDesktop      = _rememberDesktop.isChecked
  fixesBlackscreen      = _blackscreenFix.isChecked
  remembersMUDDOPos     = _rememberMUDDOPos.isChecked
  remembersMUDDOSize    = _rememberMUDDOSize.isChecked
  remembersMUDDODesktop = _rememberMUDDODesktop.isChecked
  audioOptions          = _audioOptions.currentText
  borderOptions         = _borderOptions.currentText
  logOptions            = _logOptions.currentText

#---------------------------------------------------------------------------------------------------------------
@dataclass
class dPlugins:
  _dhExec         = QLineEdit()
  _milvianSHMPath = QLineEdit()
  _useDH          = QCheckBox("enable Dungeon Helper")
  _useMilvian     = QCheckBox("enable Milvian Bridge")
  _btnDHExec      = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually select DungeonHelper executable")
  _btnMilvianSHMPath = cOrbSmall(icon=P_ICON_OPENFOLDER, tooltip="Manually set path for Milvian Bridges")

  dhExec         = _dhExec.text
  milvianSHMPath = _milvianSHMPath.text
  usesDH         = _useDH.isChecked
  usesMilvian    = _useMilvian.isChecked

#---------------------------------------------------------------------------------------------------------------
@dataclass
class dSession:
  lastWorld = ""
  lastAccounts = []
  macros = []

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            P R O F I L E   D A T A 
#                                  
#
#---------------------------------------------------------------------------------------------------------------
class cProfileNew(QDialog):
  widgetID = "profile"
   
  def __init__(self, name : str, parent):
    super().__init__(parent)
    self.tab  = QTabWidget(self)
    self.name = name
    self.launcher = dLauncher()
    self.xsettings= dXSettings()
    self.plugins  = dPlugins()
    self.session   = dSession()
    # self.toolbar  = SimpleNamespace()

    self.initializeLayout()
    self.connectSignals()

  #----------------------------------------------------------------------------------------------------------
  def initializeLayout(self):
    self.setFixedSize(800,800)
    glauncher = cGridLayout()
    glauncher.appendRow([self.launcher.backend,    "Proton executable:", self.launcher.protonExec, self.launcher.btnProtonExec])
    glauncher.appendRow([self.launcher.language,   "STEAM_COMPAT_DATA:", self.launcher.compatData, self.launcher.btnCompatData])
    glauncher.appendRow([self.launcher.useDebug,   "STEAM_ROOT:",        self.launcher.steamRoot,  self.launcher.btnSteamRoot])
    glauncher.appendRow([self.launcher.useHighRes, "Game executable:",   self.launcher.gameExec,   self.launcher.btnGameExec])

    gxl = cGridLayout()
    gxl.appendRow([self.xsettings.rememberPos, self.xsettings.rememberSize, self.xsettings.rememberDesktop])
    gxl.appendRow(["Border:", ">", self.xsettings.borderOptions])
    gxl.appendRow(["Audio:",  ">", self.xsettings.audioOptions])
    gxl.appendRow(["Logs:",   ">", self.xsettings.logOptions])
    gxl.appendRow([">",   ">",     self.xsettings.blackscreenFix])
    gxr = cGridLayout()
    gxr.appendRow([self.xsettings.rememberMUDDOPos, self.xsettings.rememberMUDDOSize, self.xsettings.rememberMUDDODesktop])
    gxr.appendRow([" "])
    gxr.appendRow([" "])
    gxr.appendRow(["Logs:",   ">", self.xsettings.MUDDOLog])
    gxr.appendRow([" "])

    gbxl = QGroupBox(title="Game Client")
    gbxr = QGroupBox(title="μDDO")
    gbxl.setLayout(gxl)
    gbxr.setLayout(gxr)

    gplugins = cGridLayout()
    gplugins.appendRow([self.plugins.useDH,      "Dungeon Helper executable:", self.plugins.dhExec,         self.plugins.btnDHExec])
    gplugins.appendRow([self.plugins.useMilvian, "Milvian SHM Path:",          self.plugins.milvianSHMPath, self.plugins.btnMilvianSHMPath])

    self.tab.addTab(newVFrame([glauncher, "__stretch__"]), "Launcher")
    self.tab.addTab(newVFrame([newHLayout([gbxl, gbxr]), "__stretch__"]), "X && Audio")
    self.tab.addTab(newVFrame([gplugins, "__stretch__"]), "Plugins")
    self.setLayout(newVLayout([self.tab]))

  #----------------------------------------------------------------------------------------------------------
  def connectSignals(self):
    pass


