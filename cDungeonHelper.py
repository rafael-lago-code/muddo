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
from cWidgets.util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

#----------------------------------------------------------------------------------------------------------
class cDungeonHelper(aProcessItem):
  def __init__(self, main : cMainWindow):
    super().__init__(main)
    self.key = "dh_"+self.profile.name
    
    self.profileID.setText(self.profile.name)
    self.worldname.setText("")
    self.username.setText("Dungeon Helper")
    self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnRemove.setEnabled(True)

    self.sigGotPID.connect(self.updateTooltip)

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    if not self.profile.useDungeonHelper.isChecked(): return
    if self.status != self.P_STATUS_RUNNING:
      self.console.info(f"Launching DungeonHelper.exe...")
      self.status = self.P_STATUS_RUNNING

      dhexec = self.profile.DungeonHelperExec.text()
      cmd  = f"STEAM_ROOT=\"{self.profile.steamRoot.text()}\" PROTON_LOG=1 "
      cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.profile.compatData.text()}\" "
      cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.profile.compatData.text()}\" "
      cmd += f"\"{self.profile.protonExec.text()}\" run "
      cmd += f"\"{pathLinux2Windows(dhexec)}\""

      exec = tDungeonHelperExecutable(self, cmd)
      QtCore.QThreadPool.globalInstance().start(exec)
      self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
      self.status = self.P_STATUS_RUNNING
      self.pid.setText("L")
      pidw = tDHPIDWatcher(self, dhexec)
      QtCore.QThreadPool.globalInstance().start(pidw)

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
  