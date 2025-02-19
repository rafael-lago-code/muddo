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
from PyQt6.QtWidgets import QHBoxLayout, QGridLayout, QComboBox, QFileDialog,\
  QPushButton, QCheckBox, QLineEdit
from util import *
from cCollapsible import cCollapsible
import os
import subprocess
import json

class cSettings(cCollapsible):

  def __init__(self, main):
    super().__init__("Settings")
    self.main = main
    self.console = main.console
    self.useHighRes = QCheckBox("Use HighRes")
    self.useHighRes.setChecked(True)
    self.languageList = QComboBox()
    self.languageList.addItems(["English", "German", "French"])
    self.languageList.currentIndexChanged.connect(self.changeLanguage)

    self.launcherList = QComboBox()
    self.launcherList.addItems(["Steam Proton", "Wine64", "Wine32"])
    self.launcherList.currentIndexChanged.connect(self.changeLauncher)
    
    self.launcherBinary = QLineEdit()
    self.wineExec = ""
    self.protonExec = ""
    self.winePrefix = ""
    self.protonPrefix = ""
    self.gameExec = QLineEdit()
    self.launcherPrefix   = QLineEdit()
    self.steamRoot= QLineEdit()
    self.btnSelectLauncher = QPushButton()
    self.btnSelectPrefix   = QPushButton()
    self.btnSelectSteamRoot= QPushButton()
    self.btnSelectGameExec = QPushButton()

    self.btnSelectLauncher.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectPrefix.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectSteamRoot.setIcon(getIcon(P_ICON_OPENFOLDER))
    self.btnSelectGameExec.setIcon(getIcon(P_ICON_OPENFOLDER))

    self.btnSelectLauncher.clicked.connect(self.selectLauncher)
    self.btnSelectPrefix.clicked.connect(self.selectPrefix)
    self.btnSelectSteamRoot.clicked.connect(self.selectSteamRoot)
    self.btnSelectGameExec.clicked.connect(self.selectGameExec)

    self.lblPrefix     = quickQLabel("STEAM_COMPAT_DATA: ")
    self.lblSteamRoot  = quickQLabel("STEAM_ROOT: ")

    self.launcherBinary.textChanged.connect(self.copyLauncherBinaryText)
    self.launcherPrefix.textChanged.connect(self.copyPrefixText)

    btnSave = QPushButton("Save")
    btnSave.setIcon(getIcon(P_ICON_SAVE))
    btnRefresh = QPushButton("Reload")
    btnRefresh.setIcon(getIcon(P_ICON_REFRESH))
    P_ICON_REFRESH
    btnSave.clicked.connect(self.save)
    btnRefresh.clicked.connect(self.load)
    h = QHBoxLayout()
    h.addWidget(btnSave)
    h.addWidget(btnRefresh)
    
    g = QGridLayout()
    g.addWidget(self.launcherList,  0, 0)
    g.addWidget(self.languageList,   1, 0)
    g.addWidget(self.useHighRes, 2, 0)
    g.addLayout(h, 3, 0)

    g.addWidget(quickQLabel("Launcher exec: "), 0, 1)
    g.addWidget(self.launcherBinary,  0,  2)
    g.addWidget(self.btnSelectLauncher, 0, 3)

    g.addWidget(self.lblPrefix, 1, 1)
    g.addWidget(self.launcherPrefix, 1, 2)
    g.addWidget(self.btnSelectPrefix, 1, 3)

    g.addWidget(self.lblSteamRoot, 2, 1)
    g.addWidget(self.steamRoot, 2, 2)
    g.addWidget(self.btnSelectSteamRoot, 2, 3)

    g.addWidget(quickQLabel("Game exec: "), 3, 1)
    g.addWidget(self.gameExec, 3, 2)
    g.addWidget(self.btnSelectGameExec, 3, 3)
    
    self.body.setLayout(g)

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
    self.console.info(f"Setting up {self.launcherList.currentText()}...")
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
        result = result.stdout.decode('utf-8')
        self.launcherBinary.setText(result)
        self.console.info(f"Setting wine binary to {result}...")
      else:
        self.console.info("[W] Wine binary not found! Please set it manually...")

  #----------------------------------------------------------------------------------------------------------
  def findProton(self):
    if self.launcherBinary.text()=="":
      self.console.info("[W] findProton function not yet implemented!")
  
  #----------------------------------------------------------------------------------------------------------
  def selectPrefix(self):
    filename = QFileDialog.getExistingDirectory(self, "Select Prefix...")
    if filename:
      self.launcherPrefix.setText(filename[0])

  #----------------------------------------------------------------------------------------------------------
  def selectSteamRoot(self):
    filename = QFileDialog.getExistingDirectory(self, "Select STEAM_ROOT...")
    if filename:
      self.steamRoot.setText(filename)

  #----------------------------------------------------------------------------------------------------------
  def selectGameExec(self):
    filename = QFileDialog.getOpenFileName(self, "Select game executable...")
    if filename:
      self.gameExec.setText(filename[0])

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
        if 'wineExec'   in values.keys(): self.wineExec   = values['wineExec']
        if 'protonExec' in values.keys(): self.protonExec = values['protonExec']
        if 'winePrefix'   in values.keys(): self.winePrefix   = values['winePrefix']
        if 'protonPrefix' in values.keys(): self.protonPrefix = values['protonPrefix']
        if 'gameExec'     in values.keys(): self.gameExec.setText(values['gameExec'])
        if 'steamRoot'    in values.keys(): self.steamRoot.setText(values['steamRoot'])
        if 'useHighRes'   in values.keys(): self.useHighRes.setChecked(values['useHighRes'])
        if 'launcher'     in values.keys(): self.launcherList.setCurrentIndex(self.launcherList.findText(values['launcher']))
        if 'language'     in values.keys(): self.languageList.setCurrentIndex(self.languageList.findText(values['language']))
        self.changeLauncher()

        if 'settingsCollapsed' in values.keys(): self.main.settings.setCollapsed(values['settingsCollapsed'])
        if 'newsCollapsed' in values.keys(): self.main.news.setCollapsed(values['newsCollapsed'])
        if 'patchCollapsed' in values.keys(): self.main.patch.setCollapsed(values['patchCollapsed'])

        if 'multiAccount' in values.keys(): 
          self.main.credentials.multiAccount.setChecked(values['multiAccount'])
          self.main.credentials.updateMultiAccount()
        
        if 'lastWorld' in values.keys(): self.main.credentials.selectWorld(values['lastWorld'])
        if 'lastAccounts' in values.keys(): self.main.credentials.selectAccounts(values['lastAccounts'])

      except Exception as e:
        self.console.error(f"cSettings.load: error loading settings from {P_DEFAULT_CONFIGFILE}", e)

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      os.mkdir(os.path.dirname(P_DEFAULT_CONFIGFILE))
    except: pass

    values = {}
    values['wineExec']      = self.wineExec
    values['protonExec' ]   = self.protonExec
    values['winePrefix']    = self.winePrefix
    values['protonPrefix']  = self.protonPrefix
    values['launcher']      = self.launcherList.currentText()
    values['language']      = self.languageList.currentText()
    values['gameExec']      = self.gameExec.text()
    values['steamRoot']     = self.steamRoot.text()
    values['useHighRes']    = self.useHighRes.isChecked()
    values['settingsCollapsed'] = self.main.settings.isCollapsed()
    values['newsCollapsed'] = self.main.news.isCollapsed()
    values['patchCollapsed']= self.main.patch.isCollapsed()
    values['multiAccount']  = self.main.credentials.multiAccount.isChecked()
    values['lastWorld']     = self.main.credentials.getSelectedWorld()
    values['lastAccounts']  = self.main.credentials.getSelectedAccounts()

    try:
      json.dump(values, open(P_DEFAULT_CONFIGFILE,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cSettings.save: could not create {P_DEFAULT_CONFIGFILE} to store settings!",e)
    else:
      self.console.info(f"Settings saved in {P_DEFAULT_CONFIGFILE}")
    
  


