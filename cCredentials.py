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
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,\
    QLabel, QLineEdit, QCheckBox, QListWidget, QPushButton, QSizePolicy, QListWidgetItem
from PyQt6 import QtCore
from cWorlds import cWorldList
from tServerInfo import tServerInfo
from util import *
import json

from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cCredentials(QWidget):
  sigFetchedGLS        = QtCore.pyqtSignal(bool)
  sigFetchedWorld      = QtCore.pyqtSignal(tuple)
  sigFetchedWorldsInfo = QtCore.pyqtSignal(bool)
  sigFetchedQueueInfo  = QtCore.pyqtSignal(bool)

  def __init__(self, main : cMainWindow):
    super().__init__()

    self.main = main
    self.accounts = {}
    self.console = main.console
    self.serverInfo = None

    self.listAccounts = QListWidget()
    # self.listAccounts.setFixedHeight(200)
    self.listWorlds = cWorldList(main)
    # self.listWorlds.setFixedHeight(200)
    self.username = QLineEdit()
    self.password = QLineEdit()
    self.password.setEchoMode(QLineEdit.EchoMode.Password)
    self.showPassword = QCheckBox("Sho&w Password")
    self.multiAccount = QCheckBox("&Multi Account")
    
    btnAdd = QPushButton(" &Add")
    btnDel = QPushButton(" &Del")
    btnClear = QPushButton(" &Clear")
    
    btnAdd.setIcon(getIcon(P_ICON_ADD))
    btnDel.setIcon(getIcon(P_ICON_REMOVE))
    btnClear.setIcon(getIcon(P_ICON_CLEAR))

    btnAdd.clicked.connect(self.addAccount)
    btnDel.clicked.connect(self.delAccount)
    btnClear.clicked.connect(self.clearEdits)
    
    self.listAccounts.currentRowChanged.connect(self.updateUsernamePassword)
    self.showPassword.clicked.connect(self.updateShowPassword)
    self.multiAccount.clicked.connect(self.updateMultiAccount)
    self.multiAccount.setChecked(True)
    self.updateMultiAccount()

    logo = QLabel()
    logo.setPixmap(QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/DDOBanner.png'))
    logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    g2 = QGridLayout()
    g2.addWidget(logo, 0, 0, 1, 3)
    g2.addWidget(newRQLabel("Username: "), 1, 0, 1, 1)
    g2.addWidget(newRQLabel("Password: "), 2, 0, 1, 1)
    g2.addWidget(self.username, 1, 1, 1, 2)
    g2.addWidget(self.password, 2, 1, 1, 2)
    g2.addWidget(btnAdd,4, 0)
    g2.addWidget(btnDel, 4, 1)
    g2.addWidget(btnClear, 4, 2)
    h = QHBoxLayout()
    h.addWidget(self.showPassword)
    h.addWidget(self.multiAccount)
    g2.addLayout(h, 3, 0, 1, 3)

    v1 = QVBoxLayout()
    v1.addWidget(QLabel("Accounts:"))
    v1.addWidget(self.listAccounts)
                 
    v2 = QVBoxLayout()
    v2.addWidget(QLabel("Worlds:"))
    v2.addWidget(self.listWorlds)

    h3 = QHBoxLayout()
    h3.addLayout(g2)
    h3.addLayout(v1)
    h3.addLayout(v2)
    self.setLayout(h3)
    self.loadAccounts()
    self.sigFetchedWorld.connect(self.listWorlds.updateWorld)
    self.sigFetchedQueueInfo.connect(self.main.btnLaunch.setEnabled)

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.serverInfo = tServerInfo(self.main)
    self.console.info("Launching server info collector...")
    QtCore.QThreadPool.globalInstance().start(self.serverInfo)

  #----------------------------------------------------------------------------------------------------------
  def addAccount(self):
    self.accounts[self.username.text()] = self.password.text()
    item = self.listAccounts.findItems(self.username.text(), QtCore.Qt.MatchFlag.MatchExactly)[0]
    if not item: 
      item = QListWidgetItem(self.username.text())
      self.listAccounts.addItem(item)
    item.setIcon(getIcon(P_ICON_LOCKCLOSE_RED) if self.password.text() == "" else getIcon(P_ICON_LOCKOPEN_GREEN))
        
    if self.password.text() != "":
      self.console.info(C_RED + "WARNING</font>: passwords are saved in plain text and not handled safely yet! Use it at your own risk!")
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
    return "" if out is None else out.text()

  #----------------------------------------------------------------------------------------------------------
  def selectWorld(self, name):
    if not name: return
    m = self.listWorlds.findItems(name, QtCore.Qt.MatchFlag.MatchExactly)
    if m:
      self.listWorlds.setCurrentItem(m[0])
    else:
      self.console.error(f"cLogin.selectWorld: world \"{name}\" not found in the list!")

  #----------------------------------------------------------------------------------------------------------
  def selectAccounts(self, accs : list):
    if not accs: return
    self.listAccounts.clearSelection()
    for name in accs:
      try:
        m = self.listAccounts.findItems(name, QtCore.Qt.MatchFlag.MatchExactly)
        self.listAccounts.setCurrentItem(m[0], QtCore.QItemSelectionModel.SelectionFlag.Select)
      except Exception as e:
        self.console.error(f"cLogin.selectAccounts: account \"{name}\" not found in the list!", e)

  #----------------------------------------------------------------------------------------------------------
  def saveAccounts(self):
    try:
      os.mkdir(P_DEFAULT_CONFIGDIR)
    except: pass
    accFileName = P_DEFAULT_CONFIGDIR+"/accounts.json"

    try:
      json.dump(self.accounts, open(accFileName,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cLogin.save: could not create {accFileName} to store credentials!",e)
  
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
    self.console.info(f" {len(selected)} accounts removed successfully")
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

