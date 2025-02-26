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
#    This software is heavily based on PyLotRO (credits to AJackson
#    <ajackson@bcs.org.uk>), which in turn is based on a lotrolauncher 
#    script by SNy (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QRunnable, pyqtSignal, Qt
from util import *
import os
import subprocess
import time
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cDungeonHelper(QWidget):
    sigGotPID = pyqtSignal(bool)
    P_STATUS_UNKNOWN = 0
    P_STATUS_LAUNCHING = 1
    P_STATUS_RUNNING = 2

    def __init__(self, main : cMainWindow):
      super().__init__()
      self.main = main
      self.console = main.console
      self.profile = main.profile()  # we should freeze the profile here, but this class needs some reworking...
      self.btnLaunch  = newToolbarButton(P_ICON_PLAY,  "Start DungeonHelper", self.launch)
      self.btnKill  = newToolbarButton(P_ICON_SKULL,  "Stop DungeonHelper", self.kill)
      self.statusLbl = QLabel()
      self.pid = ""
      self.status = self.P_STATUS_UNKNOWN

      self.btnLaunch.setEnabled(True)
      self.btnLaunch.setIconSize(P_DEFAULT_ICON_SIZE)
      self.btnKill.setEnabled(True)
      self.btnKill.setIconSize(P_DEFAULT_ICON_SIZE)

      pmap = QPixmap(os.path.dirname(os.path.abspath(__file__))+'/images/DungeonHelperIcon.png')
      self.icon = QLabel()
      self.icon.setPixmap(pmap.scaled(P_DEFAULT_ICON_SIZE))
      self.iconLabel = newRQLabel('Dungeon Helper: ')
    
    #----------------------------------------------------------------------------------------------------------
    def initialize(self):
      self.main.sigProfileChanged.connect(lambda : self.setVisible(self.main.profile().useDungeonHelper.isChecked()))

    #----------------------------------------------------------------------------------------------------------
    def setVisible(self, val : bool):
      self.icon.setVisible(val)
      self.iconLabel.setVisible(val)
      self.btnLaunch.setVisible(val)
      self.btnKill.setVisible(val)
      self.statusLbl.setVisible(val)
    
    #----------------------------------------------------------------------------------------------------------
    def getWidgets(self):
      return [self.icon, self.iconLabel, self.btnLaunch, self.btnKill, self.statusLbl]

    #----------------------------------------------------------------------------------------------------------
    def launch(self):
      self.profile = self.main.profile()
      if self.status != self.P_STATUS_RUNNING:
        self.console.info(f"Launching DungeonHelper.exe...")
        self.status = self.P_STATUS_LAUNCHING

        dhexec = self.profile.DungeonHelperExec.text()
        cmd  = f"STEAM_ROOT=\"{self.profile.steamRoot.text()}\" PROTON_LOG=1 "
        cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.profile.compatData.text()}\" "
        cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.profile.compatData.text()}\" "
        cmd += f"\"{self.profile.protonExec.text()}\" run "
        cmd += f"\"{pathLinux2Windows(dhexec)}\""

        exec = tDungeonHelperExecutable(cmd)
        QtCore.QThreadPool.globalInstance().start(exec)
        pidw = tDHPIDWatcher(self, dhexec)
        QtCore.QThreadPool.globalInstance().start(pidw)

    #----------------------------------------------------------------------------------------------------------
    def kill(self):
      if self.status == self.P_STATUS_RUNNING:
        self.console.info(f"Killing DungeonHelper...")
        try:
          out = subprocess.check_output([f"kill -9 {self.pid}"], shell=True)
        except Exception as e:
          self.console.error(f"cDungeonHelper.kill: unknown error killing process with PID {self.pid}", e)
        self.status = self.P_STATUS_UNKNOWN
        self.statusLbl.setText("")


#----------------------------------------------------------------------------------------------------------
class tDungeonHelperExecutable(QRunnable):
  def __init__(self, exec):
    super().__init__()
    self.exec = exec
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    os.system(self.exec)

#----------------------------------------------------------------------------------------------------------
class tDHPIDWatcher(QRunnable):
  def __init__(self, dhWidget : cDungeonHelper, exec : str):
    super().__init__()
    self.dhWidget = dhWidget
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
            self.dhWidget.pid = line[0]
            self.dhWidget.status = self.dhWidget.P_STATUS_RUNNING
            self.dhWidget.statusLbl.setText(f"Running with PID={line[0]}")
            self.dhWidget.sigGotPID.emit(True)
            return True
          time.sleep(0.1)
      except: pass
    self.dhWidget.console.error("cDungeonHelper.getPID: could not get PID, process may not be running anymore...")
    self.dhWidget.sigGotPID.emit(False)
    return False