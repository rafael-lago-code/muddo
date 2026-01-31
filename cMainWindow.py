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
from cSettings import cSettings
from cMacros import cMacros
from cNews import cNews
from cPatch import cPatch
from cConsole import cConsole
from cProfil import cProfil
from cDungeonHelper import cDungeonHelper
from cProcess import cProcessManager
from cDDO import cDDO
from cWidgets.cOrb import cOrb
from cWidgets.util import *

class cMainWindow(QMainWindow):
  P_POS_X = 100
  P_POS_Y = 100
  P_SIZE_W = 768
  P_SIZE_H = 1024
  sigProfileChanged = pyqtSignal(list)

  def __init__(self):
    super().__init__()
    self.setWindowTitle("μDDO")
    self.setWindowIcon(getIcon(P_MUDDO_DIR+'/images/icon.png'))
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    self.btnLaunch = cOrb("Launch", P_ICON_D20, tooltip="Launches Dungeons & Dragons Online for all selected" \
                          " accounts in the selected world. <br><b><i>Right-click for more options</i></b>")
    btnQuit = cOrb("Quit", P_ICON_EXIT)
        
    self.console = cConsole(P_DEFAULT_CONFIGDIR+'/log')
    self.credentials = cCredentials(self)
    self.news = cNews(self)
    self.patch = cPatch(self)
    self.settings = cSettings(self)
    self.macros = cMacros(self)
    self.processManager = cProcessManager()
    self.processManager.setVisible(False)    
    self.dh = cDungeonHelper(self)

    self.btnLaunch.clicked.connect(self.launchAll)
    btnQuit.clicked.connect(self.close)
    # self.btnDH.clicked.connect(self.launchDH)

    g = QGridLayout()
    g.addWidget(self.credentials.loginSummary,0,0,1,3)
    g.addWidget(newRQLabel("World: "),1,0,1,1)
    g.addWidget(newRQLabel("Profile: "),2,0,1,1)
    g.addWidget(self.credentials.listWorlds,1,1,1,2)
    g.addWidget(self.settings.profileMain,2,1,1,2)
    self.summary = QWidget()
    self.summary.setMaximumWidth(480)
    self.summary.setLayout(g)
    lButtonsBar = newHLayout([self.dh.orb, self.macros.daemon.orb, self.btnLaunch,
                              "__stretch__", self.summary, "__stretch__", 
                              self.credentials.toggler, self.processManager.toggler, self.macros.toggler, self.settings.toggler, 
                              self.patch.toggler, self.news.toggler, self.console.toggler, btnQuit])

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

    self.console.show()

    self.setCentralWidget(newVFrame([lButtonsBar]))
    self.loadState()

    if not P_CERTFILE:
      self.console.error(f"Failed to intialize certificate, is the file \"{P_CERTFILE}\" accessible? ")
    else:
      self.console.info(f"SSL certificate verification enabled! Using {P_CERTFILE}")

    self.credentials.sigFetchedWorldsInfo.connect(self.captureOrphan)

  
  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    from XHelper import XHelper
    from cMilvian import cMilvian
    from cTop import cTop
    self.sigProfileChanged.connect(lambda : self.dh.orb.setEnabled(self.profile().useDungeonHelper.isChecked()))

    cProcessManager.attachMain(self)

    self.settings.initialize()
    if self.profile() is None:
      self.console.abort("No valid profile loaded!")
    self.credentials.initialize()
    self.macros.initialize()
    self.news.initialize()
    self.patch.initialize()
    self.credentials.sigFetchedQueueInfo.connect(self.captureOrphan)

    XHelper.attachConsole(self.console)
    cTop.attachConsole(self.console)
    cMilvian.setup(os.path.dirname(self.profile().DungeonHelperExec.text()), self.console)
    
    #TODO MOVE CAPTURE ORPHANS TO cPROCESS!!!! AND CONNECT btNCAPUREORPHANS !
   

  #----------------------------------------------------------------------------------------------------------
  def profile(self, pname : str = None) -> cProfil:
    if pname in self.settings.profiles.keys():
      return self.settings.profiles[pname]
    if self.settings.profileList.currentText() in self.settings.profiles.keys():
      return self.settings.profiles[self.settings.profileList.currentText()]
    else:
      return None
    
  #----------------------------------------------------------------------------------------------------------
  def captureOrphan(self):
    import subprocess
    output = subprocess.check_output("ps -eo pid,command", shell=True, text=True)
    output = output.split("\n")
    orphanCandidates = {}
    found = False
    for line in output:
      line = (line.strip()).split(" ")
      if len(line)<2: continue
      if not self.processManager.isPIDManaged(line[0]):
        if cDDO.isDDOCmd(line[1]):
          orphanCandidates[line[0]] = " ".join(line[1:])
          orphan : cDDO = cDDO.createFromOrphan(self, " ".join(line))
          if orphan:
            found = True
            self.console.info(f"Found orphan DDO process: [{orphan.pid.text()}, {orphan.username.text()}, {C_SILVER}{orphan.worldname.text()}</font>]")
            self.processManager.addItem(orphan)
    if not found:
      self.console.info(f"No orphan DDO processes were found")
      
  #----------------------------------------------------------------------------------------------------------
  # This will queue everything; once a user is done queuing, it will emit 
  # sigQueuedUserDone. This will cause self.launchUser() to be triggered
  # for each user individually
  def launchAll(self):
    self.captureOrphan()
    accs = self.credentials.getSelectedAccounts()
    if not accs: accs = [self.credentials.username.text()]
    if not accs:
      if len(self.processManager.items)==0:
        self.console.error("No accounts selected. Please add an account or enter a username")
      return
    
    self.processManager.setVisible(True)
    world = self.credentials.listWorlds.currentItem()
    for username in accs:
      if username in self.processManager.items.keys():
        continue
      proc = cDDO(self, username, world)
      self.processManager.addItem(proc)
      proc.launch()
    self.console.info("Finished queueing...")
  
  # #----------------------------------------------------------------------------------------------------------
  # def launchDH(self):
  #   if not self.DHProcess:
  #     self.DHProcess = cDungeonHelper(self)
  #     self.processManager.addItem(self.DHProcess)
  #   self.processManager.setVisible(True)
  #   self.DHProcess.launch()

  #----------------------------------------------------------------------------------------------------------
  def loadState(self):
    settings = QSettings(P_DEFAULT_CONF)
    pos = settings.value(f"μDDO/pos",   QPoint(self.P_POS_X, self.P_POS_Y))
    size = settings.value(f"μDDO/size", QSize(self.P_SIZE_W, self.P_SIZE_H))
    self.move(pos)
    self.resize(size)
  
  #----------------------------------------------------------------------------------------------------------
  def saveState(self):
    settings = QSettings(P_DEFAULT_CONF)
    settings.setValue(f"μDDO/pos",  self.pos())
    settings.setValue(f"μDDO/size", self.size())
  
  #----------------------------------------------------------------------------------------------------------
  def close(self):
    self.settings.save()
    self.settings.close()
    self.macros.close()
    self.processManager.close()
    self.patch.close()
    self.news.close()
    self.credentials.close()
    self.console.close()
    self.saveState()
    super().close()


  


