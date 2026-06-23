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
from μProcess import aProcessItem
from μSettings import μSetup
from μAuthenticator import μAuthenticator
from μServerInfo import μServerInfo
from helpers.χHelper import χHelper, windowData
from helpers.χTop import χTop
import subprocess
import os, time, glob, threading
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
from μWorlds import μWorld, μWorldList
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  D D O
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μDDO(aProcessItem):
  sigAuthenticating = pyqtSignal(str)
  sigAuthenticated = pyqtSignal(str)
  sigQueued = pyqtSignal(str)
  sigQueueDone = pyqtSignal(str)
  gameExec = 'x64/dndclient64.exe'

  P_STATUS_AUTHENTICATING = 30
  P_STATUS_QUEUEING       = 31
  P_STATUS_QUEUEDONE      = 32

  def __init__(self, main : μMainWindow, username : str, world : μWorld):
    super().__init__()
    self.auth : μAuthenticator = None
    self.world = world
    self.widgetID = username
    # cDDO freezes profile and uses that one until the process is cleaned
    # The reason is that changing profiles during runtime cannot change the already
    # running instances
    self.frozenProfile = μSetup.profile
    
    self.profileID.setText(self.frozenProfile.name)
    self.worldname.setText(world.name)
    self.username.setText(username)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.updateTooltip()

    self.sigRunning.connect(self.watchPID)
    self.sigGotPID.connect(self.watchWinID)
    self.sigGotWinID.connect(self._onGotWinID)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _onGotWinID(self, winID):
    self.winID.setText(winID)
    self.setStatus(self.status)
    self.restoreWindow()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setStatus(self, newStatus):
    _oldstatus = self.status
    if self.status != newStatus:
      if newStatus == self.P_STATUS_AUTHENTICATING:
        self.status = self.P_STATUS_AUTHENTICATING
        self.sigAuthenticating.emit(self.username.text())
        self.pid.setText("Auth")
        μPrint.info(f"Authenticating \"{C_SILVER}{self.username.text()}</font>\"...")
      elif newStatus == self.P_STATUS_QUEUEING:
        self.status = self.P_STATUS_QUEUEING
        self.sigAuthenticated.emit(self.username.text())
        self.pid.setText("Queue")
        μPrint.info(f"Queueing \"{C_SILVER}{self.username.text()}</font>\"...")
        self.sigQueued.emit(self.username.text())
      elif newStatus == self.P_STATUS_QUEUEDONE:
        self.status = self.P_STATUS_QUEUEDONE
        self.pid.setText("Launch")
        self.sigQueueDone.emit(self.username.text())
      elif newStatus == self.P_STATUS_RUNNING:
        μPrint.info(f"Running \"{C_SILVER}{self.username.text()}</font>\"...")
    super().setStatus(newStatus)
    if _oldstatus != self.status: self.sigStatusChanged.emit(self.status)
    self.updateTooltip()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def launch(self):
    if self.status == aProcessItem.P_STATUS_RUNNING: return
    t = threading.Thread(target=self._launchThread, daemon=True)
    t.start()
    μPrint.info(f"Starting {C_SILVER}{self.username.text()}</font> in {C_SILVER}\
                      {self.worldname.text()}</font>...")
    
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _launchThread(self):
    self.auth = μAuthenticator(self)
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
    gamePath = self.frozenProfile.launcher.gamePath()
    gameExec = self.frozenProfile.launcher.gameExec()
    cmd = f'cd \"{gamePath}\" ; {self.frozenProfile.launcher.command()} "{gameExec}" {arg} '

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
      μPrint.info("tGameExecutable.run:Error launching, check logs for details!")
      exitCode = 1

    # this locks until the DDO process ends, and it is intentional!
    # If it does end, then it was closed by the user (or some error...)
    if exitCode==137:
      self.sigChangeRequest.emit(self.P_STATUS_KILLED)
    elif exitCode in (1,2,126,127):
      self.sigChangeRequest.emit(self.P_STATUS_ERROR)
    else:
      self.sigChangeRequest.emit(self.P_STATUS_TERMINATED)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def watchWinID(self):
    pid = self.pid.text()
    def _thread():
      winIDList = χHelper.waitWinID(pid, 10.0)
      if winIDList: # validateWinID
        worldPrefix = self.world.name.split(" ")[0]
        for w in winIDList:
          title = χHelper.getWindowTitle(w)
          if title == 'Dungeons and Dragons Online' or worldPrefix in title:
            self.sigGotWinID.emit(str(w))
            break
    threading.Thread(target=_thread, daemon=True).start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def watchPID(self):
    def _watchPIDThread(self):
      startTime = time.time()
      while True:
        candidates = χTop.getByCommand(self.auth.subscription)
        for c in candidates:
          if χTop.getCommand(c).startswith(μDDO.gameExec):
            self.sigGotPID.emit(str(c))
            self.sigChangeRequest.emit(self.status)
            return c
        if (time.time() - startTime) > 15.0:
          μPrint.error(f"cDDO.watchPID: timeout error while looking for PID for {self.username.text()}")
          return None
        time.sleep(0.1)

    t = threading.Thread(target=_watchPIDThread, args=(self,), daemon=True)
    t.start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioToggle(self):
    if self.pid.text().isdigit():
      if χHelper.audioQueryMuted(self.pid.text()):
        self.audioUnmute()
      else:
        self.audioMute()  

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioMute(self):
    if self.pid.text().isdigit():
      μPrint.info(f"{C_SILVER}Muting</font> {self.pid.text()}...")
      χHelper.audioMute(str(self.pid.text()))
      self.btnAudio.setIcon(getIcon(P_ICON_UNMUTE))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def audioUnmute(self):
    if self.pid.text().isdigit():
      μPrint.info(f"{C_SILVER}Unmuting</font> {self.pid.text()}...")
      χHelper.audioUnmute(str(self.pid.text()))
      self.btnAudio.setIcon(getIcon(P_ICON_MUTE))
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def saveWindow(self):
    if self.status != self.P_STATUS_RUNNING: return
    winData = χHelper.getWindowsData(int(self.winID.text()))
    prefs = self.frozenProfile.session.windowsPreferences
    prefs[self.username.text()] = (winData.posx, winData.posy, winData.width, winData.height, winData.desktop, winData.borderless, winData.audio, False)
    self.frozenProfile.session.setWindowsPreference(prefs)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def restoreWindow(self):
    if self.status != self.P_STATUS_RUNNING: return
    if not self.winID.text().isdecimal(): return
    winID = int(self.winID.text())
    prefs = self.frozenProfile.session.windowsPreferences
    if self.username.text() not in prefs:
      return
    winData = windowData(prefs[self.username.text()])
    if self.frozenProfile.xsettings.position():
      χHelper.moveWindow(winID, winData.posx, winData.posy)
    if self.frozenProfile.xsettings.size():
      # χHelper.resizeWindow(winID, winData.posx, winData.posy)
      μPrint.warning(f"[cDDO] resizing window not yet implemented")
    if self.frozenProfile.xsettings.desktop():
      χHelper.moveVirtualDesktop(winID, winData.desktop)

    if self.frozenProfile.xsettings.border() == "Remember":
      if winData.borderless: χHelper.setBorderless(winID)
      else: χHelper.setBorderyes(winID)
    elif self.frozenProfile.xsettings.border().startswith("Always"):
      χHelper.setBorderless(winID)
    elif self.frozenProfile.xsettings.border().startswith("Never"):
      χHelper.setBorderyes(winID)

    if self.frozenProfile.xsettings.audio() == "Remember":
      if winData.audio: self.audioUnmute()
      else: self.audioMute()
    elif self.frozenProfile.xsettings.audio().startswith("Always"):
      self.audioMute()
    elif self.frozenProfile.xsettings.audio().startswith("Never"):
      self.audioUnmute()

    if self.frozenProfile.xsettings.logs() == "Remember":
      if winData.log: self.logShow()
      else: self.logHide()
    elif self.frozenProfile.xsettings.audio().startswith("Always"):
      self.logShow()
    elif self.frozenProfile.xsettings.audio().startswith("Never"):
      self.logHide()

    if self.frozenProfile.xsettings.blackscreenFix():
      χHelper.remapWindow(winID)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getLogFilename(self):
    return f"{P_DEFAULT_LOGSDIR}/ddoLog_{self.username.text()}.txt"

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def parseArguments(self):
    arg = μServerInfo.gameClientArgTemplate
    arg = arg.replace("{LOGIN}", self.world.loginServer)
    arg = arg.replace("{AUTHSERVERURL}", μServerInfo.gameClientAuthServerURL)
    arg = arg.replace("{GLS}", self.auth.ticket)
    arg = arg.replace("{CHAT}", self.world.chatServer)
    arg = arg.replace("{LANG}", "English")
    arg = arg.replace("{GLSTICKETLIFETIME}", μServerInfo.gameClientGLSTicketLifetime)
    arg = arg.replace("{SUBSCRIPTION}", self.auth.subscription)
    if not self.frozenProfile.launcher.useHighRes():
      arg += " --HighResOutOfDate"
    return arg
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def isCMD(line) -> bool:
    return line.startswith(μDDO.gameExec)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def createFromOrphan(main : μMainWindow, pid : int, cmdline : str) -> μDDO:
    cmdline = cmdline.split(' ')
    pid = str(pid)
    auth = cmdline[2]        # used to figure out the account
    loginServer = cmdline[4] # used to figure out the world
    world = ""
    username = ""

    accountFiles = glob.glob(μAuthenticator.P_GLSAUTHFILE+"*")
    for a in accountFiles:
      with open(a,'r') as f:
        if auth in f.read():
          username = ((os.path.basename(a)).replace("GLSAuthServer_","")).replace(".xml","")
          break
    if not username:
      μPrint.debug(f" Trying to match orphan process failed; auth={auth} not found in any GLSAuth file.")
      return None
    
    for w in μWorldList.worlds.values():
      if w.loginServer == loginServer:
        world = w
    if not world:
      μPrint.debug(f" Trying to match orphan process failed; loginServer={loginServer} doesn't match any world")
      return None

    # missing profile info, what to do?
    orphan = μDDO(main, username, world)
    orphan.auth = μAuthenticator(orphan)
    orphan.auth.subscription = auth
    orphan.auth.status = μAuthenticator.P_STATUS_DONE
    orphan.pid.setText(pid)
    orphan.setStatus(μDDO.P_STATUS_RUNNING)
    orphan.watchWinID()
    return orphan
  