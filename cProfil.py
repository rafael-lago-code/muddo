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
#    <ajackson@bcs.org.uk>), which in turn is based on a lotrolauncher 
#    script by SNy (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
from PyQt6.QtWidgets import QHBoxLayout, QGridLayout, QComboBox, QFileDialog,\
  QPushButton, QCheckBox, QLineEdit, QWidget
from PyQt6.QtGui import QAction
from util import *
from cTab import cTab
from cGridLayout import cGridLayout
import os
import subprocess
import json
import glob
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cProfil(QWidget):

  def __init__(self, main : cMainWindow, name : str ):
    super().__init__()
    self.main = main
    self.console = main.console
    self.name = name
    self.useHighRes = QCheckBox("Use HighRes")
    self.usexdotool = QCheckBox("Use xdotool")
    self.useDungeonHelper = QCheckBox("Use DungeonHelper")
    self.useHighRes.setChecked(True)
    self.languageCombo = QComboBox()
    self.languageCombo.addItems(["English", "German", "French"])
    self.languageCombo.currentIndexChanged.connect(self.changeLanguage)

    self.launcherCombo = QComboBox()
    self.launcherCombo.addItems(["Steam Proton", "Wine64", "Wine32"])
    self.launcherCombo.currentIndexChanged.connect(self.changeLauncher)
    
    self.windowsPreferences = {}

    self.wineExecold = ""
    self.protonExecold = ""
    self.winePrefixold = ""
    self.protonPrefixold = ""

    self.protonExec  = QLineEdit()
    self.wineExec    = QLineEdit()
    self.compatData  = QLineEdit()
    self.winePrefix  = QLineEdit()
    self.gameDir     = QLineEdit()
    self.steamRoot   = QLineEdit()
    self.xdotoolExec = QLineEdit()
    self.DungeonHelperExec = QLineEdit()

    self.btnSelectLauncher    = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    self.btnSelectPrefix      = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    self.btnSelectSteamRoot   = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    self.btnSelectGameDir     = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    self.btnSelectxdotoolExec = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    self.btnSelectDungeonHelperExec = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))

    self.btnSelectLauncher.clicked.connect(self.selectLauncher)
    self.btnSelectPrefix.clicked.connect(self.selectPrefix)
    self.btnSelectSteamRoot.clicked.connect(self.selectSteamRoot)
    self.btnSelectGameDir.clicked.connect(self.selectGameExec)
    self.btnSelectxdotoolExec.clicked.connect(self.selectxdotoolExec)
    self.btnSelectDungeonHelperExec.clicked.connect(self.selectDungeonHelperExec)

    self.lblWineExec   = newRQLabel("Wine Executable: ")
    self.lblWinePrefix = newRQLabel("WINEPREFIX: ")
    self.lblProtonExec = newRQLabel("Proton Executable: ")
    self.lblCompatData = newRQLabel("STEAM_COMPAT_DATA: ")
    self.lblSteamRoot  = newRQLabel("STEAM_ROOT: ")

    self.lblWineExec.setVisible(False)
    self.lblWinePrefix.setVisible(False)
    self.wineExec.setVisible(False)
    self.winePrefix.setVisible(False)

    g = cGridLayout()
    # g.appendColumn([self.launcherCombo, self.languageCombo, self.useHighRes,
                    # self.usexdotool, self.useDungeonHelper])
    # g.firstColumn = 1

    g.appendRow([self.launcherCombo, self.lblProtonExec, self.protonExec,  self.btnSelectLauncher])
    g.appendRow([self.languageCombo, self.lblCompatData, self.compatData,  self.btnSelectPrefix])
    g.appendRow([None,               self.lblSteamRoot,  self.steamRoot,   self.btnSelectSteamRoot])
    g.appendRow([self.useHighRes,    newRQLabel("Game Path: "),           self.gameDir,     self.btnSelectGameDir])
    g.appendRow([self.usexdotool,    newRQLabel("xdotool exec: "),        self.xdotoolExec, self.btnSelectxdotoolExec])
    g.appendRow([self.useDungeonHelper, newRQLabel("DungeonHelper exec: "), self.DungeonHelperExec, self.btnSelectDungeonHelperExec])


    g.addWidget(self.lblWineExec, 0, 1)
    g.addWidget(self.wineExec,    0, 2)
    g.addWidget(self.lblWinePrefix, 1, 1)
    g.addWidget(self.winePrefix, 1, 2)

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
  def save(self):
    try:
      os.mkdir(P_DEFAULT_CONFIGDIR)
    except: pass

    values = {}
    values['wineExec']     = self.wineExec.text()
    values['protonExec' ]  = self.protonExec.text()
    values['winePrefix']   = self.winePrefix.text()
    values['protonPrefix'] = self.compatData.text()
    values['launcher']     = self.launcherCombo.currentText()
    values['language']     = self.languageCombo.currentText()
    values['gameDir']      = self.gameDir.text()
    values['steamRoot']    = self.steamRoot.text()
    values['useHighRes']   = self.useHighRes.isChecked()
    values['usexdotool']   = self.usexdotool.isChecked()
    values['xdotoolExec']  = self.xdotoolExec.text()
    values['useDungeonHelper']  = self.useDungeonHelper.isChecked()
    values['DungeonHelperExec'] = self.DungeonHelperExec.text()

    values['lastWorld']     = self.main.credentials.getSelectedWorld()
    values['lastAccounts']  = self.main.credentials.getSelectedAccounts()
    values['windowsPreferences']  = self.windowsPreferences

    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + self.name + ".json"
    try:
      json.dump(values, open(filename,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cSettings.saveProfile: could not create {filename} to store profile settings!",e)
    else:
      self.console.info(f"Profile saved in {filename}")


  #----------------------------------------------------------------------------------------------------------
  def load(self):
    values = None
    filename = P_DEFAULT_CONFIGDIR + os.sep + "profile_" + self.name + ".json"
    if os.path.exists(filename):
      with open(filename,"r") as f:
        values = json.load(f)
      self.console.info(f'Profile loaded from {filename}')
    else:
      self.console.error(f"cSettings.loadProfile: file {filename} not found")
    
    if values:
      try:
        if 'wineExec'     in values.keys(): self.wineExec.setText(values['wineExec'])
        if 'protonExec'   in values.keys(): self.protonExec.setText(values['protonExec'])
        if 'winePrefix'   in values.keys(): self.winePrefix.setText(values['winePrefix'])
        if 'compatData'   in values.keys(): self.compatData.setText(values['compatData'])
        if 'gameDir'      in values.keys(): self.gameDir.setText(values['gameDir'])
        if 'steamRoot'    in values.keys(): self.steamRoot.setText(values['steamRoot'])
        if 'useHighRes'   in values.keys(): self.useHighRes.setChecked(values['useHighRes'])
        if 'usexdotool'   in values.keys(): self.usexdotool.setChecked(values['usexdotool'])
        if 'xdotoolExec'  in values.keys(): self.xdotoolExec.setText(values['xdotoolExec'])
        if 'launcher'     in values.keys(): self.launcherCombo.setCurrentIndex(self.launcherCombo.findText(values['launcher']))
        if 'language'     in values.keys(): self.languageCombo.setCurrentIndex(self.languageCombo.findText(values['language']))
        if 'DungeonHelperExec' in values.keys(): self.DungeonHelperExec.setText(values['DungeonHelperExec'])
        if 'useDungeonHelper'  in values.keys(): self.useDungeonHelper.setChecked(values['useDungeonHelper'])
        self.changeLauncher()

        if 'lastWorld'    in values.keys(): self.main.credentials.selectWorld(values['lastWorld'])
        if 'lastAccounts' in values.keys(): self.main.credentials.selectAccounts(values['lastAccounts'])
        if 'windowsPreferences' in values.keys(): self.windowsPreferences = values['windowsPreferences']

      except Exception as e:
        self.console.error(f"cSettings.loadProfile: error loading settings from {filename}", e)


  #----------------------------------------------------------------------------------------------------------
  def connectAction2Profile(self, a : QAction, p : str):
    idx = self.profile.findText(p)
    a.triggered.connect(lambda x : self.profile.setCurrentIndex(idx))

  #----------------------------------------------------------------------------------------------------------
  def copyPrefixText(self):
    if self.launcherCombo.currentText()=="Steam Proton":
      self.protonPrefixold = self.compatData.text()
    else:
      self.winePrefixold = self.compatData.text()

  #----------------------------------------------------------------------------------------------------------
  def copyLauncherBinaryText(self):
    if self.launcherCombo.currentText()=="Steam Proton":
      self.protonExecold = self.protonExec.text()
    else:
      self.wineExecold = self.protonExec.text()

  #----------------------------------------------------------------------------------------------------------
  def changeLanguage(self):
    self.console.info(f"[W] Switching languages is not yet supported!!")

  #----------------------------------------------------------------------------------------------------------
  def changeLauncher(self):
    # self.console.info(f"Setting up {self.launcherList.currentText()}...")
    # proton = True
    if self.launcherCombo.currentText()=="Steam Proton":
      self.lblWineExec.setVisible(False)
      self.lblWinePrefix.setVisible(False)
      self.wineExec.setVisible(False)
      self.winePrefix.setVisible(False)

      self.lblProtonExec.setVisible(True)
      self.lblCompatData.setVisible(True)
      self.protonExec.setVisible(True)
      self.compatData.setVisible(True)

      self.lblSteamRoot.setVisible(True)
      self.steamRoot.setVisible(True)
      self.btnSelectSteamRoot.setVisible(True)

      self.steamRoot.setEnabled(True)
      self.btnSelectSteamRoot.setEnabled(True)
    else:
      self.console.info(f"{C_RED}[WARNING]</font> Wine32 and Wine64 are untested!")
      s = self.lblCompatData.size()
      self.lblWinePrefix.setFixedSize(s) # only need to resize one to the widest size
                                         # since the layout is

      self.lblWineExec.setVisible(True)
      self.lblWinePrefix.setVisible(True)
      self.wineExec.setVisible(True)
      self.winePrefix.setVisible(True)

      self.lblProtonExec.setVisible(False)
      self.lblCompatData.setVisible(False)
      self.protonExec.setVisible(False)
      self.compatData.setVisible(False)

      self.lblSteamRoot.setVisible(False)
      self.steamRoot.setVisible(False)
      self.btnSelectSteamRoot.setVisible(False)

      self.steamRoot.setEnabled(False)
      self.btnSelectSteamRoot.setEnabled(False)
  
  #----------------------------------------------------------------------------------------------------------
  def findWine(self):
    if self.protonExec.text()=="":
      result = subprocess.run(["which", "wine"], stdout=subprocess.PIPE)
      if result.stdout:
        result = result.stdout.decode('utf-8').strip()
        self.protonExec.setText(result)
        self.console.info(f"Setting wine binary to {result}...")
      else:
        self.console.info(f"{C_RED}[WARNING]</font> Wine binary not found! Please set it manually...")

  #----------------------------------------------------------------------------------------------------------
  def findDungeonHelper(self):
    if self.useDungeonHelper.isChecked() and self.DungeonHelperExec.text()=="":
      if self.compatData.text():
        try:
          out = subprocess.check_output([f"find {self.compatData.text()} -iname DungeonHelper.exe"], shell=True)
          if out:
            out = out.decode('utf-8').strip()
            self.DungeonHelperExec.setText(out)
            self.console.info(f"Setting DungeonHelper binary to {out}...")
          else:
            self.console.info(f"{C_RED}[WARNING]</font>  DungeonHelper binary not found! Is it installed? If so, please set it manually...")
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
          self.console.info(f"{C_RED}[WARNING]</font> xdotool binary not found! Is it installed? If so, please set it manually...")
      except Exception as e:
        self.console.error("Error looking for xdotool binary", e)

  #----------------------------------------------------------------------------------------------------------
  def findProton(self):
    if self.protonExec.text()=="":
      self.console.info(f"{C_RED}[WARNING]</font> findProton function not yet implemented!")
  
  #----------------------------------------------------------------------------------------------------------
  def selectPrefix(self):
    filename = QFileDialog.getExistingDirectory(self, "Select Prefix...")
    if filename:
      self.compatData.setText(filename[0])

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
      self.protonExec.setText(filename[0])

  