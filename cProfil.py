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

    btnSelectProtonExec  = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectCompatData  = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectWineExec    = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectWinePrefix  = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectSteamRoot   = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectGameDir     = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectxdotoolExec = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))
    btnSelectDungeonHelperExec = QPushButton(icon=getIcon(P_ICON_OPENFOLDER))

    lblWineExec   = newRQLabel("Wine Executable: ")
    lblWinePrefix = newRQLabel("WINEPREFIX: ")
    lblProtonExec = newRQLabel("Proton Executable: ")
    lblCompatData = newRQLabel("STEAM_COMPAT_DATA: ")
    lblSteamRoot  = newRQLabel("STEAM_ROOT: ")

    lblWineExec.setVisible(False)
    lblWinePrefix.setVisible(False)
    self.wineExec.setVisible(False)
    self.winePrefix.setVisible(False)
    btnSelectWineExec.setVisible(False)
    btnSelectWinePrefix.setVisible(False)

    g = cGridLayout()
    g.appendRow([self.launcherCombo,    lblProtonExec, self.protonExec,  btnSelectProtonExec])
    g.appendRow([self.languageCombo,    lblCompatData, self.compatData,  btnSelectCompatData])
    g.appendRow([None,                  lblSteamRoot,  self.steamRoot,   btnSelectSteamRoot])
    g.appendRow([self.useHighRes,       newRQLabel("Game Path: "),    self.gameDir,     btnSelectGameDir])
    g.appendRow([self.useDungeonHelper, newRQLabel("DungeonHelper exec: "), self.DungeonHelperExec, btnSelectDungeonHelperExec])
    g.appendRow([self.usexdotool,       newRQLabel("xdotool exec: "), self.xdotoolExec, btnSelectxdotoolExec])

    # I am overlapping on purpose, because only one of the two will be visible at the same time
    g.lastRow = 0
    g.appendRow([self.launcherCombo, lblWineExec,   self.wineExec,   btnSelectWineExec])
    g.appendRow([None,               lblWinePrefix, self.winePrefix, btnSelectWinePrefix])
    g.setColumnMinimumWidth(1, 150)
    self.setLayout(g)

    self.usexdotool.toggled.connect(btnSelectxdotoolExec.setEnabled)
    self.usexdotool.toggled.connect(self.xdotoolExec.setEnabled)
    self.usexdotool.toggled.connect(self.findxdotool)
    self.usexdotool.setChecked(False)
    self.xdotoolExec.setEnabled(False)
    btnSelectxdotoolExec.setEnabled(False)

    self.useDungeonHelper.toggled.connect(btnSelectDungeonHelperExec.setEnabled)
    self.useDungeonHelper.toggled.connect(self.DungeonHelperExec.setEnabled)
    self.useDungeonHelper.toggled.connect(self.findDungeonHelper)
    self.useDungeonHelper.setChecked(False)
    self.DungeonHelperExec.setEnabled(False)
    btnSelectDungeonHelperExec.setEnabled(False)

    self.launcherCombo.currentIndexChanged.connect(lambda : lblWineExec.setVisible(self.launcherCombo.currentText().startswith("Wine")))
    self.launcherCombo.currentIndexChanged.connect(lambda : self.wineExec.setVisible(self.launcherCombo.currentText().startswith("Wine")))
    self.launcherCombo.currentIndexChanged.connect(lambda : btnSelectWineExec.setVisible(self.launcherCombo.currentText().startswith("Wine")))
    self.launcherCombo.currentIndexChanged.connect(lambda : lblWinePrefix.setVisible(self.launcherCombo.currentText().startswith("Wine")))
    self.launcherCombo.currentIndexChanged.connect(lambda : self.winePrefix.setVisible(self.launcherCombo.currentText().startswith("Wine")))
    self.launcherCombo.currentIndexChanged.connect(lambda : btnSelectWinePrefix.setVisible(self.launcherCombo.currentText().startswith("Wine")))

    self.launcherCombo.currentIndexChanged.connect(lambda : lblProtonExec.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : self.protonExec.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : btnSelectProtonExec.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : lblCompatData.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : self.compatData.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : btnSelectCompatData.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : lblSteamRoot.setVisible(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : self.steamRoot.setEnabled(self.launcherCombo.currentText().startswith("Steam Proton")))
    self.launcherCombo.currentIndexChanged.connect(lambda : btnSelectSteamRoot.setEnabled(self.launcherCombo.currentText().startswith("Steam Proton")))

    btnSelectWineExec.clicked.connect(   lambda x : self.selectDialog(self.steamRoot, "wine executable", False))
    btnSelectWinePrefix.clicked.connect( lambda x : self.selectDialog(self.steamRoot, "WINEPREFIX"))
    btnSelectProtonExec.clicked.connect( lambda x : self.selectDialog(self.steamRoot, "Steam Proton executable", False))
    btnSelectCompatData.clicked.connect( lambda x : self.selectDialog(self.steamRoot, "STEAM_COMPAT_DATA"))
    btnSelectSteamRoot.clicked.connect(  lambda x : self.selectDialog(self.steamRoot, "STEAM_ROOT"))
    btnSelectGameDir.clicked.connect(    lambda x : self.selectDialog(self.gameDir,   "game path"))
    btnSelectxdotoolExec.clicked.connect(lambda x : self.selectDialog(self.xdotoolExec, "xdotool executable", False))
    btnSelectDungeonHelperExec.clicked.connect(lambda x : self.selectDialog(self.xdotoolExec, "DungeonHelper executable", False))

  #----------------------------------------------------------------------------------------------------------
  def save(self):
    try:
      os.mkdir(P_DEFAULT_CONFIGDIR)
    except: pass

    values = {}
    values['launcher']     = self.launcherCombo.currentText()
    values['language']     = self.languageCombo.currentText()
    values['wineExec']     = self.wineExec.text()
    values['protonExec' ]  = self.protonExec.text()
    values['winePrefix']   = self.winePrefix.text()
    values['compatData']   = self.compatData.text()
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
      self.console.error(f"cProfil.save: could not create {filename} to store profile!",e)
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
      self.console.error(f"cProfil.load: file {filename} not found")
    
    if values:
      try:
        if 'launcher'     in values.keys(): self.launcherCombo.setCurrentIndex(self.launcherCombo.findText(values['launcher']))
        if 'language'     in values.keys(): self.languageCombo.setCurrentIndex(self.languageCombo.findText(values['language']))
        if 'wineExec'     in values.keys(): self.wineExec.setText(values['wineExec'])
        if 'protonExec'   in values.keys(): self.protonExec.setText(values['protonExec'])
        if 'winePrefix'   in values.keys(): self.winePrefix.setText(values['winePrefix'])
        if 'compatData'   in values.keys(): self.compatData.setText(values['compatData'])
        if 'gameDir'      in values.keys(): self.gameDir.setText(values['gameDir'])
        if 'steamRoot'    in values.keys(): self.steamRoot.setText(values['steamRoot'])
        if 'useHighRes'   in values.keys(): self.useHighRes.setChecked(values['useHighRes'])
        if 'usexdotool'   in values.keys(): self.usexdotool.setChecked(values['usexdotool'])
        if 'xdotoolExec'  in values.keys(): self.xdotoolExec.setText(values['xdotoolExec'])
        if 'DungeonHelperExec' in values.keys(): self.DungeonHelperExec.setText(values['DungeonHelperExec'])
        if 'useDungeonHelper'  in values.keys(): self.useDungeonHelper.setChecked(values['useDungeonHelper'])

        if 'lastWorld'    in values.keys(): self.main.credentials.selectWorld(values['lastWorld'])
        if 'lastAccounts' in values.keys(): self.main.credentials.selectAccounts(values['lastAccounts'])
        if 'windowsPreferences' in values.keys(): self.windowsPreferences = values['windowsPreferences']

      except Exception as e:
        self.console.error(f"cProfil.load: error loading profile from {filename}", e)


  # #----------------------------------------------------------------------------------------------------------
  # def connectAction2Profile(self, a : QAction, p : str):
  #   idx = self.profile.findText(p)
  #   a.triggered.connect(lambda x : self.profile.setCurrentIndex(idx))

  # #----------------------------------------------------------------------------------------------------------
  # def copyPrefixText(self):
  #   if self.launcherCombo.currentText()=="Steam Proton":
  #     self.protonPrefixold = self.compatData.text()
  #   else:
  #     self.winePrefixold = self.compatData.text()

  # #----------------------------------------------------------------------------------------------------------
  # def copyLauncherBinaryText(self):
  #   if self.launcherCombo.currentText()=="Steam Proton":
  #     self.protonExecold = self.protonExec.text()
  #   else:
  #     self.wineExecold = self.protonExec.text()

  #----------------------------------------------------------------------------------------------------------
  def changeLanguage(self):
    self.console.info(f"{C_RED}[WARNING]</font> Switching languages is not yet supported!!")

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
  def selectDialog(self, target : QLineEdit, title, dir = True):
    if dir: filename = QFileDialog.getExistingDirectory(self, f"Select {title}...")
    else: filename = QFileDialog.getOpenFileName(self, f"Select {title}...")
    if filename:
      target.setText(filename[0])
    else:
      self.console.error(f"{C_RED}[WARNING] invalid {title} selected, doing nothing...")
