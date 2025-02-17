# coding=utf-8
###########################################################################
# Name:   μDDO
# Author: Rafael Lago
# Date:   February 2025
#
# Support classes for the Linux based launcher
# for the game Dungeons & Dragons Online
#
# Based on PyLotRO by AJackson <ajackson@bcs.org.uk>
# Based on a script by SNy <SNy@bmx-chemnitz.de>
#
# (C) 2025 Rafael Lago
#
# This file is part of PyLotRO
#
# μDDO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# μDDO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with μDDO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################

from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,\
    QLabel, QLineEdit, QCheckBox, QListWidget, QPushButton
from PyQt6 import QtCore
from cWorlds import cWorldList
from tServerInfo import tServerInfo
from util import *
import json

class cLogin(QWidget):
  sigFetchedGLS        = QtCore.pyqtSignal(bool)
  sigFetchedWorld      = QtCore.pyqtSignal(tuple)
  sigFetchedWorldsInfo = QtCore.pyqtSignal(bool)
  sigFetchedQueueInfo  = QtCore.pyqtSignal(bool)

  def __init__(self, main):
    super().__init__()

    self.main = main
    self.accounts = {}
    self.console = main.console
    self.serverInfo = None

    self.listAccounts = QListWidget()
    self.listWorlds = cWorldList(main)
    self.username = QLineEdit()
    self.password = QLineEdit()
    self.password.setEchoMode(QLineEdit.EchoMode.Password)
    self.showPassword = QCheckBox("Sho&w Password")
    self.multiAccount = QCheckBox("&Multi Account")
    
    btnAdd = QPushButton("&Add")
    btnDel = QPushButton("&Del")
    btnClear = QPushButton("&Clear")
    
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

    g2 = QGridLayout()
    g2.addWidget(quickQLabel("Username: "), 0, 0, 1, 1)
    g2.addWidget(quickQLabel("Password: "), 1, 0, 1, 1)
    g2.addWidget(self.username, 0, 1, 1, 2)
    g2.addWidget(self.password, 1, 1, 1, 2)
    g2.addWidget(btnAdd,3, 0)
    g2.addWidget(btnDel, 3, 1)
    g2.addWidget(btnClear, 3, 2)
    h = QHBoxLayout()
    h.addWidget(self.showPassword)
    h.addWidget(self.multiAccount)
    g2.addLayout(h, 2, 0, 1, 3)

    g1 = QGridLayout()
    g1.addLayout(g2, 1, 0)
    g1.addWidget(QLabel("Accounts:"), 0, 1)
    g1.addWidget(QLabel("Worlds:"),    0, 2)
    g1.addWidget(self.listAccounts,   1, 1, 2, 1)
    g1.addWidget(self.listWorlds,      1, 2, 2, 1)

    self.setLayout(g1)
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
    if not self.listAccounts.findItems(self.username.text(), QtCore.Qt.MatchFlag.MatchExactly):
      self.listAccounts.addItem(self.username.text())
    self.accounts[self.username.text()] = self.password.text()
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
    s = self.listAccounts.selectedItems()
    acc = []
    for i in s:
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
      self.listAccounts.addItem(a)

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
    self.listAccounts.setCurrentRow(-1)
  
  #----------------------------------------------------------------------------------------------------------
  def updateShowPassword(self):
    if self.showPassword.isChecked():
      self.password.setEchoMode(QLineEdit.EchoMode.Normal)
    else:
      self.password.setEchoMode(QLineEdit.EchoMode.Password)

