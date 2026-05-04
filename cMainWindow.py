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
#
from PyQt6.QtWidgets import QMainWindow, QWidget, QMenu, QSplitter, QGridLayout
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QPoint, QSize, Qt
from cCredentials import cCredentials
from cSettingsProfile import cSettingsProfile
from cSettings import cSettings
from cMacros import cMacros
from cNews import cNews
from cPatch import cPatch
from cConsole import cConsole
from cDungeonHelper import cDungeonHelper
from cProcess import cProcessManager
from cStorage import cStorageManager
from cDDO import cDDO
from cToolbar import cToolbar
from widgets.cOrb import cOrb
from helpers.cImageFactory import *
from helpers.cPrint import cPrint

class cMainWindow(QMainWindow):
  P_POS_X = 100
  P_POS_Y = 100
  P_SIZE_W = 768
  P_SIZE_H = 1024
  sigProfileChanged = pyqtSignal(list)

  def __init__(self):
    super().__init__()
    self._state = QSettings(P_DEFAULT_CONF)
    self.setWindowTitle("μDDO")
    self.setWindowIcon(getIcon(P_MUDDO_DIR+'/images/icon.png'))
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

    self.btnLaunch = cOrb("Launch", P_ICON_D20, tooltip="Launches Dungeons & Dragons Online for all selected" \
                          " accounts in the selected world. <br><b><i>Right-click for more options</i></b>")
    btnQuit = cOrb("Quit", P_ICON_EXIT)
        
    self.console = cConsole(P_DEFAULT_LOGSDIR+'/log')
    cPrint.attachConsole(self.console)
    self.credentials = cCredentials(self)
    self.news = cNews(self)
    self.patch = cPatch(self)
    self.settings = cSettings(self)
    self.macros = cMacros(self)
    self.processManager = cProcessManager()
    self.dh = cDungeonHelper(self)
    self.storageManager = cStorageManager(self)
    self.toolbar = cToolbar(self)

    self.btnLaunch.clicked.connect(self.launchAll)
    btnQuit.clicked.connect(self.close)

    g = QGridLayout()
    g.addWidget(self.credentials.loginSummary,0,0,1,3)
    g.addWidget(newRQLabel("World: "),1,0,1,1)
    g.addWidget(newRQLabel("Profile: "),2,0,1,1)
    g.addWidget(self.credentials.listWorlds,1,1,1,2)
    g.addWidget(self.settings.profileMain,2,1,1,2)
    self.summary = QWidget()
    self.summary.setMaximumWidth(480)
    self.summary.setLayout(g)
    lButtonsBar = newHLayout([self.toolbar.widget, self.dh.orb, self.macros.daemon.orb, self.btnLaunch,
                              "__stretch__", self.summary, "__stretch__", 
                              self.credentials.toggler, self.processManager.toggler, self.storageManager.toggler, 
                              self.macros.toggler, self.settings.toggler, self.patch.toggler, self.news.toggler, self.console.toggler, btnQuit])

    aLaunchAll = self.btnLaunch.menu.addAction("Launch all")
    aKillAll = self.btnLaunch.menu.addAction("Kill all")
    aRestoreAll = self.btnLaunch.menu.addAction("Restore all windows positions")
    aSaveAll = self.btnLaunch.menu.addAction("Save all windows positions")
    aConf = self.btnLaunch.menu.addAction("Show/Hide setting UI")
    aLaunchAll.triggered.connect(self.processManager.startAll)
    aKillAll.triggered.connect(self.processManager.terminateAll)
    aRestoreAll.triggered.connect(self.processManager.restoreWindowAll)
    aSaveAll.triggered.connect(self.processManager.saveWindowAll)
    aConf.triggered.connect(self.credentials.toggle)
    aConf.triggered.connect(self.processManager.toggle)

    self.setCentralWidget(newVFrame([lButtonsBar]))

    self._docks = [self.credentials, self.settings, self.macros, self.processManager,
                   self.storageManager, self.patch, self.news, self.console]
    for dock in self._docks:
      self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
      dock.setFloating(True)

    self.loadState()

    if not P_CERTFILE:
      self.console.error(f"Failed to intialize certificate, is the file \"{P_CERTFILE}\" accessible? ")
    else:
      self.console.info(f"SSL certificate verification enabled! Using {P_CERTFILE}")

  
  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    from cMilvian import cMilvian

    cProcessManager.attachMain(self)
    self.credentials.sigFetchedWorldsInfo.connect(self.processManager.captureOrphan)

    self.settings.initialize()
    if cSettings.profile is None:
      self.console.abort("No valid profile loaded!")
    self.credentials.initialize()
    self.macros.initialize()
    self.news.initialize()
    self.patch.initialize()
    cMilvian.setup()
    self.storageManager.initialize(self.macros.daemon)
    cToolbar.setup()
    # cToolbar.TESTITEMS()

  #----------------------------------------------------------------------------------------------------------
  # This will queue everything; once a user is done queuing, it will emit 
  # sigQueuedUserDone. This will cause self.launchUser() to be triggered
  # for each user individually
  def launchAll(self):
    self.processManager.captureOrphan()
    accs = self.credentials.getSelectedAccounts()
    if not accs: accs = [self.credentials.username.text()]
    if not accs:
      if len(self.processManager.items)==0:
        cPrint.error("No accounts selected. Please add an account or enter a username")
      return
    
    self.processManager.setVisible(True)
    world = self.credentials.listWorlds.currentItem()
    for username in accs:
      if username in self.processManager.items.keys():
        proc = self.processManager.items[username]
      else:
        proc = cDDO(self, username, world)
        self.processManager.addItem(proc)
      proc.launch()
    cPrint.info("Finished queueing...")
  
  #----------------------------------------------------------------------------------------------------------
  def loadState(self):
    pos = self._state.value(f"μDDO/pos",   QPoint(self.P_POS_X, self.P_POS_Y))
    size = self._state.value(f"μDDO/size", QSize(self.P_SIZE_W, self.P_SIZE_H))
    self.move(pos)
    self.resize(size)
    dockState = self._state.value("μDDO/dockState")
    if dockState:
      QMainWindow.restoreState(self, dockState)
  
  #----------------------------------------------------------------------------------------------------------
  def saveState(self):
    self._state.setValue(f"μDDO/pos",  self.pos())
    self._state.setValue(f"μDDO/size", self.size())
    self._state.setValue("μDDO/dockState", QMainWindow.saveState(self))
    for dock in self._docks:
      self._state.setValue(f"{dock.widgetID}/visible", dock.isVisible())
  
  #----------------------------------------------------------------------------------------------------------
  #----------------------------------------------------------------------------------------------------------
  def showEvent(self, event):
    super().showEvent(event)
    for dock in self._docks:
      dock.setVisible(self._state.value(f"{dock.widgetID}/visible", False, type=bool))

  #----------------------------------------------------------------------------------------------------------
  def close(self):
    self.saveState()
    self.settings.save()
    self.settings.close()
    self.macros.close()
    self.processManager.close()
    self.patch.close()
    self.news.close()
    self.credentials.close()
    self.console.close()
    self.storageManager.close()
    super().close()


  


