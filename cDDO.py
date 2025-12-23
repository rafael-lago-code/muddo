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
from PyQt6.QtCore import QRunnable, pyqtSignal
from cProcess import aProcessItem
from tAuthenticator import tAuthenticator
# from tWinManager import tWinManager
from XHelper import XHelper
import subprocess
import os, time, glob
from cWidgets.util import *
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
  gameExec = 'x64/dndclient64.exe'

  def __init__(self, main : cMainWindow, username : str, world : cWorld):
    super().__init__(main)
    self.auth : tAuthenticator = None
    self.world = world
    self.key = username
    
    self.profileID.setText(self.profile.name)
    self.worldname.setText(world.name)
    self.username.setText(username)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.updateTooltip()

    self.sigAuthenticated.connect(self.updateTooltip) # also calls self.auth.queue()
    self.sigRunning.connect(self.watchPID)
    self.sigGotPID.connect(self.watchWinID)
    self.sigGotWinID.connect(self.restoreWindow)
    self.sigGotWinID.connect(self.btnSave.setEnabled)
    self.sigGotWinID.connect(self.btnRestore.setEnabled)

    self.sigAuthenticating.connect(lambda : self.pid.setText("Auth"))
    self.sigQueued.connect(lambda : self.pid.setText("Queue"))
    self.sigQueueDone.connect(lambda : self.pid.setText("Launch"))

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    exec = tGameExecutable(self)
    QtCore.QThreadPool.globalInstance().start(exec)
    self.setStatus(cDDO.P_STATUS_RUNNING)
    self.console.info(f"Launching {C_SILVER}{self.username.text()}</font> in {C_SILVER}\
                      {self.worldname.text()}</font>...")
  
  #----------------------------------------------------------------------------------------------------------
  def watchPID(self):
    pidw = tPIDWatcher(self)
    QtCore.QThreadPool.globalInstance().start(pidw)

  #----------------------------------------------------------------------------------------------------------
  def watchWinID(self):
    def validateWinID(pid : int, winIDList : list):
      xh = XHelper()
      if int(self.pid.text()) != pid:
        print(" --------------> watchWinID: ERROR WRONG PID!!!")
        return
      worldPrefix = self.world.name.split(" ")[0]
      for w in winIDList:
        title = xh.getWindowTitle(w)
        if title == 'Dungeons and Dragons Online' or worldPrefix in title:
          self.winID.setText(str(w))
          self.sigGotWinID.emit(True)
  
    xh = XHelper()
    xh.sigGotWinID.connect(validateWinID)
    xh.requestWinID(self.pid.text(), 10.0)
  
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
    if self.status != self.P_STATUS_RUNNING: return
    xh = XHelper()
    geo = xh.getWindowGeometry(int(self.winID.text()))
    self.profile.windowsPreferences[self.username.text()] = (int(geo[0]), int(geo[1]))
    self.profile.save()

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    if self.status != self.P_STATUS_RUNNING: return
    if self.username.text() in self.profile.windowsPreferences.keys():
      pos1, pos2 = self.profile.windowsPreferences[self.username.text()]
    else: 
      return
    xh = XHelper()
    xh.moveWindow(int(self.winID.text()), pos1, pos2)
  
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
  @staticmethod
  def isDDOCmd(line) -> bool:
    return line.startswith(cDDO.gameExec)
  
  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def createFromOrphan(main : cMainWindow, line : str) -> cDDO:
    line = line.split(' ')
    pid = line[0]
    auth = line[3]        # used to figure out the account
    loginServer = line[5] # used to figure out the world
    world = ""
    username = ""

    accountFiles = glob.glob(tAuthenticator.P_GLSAUTHFILE+"*")
    for a in accountFiles:
      with open(a,'r') as f:
        if auth in f.read():
          username = ((os.path.basename(a)).replace("GLSAuthServer_","")).replace(".xml","")
          break
    if not username:
      main.console.debugMessage(f" Trying to match orphan process failed; auth={auth} not found in any GLSAuth file.")
      return None
    
    for w in main.credentials.listWorlds.worlds.values():
      if w.loginServer == loginServer:
        world = w
    if not world:
      main.console.debugMessage(f" Trying to match orphan process failed; loginServer={loginServer} doesn't match any world")
      return None

    # missing profile info, what to do?
    orphan = cDDO(main, username, world)
    orphan.pid.setText(pid)
    orphan.setStatus(cDDO.P_STATUS_RUNNING)
    orphan.watchWinID()
    return orphan


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

    cmd  = f"cd \"{gameDir}\" ; "
    cmd += f"STEAM_ROOT=\"{self.ddo.profile.steamRoot.text()}\" PROTON_LOG=1 "
    cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.ddo.profile.compatData.text()}\" "
    cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.ddo.profile.compatData.text()}\" "
    cmd += f"\"{self.ddo.profile.protonExec.text()}\" run "
    cmd += f"{cDDO.gameExec} "
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

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    for i in range(100):
      try:
        out = subprocess.check_output([f"ps a -o pid,command | grep {self.ddo.auth.subscription}"], shell=True)
        for line in out.decode().strip().split('\n'):
          line = line.split()
          if line[1] == cDDO.gameExec:
            self.ddo.pid.setText(line[0])
            self.ddo.sigGotPID.emit(True)
            return True
      except: pass
      time.sleep(0.1)
    self.ddo.console.error("tPIDWatcher: could not get PID, process may not be running anymore...")
    self.ddo.sigGotPID.emit(False)
    return False


  