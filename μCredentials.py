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
from PyQt6.QtWidgets import QWidget, QGridLayout, QListWidget, QSizePolicy, QListWidgetItem, QCheckBox, QLineEdit
from PyQt6.QtCore import Qt, QSize
from widgets.μCombo import μCheckCombo
from μSettings import μSetup
from μWorlds import μWorldList
from μServerInfo import μServerInfo
from helpers.χPrint import χPrint
from widgets.μText import μDisplayLabel
from widgets.μOrb import μOrbSmall
from helpers.μImageFactory import *
from helpers.μYAML import μYAML

from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow
   from μSettings   import μSettingsProfile

class μCredentials(QWidget):

  def __init__(self, main : μMainWindow):
    super().__init__()
    self.main = main
    self.accounts = {}
    self.accountsList  = QListWidget()
    self.accountsCombo = μCheckCombo()
    self.username       = QLineEdit()
    self.password       = QLineEdit()
    self.password.setEchoMode(QLineEdit.EchoMode.Password)
    self.showPassword   = QCheckBox("Sho&w Password")

    btnAdd   = μOrbSmall(icon=P_ICON_ADD,    tooltip="Add a new account with the username and password from current fields.\nIf the username exists, it updates the password")
    btnDel   = μOrbSmall(icon=P_ICON_REMOVE, tooltip="Delete currently selected account(s)")
    btnClear = μOrbSmall(icon=P_ICON_CLEAR,  tooltip="Deselects accounts and clear all text boxes")

    btnAdd.clicked.connect(self.addAccount)
    btnDel.clicked.connect(self.delAccount)
    btnClear.clicked.connect(self.clearEdits)

    self.accountsList.currentRowChanged.connect(self.updateUsernamePassword)
    self.password.editingFinished.connect(self.addAccount)
    self.showPassword.clicked.connect(self.updateShowPassword)

    g = QGridLayout()
    g.addWidget(newRQLabel("Username: "), 0, 0, 1, 1)
    g.addWidget(newRQLabel("Password: "), 1, 0, 1, 1)
    g.addWidget(self.username, 0, 1, 1, 2)
    g.addWidget(self.password, 1, 1, 1, 2)
    g.addWidget(btnAdd,   0, 3)
    g.addWidget(btnDel,   1, 3)
    g.addWidget(btnClear, 2, 3)
    g.addWidget(self.showPassword, 2, 0, 1, 3)

    self.setLayout(newHLayout([g, newVLayout(["Accounts:", self.accountsList])]))
    self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    self.loadAccounts()

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    μServerInfo.sigFetchedWorld.connect(μWorldList.updateWorld)
    μServerInfo.sigFetchedQueueInfo.connect(self.main.btnLaunch.setEnabled)
    μServerInfo.sigFetchedWorldsInfo.connect(self.main.processManager.captureOrphan)
    self.accountsCombo.changed.connect(lambda x=μSetup: x.session.setAccounts(self.getSelectedAccounts()))
    μWorldList.currentTextChanged.connect(lambda x, y=μSetup: y.session.setWorld(x))
    μSetup.widget.sigProfileChanged.connect(self.updateProfile)
    self.updateProfile(μSetup.profile, μSetup.lastProfile)
    χPrint.info("Launching server info collector...")
    μServerInfo.collect()

  #----------------------------------------------------------------------------------------------------------
  def updateProfile(self, prof : μSettingsProfile, last : str):
    if prof.session.world:    μWorldList.selectWorld(prof.session.world)
    if prof.session.accounts: self.selectAccounts(prof.session.accounts)

  #----------------------------------------------------------------------------------------------------------
  def _accountIcon(self, username):
    return getIcon(P_ICON_LOCKCLOSE_RED) if self.accounts.get(username, "") == "" else getIcon(P_ICON_LOCKOPEN_GREEN)

  #----------------------------------------------------------------------------------------------------------
  def addAccount(self):
    name = self.username.text()
    if not name: return
    self.accounts[name] = self.password.text()
    icon = self._accountIcon(name)

    # Update listAccounts icon or add new item
    items = self.accountsList.findItems(name, Qt.MatchFlag.MatchExactly)
    if items:
      items[0].setIcon(icon)
    else:
      self.accountsList.addItem(QListWidgetItem(icon, name))

    # Update accountsSummary icon or add new item
    for i in range(1, self.accountsCombo.rowModel.rowCount()):
      if self.accountsCombo.rowModel.item(i).text() == name:
        self.accountsCombo.rowModel.item(i).setIcon(icon)
        self.saveAccounts()
        return
    self.accountsCombo.addCheckItem(name, True, icon)

    if self.password.text() != "":
      χPrint.info(C_RED + "WARNING</font>: passwords are saved in plain text and not handled safely yet! Use it at your own risk!")
    self.saveAccounts()

  #----------------------------------------------------------------------------------------------------------
  def updateUsernamePassword(self):
    if self.accountsList.currentRow() >= 0:
      self.username.setText(self.accountsList.currentItem().text())
      self.password.setText(self.accounts[self.username.text()])

  #----------------------------------------------------------------------------------------------------------
  def getSelectedAccounts(self) -> list:
    return self.accountsCombo.getChecked()

  #----------------------------------------------------------------------------------------------------------
  def selectAccounts(self, accs : list):
    if not accs: return
    for i in range(1, self.accountsCombo.rowModel.rowCount()):
      item = self.accountsCombo.rowModel.item(i)
      item.setData(item.text() in accs, Qt.ItemDataRole.UserRole)
    self.accountsCombo.refreshHeader()

  #----------------------------------------------------------------------------------------------------------
  def saveAccounts(self):
    try:
      db = μYAML(P_DEFAULT_CONFIGDIR+"/accounts.yaml")
      db.raw = self.accounts
      db.save()
    except Exception as e:
      χPrint.error(f"cLogin.save: could not create accounts.yaml to store credentials!", e)

  #----------------------------------------------------------------------------------------------------------
  def loadAccounts(self):
    self.accounts = μYAML(P_DEFAULT_CONFIGDIR+"/accounts.yaml").raw
    for a in self.accounts.keys():
      icon = self._accountIcon(a)
      self.accountsList.addItem(QListWidgetItem(icon, a))
      self.accountsCombo.addCheckItem(a, True, icon)

  #----------------------------------------------------------------------------------------------------------
  def delAccount(self):
    selected = self.accountsList.selectedItems()
    for i in selected:
      name = i.text()
      del self.accounts[name]
      self.accountsList.takeItem(self.accountsList.row(i))
      for j in range(1, self.accountsCombo.rowModel.rowCount()):
        if self.accountsCombo.rowModel.item(j).text() == name:
          self.accountsCombo.rowModel.removeRow(j)
          break
    χPrint.info(f"{len(selected)} accounts removed successfully")
    self.saveAccounts()

  #----------------------------------------------------------------------------------------------------------
  def clearEdits(self):
    self.username.clear()
    self.password.clear()
    self.accountsList.clearSelection()

  #----------------------------------------------------------------------------------------------------------
  def updateShowPassword(self):
    if self.showPassword.isChecked():
      self.password.setEchoMode(QLineEdit.EchoMode.Normal)
    else:
      self.password.setEchoMode(QLineEdit.EchoMode.Password)
