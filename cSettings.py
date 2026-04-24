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
from PyQt6.QtCore import QSettings
from cSettingsProfile import cSettingsProfile
from helpers.cPrint import cPrint
from widgets.cOrb import cOrbSmall
from helpers.util import *
from widgets.cToggler import cToggler
from cProfilasdfasdfasdf import cProfil
import os, json, glob
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            S E T T I N G S
#                                  
#   This is a static class. Don't instantiate it.
#---------------------------------------------------------------------------------------------------------------
class cSettings(cToggler):
  widgetID = "settings"
  lastProfile = ""
  profiles : dict[str, cProfil] = {}  # This will hold all profiles
  hiddenLayer = QVBoxLayout()

  def __init__(self, main : cMainWindow):
    super().__init__("&Settings", P_ICON_GEARSTACK)
    self.toggler.setToolTip("Toggle Settings UI")
    self.main = main
    # self.profiles : dict[str, cProfil] = {}  # This will hold all profiles

    # self.hiddenLayer = QVBoxLayout()
    profileLbl = QLabel("Profile: ")
    profileLbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.profileMain = QComboBox()
    self.profileMain.setMinimumWidth(200)
    self.profileList = QComboBox()
    self.profileList.setEditable(True)
    self.profileList.setMinimumWidth(200)

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
    self.profileList.currentIndexChanged.connect(lambda : self.changeProfile("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : self.changeProfile("main"))

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def switchProfile(cls, name):
    cls.launcher  = cls.profiles[name].launcher
    cls.xsettings = cls.profiles[name].xsettings
    cls.plugins   = cls.profiles[name].plugins
    cls.session   = cls.profiles[name].session

  #----------------------------------------------------------------------------------------------------------
  def setProfilesList(self, profiles):
    try:
      self.profileList.currentIndexChanged.disconnect()
      self.profileMain.currentIndexChanged.disconnect()
    except: pass
    self.profileList.clear()
    # self.main.launchMenu.clear()
    # self.main.launchMenu.addSection("Switch profile to...")
    for p in profiles:
      if p == "": continue
      self.profileList.addItem(p)
      self.profileMain.addItem(p)
      # act = QAction(f"\"{p}\" profile", self.main)
      # self.main.launchMenu.addAction(act)
      # self.connectAction2Profile(act, p)
      if p not in self.profiles.keys():
        self.profiles[p] = cSettingsProfile(p, self.main)
        self.hiddenLayer.addWidget(self.profiles[p])
      self.profiles[p].setVisible(False)
      self.profiles[p].load()
    self.profileList.currentIndexChanged.connect(lambda : self.changeProfile("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : self.changeProfile("main"))

  #----------------------------------------------------------------------------------------------------------
  def removeProfile(self):
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
  def setProfilesList(self, profiles):
    try:
      self.profileList.currentIndexChanged.disconnect()
      self.profileMain.currentIndexChanged.disconnect()
    except: pass
    self.profileList.clear()
    # self.main.launchMenu.clear()
    # self.main.launchMenu.addSection("Switch profile to...")
    for p in profiles:
      if p == "": continue
      self.profileList.addItem(p)
      self.profileMain.addItem(p)
      # act = QAction(f"\"{p}\" profile", self.main)
      # self.main.launchMenu.addAction(act)
      # self.connectAction2Profile(act, p)
      if p not in self.profiles.keys():
        self.profiles[p] = cSettingsProfile(p, self.main)
        self.hiddenLayer.addWidget(self.profiles[p])
      self.profiles[p].setVisible(False)
      self.profiles[p].load()
    self.profileList.currentIndexChanged.connect(lambda : self.changeProfile("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : self.changeProfile("main"))

  # #----------------------------------------------------------------------------------------------------------
  # def connectAction2Profile(self, a : QAction, p : str):
  #   idx = self.profileList.findText(p)
  #   a.triggered.connect(lambda x : self.profileList.setCurrentIndex(idx))

  #----------------------------------------------------------------------------------------------------------
  def changeProfile(self, source="settings"):
    try:
      self.profileList.currentIndexChanged.disconnect()
      self.profileMain.currentIndexChanged.disconnect()
    except: pass

    if source=="settings":
      pname = self.profileList.currentText()
      idx = self.profileList.currentIndex()
      self.profileMain.setCurrentIndex(idx)
    else:
      pname = self.profileMain.currentText()
      idx = self.profileMain.currentIndex()
      self.profileList.setCurrentIndex(idx)

    self.profileList.currentIndexChanged.connect(lambda : self.changeProfile("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : self.changeProfile("main"))

    if not pname: return
    if pname in self.profiles.keys():
      if self.lastProfile in self.profiles.keys():
        self.profiles[self.lastProfile].setVisible(False)
        self.profiles[self.lastProfile].aggregate()
      self.profiles[pname].setVisible(True)
      self.profiles[pname].propagate()
      self.main.patch.updateTimestamp()
      self.lastProfile = pname
      self.main.sigProfileChanged.emit([self.lastProfile, pname])
    else:
      cPrint.error(f"{C_RED}[WARNING]</font> Trying to change to profile \"{pname}\",\
                          but it was not found! Doing nothing instead...")

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    settings = QSettings(P_DEFAULT_CONF)
    self.lastProfile  = settings.value("lastProfile", "")    # goes in the "General" section of the settings file
    multiAccount = settings.value("multiAccount") == "true"  # goes in the "General" section of the settings file

    self.main.credentials.multiAccount.setChecked(multiAccount)
    self.main.credentials.updateMultiAccount()
    
    try:
      files = glob.glob(P_DEFAULT_CONFIGDIR+os.sep+"newprofile_*.conf")
      files = [ os.path.splitext(os.path.basename(f))[0][11:].strip() for f in files ]
      self.setProfilesList(files)
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
      
      if self.profileList.currentText(): self.main.profile().load()

    except Exception as e:
      cPrint.error(f"[cSettings] error loading settings from \"{C_SILVER}{settings.fileName()}</font>\"", e)
    else:
      cPrint.info(f"[cSettings] loaded from \"{C_SILVER}{settings.fileName()}</font>\"")

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      settings = QSettings(P_DEFAULT_CONF)
      settings.setValue("multiAccount", self.main.credentials.multiAccount.isChecked()) # goes in the "General" section of the settings file
      settings.setValue("lastProfile", self.profileList.currentText())                  # goes in the "General" section of the settings file
      self.main.profile().save()
    except Exception as e:
      cPrint.error(f"[cSettings] could not create \"{C_SILVER}{settings.fileName()}</font>\" to store settings!",e)
    else:
      cPrint.info(f"[cSettings] saved in \"{C_SILVER}{settings.fileName()}</font>\"")
    
  


