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
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QCheckBox, QListWidget, \
  QSizePolicy, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal, QThreadPool, QItemSelectionModel, QSize
from cWorlds import cWorldList
from tServerInfo import tServerInfo
from helpers.cPrint import cPrint
from widgets.cToggler import cToggler
from widgets.cOrb import cOrbSmall
from helpers.util import *
import json

from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cCredentials(cToggler):
  sigFetchedGLS        = pyqtSignal(bool)
  sigFetchedWorld      = pyqtSignal(tuple)
  sigFetchedWorldsInfo = pyqtSignal(bool)
  sigFetchedQueueInfo  = pyqtSignal(bool)

  def __init__(self, main : cMainWindow):
    self.widgetID = "credentials"
    super().__init__("Accounts", P_ICON_LOGIN)
    self.toggler.setToolTip("Toggle Accounts UI for selecting, adding or removing accounts and for changing the game World")

    self.main = main
    self.accounts = {}
    self.console = main.console
    self.serverInfo = None

    self.listAccounts = QListWidget()
    self.loginSummary = QLabel()
    self.loginSummary.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.listWorlds = cWorldList(main)
    self.username = QLineEdit()
    self.password = QLineEdit()
    self.password.setEchoMode(QLineEdit.EchoMode.Password)
    self.showPassword = QCheckBox("Sho&w Password")
    self.multiAccount = QCheckBox("&Multi Account")
    
    btnAdd = cOrbSmall(icon=P_ICON_ADD, tooltip="Add a new account with the username and password from current fields."\
                                                "\nIf the username exists, it updates the password")
    btnDel = cOrbSmall(icon=P_ICON_REMOVE, tooltip="Delete currently selected account(s)")
    btnClear = cOrbSmall(icon=P_ICON_CLEAR, tooltip="Deselects accounts and clear all text boxes")
    
    btnAdd.clicked.connect(self.addAccount)
    btnDel.clicked.connect(self.delAccount)
    btnClear.clicked.connect(self.clearEdits)
    
    self.listAccounts.currentRowChanged.connect(self.updateUsernamePassword)
    self.listAccounts.itemSelectionChanged.connect(self.updateSummary)
    self.showPassword.clicked.connect(self.updateShowPassword)
    self.multiAccount.clicked.connect(self.updateMultiAccount)
    self.multiAccount.setChecked(True)
    self.updateMultiAccount()

    # logo = QLabel()
    # logo.setPixmap(QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/DDOBanner.png'))
    # logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    g = QGridLayout()
    # g.addWidget(logo, 0, 0, 1, 3)
    g.addWidget(newRQLabel("Username: "), 0, 0, 1, 1)
    g.addWidget(newRQLabel("Password: "), 1, 0, 1, 1)
    g.addWidget(self.username, 0, 1, 1, 2)
    g.addWidget(self.password, 1, 1, 1, 2)
    g.addWidget(btnAdd,   0, 3)
    g.addWidget(btnDel,   1, 3)
    g.addWidget(btnClear, 2, 3)
    g.addLayout(newHLayout([self.showPassword, self.multiAccount]), 2, 0, 1, 3)

    self.setLayout(newHLayout([g, newVLayout(["Accounts:", self.listAccounts])]))
                              
    self.loadAccounts()
    self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    self.sigFetchedWorld.connect(self.listWorlds.updateWorld)
    self.sigFetchedQueueInfo.connect(self.main.btnLaunch.setEnabled)

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.serverInfo = tServerInfo(self.main)
    cPrint.info("Launching server info collector...")
    QThreadPool.globalInstance().start(self.serverInfo)

  #----------------------------------------------------------------------------------------------------------
  def addAccount(self):
    self.accounts[self.username.text()] = self.password.text()
    item = self.listAccounts.findItems(self.username.text(), Qt.MatchFlag.MatchExactly)
    if not item: 
      item = QListWidgetItem(self.username.text())
      self.listAccounts.addItem(item)
    else:
      item = item[0]
    item.setIcon(getIcon(P_ICON_LOCKCLOSE_RED) if self.password.text() == "" else getIcon(P_ICON_LOCKOPEN_GREEN))
        
    if self.password.text() != "":
      cPrint.info(C_RED + "WARNING</font>: passwords are saved in plain text and not handled safely yet! Use it at your own risk!")
    self.saveAccounts()
  
  #----------------------------------------------------------------------------------------------------------
  def updateUsernamePassword(self):
    if self.listAccounts.currentRow() >= 0:
      self.username.setText(self.listAccounts.currentItem().text())
      self.password.setText(self.accounts[self.username.text()])

  #----------------------------------------------------------------------------------------------------------
  def updateMultiAccount(self):
    if self.multiAccount.isChecked():
      self.listAccounts.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
    else:
      self.listAccounts.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
  
  #----------------------------------------------------------------------------------------------------------
  def getSelectedAccounts(self):
    acc = []
    for i in self.listAccounts.selectedItems():
      acc.append(i.text())
    return acc

  #----------------------------------------------------------------------------------------------------------
  def getSelectedWorld(self):
    out = self.listWorlds.currentItem()
    return "" if out is None else out.name

  #----------------------------------------------------------------------------------------------------------
  def selectWorld(self, name):
    if not name: return
    w = self.listWorlds.worlds.get(name,None)
    if w:
      self.listWorlds.setCurrentIndex(w.index)
    else:
      cPrint.error(f"cLogin.selectWorld: world \"{name}\" not found in the list!")

  #----------------------------------------------------------------------------------------------------------
  def selectAccounts(self, accs : list):
    if not accs: return
    self.listAccounts.clearSelection()
    for name in accs:
      try:
        m = self.listAccounts.findItems(name, Qt.MatchFlag.MatchExactly)
        self.listAccounts.setCurrentItem(m[0], QItemSelectionModel.SelectionFlag.Select)
      except Exception as e:
        cPrint.error(f"cLogin.selectAccounts: account \"{name}\" not found in the list!", e)
        return
    
  #----------------------------------------------------------------------------------------------------------
  def updateSummary(self):
    accs = [i for i in self.listAccounts.selectedItems()]
    if len(accs)==1:
      self.loginSummary.setText(f"{accs[0].text()} account selected")
    else:
      self.loginSummary.setText(f"{len(accs)} accounts selected")

  #----------------------------------------------------------------------------------------------------------
  def saveAccounts(self):
    try:
      os.mkdir(P_DEFAULT_CONFIGDIR)
    except: pass
    accFileName = P_DEFAULT_CONFIGDIR+"/accounts.json"

    try:
      json.dump(self.accounts, open(accFileName,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      cPrint.error(f"cLogin.save: could not create {accFileName} to store credentials!",e)
  
  #----------------------------------------------------------------------------------------------------------
  def loadAccounts(self):
    accFileName = P_DEFAULT_CONFIGDIR+"/accounts.json"

    if os.path.exists(accFileName):
      with open(accFileName,"r") as f:
        self.accounts = json.load(f)
    else:
      self.accounts = {}
    
    for a in self.accounts.keys():
      self.listAccounts.addItem(QListWidgetItem(getIcon(P_ICON_LOCKCLOSE_RED) if self.accounts[a] == ""\
                                else getIcon(P_ICON_LOCKOPEN_GREEN), a))

  #----------------------------------------------------------------------------------------------------------
  def delAccount(self):
    selected = self.listAccounts.selectedItems()
    for i in selected:
      del self.accounts[i.text()]
      self.listAccounts.takeItem(self.listAccounts.row(i))
    cPrint.info(f" {len(selected)} accounts removed successfully")
    self.saveAccounts()

  #----------------------------------------------------------------------------------------------------------
  def clearEdits(self):
    self.username.clear()
    self.password.clear()
    self.listAccounts.clearSelection()
  
  #----------------------------------------------------------------------------------------------------------
  def updateShowPassword(self):
    if self.showPassword.isChecked():
      self.password.setEchoMode(QLineEdit.EchoMode.Normal)
    else:
      self.password.setEchoMode(QLineEdit.EchoMode.Password)

