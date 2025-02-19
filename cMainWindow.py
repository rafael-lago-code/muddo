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
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,\
  QPushButton, QLabel
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from cCredentials import cCredentials
from cSettings import cSettings
from cNews import cNews
from cPatch import cPatch
from cConsole import cConsole
from cProcess import cProcessManager, cProcessItem
from tAccount import tAccount
from util import *
import json

P_DEFAULT_WINDOWSPREFERENCE=P_DEFAULT_CONFIGDIR+os.sep+"windowPreferences.json"

class cMainWindow(QMainWindow):
  sigAuthenticatedUser = pyqtSignal(str)
  sigQueuedUser = pyqtSignal(str)
  sigQueuedUserDone = pyqtSignal(str)

  def __init__(self):
    super().__init__()
    self.setWindowTitle("μDDO")
    self.setWindowIcon(QIcon(QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/icon.png')))

    self.windowsPreferences = {}

    self.btnLaunch = QPushButton("Launch")
    self.btnLaunch.setEnabled(False)
    lButtonsBar = QHBoxLayout()
    btnDHelper = QPushButton("DungeonHelper")
    btnClose = QPushButton("Close")
    lButtonsBar.addWidget(btnDHelper)
    lButtonsBar.addStretch()
    lButtonsBar.addWidget(self.btnLaunch)
    lButtonsBar.addWidget(btnClose)

    btnClose.clicked.connect(self.close)
    self.btnLaunch.clicked.connect(self.queueAll)

    self.console = cConsole(P_DEFAULT_CONFIGDIR+'/log')
    self.credentials = cCredentials(self)
    self.news = cNews()
    self.patch = cPatch()
    self.settings = cSettings(self)
    self.processManager = cProcessManager(self)
    self.processManager.setCollapsed(True)
    l = QVBoxLayout()
    l.addWidget(self.credentials)
    l.addWidget(self.settings)
    l.addWidget(self.processManager)
    l.addWidget(self.news)
    l.addWidget(self.patch)
    l.addWidget(self.console)
    l.addLayout(lButtonsBar)

    w = QWidget()
    w.setLayout(l)
    self.setCentralWidget(w)
    self.resize(768,1024)

    self.settings.load()
    if not P_CERTFILE:
      self.console.error(f"Failed to intialize certificate, is the file \"{P_CERTFILE}\" accessible? ")
    else:
      self.console.info(f"SSL certificate verification enabled! Using {P_CERTFILE}")
    
    self.credentials.initialize()
    # self.news.initialize()
    # self.patch.initialize()

    self.sigQueuedUserDone.connect(self.launchUser)


  #----------------------------------------------------------------------------------------------------------
  # This will queue everything; once a user is done queuing, it will emit 
  # sigQueuedUserDone. This will cause self.launchUser() to be triggered
  # for each user individually
  def queueAll(self):
    accs = self.credentials.getSelectedAccounts()
    if not accs: accs = [self.credentials.username.text()]
    if not accs:
      self.console.error("No accounts selected. Please add an account or enter a username")
      return
    
    self.processManager.setCollapsed(False)
    world = self.credentials.listWorlds.currentItem()
    for username in accs:
      self.console.info(f"Authenticating \"{C_SILVER}{username}</font>\"...")
      proc = cProcessItem(self, username, world)
      self.processManager.addProcess(proc)
    self.console.info("Finished submitting authentication, waiting for tickets")


  #----------------------------------------------------------------------------------------------------------
  def launchUser(self, username):
    self.processManager.items[username].launch()

  #----------------------------------------------------------------------------------------------------------
  def loadWindowsPreferences(self):
    values = None
    if os.path.exists(P_DEFAULT_WINDOWSPREFERENCE):
      with open(P_DEFAULT_WINDOWSPREFERENCE,"r") as f:
        values = json.load(f)
      self.windowsPreferences = values

  #----------------------------------------------------------------------------------------------------------
  def saveWindowsPreferences(self):
    if not self.windowsPreferences: return

    try:
      os.mkdir(os.path.dirname(P_DEFAULT_WINDOWSPREFERENCE))
    except: pass

    try:
      json.dump(self.windowsPreferences, open(P_DEFAULT_WINDOWSPREFERENCE,"w"), separators=(', ',': '), indent=2)
    except Exception as e:
      self.console.error(f"cMain.saveWindowsPreferences: could not create {P_DEFAULT_WINDOWSPREFERENCE} to store windows preferences!",e)

  #----------------------------------------------------------------------------------------------------------
  def close(self):
    self.settings.save()
    super().close()


  


