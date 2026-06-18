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
from μProcess import aProcessItem
from μSettings import μSettings
from helpers.χHelper import χHelper
from helpers.χTop import χTop
import subprocess
import os, time, threading
from widgets.μOrb import μOrb
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow
import glob

#----------------------------------------------------------------------------------------------------------
class μDungeonHelper(aProcessItem):
  dhExec = "DungeonHelper.exe"
  widgetID = "dh"

  def __init__(self, main : μMainWindow):
    super().__init__()
    self.profileID.setText("")
    self.worldname.setText("")
    self.username.setText("Dungeon Helper")
    self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnClear.setEnabled(False)
    self.orb = μOrb("Dungeon\nHelper", getIcon('dm_kundarak'),
                    tooltip="Launches Dungeon Helper (it if is installed); activates on all instances" \
                     " of the game for as long as it runs.<br><b>Ctrl+Click to purge any instances and restart Dungeon Helper.<br><b><i>Right-click for more options</i></b>")
    self.orb.setCheckable(True)
    self.actionToggle       = self.orb.menu.addAction("Launch DungeonHelper")
    self.actionRestart      = self.orb.menu.addAction("Restart DungeonHelper")
    self.actionKill         = self.orb.menu.addAction("Kill DungeonHelper")
    self.actionToggleUI     = self.orb.menu.addAction("Show/Hide UI")
    self.actionToggleOv     = self.orb.menu.addAction("Show/Hide Overlay")
    self.actionToggleUIov   = self.orb.menu.addAction("Show/Hide UI + Overlay")

    self.orb.clicked.connect(self.toggle)
    self.orb.ctrlClicked.connect( lambda : self.restart(purge=True))
    self.actionToggle.triggered.connect(self.toggle)
    self.actionRestart.triggered.connect(self.restart)
    self.actionKill.triggered.connect(self.kill)
    self.actionToggleUI.triggered.connect(lambda: self.toggleUI())
    self.actionToggleOv.triggered.connect(lambda: self.toggleOverlay())
    self.actionToggleUIov.triggered.connect(lambda: self.toggleUIOverlay())

    self.sigRunning.connect(self.watchPID)
    self.sigGotPID.connect(self.watchWinID)
    self.sigGotWinID.connect(lambda : self.setStatus(self.status))
    # self.sigGotWinID.connect(lambda x: self.restoreWindow(x!=None))
    # self.sigGotWinID.connect(lambda x: self.btnSave.setEnabled(x!=None))
    # self.sigGotWinID.connect(lambda x: self.btnRestore.setEnabled(x!=None))

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    μSettings.plugins._useDH.stateChanged.connect(lambda x: self.setEnabled(x))

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    # if not self.main.profile().useDungeonHelper.isChecked(): return
    if self.status == self.P_STATUS_RUNNING:
      μPrint.warning(" Attempting to launch Dungeon Helper, but it is already running."+
                        " Try right-click->kill to cleanup state.")
      return
    self.pid.setText("")
    μPrint.info(f"Starting {C_SILVER}DungeonHelper.exe</font>...")
    self.show()
    t = threading.Thread(target=self._launchThread, daemon=True)
    t.start()
    
  #----------------------------------------------------------------------------------------------------------
  def _launchThread(self):
    
    cmd = f'{μSettings.launcher.command()} "{μSettings.plugins.dhExec()}"'

    logFile = open(self.getLogFilename(), "w")
    proc = subprocess.Popen(
        cmd,
        shell=True,                     # Needed for env var prefix + cd + &&
        stdout=logFile,
        stderr=subprocess.STDOUT,       # Merge stderr → stdout → log
        start_new_session=True,         # New session → survives Python exit
        close_fds=True,
        env=os.environ.copy(),          # Inherit + your vars are in cmd
    )

    if proc:
      self.sigChangeRequest.emit(self.P_STATUS_RUNNING)
      exitCode = proc.wait()
    else:
      μPrint.info("cDungeonHelper.launchThread: error launching, check logs for details!")
      exitCode = 1

    # this locks until the DH process ends, and it is intentional!
    # If it does end, then it was closed by the user (or some error...)
    logFile.close()
    if exitCode==137:
      self.sigChangeRequest.emit(self.P_STATUS_KILLED)
    elif exitCode in (1,2,126,127):
      self.sigChangeRequest.emit(self.P_STATUS_ERROR)
    else:
      self.sigChangeRequest.emit(self.P_STATUS_TERMINATED)

  #----------------------------------------------------------------------------------------------------------
  def watchPID(self):
    def _watchPIDThread(self, baseExec):
      startTime = time.time()
      while True:
        candidates = χTop.getByCommand(baseExec)
        for c in candidates:
          if χTop.getCommand(c).startswith('C:\\'):
            self.sigGotPID.emit(str(c))
            self.sigChangeRequest.emit(self.status) # just to refresh
            return c
        if (time.time() - startTime) > 15.0:
          μPrint.error(f"cDungeonHelper.watchPID: timeout error while looking for PID")
          return None
        time.sleep(0.1)
    baseExec = os.path.basename(μSettings.plugins.dhExec())
    t = threading.Thread(target=_watchPIDThread, args=(self,baseExec), daemon=True)
    t.start()

  #----------------------------------------------------------------------------------------------------------
  def watchWinID(self):
    def _watchWinIDThread(self):
      xh = χHelper()
      startTime = time.time()
      while True:
        candidates = xh.getWinID(self.pid.text())
        if candidates:
          self.sigGotWinID.emit(str(candidates[0]))
          self.sigChangeRequest.emit(self.status) # just to refresh
          return candidates[0]
        if (time.time() - startTime) > 15.0:
          μPrint.error(f"cDungeonHelper.watchWinID: timeout error while looking for WinID")
          return None
        time.sleep(0.1)

    t = threading.Thread(target=_watchWinIDThread, args=(self,), daemon=True)
    t.start()

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, newStatus):
    if newStatus != self.P_STATUS_RUNNING:
        self.pid.setText("")
    super().setStatus(newStatus)
    self.btnAudio.setEnabled(False)
    self.updateTooltip()

  #----------------------------------------------------------------------------------------------------------
  def getLogFilename(self):
    return f"{P_DEFAULT_LOGSDIR}/dhelper.txt"

  #----------------------------------------------------------------------------------------------------------
  def terminate(self):
    super().terminate()
    baseExec = os.path.basename(μSettings.plugins.dhExec())
    χTop.terminateAll(baseExec)
    self.clear()
  
  #----------------------------------------------------------------------------------------------------------
  def toggleUI(self, val=None):
    winIDs = χHelper.getWinIDByName("dungeon helper")
    for w in winIDs: χHelper.iconify(w, val)
    winIDs = χHelper.getWinIDByName("wine system tray")
    for w in winIDs: χHelper.iconify(w, val)

  #----------------------------------------------------------------------------------------------------------
  def toggleOverlay(self, val=None):
    winIDs = χHelper.getWinIDByName("dungeon helper overlay")
    for w in winIDs: χHelper.iconify(w, val)

  #----------------------------------------------------------------------------------------------------------
  def toggleUIOverlay(self, val=None):
    winIDs = χHelper.getWinIDByName("dungeon helper*")
    for w in winIDs: χHelper.iconify(w, val)
    winIDs = χHelper.getWinIDByName("wine system tray")
    for w in winIDs: χHelper.iconify(w, val)
  
  #----------------------------------------------------------------------------------------------------------
  def clear(self, kill=False):
    self.profileID.setText("")
    self.worldname.setText("")
    self.username.setText("Dungeon Helper")
    self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnClear.setEnabled(False)
    self.hide()

  #----------------------------------------------------------------------------------------------------------
  def kill(self):
    super().kill()
    baseExec = os.path.basename(μSettings.plugins.dhExec())
    μPrint.warning(f"Killing all processes containing {baseExec}...")
    χTop.killAll(baseExec)
    self.clear()

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, status):
    super().setStatus(status)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnAudio.setEnabled(False)
    if status == aProcessItem.P_STATUS_RUNNING:
      self.orb.setChecked(True)
      self.main.processManager.addItem(self)
      # self.actionToggle.setText("Stop")
    else:
      self.orb.setChecked(False)
      # self.actionToggle.setText("Launch")

  #----------------------------------------------------------------------------------------------------------
  def restart(self, force=False):
    if force:
      self.kill()
    else:
      self.terminate()
    self.launch()

  #----------------------------------------------------------------------------------------------------------
  def updateTooltip(self):
    if self.pid.text().isdecimal():
      text = "<b>Running</b>"
    else:
      text = "<i>Not running</i>"
    self.setToolTip(text)

  #----------------------------------------------------------------------------------------------------------
  def createFromOrphan(self, pid : int):
    self.sigGotPID.emit(str(pid))
    self.sigChangeRequest.emit(self.P_STATUS_RUNNING)
    self.show()
    return True

  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def isCMD(line) -> bool:
    return line.startswith('C:\\users\\') and line.endswith(μDungeonHelper.dhExec)
  