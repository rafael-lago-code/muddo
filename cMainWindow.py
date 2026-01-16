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
from PyQt6.QtWidgets import QMainWindow, QWidget, QMenu, QSplitter
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QPoint, QSize, Qt
from cCredentials import cCredentials
from cSettings import cSettings
from cShortcuts import cShortcuts
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
    self.launchMenu = QMenu() # filled in cSettings

    self.lblProfile = QLabel()
    self.lblProfile.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.lblProfile.mousePressEvent = lambda e: self.launchMenu.exec(self.lblProfile.mapToGlobal(e.pos()))

    self.btnLaunch = cOrb("Launch", P_ICON_D20)
    self.btnDH = cOrb("Dungeon\nHelper", getIcon(P_MUDDO_DIR+'/images/DungeonHelperIcon32.png'),
                                         tooltip="Launches Dungeon Helper (it if is installed); activates on all instances of the game for as long as it runs.")
    btnQuit = cOrb("Quit", P_ICON_EXIT)
    
    self.console = cConsole(P_DEFAULT_CONFIGDIR+'/log')
    self.credentials = cCredentials(self)
    self.news = cNews(self)
    self.patch = cPatch(self)
    self.settings = cSettings(self)
    self.shortcuts = cShortcuts(self)
    self.processManager = cProcessManager(self)
    self.processManager.setVisible(False)    

    self.btnLaunch.clicked.connect(self.launchAll)
    btnQuit.clicked.connect(self.close)
    self.btnDH.clicked.connect(self.launchDH)

    lButtonsBar = newHLayout([self.btnDH, self.shortcuts.btnDaemonToggle, self.lblProfile, 
                              self.btnLaunch, btnQuit])

    tabController  = QWidget()
    tabController.setLayout(newHLayout([self.settings.toggler, self.processManager.toggler, 
                                        self.shortcuts.toggler, self.patch.toggler, self.news.toggler]))

    self.console.show()

    w = QWidget()
    # w.setLayout(newVLayout([self.credentials, tabController, self.settings, 
    #             self.processManager, self.shortcuts, self.news, self.patch, self.console, lButtonsBar]))
    w.setLayout(newVLayout([self.credentials, tabController, lButtonsBar]))
    self.setCentralWidget(w)
    self.loadState()

    if not P_CERTFILE:
      self.console.error(f"Failed to intialize certificate, is the file \"{P_CERTFILE}\" accessible? ")
    else:
      self.console.info(f"SSL certificate verification enabled! Using {P_CERTFILE}")

    self.credentials.sigFetchedWorldsInfo.connect(self.captureOrphan)

  
  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.sigProfileChanged.connect(lambda : self.btnDH.setVisible(self.profile().useDungeonHelper.isChecked()))
    self.sigProfileChanged.connect(lambda p: self.lblProfile.setText(f"Profile: {p[1]}{getArrow()}"))

    self.settings.initialize()
    if self.profile() is None:
      self.console.abort("No valid profile loaded!")
    self.credentials.initialize()
    self.shortcuts.initialize()
    self.news.initialize()
    self.patch.initialize()
    self.credentials.sigFetchedQueueInfo.connect(self.captureOrphan)

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
  
  #----------------------------------------------------------------------------------------------------------
  def launchDH(self):
    self.processManager.setVisible(True)
    dh = cDungeonHelper(self)
    self.processManager.addItem(dh)
    dh.launch()

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
    self.console.close()
    self.settings.close()
    self.shortcuts.close()
    self.patch.close()
    self.news.close()
    self.saveState()
    super().close()


  


