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

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,\
  QPushButton, QLabel
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QThreadPool
from cLogin import cLogin
from cSettings import cSettings
from cNews import cNews
from cPatch import cPatch
from cConsole import cConsole
from util import *
from tServerInfo import tServerInfo
import sys

class cMainWindow(QMainWindow):

  def __init__(self):
    super().__init__()
    self.setWindowTitle("μDDO")
    self.setWindowIcon(QIcon(QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/DDOLinuxIcon.png')))

    self.serverData = None

    lButtonsBar = QHBoxLayout()
    btnDHelper = QPushButton("DungeonHelper")
    btnLaunch = QPushButton("Launch")
    btnClose = QPushButton("Close")
    lButtonsBar.addWidget(btnDHelper)
    lButtonsBar.addStretch()
    lButtonsBar.addWidget(btnLaunch)
    lButtonsBar.addWidget(btnClose)

    btnClose.clicked.connect(self.close)
    btnLaunch.clicked.connect(self.launch)

    self.console = cConsole(P_DEFAULT_CONFIGDIR+'/log')
    self.login = cLogin(self)
    self.news = cNews()
    self.settings = cSettings(self)
    self.patch = cPatch()
    l = QVBoxLayout()
    l.addWidget(self.login)
    l.addWidget(self.settings)
    l.addWidget(self.news)
    l.addWidget(self.patch)
    l.addWidget(self.console)
    l.addLayout(lButtonsBar)

    w = QWidget()
    w.setLayout(l)
    self.setCentralWidget(w)
    self.resize(768,768)

    self.settings.load()
    if not P_CERTFILE:
      self.console.error(f"Failed to intialize certificate, is the file \"{P_CERTFILE}\" accessible? ")
    else:
      self.console.info(f"SSL certificate verification enabled! Using {P_CERTFILE}")
    self.startFecthingServerData()
    self.console.info("Initialized...")

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def startFecthingServerData(self):
    self.console.info("Launching server info collector...")
    serverData = tServerInfo(self)
    QThreadPool.globalInstance().start(serverData)

    # try:
    #   self.serverData = tServerInfo(self)
    #   self.serverData.getGLSData()
    # except Exception as e:
    #   self.console.error("Error attempting to download server info", e)
    
    # if self.serverData.realmList:
    #   self.login.listWorlds.populate(self.serverData.realmList)
    # else:
    #   self.console.error(f"Got an empty realmList! Is the GLSDataCenter up?<br>Check the URL \"{self.serverData.urlGLSDataCenter}\"")
    #   self.console.error(f"Please solve the issue and restart μDDO")


  #----------------------------------------------------------------------------------------------------------
  def close(self):
    self.settings.save()
    super().close()


  


