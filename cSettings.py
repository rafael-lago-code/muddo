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
from PyQt6.QtWidgets import QGridLayout, QComboBox
from PyQt6.QtGui import QAction
from cWidgets.cOrb import cOrbSmall
from cWidgets.util import *
from cWidgets.cToggler import cToggler
from cWidgets.cButton import cButton
from cProfil import cProfil
import os
import subprocess
import json
import glob
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cSettings(cToggler):

  def __init__(self, main : cMainWindow):
    self.widgetID = "settings"
    super().__init__("&Settings", P_ICON_GEARSTACK)
    self.toggler.setToolTip("Toggle Settings UI")
    self.main = main
    self.profiles : dict[str, cProfil] = {}  # This will hold all profiles
    self.lastProfile = ""

    profileLbl = QLabel("Profile: ")
    profileLbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.profileMain = QComboBox()
    self.profileMain.setMinimumWidth(200)
    self.profileList = QComboBox()
    self.profileList.setEditable(True)
    self.profileList.setMinimumWidth(200)

    self.btnSave = cOrbSmall(icon=P_ICON_SAVE, tooltip="Save current settings and profile")
    self.btnRemoveProfile = cOrbSmall(icon=P_ICON_TRASH, tooltip="Delete current profile and its associated files (main settings remain untouched)")
    self.btnReload = cOrbSmall(icon=P_ICON_REFRESH, tooltip="Reload current profile and all settings from file")

    # g = QGridLayout()
    self.hiddenLayer = QVBoxLayout()
    # g.addLayout(newHLayout(["__stretch__", "Profile: ", self.profileList, self.btnSave, self.btnRemoveProfile, self.btnReload, "__stretch__"]))
    # g.addLayout(newHLayout(["Profile: ", self.profileList, self.btnSave, self.btnRemoveProfile, self.btnReload]),  0, 0, 1, 4)
    # g.addLayout(self.hiddenLayer, 1, 0, 1, 4)
    self.setLayout(newVLayout([newHLayout(["__stretch__", "Profile: ", self.profileList, self.btnSave, self.btnRemoveProfile, self.btnReload, "__stretch__"]),
                               self.hiddenLayer,
                               "__stretch__"]))

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.load()

    self.btnSave.clicked.connect(self.save)
    self.btnRemoveProfile.clicked.connect(self.removeProfile)
    self.btnReload.clicked.connect(self.load)
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
        self.profiles[p] = cProfil(self.main, p)
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
      self.main.console.error(f"{C_RED}[WARNING]</font> Trying to change to profile \"{pname}\",\
                          but it was not found! Doing nothing instead...")

  # #----------------------------------------------------------------------------------------------------------
  # def findxdotool(self):
  #   if self.usexdotool.isChecked() and self.xdotoolExec.text()=="":
  #     try:
  #       result = subprocess.run(["which", "xdotool"], stdout=subprocess.PIPE)
  #       if result.stdout:
  #         result = result.stdout.decode('utf-8').strip()
  #         self.xdotoolExec.setText(result)
  #         self.main.console.info(f"Setting xdotool binary to {result}...")
  #       else:
  #         self.main.console.info("[W] xdotool binary not found! Is it installed? If so, please set it manually...")
  #     except Exception as e:
  #       self.main.console.error("Error looking for xdotool binary", e)

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    values = None
    if os.path.exists(P_DEFAULT_CONFIGFILE):
      try:
        with open(P_DEFAULT_CONFIGFILE,"r") as f:
          values = json.load(f)
        self.main.console.info(f'Settings loaded from {P_DEFAULT_CONFIGFILE}')
      except Exception as e:
        self.main.console.error(f"{C_RED}ERROR:</font> failed loading {P_DEFAULT_CONFIGFILE}!", e)
        print(f"{C_RED}ERROR:</font> failed loading {P_DEFAULT_CONFIGFILE}!")
        print(e)
    else:
      self.main.console.error(f"cSettings.load: file {P_DEFAULT_CONFIGFILE} not found")
    
    if values:
      try:
        if 'settingsVisible' in values.keys(): self.main.settings.setVisible(values['settingsVisible'])
        if 'newsVisible'  in values.keys(): self.main.news.setVisible(values['newsVisible'])
        if 'patchVisible' in values.keys(): self.main.patch.setVisible(values['patchVisible'])
        if 'shortcutsVisible' in values.keys(): self.main.macros.setVisible(values['shortcutsVisible'])
        if 'multiAccount' in values.keys(): 
          self.main.credentials.multiAccount.setChecked(values['multiAccount'])
          self.main.credentials.updateMultiAccount()
        
        files = glob.glob(P_DEFAULT_CONFIGDIR+os.sep+"profile_*.json")
        files = [ os.path.splitext(os.path.basename(f))[0][8:].strip() for f in files ]
        self.setProfilesList(files)
        if 'lastProfile' in values.keys():
          self.lastProfile = values['lastProfile']
          self.profileList.setCurrentIndex(-1)
          self.profileList.setCurrentIndex(self.profileList.findText(self.lastProfile))
          self.profileMain.setCurrentIndex(-1)
          self.profileMain.setCurrentIndex(self.profileMain.findText(self.lastProfile))
        else:
          self.profileList.setCurrentIndex(0)
          self.profileMain.setCurrentIndex(0)
        
        if self.profileList.currentText(): self.main.profile().load()

      except Exception as e:
        self.main.console.error(f"cSettings.load: error loading settings from \"{C_SILVER}{P_DEFAULT_CONFIGFILE}</font>\"", e)

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      os.mkdir(os.path.dirname(P_DEFAULT_CONFIGFILE))
    except: pass

    values = {}
    values['settingsVisible'] = self.main.settings.isVisible()
    values['newsVisible']  = self.main.news.isVisible()
    values['patchVisible'] = self.main.patch.isVisible()
    values['shortcutsVisible'] = self.main.macros.isVisible()
    values['multiAccount'] = self.main.credentials.multiAccount.isChecked()
    values['lastProfile']  = self.profileList.currentText()
    if self.profileList.currentText(): self.main.profile().save()

    try:
        json.dump(values, open(P_DEFAULT_CONFIGFILE,"w"), cls=muJSONEncoder)
    except Exception as e:
      self.main.console.error(f"cSettings.save: could not create \"{C_SILVER}{P_DEFAULT_CONFIGFILE}</font>\" to store settings!",e)
    else:
      self.main.console.info(f"Settings saved in \"{C_SILVER}{P_DEFAULT_CONFIGFILE}</font>\"")
    
  


