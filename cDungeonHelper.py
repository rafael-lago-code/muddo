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
from PyQt6.QtCore import QRunnable
from cProcess import aProcessItem
import subprocess
import os, time
from cWidgets.cOrb import cOrb
from cWidgets.util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

#----------------------------------------------------------------------------------------------------------
class cDungeonHelper(aProcessItem):
  def __init__(self, main : cMainWindow):
    super().__init__()
    self.key = "dh"    
    self.profileID.setText("")
    self.worldname.setText("")
    self.username.setText("Dungeon Helper")
    self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnClear.setEnabled(False)

    self.orb = cOrb("Dungeon\nHelper", getIcon(P_MUDDO_DIR+'/images/DungeonHelperIcon32.png'),
                    tooltip="Launches Dungeon Helper (it if is installed); activates on all instances" \
                     " of the game for as long as it runs.<br><b><i>Right-click for more options</i></b>")
    self.orb.setCheckable(True)
    self.actionToggle  = self.orb.menu.addAction("Launch DungeonHelper")
    self.actionRestart = self.orb.menu.addAction("Restart DungeonHelper")
    self.actionKill    = self.orb.menu.addAction("Kill DungeonHelper")
    self.actionConf    = self.orb.menu.addAction("Show/Hide setting UI")

    self.orb.clicked.connect(self.toggle)
    self.orb.ctrlClicked.connect( lambda : self.restart(purge=True))
    self.actionToggle.triggered.connect(self.toggle)
    self.actionRestart.triggered.connect(self.restart)
    self.actionKill.triggered.connect(lambda : self.terminate(force=True))
    self.actionConf.triggered.connect(lambda : main.settings.toggle())

    self.sigGotPID.connect(self.updateTooltip)    
  
  #----------------------------------------------------------------------------------------------------------
  # def launchDH(self):
  #   if not self.DHProcess:
  #     self.DHProcess = cDungeonHelper(self)
  #     self.processManager.addItem(self.DHProcess)
  #   self.processManager.setVisible(True)
  #   self.DHProcess.launch()

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.main.profile().useDungeonHelper.stateChanged.connect(lambda x: self.setEnabled(self.main.profile().useDungeonHelper.isChecked()))

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    if not self.main.profile().useDungeonHelper.isChecked(): return
    if self.status != self.P_STATUS_RUNNING:
      self.console.info(f"Launching DungeonHelper.exe...")

      dhexec = self.main.profile().DungeonHelperExec.text()
      cmd  = f"STEAM_ROOT=\"{self.main.profile().steamRoot.text()}\" PROTON_LOG=1 "
      cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.profile().compatData.text()}\" "
      cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.profile().compatData.text()}\" "
      cmd += f"\"{self.profile().protonExec.text()}\" run "
      cmd += f"\"{pathLinux2Windows(dhexec)}\""

      exec = tDungeonHelperExecutable(self, cmd)
      QtCore.QThreadPool.globalInstance().start(exec)
      self.profileID.setText(self.main.profile().name)
      self.pid.setText("L")
      pidw = tDHPIDWatcher(self, dhexec)
      QtCore.QThreadPool.globalInstance().start(pidw)

      if not self.main.processManager.itemExists(self):
        self.main.processManager.addItem(self)
      self.setStatus(self.P_STATUS_RUNNING)
    else:
      self.main.console.warning(" Attempting to launch Dungeon Helper it is already running."+
                                " Try right-click->kill to cleanup state.")

  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.status == self.P_STATUS_RUNNING:
      self.terminate()
    else:
      self.launch()

  #----------------------------------------------------------------------------------------------------------
  def terminate(self, force=False):
    super().terminate(force)
    self.setStatus(self.P_STATUS_KILLED)
    self.clear()

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, status):
    super().setStatus(status)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnMute.setEnabled(False)
    if status == aProcessItem.P_STATUS_RUNNING:
      self.orb.setChecked(True)
      # self.actionToggle.setText("Stop")
    else:
      self.orb.setChecked(False)
      # self.actionToggle.setText("Launch")

  #----------------------------------------------------------------------------------------------------------
  def restart(self, force=False):
    self.terminate(force)
    self.launch()

  #----------------------------------------------------------------------------------------------------------
  def updateTooltip(self):
    if self.pid.text().isdecimal():
      text = "<b>Running</b>"
    else:
      text = "<i>Not running</i>"
    self.setToolTip(text)
  
#----------------------------------------------------------------------------------------------------------
class tDungeonHelperExecutable(QRunnable):
  def __init__(self,dh : cDungeonHelper, exec):
    super().__init__()
    self.dh = dh
    self.exec = exec
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    os.system(self.exec)
    if self.dh.status == self.dh.P_STATUS_RUNNING:
      self.dh.sigTerminated.emit(True)


#----------------------------------------------------------------------------------------------------------
class tDHPIDWatcher(QRunnable):
  def __init__(self, dhWidget : cDungeonHelper, exec : str):
    super().__init__()
    self.dh = dhWidget
    self.exec = exec

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    baseExec = os.path.basename(self.exec)
    for i in range(100):
      try:
        out = subprocess.check_output([f"ps x | grep {baseExec}"], shell=True)
        for line in out.decode().strip().split('\n'):
          line = line.split()
          if line[4].startswith("C:\\"):
            self.dh.pid.setText(line[0])
            self.dh.status = self.dh.P_STATUS_RUNNING
            self.dh.sigGotPID.emit(True)
            return True
      except: pass
      time.sleep(0.1)
    self.dh.console.error("tDHPIDWatcher: could not get PID, process may not be running anymore...")
    self.dh.sigGotPID.emit(False)
    return False
  