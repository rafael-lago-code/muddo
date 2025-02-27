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
from PyQt6.QtWidgets import QMainWindow, QWidget, QPushButton, QMenu, QToolButton
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from cCredentials import cCredentials
from cSettings import cSettings
from cNews import cNews
from cPatch import cPatch
from cConsole import cConsole
from cProfil import cProfil
from cDungeonHelper import cDungeonHelper
from cProcess import cProcessManager, cProcessItem
from tAccount import tAccount
from util import *
import json

class cMainWindow(QMainWindow):
  sigAuthenticatedUser = pyqtSignal(str)
  sigQueuedUser = pyqtSignal(str)
  sigQueuedUserDone = pyqtSignal(str)
  sigProfileChanged = pyqtSignal(list)

  def __init__(self):
    super().__init__()
    self.setWindowTitle("μDDO")
    self.setWindowIcon(QIcon(QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/icon.png')))
    self.launchMenu = QMenu() # filled in cSettings

    self.btnProfile = QPushButton()
    self.btnProfile.setMenu(self.launchMenu)
    self.btnProfile.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.btnProfile.setFixedWidth(25)

    self.btnLaunch = QPushButton(getIcon(P_ICON_D20), " &Launch")
    self.btnLaunch.setEnabled(False)
    self.btnLaunch.setIconSize(P_DEFAULT_ICON_SIZE)
    self.btnLaunch.setFixedWidth(120)
    self.btnLaunch.clicked.connect(self.launchAll)
    
    launchLay = newHLayout([self.btnLaunch, self.btnProfile])
    launchLay.setSpacing(0)

    btnQuit = QPushButton(getIcon(P_ICON_EXIT), " &Quit")
    btnQuit.setIconSize(P_DEFAULT_ICON_SIZE)
    btnQuit.setFixedWidth(120)
    btnQuit.clicked.connect(self.close)

    self.console = cConsole(P_DEFAULT_CONFIGDIR+'/log')
    self.credentials = cCredentials(self)
    self.news = cNews()
    self.patch = cPatch(self)
    self.settings = cSettings(self)
    self.processManager = cProcessManager(self)
    self.processManager.setVisible(False)

    self.DungeonHelperWidget = cDungeonHelper(self)
    lButtonsBar = newHLayout(self.DungeonHelperWidget.getWidgets()+ ['__stretch__',launchLay, btnQuit])

    tabController  = QWidget()
    tabController.setLayout(newHLayout([self.settings.toggler, self.processManager.toggler, self.patch.toggler, self.news.toggler]))

    w = QWidget()
    w.setLayout(newVLayout([self.credentials, tabController, self.settings, 
                self.processManager, self.news, self.patch, self.console, lButtonsBar]))
    self.setCentralWidget(w)
    self.resize(768,1024)

    if not P_CERTFILE:
      self.console.error(f"Failed to intialize certificate, is the file \"{P_CERTFILE}\" accessible? ")
    else:
      self.console.info(f"SSL certificate verification enabled! Using {P_CERTFILE}")
    
  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.settings.initialize()
    if self.profile() is None:
      self.console.abort("No valid profile loaded!")
    self.credentials.initialize()

    self.DungeonHelperWidget.initialize()
    self.news.initialize()
    self.patch.initialize()
    # self.sigQueuedUserDone.connect(self.launchUser)

  #----------------------------------------------------------------------------------------------------------
  def profile(self, pname : str = None) -> cProfil:
    if pname in self.settings.profiles.keys():
      return self.settings.profiles[pname]
    if self.settings.profileList.currentText() in self.settings.profiles.keys():
      return self.settings.profiles[self.settings.profileList.currentText()]
    else:
      return None


  #----------------------------------------------------------------------------------------------------------
  # This will queue everything; once a user is done queuing, it will emit 
  # sigQueuedUserDone. This will cause self.launchUser() to be triggered
  # for each user individually
  def launchAll(self):
    accs = self.credentials.getSelectedAccounts()
    if not accs: accs = [self.credentials.username.text()]
    if not accs:
      self.console.error("No accounts selected. Please add an account or enter a username")
      return
    
    self.processManager.setVisible(True)
    world = self.credentials.listWorlds.currentItem()
    for username in accs:
      self.console.info(f"Authenticating \"{C_SILVER}{username}</font>\"...")
      proc = cProcessItem(self, username, world)
      self.processManager.addProcess(proc)
      proc.launch()
    self.console.info("Finished submitting authentication, waiting for tickets")

  # #----------------------------------------------------------------------------------------------------------
  # def launchUser(self, username):
    # self.processManager.items[username].launch()

  #----------------------------------------------------------------------------------------------------------
  def close(self):
    self.settings.save()
    super().close()


  


