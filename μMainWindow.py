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
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QPoint, QSize, Qt
from μCredentials import μCredentials
from μServerInfo import μServerInfo
from μWorlds import μWorldList
from μMap import μMap
from μSettings import μSetup
from μMacros import μMacros, μMacroRegistry
from μPatch import μPatch
from μConsole import μConsole
from μDungeonHelper import μDungeonHelper
from μProcess import μProcessManager
from μStorage import μStorage
from μDDO import μDDO
from μBrowser import μBrowser
from μStrategy import μStrategy
from μSummary import μSummary
from μToolbar import μToolbar
from widgets.μOrb import μOrb
from helpers.μImageFactory import *
from helpers.μPrint import χPrint
from helpers.χHelper import χHelper

class μMainWindow(QMainWindow):
  P_POS_X = 100
  P_POS_Y = 100
  P_SIZE_W = 768
  P_SIZE_H = 1024
  sigProfileChanged = pyqtSignal(list)

  def __init__(self):
    super().__init__()
    μImageFactory.setMask((255,128,255))
    self._state = QSettings(P_DEFAULT_CONF)
    self.setWindowTitle("μDDO")
    self.setWindowIcon(getIcon(P_MUDDO_DIR+'/images/icon.png'))
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

    self.btnLaunch = μOrb("Launch", P_ICON_D20, tooltip="Launches Dungeons & Dragons Online for all selected" \
                          " accounts in the selected world. <br><b><i>Right-click for more options</i></b>")
    btnQuit = μOrb("Quit", P_ICON_EXIT)

    self.console = μConsole(P_DEFAULT_LOGSDIR+'/log')
    χPrint.attachConsole(self.console)
    μServerInfo()
    μWorldList()
    self.credentials = μCredentials(self)
    self.patch = μPatch(self)
    self.setup = μSetup(self)
    self.macros = μMacros(self)
    self.browser = μBrowser(self)
    self.processManager = μProcessManager()
    self.dh = μDungeonHelper(self)
    self.storageManager = μStorage(self)
    self.toolbar = μToolbar(self)
    self.strategy = μStrategy(self)
    self.map = μMap(self)

    self.btnLaunch.clicked.connect(self.launchAll)
    btnQuit.clicked.connect(self.close)

    μSummary.setup(self.credentials)
    lButtonsBar = newHLayout(["__stretch__", self.dh.orb, self.macros.daemon.orb, self.strategy.toggler, self.map.toggler, self.btnLaunch,
                              μSummary.widget, self.browser.toggler, self.processManager.toggler, self.storageManager.toggler, 
                              self.macros.toggler, self.setup.toggler, self.patch.toggler, self.console.toggler, btnQuit,"__stretch__"])

    aLaunchAll = self.btnLaunch.menu.addAction("Launch all")
    aKillAll = self.btnLaunch.menu.addAction("Kill all")
    aRestoreAll = self.btnLaunch.menu.addAction("Restore all windows positions")
    aSaveAll = self.btnLaunch.menu.addAction("Save all windows positions")
    aConf = self.btnLaunch.menu.addAction("Show/Hide setting UI")
    aLaunchAll.triggered.connect(self.processManager.startAll)
    aKillAll.triggered.connect(self.processManager.terminateAll)
    aRestoreAll.triggered.connect(self.processManager.restoreWindowAll)
    aSaveAll.triggered.connect(self.processManager.saveWindowAll)
    aConf.triggered.connect(self.processManager.toggle)

    self.setCentralWidget(newVFrame([lButtonsBar]))

    self._docks = [self.setup, self.macros, self.browser, self.processManager,
                   self.storageManager, self.patch, self.console, self.strategy, self.map]
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
    from μMilvian import μMilvian

    μProcessManager.attachMain(self)

    self.setup.initialize()
    if μSetup.profile is None:
      self.console.abort("No valid profile loaded!")
    μStrategy.restoreSession()
    self.credentials.initialize()
    self.macros.initialize()
    self.patch.initialize()
    χHelper.setup()
    χHelper.registerWindow(int(self.winId()))
    for dock in self._docks:
      χHelper.registerWindow(int(dock.winId()))
    μMacroRegistry.uiTargets = {
      'map':       self.map,
      'strategy':  self.strategy,
      'console':   self.console,
      'browser':   self.browser,
      'process':   self.processManager,
      'setup':     self.setup,
      'macros':    self.macros,
      'patch':     self.patch,
      'storage':   self.storageManager,
      'dh':        self.dh,
    }
    χHelper.startScd()
    μMacroRegistry.buildUIHotkeys()
    μMilvian.setup()
    self.storageManager.initialize(self.macros.daemon)
    μToolbar.setup()
    self._applyStrategyVisibility(μSetup.profile)
    μSetup.widget.sigProfileChanged.connect(lambda profile, _: self._applyStrategyVisibility(profile))
    # cToolbar.TESTITEMS()

  #----------------------------------------------------------------------------------------------------------
  def _applyStrategyVisibility(self, profile):
    enabled = profile.plugins.useStrategy()
    self.strategy.toggler.setVisible(enabled)
    if not enabled: self.strategy.setVisible(False)
    try: profile.plugins._useStrategy.stateChanged.disconnect(self._onStrategyToggled)
    except: pass
    profile.plugins._useStrategy.stateChanged.connect(self._onStrategyToggled)

  def _onStrategyToggled(self, enabled):
    self.strategy.toggler.setVisible(enabled)
    if not enabled: self.strategy.setVisible(False)

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
        χPrint.error("No accounts selected. Please add an account or enter a username")
      return
    
    self.processManager.setVisible(True)
    world = μWorldList.currentItem()
    for username in accs:
      if username in self.processManager.items.keys():
        proc = self.processManager.items[username]
      else:
        proc = μDDO(self, username, world)
        self.processManager.addItem(proc)
      proc.launch()
    χPrint.info("Finished queueing...")
  
  #----------------------------------------------------------------------------------------------------------
  def loadState(self):
    pos = self._state.value(f"μDDO/pos",   QPoint(self.P_POS_X, self.P_POS_Y))
    size = self._state.value(f"μDDO/size", QSize(self.P_SIZE_W, self.P_SIZE_H))
    self.move(pos)
    self.resize(size)
    dockState = self._state.value("μDDO/dockState")
    if dockState:
      QMainWindow.restoreState(self, dockState)
    μToolbar.widget.setVisible(False)
  
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
    μToolbar.widget.setVisible(False)
    for dock in self._docks:
      dock.setVisible(self._state.value(f"{dock.widgetID}/visible", False, type=bool))

  #----------------------------------------------------------------------------------------------------------
  def close(self):
    self.saveState()
    χHelper.stopScd()
    χHelper.unregisterWindow(int(self.winId()))
    for dock in self._docks:
      χHelper.unregisterWindow(int(dock.winId()))
    self.setup.save()
    self.setup.close()
    self.macros.close()
    self.processManager.close()
    self.patch.close()
    self.storageManager.close()
    self.map.close()
    self.strategy.close()
    self.browser.close()
    # Console must be closed last: the closers above still log through μPrint,
    # and writing to a closed console log raised inside a slot aborts the app
    self.console.close()
    super().close()


  


