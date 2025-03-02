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
#    <ajackson@bcs.org.uk>), which in turn is based on a script by SNy
#    (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
from PyQt6.QtCore import QRunnable, pyqtSignal
from cProcess import aProcessItem
from tAuthenticator import tAuthenticator
from tWinManager import tWinManager
import subprocess
import os, time
from util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow
   from cWorlds import cWorld

#----------------------------------------------------------------------------------------------------------
class cDDO(aProcessItem):
  sigAuthenticating = pyqtSignal(str)
  sigAuthenticated = pyqtSignal(str)
  sigQueued = pyqtSignal(str)
  sigQueueDone = pyqtSignal(str)
  sigGotWinID = pyqtSignal(bool)

  def __init__(self, main : cMainWindow, username : str, world : cWorld):
    super().__init__(main)
    self.auth : tAuthenticator = None
    self.world = world
    self.key = username
    
    self.profileID.setText(self.profile.name)
    self.worldname.setText(world.name)
    self.username.setText(username)
    self.updateTooltip()

    self.sigAuthenticated.connect(self.updateTooltip) # also calls self.auth.queue()
    self.sigRunning.connect(self.watchPID)
    self.sigGotPID.connect(self.autoRestore)
    self.sigGotPID.connect(self.btnSave.setEnabled)
    self.sigGotPID.connect(self.btnRestore.setEnabled)

    self.sigAuthenticating.connect(lambda : self.pid.setText("A"))
    self.sigQueued.connect(lambda : self.pid.setText("Q"))
    self.sigQueueDone.connect(lambda : self.pid.setText("L"))

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    exec = tGameExecutable(self)
    QtCore.QThreadPool.globalInstance().start(exec)
    self.btnToggle.setEnabled(True)
    self.btnRemove.setEnabled(True)
    self.console.info(f"Launching {C_SILVER}{self.username.text()}</font> in {C_SILVER}\
                      {self.worldname.text()}</font>...")
    self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
    self.status = self.P_STATUS_RUNNING
  
  #----------------------------------------------------------------------------------------------------------
  def watchPID(self):
    pidw = tPIDWatcher(self)
    QtCore.QThreadPool.globalInstance().start(pidw)
  
  #----------------------------------------------------------------------------------------------------------
  def updateTooltip(self):
    if self.auth is None:
      text = "<i>Not yet authenticated...</i>"
    else:
      arg = self.parseArguments().split(" ")
      text = "<b>Commandline arguments:<br>-----------------------------------------------------</b></br>"
      for a in arg:
        if a.startswith("-"):
          text += "<br><b>"+a+"</b> "
        else:
          text += a
    self.setToolTip(text)
  
  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    if not self.profile.usexdotool.isChecked(): return
    wm = tWinManager(self, 'saveWindow')
    QtCore.QThreadPool.globalInstance().start(wm)

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    if not self.profile.usexdotool.isChecked(): return
    wm = tWinManager(self, 'restoreWindow')
    QtCore.QThreadPool.globalInstance().start(wm)
  
  #----------------------------------------------------------------------------------------------------------
  # autoRestore
  #   This is silly but it takes a while for the window management to work...
  def autoRestore(self):
    time.sleep(1.0)
    self.restoreWindow()

  #----------------------------------------------------------------------------------------------------------
  def parseArguments(self):
    arg = self.auth.credentials.serverInfo.gameClientArgTemplate
    arg = arg.replace("{LOGIN}", self.world.loginServer)
    arg = arg.replace("{AUTHSERVERURL}", self.auth.credentials.serverInfo.gameClientAuthServerURL)
    arg = arg.replace("{GLS}", self.auth.ticket)
    arg = arg.replace("{CHAT}", self.world.chatServer)
    arg = arg.replace("{LANG}", "English")
    arg = arg.replace("{GLSTICKETLIFETIME}", self.auth.credentials.serverInfo.gameClientGLSTicketLifetime)
    arg = arg.replace("{SUBSCRIPTION}", self.auth.subscription)
    if not self.profile.useHighRes.isEnabled():
      arg += " --HighResOutOfDate"
    return arg


#----------------------------------------------------------------------------------------------------------
class tGameExecutable(QRunnable):
  def __init__(self, ddo : cDDO):
    super().__init__()
    self.ddo = ddo
    self.console = ddo.console

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    self.ddo.auth = tAuthenticator(self.ddo)
    self.ddo.status = self.ddo.P_STATUS_AUTHENTICATING
    self.ddo.sigAuthenticating.emit(self.ddo.username.text())
    self.console.info(f"Authenticating \"{C_SILVER}{self.ddo.username.text()}</font>\"...")

    if not self.ddo.auth.authenticate():
      self.ddo.status = self.ddo.P_STATUS_ERROR
      return
    
    self.ddo.sigAuthenticated.emit(self.ddo.username.text())
    self.ddo.status = self.ddo.P_STATUS_QUEUEING
    self.ddo.sigQueued.emit(self.ddo.username.text())
    self.console.info(f"Queueing \"{C_SILVER}{self.ddo.username.text()}</font>\"...")
    if not self.ddo.auth.wait():
      self.ddo.status = self.ddo.P_STATUS_ERROR
      return
    
    self.ddo.sigQueueDone.emit(self.ddo.username.text())

    arg = self.ddo.parseArguments()
    gameDir = self.ddo.profile.gameDir.text()
    # TODO: gameExec is supposed to be something like 
    #    'x64/' if self.settings.use64bits.isChecked() else '' + self.auth.serverInfo.gameClientFilename
    # Since I'm not testing for 32-bits client anyways, I might as well just keep it hardcoded.
    gameExec = 'x64/dndclient64.exe'

    cmd  = f"cd \"{gameDir}\" ; "
    cmd += f"STEAM_ROOT=\"{self.ddo.profile.steamRoot.text()}\" PROTON_LOG=1 "
    cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.ddo.profile.compatData.text()}\" "
    cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.ddo.profile.compatData.text()}\" "
    cmd += f"\"{self.ddo.profile.protonExec.text()}\" run "
    cmd += f"{gameExec} "
    cmd += f"{arg}"

    # TODO: I was supposed to use subprocess and set environment variables and CWD properly
    # but it simply does not start the game. Once I figure it out I will use it instead of
    # os.system call. For the time being, everything needs to be a oneliner.
    # TODO: logfile is not working anyways...
    # logname = P_DEFAULT_CONFIGDIR+os.sep+self.auth.world.name+"_"+self.auth.username
    # if os.path.exists(logname+".out"): os.rename(logname+".out",logname+".out.old")
    # if os.path.exists(logname+".err"): os.rename(logname+".err",logname+".err.old")
    self.ddo.status = self.ddo.P_STATUS_RUNNING
    self.ddo.sigRunning.emit(True)
    self.console.info(f"Launching \"{C_SILVER}{self.ddo.username.text()}</font>\"...")
    os.system(cmd)

    if self.ddo.status == self.ddo.P_STATUS_RUNNING:
      self.ddo.sigTerminated.emit(True)
    # out = subprocess.Popen([self.cmd], cwd=self.gameDir, env=self.evars, \
    #                        stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    # while True:
    #   line = out.stdout.readline()
    #   if line: print(line)
    #   line = out.stderr.readline()
    #   if line: print(line)

#----------------------------------------------------------------------------------------------------------
class tPIDWatcher(QRunnable):
  def __init__(self, ddo : cDDO):
    super().__init__()
    self.ddo = ddo
    self.gameExec = 'x64/dndclient64.exe'

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    for i in range(100):
      try:
        out = subprocess.check_output([f"ps a -o pid,command | grep {self.ddo.auth.subscription}"], shell=True)
        for line in out.decode().strip().split('\n'):
          line = line.split()
          if line[1] == self.gameExec:
            self.ddo.pid.setText(line[0])
            self.ddo.sigGotPID.emit(True)
            return True
      except: pass
      time.sleep(0.1)
    self.ddo.console.error("tPIDWatcher: could not get PID, process may not be running anymore...")
    self.ddo.sigGotPID.emit(False)
    return False
  