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
from PyQt6.QtWidgets import QComboBox, QTabWidget, QWidget, QCheckBox, QGroupBox, QGridLayout, QTextEdit
from PyQt6.QtCore import QSettings, pyqtSignal
from cSettingsProfile import cSettingsProfile
from helpers.cPrint import cPrint
from widgets.cOrb import cOrbSmall
from helpers.util import *
from widgets.cToggler import cToggler
import os, json, glob
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            S E T T I N G S
#                                  
#   This is a hybrid class.
#   One instance lives in cMainWindow. __init__ calls cSettings.setup. Most of the time just use it as a
#   static class, use cSettings.widget for the instance.
#---------------------------------------------------------------------------------------------------------------
class cSettings(cToggler):
  widget : cSettings = None
  sigProfileChanged = pyqtSignal(cSettingsProfile, str)
  widgetID = "settings"
  lastProfile : str = ""
  multiAccount : bool = False
  profiles : dict[str, cSettingsProfile] = {}  # This will hold all profiles
  hiddenLayer = None # QVBoxLayout()
  profileList = None # QComboBox()
  profileMain = None # QComboBox()
  profile = None


  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(cls, widget : cSettings):
    cls.widget = widget
    cls.hiddenLayer = QVBoxLayout()
    cls.profileMain = QComboBox()
    cls.profileMain.setMinimumWidth(200)
    cls.profileList = QComboBox()
    cls.profileList.setEditable(True)
    cls.profileList.setMinimumWidth(200)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def addProfile(cls, name):
    if cls.profiles.get(name): return
    try:
      newProfile = cSettingsProfile(name, cls.widget)
      cls.profiles[name] = newProfile
      cls.hiddenLayer.addWidget(newProfile)
      cls.profileList.addItem(name)
      cls.profileMain.addItem(name)
      newProfile.setVisible(False)
    except Exception as e:
      cPrint.error(f"[cSettings] failed to load profile \"{name}\". Skipping it...", e)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def getWidget(cls) -> cSettings:
    return cls.widget
  
  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def syncProfileLists(cls, source="settings"):
    try:
      cls.profileList.currentIndexChanged.disconnect()
      cls.profileMain.currentIndexChanged.disconnect()
    except: pass

    if source=="settings":
      name = cls.profileList.currentText()
      idx = cls.profileList.currentIndex()
      cls.profileMain.setCurrentIndex(idx)
    else:
      name = cls.profileMain.currentText()
      idx = cls.profileMain.currentIndex()
      cls.profileList.setCurrentIndex(idx)

    cls.profileList.currentIndexChanged.connect(lambda : cls.syncProfileLists("settings"))
    cls.profileMain.currentIndexChanged.connect(lambda : cls.syncProfileLists("main"))

    if not name: return
    if name in cls.profiles.keys():
      cSettings.switchProfile(name)
    else:
      cPrint.warning(f"Trying to change to profile \"{name}\", but it was not found! Doing nothing instead...")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def switchProfile(cls, name):
    cls.profile   = cls.profiles[name]
    cls.launcher  = cls.profiles[name].launcher
    cls.xsettings = cls.profiles[name].xsettings
    cls.plugins   = cls.profiles[name].plugins
    cls.session   = cls.profiles[name].session

    if cls.lastProfile in cls.profiles.keys():
      cls.profiles[cls.lastProfile].setVisible(False)
    cls.profiles[name].setVisible(True)
    # cls.main.patch.updateTimestamp()
    cls.widget.sigProfileChanged.emit(cls.profiles[name], cls.lastProfile)
    cls.lastProfile = name

  #----------------------------------------------------------------------------------------------------------
  def __init__(self, main : cMainWindow):
    super().__init__("&Settings", P_ICON_GEARSTACK, main)
    self.toggler.setToolTip("Toggle Settings UI")
    self.main = main
    cSettings.setup(self)

    profileLbl = QLabel("Profile: ")
    profileLbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

    self.btnNew = cOrbSmall(icon=P_ICON_DUPDOC, tooltip="Save current settings and profile")
    self.btnSave = cOrbSmall(icon=P_ICON_SAVE, tooltip="Save current settings and profile")
    self.btnRemoveProfile = cOrbSmall(icon=P_ICON_TRASH, tooltip="Delete current profile and its associated files (main settings remain untouched)")
    self.btnReload = cOrbSmall(icon=P_ICON_REFRESH, tooltip="Reload current profile and all settings from file")

    self.setLayout(newVLayout([self.hiddenLayer, newHLayout(["__stretch__", "Profile: ", self.profileList, self.btnNew,
                            self.btnSave, self.btnRemoveProfile, self.btnReload, "__stretch__"]), "__stretch__"]))
    
  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.load()
    self.btnSave.clicked.connect(self.save)
    self.btnRemoveProfile.clicked.connect(self.removeProfile)
    self.btnReload.clicked.connect(self.load)
    self.profileList.currentIndexChanged.connect(lambda : cSettings.syncProfileLists("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : cSettings.syncProfileLists("main"))

  #----------------------------------------------------------------------------------------------------------
  def removeProfile(self):
    print("   removeProfile removeProfile vremoveProfile NOOOOOOOOOOOOOOOOT IMPELMENETEEEEEEEEEEEED!!!")
    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + self.profileList.lineEdit().text() + ".json"
    try:
      idx = self.profileList.findText(self.profileList.lineEdit().text(), QtCore.Qt.MatchFlag.MatchExactly)
      if idx >= 0:
        self.profileList.removeItem(idx)
        self.profileMain.removeItem(idx)
      os.remove(filename)
    except:
      pass

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    self.lastProfile  = self._state.value("lastProfile", "")         # goes in the "General" section of the settings file
    self.multiAccount = self._state.value("multiAccount") == "true"  # goes in the "General" section of the settings file

    self.main.credentials.multiAccount.setChecked(self.multiAccount)
    self.main.credentials.updateMultiAccount()
    
    try:
      files = glob.glob(P_DEFAULT_CONFIGDIR+os.sep+"profile_*.conf")
      files = [ os.path.splitext(os.path.basename(f))[0][8:].strip() for f in files ]
      try:
        self.profileList.currentIndexChanged.disconnect()
        self.profileMain.currentIndexChanged.disconnect()
      except: pass

      self.profileList.clear()
      self.profileMain.clear()
      for p in files:
        if p != "": cSettings.addProfile(p)
      self.profileList.currentIndexChanged.connect(lambda : cSettings.syncProfileLists("settings"))
      self.profileMain.currentIndexChanged.connect(lambda : cSettings.syncProfileLists("main"))

      lpIdx = self.profileList.findText(self.lastProfile)
      if lpIdx == -1:
        self.profileList.setCurrentIndex(0)
        self.profileMain.setCurrentIndex(0)
        cPrint.warning(f"[cSettings] last profile \"{self.lastProfile}\" was not found. Loading \"{self.profileMain.itemText(0)}\" instead...")
      else:
        self.profileList.setCurrentIndex(-1)
        self.profileList.setCurrentIndex(lpIdx)
        self.profileMain.setCurrentIndex(-1)
        self.profileMain.setCurrentIndex(lpIdx)
      
    except Exception as e:
      cPrint.error(f"[cSettings] error loading settings from \"{C_SILVER}{self._state.fileName()}</font>\"", e)
    else:
      cPrint.info(f"[cSettings] loaded from \"{C_SILVER}{self._state.fileName()}</font>\"")

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      self._state.setValue("multiAccount", self.main.credentials.multiAccount.isChecked()) # goes in the "General" section of the settings file
      self._state.setValue("lastProfile", self.profileList.currentText())                  # goes in the "General" section of the settings file
    except Exception as e:
      cPrint.error(f"[cSettings] could not create \"{C_SILVER}{self._state.fileName()}</font>\" to store settings!",e)
    else:
      cPrint.info(f"[cSettings] saved in \"{C_SILVER}{self._state.fileName()}</font>\"")
    
  


