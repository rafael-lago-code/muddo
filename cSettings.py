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
from cWidgets.util import *
from cWidgets.cTab import cTab
from cWidgets.cButton import cButton
from cProfil import cProfil
import os
import subprocess
import json
import glob
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cSettings(cTab):

  def __init__(self, main : cMainWindow):
    super().__init__("&Settings")
    self.main = main
    self.console = main.console
    self.profiles : dict[str, cProfil] = {}  # This will hold all profiles
    self.lastProfile = ""

    profileLbl = QLabel("Profile: ")
    profileLbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.profileList = QComboBox()
    self.profileList.setEditable(True)

    self.btnSave = cButton("Save", P_ICON_SAVE, tooltip="Save current settings and profile")
    self.btnRemoveProfile = cButton("Delete", P_ICON_TRASH, tooltip="Delete current profile and its associated files (main settings remain untouched)")
    self.btnReload = cButton("Reload", P_ICON_REFRESH, tooltip="Reload current profile and all settings from file")

    g = QGridLayout()
    self.hiddenLayer = QVBoxLayout()
    g.addLayout(self.hiddenLayer, 0, 0, 1, 4)
    g.addLayout(newHLayout([profileLbl, self.profileList, self.btnSave, self.btnRemoveProfile, self.btnReload]),  1, 0, 1, 4)
    self.setLayout(g)

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.load()

    self.btnSave.clicked.connect(self.save)
    self.btnRemoveProfile.clicked.connect(self.removeProfile)
    self.btnReload.clicked.connect(self.load)
    self.profileList.currentIndexChanged.connect(self.changeProfile)

  #----------------------------------------------------------------------------------------------------------
  def removeProfile(self):
    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + self.profileList.lineEdit().text() + ".json"
    try:
      idx = self.profileList.findText(self.profileList.lineEdit().text(), QtCore.Qt.MatchFlag.MatchExactly)
      if idx >= 0:
        self.profileList.removeItem(idx)
      os.remove(filename)
    except:
      pass

  #----------------------------------------------------------------------------------------------------------
  def setProfilesList(self, profiles):
    try:
      self.profileList.currentIndexChanged.disconnect(self.changeProfile)
    except: pass
    self.profileList.clear()
    self.main.launchMenu.clear()
    self.main.launchMenu.addSection("Switch profile to...")
    for p in profiles:
      if p == "": continue
      self.profileList.addItem(p)
      act = QAction(f"\"{p}\" profile", self.main)
      self.main.launchMenu.addAction(act)
      self.connectAction2Profile(act, p)
      if p not in self.profiles.keys():
        self.profiles[p] = cProfil(self.main, p)
        self.hiddenLayer.addWidget(self.profiles[p])
      self.profiles[p].setVisible(False)
      self.profiles[p].load()
    self.profileList.currentIndexChanged.connect(self.changeProfile)

  #----------------------------------------------------------------------------------------------------------
  def connectAction2Profile(self, a : QAction, p : str):
    idx = self.profileList.findText(p)
    a.triggered.connect(lambda x : self.profileList.setCurrentIndex(idx))

  #----------------------------------------------------------------------------------------------------------
  def changeProfile(self):
    pname = self.profileList.currentText()
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
      self.console.error(f"{C_RED}[WARNING]</font> Trying to change to profile \"{p}\",\
                          but it was not found! Doing nothing instead...")

  #----------------------------------------------------------------------------------------------------------
  def findxdotool(self):
    if self.usexdotool.isChecked() and self.xdotoolExec.text()=="":
      try:
        result = subprocess.run(["which", "xdotool"], stdout=subprocess.PIPE)
        if result.stdout:
          result = result.stdout.decode('utf-8').strip()
          self.xdotoolExec.setText(result)
          self.console.info(f"Setting xdotool binary to {result}...")
        else:
          self.console.info("[W] xdotool binary not found! Is it installed? If so, please set it manually...")
      except Exception as e:
        self.console.error("Error looking for xdotool binary", e)

  #----------------------------------------------------------------------------------------------------------
  def load(self):
    values = None
    if os.path.exists(P_DEFAULT_CONFIGFILE):
      with open(P_DEFAULT_CONFIGFILE,"r") as f:
        values = json.load(f)
      self.console.info(f'Settings loaded from {P_DEFAULT_CONFIGFILE}')
    else:
      self.console.error(f"cSettings.load: file {P_DEFAULT_CONFIGFILE} not found")
    
    if values:
      try:
        if 'settingsVisible' in values.keys(): self.main.settings.setVisible(values['settingsVisible'])
        if 'newsVisible'  in values.keys(): self.main.news.setVisible(values['newsVisible'])
        if 'patchVisible' in values.keys(): self.main.patch.setVisible(values['patchVisible'])
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
        else:
          self.profileList.setCurrentIndex(0)
        
        if self.profileList.currentText(): self.main.profile().load()

      except Exception as e:
        self.console.error(f"cSettings.load: error loading settings from {P_DEFAULT_CONFIGFILE}", e)

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      os.mkdir(os.path.dirname(P_DEFAULT_CONFIGFILE))
    except: pass

    values = {}
    values['settingsVisible'] = self.main.settings.isVisible()
    values['newsVisible']  = self.main.news.isVisible()
    values['patchVisible'] = self.main.patch.isVisible()
    values['multiAccount'] = self.main.credentials.multiAccount.isChecked()
    values['lastProfile']  = self.profileList.currentText()
    if self.profileList.currentText(): self.main.profile().save()

    try:
      json.dump(values, open(P_DEFAULT_CONFIGFILE,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cSettings.save: could not create {P_DEFAULT_CONFIGFILE} to store settings!",e)
    else:
      self.console.info(f"Settings saved in {P_DEFAULT_CONFIGFILE}")
    
  


