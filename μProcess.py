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
from widgets.μOrb import μBoxCheck
from widgets.μFloating import μToggler
from widgets.μOrb import μOrbCheck, μOrbSmall
from helpers.μImageFactory import *
from widgets.μLog import μLog
from helpers.χTop import χTop
from helpers.χHelper import χHelper
from helpers.μPrint import χPrint
from collections import OrderedDict
import re
import signal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
# 
#   ❖  P R O C E S S   M A N A G E R
#                                  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μProcessManager(μToggler):
  main = None      # set in attachMain
  widgetID = "ProcessManager"

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def attachMain(cls, main : μMainWindow):
    cls.main = main
    αProcessItem.attachMain(main)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self):
    super().__init__("Process\nManager", P_ICON_PROPERTIES)
    self.toggler.setToolTip("Toggle Process Manager and allows control of individual launched processes")
    self.items : OrderedDict[str, αProcessItem] = OrderedDict()
    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)

    header = QWidget()
    header.setLayout(newHLayout([newHeaderLabel("", 64), newHeaderLabel("PID", 50), newHeaderLabel("WinID"),\
                     newHeaderLabel("World"), newHeaderLabel("Profile"), "Username"]))

    self.btnStartAll   = μOrbSmall(icon=P_ICON_PLAY,    tooltip="Starts all processes which are not yet already running")
    self.btnKillAll    = μOrbSmall(icon=P_ICON_SKULL,   tooltip="Terminates selected running processes<br><b><i>Ctrl+Click</i></b>: force termination (SIGKILL) selected processes")
    self.btnSaveAll    = μOrbSmall(icon=P_ICON_SAVEALL, tooltip="Saves selected windows positions")
    self.btnRestoreAll = μOrbSmall(icon=P_ICON_UNDO,    tooltip="Reloads previously saved positions for selected windows")
    self.btnCleanAll   = μOrbSmall(icon=P_ICON_CLEAR,   tooltip="Clear all processes<br><b><i>Ctrl+Click</i></b>: kill and clear all processes")
    self.btnAudioAll   = μOrbSmall(icon=P_ICON_MUTE,    tooltip="Toggles audio on/off for all processes. <br><b><i>Ctrl+Click</i></b>: mute all processes")
    self.btnLogAll     = μOrbSmall(icon=P_ICON_NOTES,   tooltip="Toggles logs on/off for all processes")
    self.btnFixBlackScreen = μOrbSmall(icon=P_ICON_BLACKSCREEN, tooltip="Attempt to solve the blackscreen bug in all running instances.")
    self.btnCaptureOrphans = μOrbSmall(icon=getIcon(P_MUDDO_DIR+'/images/custom-icons/link.png'), tooltip="Attempts to find running instances of DDO and capture them"\
                                     " into our own process manager.\n<b><i>WARNING</i></b>: this will not try to guess which"\
                                     " profile (if any) was used to launch the original DDO instance!")
    self.btnSelectAll  = μBoxCheck(tooltip="Select/deselect all processes for batch Save/Kill/Reload")
    self.btnSelectAll.setChecked(True)
    
    self.btnCaptureOrphans.clicked.connect(self.captureOrphan)
    self.btnSelectAll.clicked.connect(self.applySelectAll)
    self.btnStartAll.clicked.connect(self.startAll)
    self.btnKillAll.clicked.connect(self.terminateAll)
    self.btnKillAll.ctrlClicked.connect(lambda : self.killAll())
    self.btnSaveAll.clicked.connect(self.saveWindowAll)
    self.btnRestoreAll.clicked.connect(self.restoreWindowAll)
    self.btnCleanAll.clicked.connect(self.cleanAll)
    self.btnCleanAll.ctrlClicked.connect(lambda : self.cleanAll(True))
    self.btnAudioAll.clicked.connect(self.toggleAudioAll)
    self.btnAudioAll.ctrlClicked.connect(self.audioMuteAll)
    self.btnFixBlackScreen.clicked.connect(self.fixBlackScreenAll)

    justSpace = QLabel(" ")
    justSpace.setMinimumWidth(2)
    
    self.content = newVLayout([header])
    self.setLayout(newVLayout([self.content, newHLayout([self.btnSelectAll, self.btnFixBlackScreen, self.btnCaptureOrphans,"__stretch__", "All processes: ", self.btnStartAll,\
      self.btnKillAll, self.btnSaveAll, self.btnRestoreAll, self.btnCleanAll, self.btnLogAll, self.btnAudioAll, justSpace]),
                    "__stretch__"]))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def show(self):
    for i in self.items.values():
      if i.isAlive(): i.setStatus(αProcessItem.P_STATUS_RUNNING)
      else: i.setStatus(αProcessItem.P_STATUS_TERMINATED)
    super().show()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clearItem(self, item : αProcessItem, kill=False):
    if kill and item.status == item.P_STATUS_RUNNING:
      try:
        item.terminate()
      except Exception as e:
        χPrint.error(f"[μProcessManager] cleanItem: error killing \"{item.widgetID}\"", e)
    elif item.status == item.P_STATUS_RUNNING:
      return
    
    try:
      self.layout().removeWidget(item)
      del self.items[item.widgetID]
    except Exception as e:
      χPrint.error(f"[μProcessManager] cleanItem: unknown error removing item \"{item.widgetID}\"", e)

    item.hide()
    self.main.processManager.resetColour()
    # item.deleteLater()


  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def cleanAll(self, kill=False):
    allItems  = set(self.items.values())
    for i in allItems: 
      self.clearItem(i,kill)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def startAll(self):
    for u in self.items.keys(): 
      if u.startswith("dh_"): continue
      if self.items[u].status != αProcessItem.P_STATUS_RUNNING:
        self.items[u].launch()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def selectedItems(self):
    return [p for k, p in self.items.items() if not k.startswith("dh_") and p.btnSelect.isChecked()]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def applySelectAll(self):
    state = self.btnSelectAll.isChecked()
    for k, p in self.items.items():
      if k.startswith("dh_"): continue
      p.btnSelect.setChecked(state)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def terminateAll(self):
    for p in self.selectedItems():
      p.terminate()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def killAll(self):
    for p in self.selectedItems():
      p.kill()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def toggleAudioAll(self):
    allItems = list(self.items.keys())
    for i in allItems:
      self.items[i].audioToggle()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioMuteAll(self):
    allItems = list(self.items.keys())
    for i in allItems:
      self.items[i].audioMute()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveWindowAll(self):
    for p in self.selectedItems(): p.saveWindow()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def restoreWindowAll(self):
    for p in self.selectedItems(): p.restoreWindow()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def fixBlackScreenAll(self):
    for p in self.selectedItems():
      winID = p.winID.text()
      if winID.isdigit():
        χHelper.remapWindow(int(winID))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def itemExists(self, p : αProcessItem):
    for key, proc in self.items.items():
      if key == p.widgetID: return True
      if proc == p: return True
    return False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addItem(self, p : αProcessItem):
    if self.itemExists(p): return
    self.btnKillAll.setEnabled(True)
    self.btnSaveAll.setEnabled(True)
    self.btnRestoreAll.setEnabled(True)
    self.btnCleanAll.setEnabled(True)
    self.items[p.widgetID] = p
    self.setColour(p)
    self.content.addWidget(p)
    p.show()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def isPIDManaged(self, pid) -> bool:
    for i in self.items.values():
      if i.pid.text() == str(pid): return True
    return False
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setColour(self,p : αProcessItem):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, self.colour2)
    p.setAutoFillBackground(True)
    p.setPalette(pal)
    tmp = self.colour2
    self.colour2 = self.colour1
    self.colour1 = tmp

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def resetColour(self):
    if len(self.items.keys())==0: return

    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)
    for u in self.items.keys():
      self.setColour(self.items[u])

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def captureOrphan(self):
    from μDDO import μDDO
    from μDungeonHelper import μDungeonHelper
    # output = subprocess.check_output("ps -eo pid,command", shell=True, text=True)
    # output = output.split("\n")
    found = 0
    orphanCandidates = χTop.getByCommand(μDDO.gameExec)
    for c in orphanCandidates:
      cmdline = χTop.getCommand(c)
      cmdline = cmdline.replace("\x00", " ")
      if μDDO.isCMD(cmdline) and not self.isPIDManaged(c):
        orphan : μDDO = μDDO.createFromOrphan(self.main, c, cmdline)
        if orphan:
          found += 1
          χPrint.info(f"[μProcessManager] found orphan DDO process: [{orphan.pid.text()}, {orphan.username.text()}, {C_SILVER}{orphan.worldname.text()}</font>]")
          self.addItem(orphan)
          orphan.printInfo = χPrint.info # restores printing ability of orphan
    if found == 0:
      χPrint.info(f"[μProcessManager] no orphan DDO processes were found")
    
    orphanCandidates = χTop.getByCommand(μDungeonHelper.dhExec)
    for c in orphanCandidates:
      cmdline = χTop.getCommand(c)
      cmdline = cmdline.replace("\x00", " ").strip()
      if μDungeonHelper.isCMD(cmdline) and not self.isPIDManaged(c):
        self.main.dh.createFromOrphan(c)
        χPrint.info(f"[μProcessManager] found orphan DungeonHelper: [{c}]")
        break
      


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  P R O C E S S   I T E M
#
#       Abstract class
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class αProcessItem(QWidget):
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

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def attachMain(cls, main : μMainWindow):
    cls.main = main

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self):
    super().__init__()
    self.widgetID = ""
    self.status     = self.P_STATUS_UNKNOWN
    self.pid        = newProcessField("", 50)
    self.winID      = newProcessField("")
    self.profileID  = newProcessField("")
    self.worldname  = newProcessField("")
    self.username   = QLabel()
    self.logger     = None

    self.btnSelect  = μBoxCheck(tooltip="Include this process in batch Save/Kill/Reload actions")
    self.btnToggle  = μOrbSmall(icon=P_ICON_PLAY,  tooltip="Toggles launch/terminate process.<br><b><i>Ctrl+Click</i></b>: to force kill (SIGKILL)")
    self.btnSave    = μOrbSmall(icon=P_ICON_SAVE,  tooltip="Save this windows's position")
    self.btnRestore = μOrbSmall(icon=P_ICON_UNDO,  tooltip="Restore previously saved windows position")
    self.btnClear   = μOrbSmall(icon=P_ICON_TRASH, tooltip="Left click: Removes this process from the list of processes.<br><b><i>Ctrl+Click</i></b>: force kill and remove")
    self.btnLog     = μOrbSmall(icon=P_ICON_NOTES, tooltip="Toggles follow log")
    self.btnAudio   = μOrbSmall(icon=P_ICON_MUTE,  tooltip="Toggles audio on/off for this process.<br><b><i>Ctrl+Click</i></b>: mute all processes")

    self.btnSelect.setChecked(True)
    self.btnLog.setCheckable(True)
    self.btnToggle.clicked.connect(self.toggle)
    self.btnToggle.ctrlClicked.connect(lambda : self.toggle(True))
    self.btnSave.clicked.connect(self.saveWindow)
    self.btnRestore.clicked.connect(self.restoreWindow)
    self.btnClear.clicked.connect(self.clear)
    self.btnClear.ctrlClicked.connect(lambda : self.clear(True))
    self.btnAudio.clicked.connect(self.audioToggle)
    self.btnAudio.ctrlClicked.connect(self.audioMute)
    self.btnLog.clicked.connect(self.logToggle)

    self.sigChangeRequest.connect(self.setStatus)
    self.sigGotPID.connect(self.pid.setText)
    self.sigGotWinID.connect(self.winID.setText)
    
    self.setLayout(newHLayout([self.btnSelect, self.pid, self.winID, self.worldname, self.profileID,
                              self.username, self.btnToggle, self.btnSave, self.btnRestore,
                              self.btnClear, self.btnLog, self.btnAudio]))
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def isAlive(self) -> bool:
    if not self.pid.text().isdigit(): return False
    return χTop.isAlive(int(self.pid.text()))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def launch(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clear(self, kill=False):
    self.main.processManager.clearItem(self, kill)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveWindow(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def restoreWindow(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioToggle(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioMute(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioUnmute(self):
    pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getLogFilename(self) -> str:
    return ""
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def logShow(self):
    if self.logger: return
    tabName = re.sub(r'<[^>]+>', '', self.username.text())
    tabName = tabName.replace("[E]", "")
    self.logger = μLog(self.getLogFilename(), tabName)
    self.btnLog.setChecked(True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def logHide(self):
    if not self.logger: return
    self.logger.deleteLater()
    self.logger = None
    self.btnLog.setChecked(False)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def logToggle(self):
    if self.logger: self.logHide()
    else:           self.logShow()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setStatus(self, newStatus):
    self.btnAudio.setEnabled(   self.pid.text().isdigit())
    self.btnSave.setEnabled(   self.winID.text().isdigit())
    self.btnRestore.setEnabled(self.winID.text().isdigit())
    self.btnLog.setEnabled(    self.winID.text().isdigit())
    self.btnClear.setEnabled(not self.winID.text().isdigit())
    if self.status != newStatus:
      if newStatus == "error" or newStatus == αProcessItem.P_STATUS_ERROR:
        self.username.setText(f"{C_RED}{self.username.text()}[E]</font>")
        self.btnToggle.setEnabled(False)
        self.btnToggle.setChecked(False)
        self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = αProcessItem.P_STATUS_ERROR 
        self.sigError.emit("APROCESS_UNKNOWN_ERROR")
      elif newStatus == "terminated" or newStatus == αProcessItem.P_STATUS_TERMINATED:
        if self.winID.text().isdigit():
          χHelper.unregisterWindow(int(self.winID.text()))
        self.pid.setText("")
        self.winID.setText("")
        self.btnToggle.setEnabled(True)
        self.btnToggle.setChecked(False)
        self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = αProcessItem.P_STATUS_UNKNOWN
        self.sigTerminated.emit()
      elif newStatus == "running" or newStatus == αProcessItem.P_STATUS_RUNNING:
        self.btnToggle.setEnabled(True)
        self.btnToggle.setChecked(True)
        self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = αProcessItem.P_STATUS_RUNNING
        self.sigRunning.emit()
      elif newStatus == "killed" or newStatus == αProcessItem.P_STATUS_KILLED:
        if self.winID.text().isdigit():
          χHelper.unregisterWindow(int(self.winID.text()))
        self.pid.setText("")
        self.winID.setText("")
        self.btnToggle.setEnabled(True)
        self.btnToggle.setChecked(False)
        self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
        self.btnClear.setEnabled(True)
        self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
        self.status = αProcessItem.P_STATUS_UNKNOWN
        self.sigKilled.emit()
      self.sigStatusChanged.emit(self.status)

  # # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # def clean(self):
  #   # this should be called when the job has already died (i.e. user closed the window)
  #   self.pid.setText("")
  #   self.winID.setText("")
  #   self.btnSave.setEnabled(False)
  #   self.btnRestore.setEnabled(False)
  #   self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
  #   self.status = self.P_STATUS_UNKNOWN

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def kill(self):
    self._terminate(signal.SIGKILL)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def terminate(self):
    self._terminate(signal.SIGTERM)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _terminate(self, sig : signal):
    if not self.pid.text().isdigit():
      χPrint.error(f"[aProcessItem] error terminating {C_SILVER}{self.username.text()}</font>, PID={C_SILVER}{self.pid.text()}</font> is invalid!")
      self.setStatus(self.P_STATUS_ERROR)
      return
    
    if self.worldname.text():
      χPrint.info(f"[aProcessItem] killing {C_SILVER}{self.username.text()}</font> in {C_SILVER}{self.worldname.text()}</font>...")
    else:
      χPrint.info(f"[aProcessItem] killing {C_SILVER}{self.username.text()}</font>, PID={C_SILVER}{self.pid.text()}</font>...")

    try:
      if sig == signal.SIGKILL:
        χTop.kill(int(self.pid.text()))
        self.setStatus(self.P_STATUS_KILLED)
      else:
        χTop.terminate(int(self.pid.text()))
        self.setStatus(self.P_STATUS_TERMINATED)
    except Exception as e:
      χPrint.error(f"[aProcessItem] unknown error terminating (signal: {sig}) process with PID {self.pid.text()}", e)
      self.setStatus(self.P_STATUS_ERROR)
 
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def toggle(self, kill=False):
    if self.status == self.P_STATUS_RUNNING:
      if kill: self.kill()
      else: self.terminate()
    else:
      self.launch()

