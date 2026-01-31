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
from XHelper import XHelper
from cTop import cTop
import subprocess
import os, time, glob, threading
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

  P_STATUS_AUTHENTICATING = 30
  P_STATUS_QUEUEING       = 31
  P_STATUS_QUEUEDONE      = 32

  def __init__(self, main : cMainWindow, username : str, world : cWorld):
    super().__init__()
    self.auth : tAuthenticator = None
    self.world = world
    self.key = username
    # cDDO freezes profile and uses that one until the process is cleaned
    # The reason is that changing profiles during runtime cannot change the already
    # running instances
    self.frozenProfile = main.profile()
    
    self.profileID.setText(self.frozenProfile.name)
    self.worldname.setText(world.name)
    self.username.setText(username)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.updateTooltip()

    self.sigRunning.connect(self.watchPID)
    self.sigGotPID.connect(self.watchWinID)
    self.sigGotWinID.connect(lambda : self.setStatus(self.status))
    self.sigGotWinID.connect(self.restoreWindow)
    self.sigGotWinID.connect(self.btnSave.setEnabled)
    self.sigGotWinID.connect(self.btnRestore.setEnabled)

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, newStatus):
    _oldstatus = self.status
    if self.status != newStatus:
      if newStatus == self.P_STATUS_AUTHENTICATING:
        self.status = self.P_STATUS_AUTHENTICATING
        self.sigAuthenticating.emit(self.username.text())
        self.pid.setText("Auth")
        self.printInfo(f"Authenticating \"{C_SILVER}{self.username.text()}</font>\"...")
      elif newStatus == self.P_STATUS_QUEUEING:
        self.status = self.P_STATUS_QUEUEING
        self.sigAuthenticated.emit(self.username.text())
        self.pid.setText("Queue")
        self.printInfo(f"Queueing \"{C_SILVER}{self.username.text()}</font>\"...")
        self.sigQueued.emit(self.username.text())
      elif newStatus == self.P_STATUS_QUEUEDONE:
        self.status = self.P_STATUS_QUEUEDONE
        self.pid.setText("Launch")
        self.sigQueueDone.emit(self.username.text())
      elif newStatus == self.P_STATUS_RUNNING:
        self.printInfo(f"Running \"{C_SILVER}{self.username.text()}</font>\"...")
    super().setStatus(newStatus)
    if _oldstatus != self.status: self.sigStatusChanged.emit(self.status)
    self.updateTooltip()

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    t = threading.Thread(target=self._launchThread, daemon=True)
    t.start()
    self.printInfo(f"Starting {C_SILVER}{self.username.text()}</font> in {C_SILVER}\
                      {self.worldname.text()}</font>...")
    
  #----------------------------------------------------------------------------------------------------------
  def _launchThread(self):
    self.auth = tAuthenticator(self)
    self.sigChangeRequest.emit(self.P_STATUS_AUTHENTICATING)

    if not self.auth.authenticate():
      self.sigChangeRequest.emit(self.P_STATUS_ERROR)
      return
    
    self.sigChangeRequest.emit(self.P_STATUS_QUEUEING)
    if not self.auth.wait():
      self.sigChangeRequest.emit(self.P_STATUS_ERROR)
      return
    self.sigChangeRequest.emit(self.P_STATUS_QUEUEDONE)

    arg = self.parseArguments()
    gameDir = self.frozenProfile.gameDir.text()

    cmd = (
        f'cd "{gameDir}" && '
        f'STEAM_ROOT="{self.frozenProfile.steamRoot.text()}" '
        f'PROTON_LOG=1 '
        f'STEAM_COMPAT_DATA_PATH="{self.frozenProfile.compatData.text()}" '
        f'STEAM_COMPAT_CLIENT_INSTALL_PATH="{self.frozenProfile.compatData.text()}" '
        f'"{self.frozenProfile.protonExec.text()}" run "{cDDO.gameExec}" {arg} '
    )

    logFile = open(f"{P_DEFAULT_CONFIGDIR}/ddoLog{self.username.text()}.txt", "w")
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
      self.printInfo("tGameExecutable.run:Error launching, check logs for details!")
      exitCode = 1

    # this locks until the DDO process ends, and it is intentional!
    # If it does end, then it was closed by the user (or some error...)
    if exitCode==137:
      self.sigChangeRequest.emit(self.P_STATUS_KILLED)
    elif exitCode in (1,2,126,127):
      self.sigChangeRequest.emit(self.P_STATUS_ERROR)
    else:
      self.sigChangeRequest.emit(self.P_STATUS_TERMINATED)

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
  def watchPID(self):
    def _watchPIDThread(self):
      startTime = time.time()
      while True:
        candidates = cTop.getByCommand(self.auth.subscription)
        for c in candidates:
          if cTop.getCommand(c).startswith(cDDO.gameExec):
            self.sigGotPID.emit(str(c))
            self.sigChangeRequest.emit(self.status)
            return c
        if (time.time() - startTime) > 15.0:
          self.printError(f"aProcessItem.watchPID: timeout error while looking for PID for {self.username.text()}")
          return None
        time.sleep(0.1)
      # candidates = cTop.waitPID(exec, self.auth.subscription, 15.0)
      # print(self.auth.subscription)
      # print(candidates)
      # if isinstance(candidates[0],int):
      #   self.sigGotPID.emit(str(candidates[0]))
      #   self.sigChangeRequest.emit(self.status)
      # else:
      # self.printError(f"aProcessItem.watchPID:Error getting PID, don't know what to do with this: {candidates}")

    t = threading.Thread(target=_watchPIDThread, args=(self,), daemon=True)
    t.start()

  #----------------------------------------------------------------------------------------------------------
  def audioToggle(self):
    if XHelper().isPIDMuted(self.pid):
      self.printInfo(f"{C_SILVER}Muting</font> {self.pid}...")
      XHelper().unmutePID(self.pid)
      self.btnMute.setIcon(getIcon(P_ICON_UNMUTE))
    else:
      self.printInfo(f"{C_SILVER}Unmuting</font> {self.pid}...")
      XHelper().mutePID(self.pid)
      self.btnMute.setIcon(getIcon(P_ICON_MUTE))
  
  #----------------------------------------------------------------------------------------------------------
  def updateTooltip(self):
    text = "<i>Not yet authenticated...</i>"
    if self.auth:
      try:
        arg = self.parseArguments().split(" ")
        text = "<b>Commandline arguments:<br>-----------------------------------------------------</b></br>"
        for a in arg:
          if a.startswith("-"):
            text += "<br><b>"+a+"</b> "
          else:
            text += a
      except:
        pass
    self.setToolTip(text)
  
  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    if self.status != self.P_STATUS_RUNNING: return
    xh = XHelper()
    geo = xh.getWindowGeometry(int(self.winID.text()))
    self.frozenProfile.windowsPreferences[self.username.text()] = (int(geo[0]), int(geo[1]))
    self.frozenProfile.save()

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    if self.status != self.P_STATUS_RUNNING: return
    if self.username.text() in self.frozenProfile.windowsPreferences.keys():
      pos1, pos2 = self.frozenProfile.windowsPreferences[self.username.text()]
    else: 
      return
    xh = XHelper()
    xh.moveWindow(int(self.winID.text()), pos1, pos2)
    # xh.remapWindow(int(self.winID.text()))
    # xh.setBorderless(int(self.winID.text()))
  
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
    if not self.frozenProfile.useHighRes.isEnabled():
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
      cDDO.printDebug(f" Trying to match orphan process failed; auth={auth} not found in any GLSAuth file.")
      return None
    
    for w in main.credentials.listWorlds.worlds.values():
      if w.loginServer == loginServer:
        world = w
    if not world:
      cDDO.printDebug(f" Trying to match orphan process failed; loginServer={loginServer} doesn't match any world")
      return None

    # missing profile info, what to do?
    orphan = cDDO(main, username, world)
    orphan.pid.setText(pid)
    orphan.setStatus(cDDO.P_STATUS_RUNNING)
    orphan.watchWinID()
  