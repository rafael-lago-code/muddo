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
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import pyqtSignal
from widgets.cToggler import cToggler
from widgets.cOrb import cOrbSmall
from helpers.util import *
from widgets.cLog import cLog
from helpers.cTop import cTop
from helpers.cPrint import cPrint
from collections import OrderedDict
import re
import signal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cProcessManager(cToggler):
  main = None      # set in attachMain
  profile = None   # set in attachMain

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def attachMain(self, main : cMainWindow):
    self.main = main
    aProcessItem.attachMain(main)

  #----------------------------------------------------------------------------------------------------------
  def __init__(self):
    self.widgetID = "processManager"
    super().__init__("Process\nManager", P_ICON_PROPERTIES)
    self.toggler.setToolTip("Toggle Process Manager and allows control of individual launched processes")
    self.items : OrderedDict[str, aProcessItem] = OrderedDict()
    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)

    header = QWidget()
    header.setLayout(newHLayout([newHeaderLabel("PID", 50), newHeaderLabel("WinID"),\
                     newHeaderLabel("World"), newHeaderLabel("Profile"), "Username"]))

    self.btnStartAll   = cOrbSmall(icon=P_ICON_PLAY,      tooltip="Starts all processes which are not yet already running")
    self.btnKillAll    = cOrbSmall(icon=P_ICON_SKULL,     tooltip="Left click: terminates all running processes<br>Ctrl+Left click or Right click: force termination (SIGKILL) all processes")
    self.btnSaveAll    = cOrbSmall(icon=P_ICON_SAVEALL,   tooltip="Saves all windows positions")
    self.btnRestoreAll = cOrbSmall(icon=P_ICON_UNDO,      tooltip="Restores all previously saved windows positions")
    self.btnCleanAll   = cOrbSmall(icon=P_ICON_CLEAR,     tooltip="Clear all processes<br>Ctrl+Left click or Right click: kill and clear all processes")
    self.btnAudioAll    = cOrbSmall(icon=P_ICON_MUTE,      tooltip="Toggles audio on/off for all processes")
    self.btnLogAll     = cOrbSmall(icon=P_ICON_NOTES,     tooltip="Toggles logs on/off for all processes")
    self.btnCaptureOrphans = cOrbSmall(icon=getIcon(P_MUDDO_DIR+'/images/chain.png'), tooltip="Attempts to find running instances of DDO and capture them"\
                                     " into our own process manager.\n<b><i>WARNING</i></b>: this will not try to guess which"\
                                     " profile (if any) was used to launch the original DDO instance!")
    
    self.btnCaptureOrphans.clicked.connect(self.captureOrphan)
    self.btnStartAll.clicked.connect(self.startAll)
    self.btnKillAll.clicked.connect(self.terminateAll)
    self.btnKillAll.ctrlClicked.connect(lambda : self.terminateAll(force=True))
    self.btnKillAll.rightClicked.connect(lambda : self.terminateAll(force=True))
    self.btnSaveAll.clicked.connect(self.saveWindowAll)
    self.btnRestoreAll.clicked.connect(self.restoreWindowAll)
    self.btnCleanAll.clicked.connect(self.cleanAll)
    self.btnCleanAll.ctrlClicked.connect(lambda : self.cleanAll(True))
    self.btnCleanAll.rightClicked.connect(lambda : self.cleanAll(True))
    self.btnAudioAll.clicked.connect(self.toggleAudioAll)
    self.btnAudioAll.ctrlClicked.connect(self.audioMuteAll)
    self.btnAudioAll.rightClicked.connect(self.audioMuteAll)

    justSpace = QLabel(" ")
    justSpace.setMinimumWidth(2)
    
    self.content = newVLayout([header])
    self.setLayout(newVLayout([self.content, newHLayout([self.btnCaptureOrphans,"__stretch__", "All processes: ", self.btnStartAll,\
      self.btnKillAll, self.btnSaveAll, self.btnRestoreAll, self.btnCleanAll, self.btnLogAll, self.btnAudioAll, justSpace]),
                    "__stretch__"]))

  #----------------------------------------------------------------------------------------------------------
  def clearItem(self, item : aProcessItem, kill=False):
    if kill and item.status == item.P_STATUS_RUNNING:
      try:
        item.terminate()
      except Exception as e:
        cPrint.error(f"cProcessManager.cleanItem: error killing \"{item.key}\"", e)
    elif item.status == item.P_STATUS_RUNNING:
      return
    
    try:
      self.layout().removeWidget(item)
      del self.items[item.key]
    except Exception as e:
      cPrint.error(f"cProcessManager.cleanItem: unknown error removing item \"{item.key}\"", e)

    item.hide()
    self.main.processManager.resetColour()
    # item.deleteLater()


  #----------------------------------------------------------------------------------------------------------
  def cleanAll(self, kill=False):
    allItems  = set(self.items.values())
    for i in allItems: 
      self.clearItem(i,kill)

  #----------------------------------------------------------------------------------------------------------
  def startAll(self):
    for u in self.items.keys(): 
      if u.startswith("dh_"): continue
      if self.items[u].status == aProcessItem.P_STATUS_RUNNING:
        self.items[u].launch()

  #----------------------------------------------------------------------------------------------------------
  def terminateAll(self):
    allItems = list(self.items.keys())
    for i in allItems: 
      if i.startswith("dh_"): continue
      self.items[i].terminate()

  #----------------------------------------------------------------------------------------------------------
  def killAll(self):
    allItems = list(self.items.keys())
    for i in allItems: 
      if i.startswith("dh_"): continue
      self.items[i].kill()

  #----------------------------------------------------------------------------------------------------------
  def toggleAudioAll(self):
    allItems = list(self.items.keys())
    for i in allItems: 
      self.items[i].audioToggle()

  #----------------------------------------------------------------------------------------------------------
  def audioMuteAll(self):
    allItems = list(self.items.keys())
    for i in allItems: 
      self.items[i].audioMute()
    
  #----------------------------------------------------------------------------------------------------------
  def saveWindowAll(self):
    for u in self.items.keys(): self.items[u].saveWindow()
  
  #----------------------------------------------------------------------------------------------------------
  def restoreWindowAll(self):
    for u in self.items.keys(): self.items[u].restoreWindow()

  #----------------------------------------------------------------------------------------------------------
  def itemExists(self, p : aProcessItem):
    for key, proc in self.items.items():
      if key == p.key: return True
      if proc == p: return True
    return False

  #----------------------------------------------------------------------------------------------------------
  def addItem(self, p : aProcessItem):
    if self.itemExists(p): return
    self.btnKillAll.setEnabled(True)
    self.btnSaveAll.setEnabled(True)
    self.btnRestoreAll.setEnabled(True)
    self.btnCleanAll.setEnabled(True)
    self.items[p.key] = p
    self.setColour(p)
    self.content.addWidget(p)
    p.show()

  #----------------------------------------------------------------------------------------------------------
  def isPIDManaged(self, pid : str) -> bool:
    for i in self.items.values():
      if i.pid.text() == pid: return True
    return False
  
  #----------------------------------------------------------------------------------------------------------
  def setColour(self,p : aProcessItem):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, self.colour2)
    p.setAutoFillBackground(True)
    p.setPalette(pal)
    tmp = self.colour2
    self.colour2 = self.colour1
    self.colour1 = tmp

  #----------------------------------------------------------------------------------------------------------
  def resetColour(self):
    if len(self.items.keys())==0: return

    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)
    for u in self.items.keys():
      self.setColour(self.items[u])

  #----------------------------------------------------------------------------------------------------------
  def captureOrphan(self):
    from cDDO import cDDO
    from cDungeonHelper import cDungeonHelper
    # output = subprocess.check_output("ps -eo pid,command", shell=True, text=True)
    # output = output.split("\n")
    found = 0
    orphanCandidates = cTop.getByCommand(cDDO.gameExec)
    for c in orphanCandidates:
      cmdline = cTop.getCommand(c)
      cmdline = cmdline.replace("\x00", " ")
      if cDDO.siCMD(cmdline) and not self.isPIDManaged(c):
        orphan : cDDO = cDDO.createFromOrphan(self.main, c, cmdline)
        if orphan:
          found += 1
          cPrint.info(f"cProcessManager: found orphan DDO process: [{orphan.pid.text()}, {orphan.username.text()}, {C_SILVER}{orphan.worldname.text()}</font>]")
          self.addItem(orphan)
          orphan.printInfo = cPrint.info # restores printing ability of orphan
    if found == 0:
      cPrint.info(f"cProcessManager: no orphan DDO processes were found")
    
    orphanCandidates = cTop.getByCommand(cDungeonHelper.dhExec)
    for c in orphanCandidates:
      cmdline = cTop.getCommand(c)
      cmdline = cmdline.replace("\x00", " ").strip()
      if cDungeonHelper.isCMD(cmdline) and not self.isPIDManaged(c):
        self.main.dh.createFromOrphan(c)
        cPrint.info(f"cProcessManager: found orphan DungeonHelper: [{c}]")
        break
      


#----------------------------------------------------------------------------------------------------------
class aProcessItem(QWidget):
  sigRunning = pyqtSignal()
  sigKilled = pyqtSignal()
  sigTerminated = pyqtSignal()
  sigError = pyqtSignal(str)

  sigChangeRequest = pyqtSignal(int)
  sigStatusChanged = pyqtSignal(int)
  sigGotPID = pyqtSignal(str)
  sigGotWinID = pyqtSignal(str)

  P_STATUS_ERROR   = -1
  P_STATUS_UNKNOWN = 0         # status if PID is unknown. Also after terminating
  P_STATUS_RUNNING = 1         # after gotPID returns it will be idle or running
  P_STATUS_KILLED  = 2         # if forcibly terminated i.e. killed
  P_STATUS_TERMINATED = P_STATUS_UNKNOWN
  P_STATUS_REFRESH = -10

  main = None      # set in attachMain
  profile = None   # set in attachMain

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def attachMain(self, main : cMainWindow):
    self.main = main
    self.profile = main.profile # pointer to the function

  #----------------------------------------------------------------------------------------------------------
  def __init__(self):
    super().__init__()
    self.key = ""
    self.status     = self.P_STATUS_UNKNOWN
    self.pid        = newProcessField("", 50)
    self.winID      = newProcessField("")
    self.profileID  = newProcessField("")
    self.worldname  = newProcessField("")
    self.username   = QLabel()
    self.logger     = None

    self.btnToggle  = cOrbSmall(icon=P_ICON_PLAY,  tooltip="Toggles launch/terminate process.<br>Right click or ctrl click to force kill (SIGKILL)")
    self.btnSave    = cOrbSmall(icon=P_ICON_SAVE,  tooltip="Save this windows's position")
    self.btnRestore = cOrbSmall(icon=P_ICON_UNDO,  tooltip="Restore previously saved windows position")
    self.btnClear   = cOrbSmall(icon=P_ICON_TRASH, tooltip="Left click: Removes this process from the list of processes.<br>Right click or ctrl click: force kill and remove")
    self.btnLog     = cOrbSmall(icon=P_ICON_NOTES, tooltip="Toggles follow log")
    self.btnAudio   = cOrbSmall(icon=P_ICON_MUTE,  tooltip="Toggles audio on/off for this process")

    self.btnLog.setCheckable(True)
    self.btnLog.setCheckable(True)
    self.btnToggle.clicked.connect(self.toggle)
    self.btnToggle.rightClicked.connect(lambda : self.toggle(True))
    self.btnToggle.ctrlClicked.connect(lambda : self.toggle(True))
    self.btnSave.clicked.connect(self.saveWindow)
    self.btnRestore.clicked.connect(self.restoreWindow)
    self.btnClear.clicked.connect(self.clear)
    self.btnClear.ctrlClicked.connect(lambda : self.clear(True))
    self.btnClear.rightClicked.connect(lambda : self.clear(True))
    self.btnAudio.clicked.connect(self.audioToggle)
    self.btnLog.clicked.connect(self.logToggle)

    self.sigChangeRequest.connect(self.setStatus)
    self.sigGotPID.connect(self.pid.setText)
    self.sigGotWinID.connect(self.winID.setText)
    
    self.setLayout(newHLayout([self.pid, self.winID, self.worldname, self.profileID, 
                              self.username, self.btnToggle, self.btnSave, self.btnRestore,
                              self.btnClear, self.btnLog, self.btnAudio]))
  
  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def clear(self, kill=False):
    self.main.processManager.clearItem(self, kill)
  
  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def audioToggle(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def audioMute(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def audioUnmute(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def getLogFilename(self) -> str:
    return ""
  
  #----------------------------------------------------------------------------------------------------------
  def logToggle(self):
    if self.logger:
      self.logger.deleteLater()
      self.logger = None
      self.btnLog.setChecked(False)
    else:
      tabName = re.sub(r'<[^>]+>', '', self.username.text())
      tabName = tabName.replace("[E]", "")
      self.logger = cLog(self.getLogFilename(), tabName)
      self.btnLog.setChecked(True)

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, newStatus):
    self.btnAudio.setEnabled(   self.pid.text().isdigit())
    self.btnSave.setEnabled(   self.winID.text().isdigit())
    self.btnRestore.setEnabled(self.winID.text().isdigit())
    self.btnLog.setEnabled(    self.winID.text().isdigit())
    self.btnClear.setEnabled(not self.winID.text().isdigit())
    if self.status != newStatus:
      if newStatus == "error" or newStatus == aProcessItem.P_STATUS_ERROR:
        self.username.setText(f"{C_RED}{self.username.text()}[E]</font>")
        self.btnToggle.setEnabled(False)
        self.btnToggle.setChecked(False)
        self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = aProcessItem.P_STATUS_ERROR 
        self.sigError.emit("APROCESS_UNKNOWN_ERROR")
      elif newStatus == "terminated" or newStatus == aProcessItem.P_STATUS_TERMINATED:
        self.pid.setText("")
        self.winID.setText("")
        self.btnToggle.setEnabled(True)
        self.btnToggle.setChecked(False)
        self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = aProcessItem.P_STATUS_UNKNOWN
        self.sigTerminated.emit()
      elif newStatus == "running" or newStatus == aProcessItem.P_STATUS_RUNNING:
        self.btnToggle.setEnabled(True)
        self.btnToggle.setChecked(True)
        self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = aProcessItem.P_STATUS_RUNNING
        self.sigRunning.emit()
      elif newStatus == "killed" or newStatus == aProcessItem.P_STATUS_KILLED:
        self.pid.setText("")
        self.winID.setText("")
        self.btnToggle.setEnabled(True)
        self.btnToggle.setChecked(False)
        self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = aProcessItem.P_STATUS_UNKNOWN
        self.sigKilled.emit()
      self.sigStatusChanged.emit(self.status)

  # #----------------------------------------------------------------------------------------------------------
  # def clean(self):
  #   # this should be called when the job has already died (i.e. user closed the window)
  #   self.pid.setText("")
  #   self.winID.setText("")
  #   self.btnSave.setEnabled(False)
  #   self.btnRestore.setEnabled(False)
  #   self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
  #   self.status = self.P_STATUS_UNKNOWN

  #----------------------------------------------------------------------------------------------------------
  def kill(self):
    self._terminate(signal.SIGKILL)

  #----------------------------------------------------------------------------------------------------------
  def terminate(self):
    self._terminate(signal.SIGTERM)

  #----------------------------------------------------------------------------------------------------------
  def _terminate(self, sig : signal):
    if not self.pid.text().isdigit():
      cPrint.error(f"aProcessItem.terminate:Error terminating {C_SILVER}{self.username.text()}</font>, PID={C_SILVER}{self.pid.text()}</font> is invalid!")
      self.setStatus(self.P_STATUS_ERROR)
      return
    
    if self.worldname.text():
      cPrint.info(f"Killing {C_SILVER}{self.username.text()}</font> in {C_SILVER}{self.worldname.text()}</font>...")
    else:
      cPrint.info(f"Killing {C_SILVER}{self.username.text()}</font>, PID={C_SILVER}{self.pid.text()}</font>...")

    try:
      if sig == signal.SIGKILL:
        cTop.kill(int(self.pid.text()))
        self.setStatus(self.P_STATUS_KILLED)
      else:
        cTop.terminate(int(self.pid.text()))
        self.setStatus(self.P_STATUS_TERMINATED)
    except Exception as e:
      cPrint.error(f"aProcessItem.terminate: unknown error terminating (signal: {sig}) process with PID {self.pid.text()}", e)
      self.setStatus(self.P_STATUS_ERROR)
 
  #----------------------------------------------------------------------------------------------------------
  def toggle(self, kill=False):
    if self.status == self.P_STATUS_RUNNING:
      if kill: self.kill()
      else:    self.terminate()
    else:
      self.launch()

