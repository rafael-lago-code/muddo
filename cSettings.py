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
#    This software is heavily based on PyLotRO (credits to AJackson
#    <ajackson@bcs.org.uk>), which in turn is based on a script by SNy
#    (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
from PyQt6.QtWidgets import QHBoxLayout, QGridLayout, QComboBox, QFileDialog,\
  QPushButton, QCheckBox, QLineEdit, QWidget
from PyQt6.QtGui import QAction
from util import *
from cTab import cTab
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
    self.useHighRes = QCheckBox("Use HighRes")
    self.usexdotool = QCheckBox("Use xdotool")
    self.useDungeonHelper = QCheckBox("Use DungeonHelper")
    self.useHighRes.setChecked(True)
    self.languageList = QComboBox()
    self.languageList.addItems(["English", "German", "French"])
    self.languageList.currentIndexChanged.connect(self.changeLanguage)

    self.launcherList = QComboBox()
    self.launcherList.addItems(["Steam Proton", "Wine64", "Wine32"])
    self.launcherList.currentIndexChanged.connect(self.changeLauncher)
    
    profileLbl = QLabel("Profile: ")
    profileLbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.profile = QComboBox()
    self.profile.setEditable(True)
    self.profile.currentIndexChanged.connect(self.loadProfile)
    self.windowsPreferences = {}
    self.btnSave = QPushButton(getIcon(P_ICON_SAVE), "Save")
    self.btnSave.setToolTip("Save current settings and profile")
    self.btnSave.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.btnSave.clicked.connect(self.save)
    self.btnDelete = QPushButton(getIcon(P_ICON_TRASH), "Delete")
    self.btnDelete.setToolTip("Delete current profile and its associated files (main settings remain untouched)")
    self.btnDelete.clicked.connect(self.removeProfile)
    self.btnDelete.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.btnReload = QPushButton(getIcon(P_ICON_REFRESH), "Reload")
    self.btnReload.setToolTip("Reload current profile and all settings from file")
    self.btnReload.clicked.connect(self.load)
    self.btnReload.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

    self.launcherBinary = QLineEdit()
    self.wineExec = ""
    self.protonExec = ""
    self.winePrefix = ""
    self.protonPrefix = ""
    self.gameDir = QLineEdit()
    self.launcherPrefix   = QLineEdit()
    self.steamRoot= QLineEdit()
    self.xdotoolExec = QLineEdit()
    self.DungeonHelperExec = QLineEdit()
    self.btnSelectLauncher = QPushButton()
    self.btnSelectPrefix   = QPushButton()
    self.btnSelectSteamRoot= QPushButton()
    self.btnSelectGameDir = QPushButton()
    self.btnSelectDungeonHelperExec = QPushButton()
    self.btnSelectxdotoolExec = QPushButton()

    self.btnSelectLauncher.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectPrefix.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectSteamRoot.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectGameDir.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectDungeonHelperExec.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectxdotoolExec.setIcon(getIcon(P_ICON_OPENFOLDER))

    self.btnSelectLauncher.clicked.connect(self.selectLauncher)
    self.btnSelectPrefix.clicked.connect(self.selectPrefix)
    self.btnSelectSteamRoot.clicked.connect(self.selectSteamRoot)
    self.btnSelectGameDir.clicked.connect(self.selectGameExec)
    self.btnSelectxdotoolExec.clicked.connect(self.selectxdotoolExec)
    self.btnSelectDungeonHelperExec.clicked.connect(self.selectDungeonHelperExec)

    self.lblPrefix     = newRQLabel("STEAM_COMPAT_DATA: ")
    self.lblSteamRoot  = newRQLabel("STEAM_ROOT: ")

    self.launcherBinary.textChanged.connect(self.copyLauncherBinaryText)
    self.launcherPrefix.textChanged.connect(self.copyPrefixText)

    g = QGridLayout()
    g.addLayout(newHLayout([profileLbl, self.profile, self.btnSave, self.btnDelete, self.btnReload]),  0, 0, 1, 4)
    g.addWidget(self.launcherList,  1, 0)
    g.addWidget(self.languageList,  2, 0)
    g.addWidget(self.useHighRes, 3, 0)
    g.addWidget(self.usexdotool, 5, 0)
    g.addWidget(self.useDungeonHelper, 6, 0)

    g.addWidget(newRQLabel("Launcher exec: "), 1, 1)
    g.addWidget(self.launcherBinary,  1,  2)
    g.addWidget(self.btnSelectLauncher, 1, 3)

    g.addWidget(self.lblPrefix, 2, 1)
    g.addWidget(self.launcherPrefix, 2, 2)
    g.addWidget(self.btnSelectPrefix, 2, 3)

    g.addWidget(self.lblSteamRoot, 3, 1)
    g.addWidget(self.steamRoot, 3, 2)
    g.addWidget(self.btnSelectSteamRoot, 3, 3)

    g.addWidget(newRQLabel("Game Path: "), 4, 1)
    g.addWidget(self.gameDir, 4, 2)
    g.addWidget(self.btnSelectGameDir, 4, 3)

    g.addWidget(newRQLabel("xdotool exec: "), 5, 1)
    g.addWidget(self.xdotoolExec, 5, 2)
    g.addWidget(self.btnSelectxdotoolExec, 5, 3)

    g.addWidget(newRQLabel("DungeonHelper exec: "), 6, 1)
    g.addWidget(self.DungeonHelperExec, 6, 2)
    g.addWidget(self.btnSelectDungeonHelperExec, 6, 3)

    self.usexdotool.toggled.connect(self.btnSelectxdotoolExec.setEnabled)
    self.usexdotool.toggled.connect(self.xdotoolExec.setEnabled)
    self.usexdotool.toggled.connect(self.findxdotool)
    self.usexdotool.setChecked(False)
    self.xdotoolExec.setEnabled(False)
    self.btnSelectxdotoolExec.setEnabled(False)

    self.useDungeonHelper.toggled.connect(self.btnSelectDungeonHelperExec.setEnabled)
    self.useDungeonHelper.toggled.connect(self.DungeonHelperExec.setEnabled)
    self.useDungeonHelper.toggled.connect(self.findDungeonHelper)
    self.useDungeonHelper.setChecked(False)
    self.btnSelectDungeonHelperExec.setEnabled(False)
    self.DungeonHelperExec.setEnabled(False)
    
    self.setLayout(g)

  #----------------------------------------------------------------------------------------------------------
  def saveProfile(self):
    name = self.profile.lineEdit().text()
    if self.profile.findText(name, QtCore.Qt.MatchFlag.MatchExactly)>=0:
      self.console.info(f"Updating profile {name}")
    else:
      self.console.info(f"Saving profile {name}")
      self.profile.addItem(name)
    
    try:
      os.mkdir(P_DEFAULT_CONFIGDIR)
    except: pass

    values = {}
    values['wineExec']      = self.wineExec
    values['protonExec' ]   = self.protonExec
    values['winePrefix']    = self.winePrefix
    values['protonPrefix']  = self.protonPrefix
    values['launcher']      = self.launcherList.currentText()
    values['language']      = self.languageList.currentText()
    values['gameExec']      = self.gameDir.text()
    values['steamRoot']     = self.steamRoot.text()
    values['useHighRes']    = self.useHighRes.isChecked()
    values['usexdotool']    = self.usexdotool.isChecked()
    values['useDungeonHelper']  = self.useDungeonHelper.isChecked()
    values['xdotoolExec']       = self.xdotoolExec.text()
    values['DungeonHelperExec'] = self.DungeonHelperExec.text()

    values['lastWorld']     = self.main.credentials.getSelectedWorld()
    values['lastAccounts']  = self.main.credentials.getSelectedAccounts()
    values['windowsPreferences']  = self.windowsPreferences

    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + name + ".json"
    try:
      json.dump(values, open(filename,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cSettings.saveProfile: could not create {filename} to store profile settings!",e)
    else:
      self.console.info(f"Profile saved in {filename}")


  #----------------------------------------------------------------------------------------------------------
  def removeProfile(self):
    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + self.profile.lineEdit().text() + ".json"
    try:
      idx = self.profile.findText(self.profile.lineEdit().text(), QtCore.Qt.MatchFlag.MatchExactly)
      if idx >= 0:
        self.profile.removeItem(idx)
      os.remove(filename)
    except:
      pass

  #----------------------------------------------------------------------------------------------------------
  def loadProfile(self):
    name = self.profile.lineEdit().text()
    if not name: return

    values = None
    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + name + ".json"
    if os.path.exists(filename):
      with open(filename,"r") as f:
        values = json.load(f)
      self.console.info(f'Profile loaded from {filename}')
    else:
      self.console.error(f"cSettings.loadProfile: file {filename} not found")
    
    if values:
      try:
        if 'wineExec'   in values.keys(): self.wineExec   = values['wineExec']
        if 'protonExec' in values.keys(): self.protonExec = values['protonExec']
        if 'winePrefix'   in values.keys(): self.winePrefix   = values['winePrefix']
        if 'protonPrefix' in values.keys(): self.protonPrefix = values['protonPrefix']
        if 'gameExec'     in values.keys(): self.gameDir.setText(values['gameExec'])
        if 'steamRoot'    in values.keys(): self.steamRoot.setText(values['steamRoot'])
        if 'useHighRes'   in values.keys(): self.useHighRes.setChecked(values['useHighRes'])
        if 'usexdotool'   in values.keys(): self.usexdotool.setChecked(values['usexdotool'])
        if 'xdotoolExec'   in values.keys(): self.xdotoolExec.setText(values['xdotoolExec'])
        if 'DungeonHelperExec' in values.keys(): self.DungeonHelperExec.setText(values['DungeonHelperExec'])
        if 'useDungeonHelper'  in values.keys(): self.useDungeonHelper.setChecked(values['useDungeonHelper'])
        if 'launcher'     in values.keys(): self.launcherList.setCurrentIndex(self.launcherList.findText(values['launcher']))
        if 'language'     in values.keys(): self.languageList.setCurrentIndex(self.languageList.findText(values['language']))
        self.changeLauncher()

        if 'lastWorld'    in values.keys(): self.main.credentials.selectWorld(values['lastWorld'])
        if 'lastAccounts' in values.keys(): self.main.credentials.selectAccounts(values['lastAccounts'])
        if 'windowsPreferences' in values.keys(): self.windowsPreferences = values['windowsPreferences']

      except Exception as e:
        self.console.error(f"cSettings.loadProfile: error loading settings from {filename}", e)
    # self.profile.lineEdit().setText(name)


  #----------------------------------------------------------------------------------------------------------
  def setProfilesList(self, profiles):
    self.profile.currentIndexChanged.disconnect(self.loadProfile)
    self.profile.clear()
    self.main.launchMenu.clear()
    self.main.launchMenu.addSection("Launch with...")
    act = QAction("current profile", self.main)
    act.triggered.connect(self.main.queueAll)
    self.main.launchMenu.addAction(act)
    for p in profiles: 
      if p != "":
        self.profile.addItem(p)
        act = QAction(f"\"{p}\" profile", self.main)
        self.main.launchMenu.addAction(act)
        self.connectAction2Profile(act, p)
    self.profile.currentIndexChanged.connect(self.loadProfile)

  #----------------------------------------------------------------------------------------------------------
  def connectAction2Profile(self, a : QAction, p : str):
    idx = self.profile.findText(p)
    a.triggered.connect(lambda x : self.main.queueAll(idx))

  #----------------------------------------------------------------------------------------------------------
  def copyPrefixText(self):
    if self.launcherList.currentText()=="Steam Proton":
      self.protonPrefix = self.launcherPrefix.text()
    else:
      self.winePrefix = self.launcherPrefix.text()

  #----------------------------------------------------------------------------------------------------------
  def copyLauncherBinaryText(self):
    if self.launcherList.currentText()=="Steam Proton":
      self.protonExec = self.launcherBinary.text()
    else:
      self.wineExec = self.launcherBinary.text()

  #----------------------------------------------------------------------------------------------------------
  def changeLanguage(self):
    self.console.info(f"[W] Switching languages is not yet supported!!")

  #----------------------------------------------------------------------------------------------------------
  def changeLauncher(self):
    # self.console.info(f"Setting up {self.launcherList.currentText()}...")
    if self.launcherList.currentText()=="Steam Proton":
      self.lblPrefix.setText("STEAM_COMPAT_DATA: ")
      self.steamRoot.setEnabled(True)
      self.btnSelectSteamRoot.setEnabled(True)
      self.launcherBinary.setText(self.protonExec)
      self.launcherPrefix.setText(self.protonPrefix)
      self.findProton()
    else:
      self.console.info(f"[W] Wine32 and Wine64 are untested!")
      s = self.lblPrefix.size()
      self.lblPrefix.setText("WINEPREFIX: ")
      self.lblPrefix.setFixedSize(s)
      self.steamRoot.setEnabled(False)
      self.btnSelectSteamRoot.setEnabled(False)
      self.launcherBinary.setText(self.wineExec)
      self.launcherPrefix.setText(self.winePrefix)
      self.findWine()
  
  #----------------------------------------------------------------------------------------------------------
  def findWine(self):
    if self.launcherBinary.text()=="":
      result = subprocess.run(["which", "wine"], stdout=subprocess.PIPE)
      if result.stdout:
        result = result.stdout.decode('utf-8').strip()
        self.launcherBinary.setText(result)
        self.console.info(f"Setting wine binary to {result}...")
      else:
        self.console.info("[W] Wine binary not found! Please set it manually...")

  #----------------------------------------------------------------------------------------------------------
  def findDungeonHelper(self):
    if self.useDungeonHelper.isChecked() and self.DungeonHelperExec.text()=="":
      if self.launcherPrefix.text():
        try:
          out = subprocess.check_output([f"find {self.launcherPrefix.text()} -iname DungeonHelper.exe"], shell=True)
          if out:
            out = out.decode('utf-8').strip()
            self.DungeonHelperExec.setText(out)
            self.console.info(f"Setting DungeonHelper binary to {out}...")
          else:
            self.console.info("[W] DungeonHelper binary not found! Is it installed? If so, please set it manually...")
        except Exception as e:
          self.console.error("Error looking for DungeonHelper binary", e)

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
  def findProton(self):
    if self.launcherBinary.text()=="":
      self.console.info("[W] findProton function not yet implemented!")
  
  #----------------------------------------------------------------------------------------------------------
  def selectPrefix(self):
    filename = QFileDialog.getExistingDirectory(self, "Select Prefix...")
    if filename:
      print(filename)
      self.launcherPrefix.setText(filename[0])

  #----------------------------------------------------------------------------------------------------------
  def selectDungeonHelperExec(self):
    filename = QFileDialog.getExistingDirectory(self, "Select DungeonHelper executable...")
    if filename:
      self.DungeonHelperExec.setText(filename)

  #----------------------------------------------------------------------------------------------------------
  def selectxdotoolExec(self):
    filename = QFileDialog.getExistingDirectory(self, "Select xdotool executable...")
    if filename:
      self.xdotoolExec.setText(filename)

  #----------------------------------------------------------------------------------------------------------
  def selectSteamRoot(self):
    filename = QFileDialog.getExistingDirectory(self, "Select STEAM_ROOT...")
    if filename:
      self.steamRoot.setText(filename)

  #----------------------------------------------------------------------------------------------------------
  def selectGameExec(self):
    filename = QFileDialog.getOpenFileName(self, "Select game executable...")
    if filename:
      self.gameDir.setText(filename[0])

  #----------------------------------------------------------------------------------------------------------
  def selectLauncher(self):
    filename = QFileDialog.getOpenFileName(self, "Select launcher executable...")
    if filename:
      self.launcherBinary.setText(filename[0])

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
        if 'newsVisible' in values.keys(): self.main.news.setVisible(values['newsVisible'])
        if 'patchVisible' in values.keys(): self.main.patch.setVisible(values['patchVisible'])
        if 'multiAccount' in values.keys(): 
          self.main.credentials.multiAccount.setChecked(values['multiAccount'])
          self.main.credentials.updateMultiAccount()
        
        files = glob.glob(P_DEFAULT_CONFIGDIR+os.sep+"profile_*.json")
        files = [ os.path.splitext(os.path.os.path.basename(f))[0][8:].strip() for f in files ]
        self.setProfilesList(files)
        if 'lastProfile'  in values.keys():
          self.profile.lineEdit().setText(values['lastProfile'])
          self.loadProfile()

      except Exception as e:
        self.console.error(f"cSettings.load: error loading settings from {P_DEFAULT_CONFIGFILE}", e)

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      os.mkdir(os.path.dirname(P_DEFAULT_CONFIGFILE))
    except: pass

    values = {}
    values['settingsVisible'] = self.main.settings.isVisible()
    values['newsVisible'] = self.main.news.isVisible()
    values['patchVisible']= self.main.patch.isVisible()
    values['multiAccount']  = self.main.credentials.multiAccount.isChecked()
    values['lastProfile']   = self.profile.lineEdit().text()
    self.saveProfile()

    try:
      json.dump(values, open(P_DEFAULT_CONFIGFILE,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cSettings.save: could not create {P_DEFAULT_CONFIGFILE} to store settings!",e)
    else:
      self.console.info(f"Settings saved in {P_DEFAULT_CONFIGFILE}")
    
  


