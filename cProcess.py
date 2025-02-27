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
from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy, QComboBox
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QRunnable, pyqtSignal, Qt
from cTab import cTab
from tAccount import tAccount
from collections import OrderedDict
import subprocess
import os, time
from util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow
   from cWorlds import cWorld

class cProcessManager(cTab):

  def __init__(self, main : cMainWindow):
    super().__init__("Process Manager")
    self.main = main
    self.console = main.console
    self.items : OrderedDict[str, cProcessItem] = OrderedDict()
    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)

    header = QWidget()
    header.setLayout(newHLayout([newHeaderLabel("PID", 50), newHeaderLabel("WinID"),\
                     newHeaderLabel("World"), newHeaderLabel("Profile"), "Username"]))

    self.btnStart   = newToolbarButton(P_ICON_PLAY,     "Start all non-running processes", self.startAll)
    self.btnKill    = newToolbarButton(P_ICON_SKULL_RED,"Force-kill all running processes", self.killAll)
    self.btnSave    = newToolbarButton(P_ICON_SAVEALL,  "Save all windows position", self.saveWindowAll)
    self.btnRestore = newToolbarButton(P_ICON_UNDO,     "Restore all previously saved windows positions", self.restoreWindowAll)
    self.btnClear   = newToolbarButton(P_ICON_CLEARALL, "Removes all processes from the list of processes", self.removeAll)

    buttons = QWidget()
    buttons.setLayout(newHLayout([newRQLabel("All processes: "), self.btnStart, self.btnKill, self.btnSave,\
                                  self.btnRestore, self.btnClear]))

    self.content = newVLayout([header])
    self.setLayout(newVLayout([self.content, buttons]))
    self.main.sigQueuedUserDone.connect(lambda u: self.items[u].launch())
    self.main.sigAuthenticatedUser.connect(lambda u: self.items[u].updateTooltip())

  #----------------------------------------------------------------------------------------------------------
  def removeAll(self):
    allItems = set(self.items.values())
    for i in allItems: i.remove()

  #----------------------------------------------------------------------------------------------------------
  def startAll(self):
    for u in self.items.keys(): 
      if self.items[u].status == cProcessItem.P_STATUS_RUNNING:
        self.items[u].launch()

  #----------------------------------------------------------------------------------------------------------
  def killAll(self):
    for u in self.items.keys(): self.items[u].kill()
    
  #----------------------------------------------------------------------------------------------------------
  def saveWindowAll(self):
    for u in self.items.keys(): self.items[u].saveWindow()
  
  #----------------------------------------------------------------------------------------------------------
  def restoreWindowAll(self):
    for u in self.items.keys(): self.items[u].restoreWindow()

  #----------------------------------------------------------------------------------------------------------
  def addProcess(self, p : cProcessItem):
    self.btnKill.setEnabled(True)
    self.btnSave.setEnabled(True)
    self.btnRestore.setEnabled(True)
    self.btnClear.setEnabled(True)
    self.items[p.username.text()] = p
    self.setColour(p)
    self.content.addWidget(p)
  
  #----------------------------------------------------------------------------------------------------------
  def setColour(self,p : cProcessItem):
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
class cProcessItem(QWidget):
  sigGotPID = pyqtSignal(bool)
  sigGotWinID = pyqtSignal(bool)
  sigNaturalTermination = pyqtSignal(bool)

  P_STATUS_UNKNOWN = 0
  P_STATUS_RUNNING = 1
  P_STATUS_KILLED = 2

  def __init__(self, main : cMainWindow, username : str, world : cWorld):
    super().__init__()
    self.main = main
    self.account : tAccount = None
    self.world = world
    self.console = main.console
    self.status = self.P_STATUS_UNKNOWN
    self.profile = main.profile() # yes, we freeze the profile here!
    
    self.pid = newProcessField("NA", 50)
    self.winID = newProcessField("NA")
    self.profileID = newProcessField(self.profile.name)
    self.worldname = newProcessField(world.name)
    self.username = QLabel(username)
    self.profileID.setFixedWidth(80)

    self.btnToggle  = newToolbarButton(P_ICON_PLAY,  "Toggle (kill/start) process", self.toggle)
    self.btnSave    = newToolbarButton(P_ICON_SAVE,  "Save this windows's position", self.saveWindow)
    self.btnRestore = newToolbarButton(P_ICON_UNDO,  "Restore previously saved windows position", self.restoreWindow)
    self.btnRemove  = newToolbarButton(P_ICON_TRASH, "Removes this process from the list of processes",  self.remove)
    self.updateTooltip()

    
    self.setLayout(newHLayout([self.pid, self.winID, self.worldname, self.profileID, 
                              self.username, self.btnToggle, self.btnSave, self.btnRestore,
                              self.btnRemove]))

  
  #----------------------------------------------------------------------------------------------------------
  def authenticate(self):
    self.account = tAccount(self.main, self.username.text(), self.world)
    QtCore.QThreadPool.globalInstance().start(self.account)
    # Once queue is done, tAccount will emit sigQueueDone which calls self.launch()
    

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    if self.account is None:
      self.authenticate()
      return
    
    self.btnToggle.setEnabled(True)
    self.btnRemove.setEnabled(True)
    self.console.info(f"Launching {C_SILVER}{self.username.text()}</font> in {C_SILVER}{self.worldname.text()}</font>...")
    # Logfile is not working anyways...
    # logname = P_DEFAULT_CONFIGDIR+os.sep+self.account.world.name+"_"+self.account.username
    # if os.path.exists(logname+".out"): os.rename(logname+".out",logname+".out.old")
    # if os.path.exists(logname+".err"): os.rename(logname+".err",logname+".err.old")

    arg = self.parseArguments()
    gameDir = self.profile.gameDir.text()
    # TODO: gameExec is supposed to be something like 
    #    'x64/' if self.settings.use64bits.isChecked() else '' + self.account.serverInfo.gameClientFilename
    # Since I'm not testing for 32-bits client anyways, I might as well just keep it hardcoded.
    gameExec = 'x64/dndclient64.exe'

    # TODO: I was supposed to use subprocess and set environment variables and CWD properly
    # but it simply does not start the game. Once I figure it out I will use it instead of
    # os.system call. For the time being, everything needs to be a oneliner.
    cmd  = f"cd \"{gameDir}\" ; "
    cmd += f"STEAM_ROOT=\"{self.profile.steamRoot.text()}\" PROTON_LOG=1 "
    cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.profile.compatData.text()}\" "
    cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.profile.compatData.text()}\" "
    cmd += f"\"{self.profile.protonExec.text()}\" run "
    cmd += f"{gameExec} "
    cmd += f"{arg}"

    exec = tGameExecutable(self.main, cmd, arg)
    QtCore.QThreadPool.globalInstance().start(exec)
    pidw = tPIDWatcher(self, gameExec)
    QtCore.QThreadPool.globalInstance().start(pidw)
    self.sigGotPID.connect(self.autoRestore)
    self.sigGotPID.connect(self.btnSave.setEnabled)
    self.sigGotPID.connect(self.btnRestore.setEnabled)

    self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
    self.status = self.P_STATUS_RUNNING
  
  #----------------------------------------------------------------------------------------------------------
  def updateTooltip(self):
    if self.account is None:
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
  def remove(self):
    try:
      self.main.processManager.layout().removeWidget(self)
      del self.main.processManager.items[self.username.text()]
    except Exception as e:
      self.console.error("cProcessItem.remove: unknown error removing item from process list", e)

    self.main.processManager.resetColour()
    self.deleteLater()

  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    wm = tWinManager(self, 'saveWindow')
    QtCore.QThreadPool.globalInstance().start(wm)

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    wm = tWinManager(self, 'restoreWindow')
    QtCore.QThreadPool.globalInstance().start(wm)
  
  #----------------------------------------------------------------------------------------------------------
  # autoRestore
  #   This is silly but it takes a while for the window management to work...
  def autoRestore(self):
    time.sleep(1.0)
    self.restoreWindow()

  
#----------------------------------------------------------------------------------------------------------
  def kill(self):
    if self.pid.text() == "NA": return
    self.console.info(f"Killing {C_SILVER}{self.username.text()}</font> in {C_SILVER}{self.worldname.text()}</font>...")
    try:
      out = subprocess.check_output([f"kill -9 {self.pid.text()}"], shell=True)
    except Exception as e:
      self.console.error(f"cProcessItem.kill: unknown error killing process with PID {self.pid.text()}", e)

    self.pid.setText("NA")
    self.winID.setText("NA")
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
    self.status = self.P_STATUS_KILLED
  
  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.status == self.P_STATUS_RUNNING:
      self.kill()
    else:
      self.launch()
      # del self.account
      # self.account = tAccount(self.main, self.username.text(), world)
      # QtCore.QThreadPool.globalInstance().start(self.account)

  #----------------------------------------------------------------------------------------------------------
  def parseArguments(self):
    arg = self.account.serverInfo.gameClientArgTemplate
    arg = arg.replace("{LOGIN}", self.account.world.loginServer)
    arg = arg.replace("{AUTHSERVERURL}", self.account.serverInfo.gameClientAuthServerURL)
    arg = arg.replace("{GLS}", self.account.ticket)
    arg = arg.replace("{CHAT}", self.account.world.chatServer)
    arg = arg.replace("{LANG}", "English")
    arg = arg.replace("{GLSTICKETLIFETIME}", self.account.serverInfo.gameClientGLSTicketLifetime)
    arg = arg.replace("{SUBSCRIPTION}", self.account.subscription)
    if not self.profile.useHighRes.isEnabled():
      arg += " --HighResOutOfDate"
    return arg

#----------------------------------------------------------------------------------------------------------
class tGameExecutable(QRunnable):
  def __init__(self, main : cMainWindow, exec, arg):
    super().__init__()
    self.exec = exec
    # self.main = main
    
    # self.gameDir = self.profile.gameDir.text()
    # # TODO: gameExec is supposed to be something like 
    # #    'x64/' if self.settings.use64bits.isChecked() else '' + self.account.serverInfo.gameClientFilename
    # # Since I'm not testing for 32-bits client anyways, I might as well just keep it hardcoded.
    # gameExec = 'x64/dndclient64.exe'
    # self.evars = {}
    # self.evars['PROTON_LOG'] = "1"
    # self.evars['STEAM_ROOT'] = self.profile.steamRoot.text()
    # self.evars['STEAM_COMPAT_DATA_PATH'] = self.profile.protonPrefix
    # self.evars['STEAM_COMPAT_CLIENT_INSTALL_PATH'] = self.profile.protonPrefix

    # self.cmd = f"\"{self.profile.protonExec}\" run \"{gameExec} {arg}\""

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    os.system(self.exec)
    # out = subprocess.Popen([self.cmd], cwd=self.gameDir, env=self.evars, \
    #                        stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    # while True:
    #   line = out.stdout.readline()
    #   if line: print(line)
    #   line = out.stderr.readline()
    #   if line: print(line)



#----------------------------------------------------------------------------------------------------------
class tPIDWatcher(QRunnable):
  def __init__(self, processWidget : cProcessItem, gameExec):
    super().__init__()
    self.processWidget = processWidget
    self.gameExec = gameExec
    self.subscription = processWidget.account.subscription
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    for i in range(100):
      try:
        out = subprocess.check_output([f"ps a -o pid,command | grep {self.processWidget.account.subscription}"], shell=True)
        for line in out.decode().strip().split('\n'):
          line = line.split()
          if line[1] == self.gameExec:
            self.processWidget.pid.setText(line[0])
            self.processWidget.sigGotPID.emit(True)
            return True
          time.sleep(0.1)
      except: pass
    self.processWidget.console.error("cProcessItem.getPID: could not get PID, process may not be running anymore...")
    self.processWidget.sigGotPID.emit(False)
    return False
  
#----------------------------------------------------------------------------------------------------------
class tWinManager(QRunnable):
  def __init__(self, processWidget : cProcessItem, cmd):
    super().__init__()
    self.processWidget = processWidget
    self.cmd = cmd
    self.msg = ""
  
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    if self.cmd == "getWinID":
      self.getWinID()
    elif self.cmd == "restoreWindow":
      self.restoreWindow()
    elif self.cmd == "saveWindow":
      self.saveWindow()

  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    if not self.processWidget.profile.usexdotool.isChecked(): return
    bin = self.processWidget.profile.xdotoolExec.text()
    for i in range(5):
      try:
        out = subprocess.check_output([f"{bin} getwindowgeometry {self.processWidget.winID.text()}"], shell=True)
        out = out.decode().strip().split('\n')
        pos = out[1].split()[1].split(',')
        self.processWidget.profile.windowsPreferences[self.processWidget.username.text()] = (int(pos[0]), int(pos[1]))
        self.processWidget.profile.save()
      except Exception as e:
        self.getWinID()
      else:
        return
    self.processWidget.console.error("tWinManager.saveWindow: unknow error trying to save position info", e)


  #----------------------------------------------------------------------------------------------------------
  # restoreWindow
  #    Tries to restore window preferences. It always checks the WinID again because these change 
  #    every now and then, which is weird. It will loop a few times until it gets a valid winID.
  def restoreWindow(self):
    if not self.processWidget.profile.usexdotool.isChecked(): return
    bin = self.processWidget.profile.xdotoolExec.text()
    # self.processWidget.profile.loadProfile()
    if self.processWidget.username.text() in self.processWidget.profile.windowsPreferences.keys():
      pos1, pos2 = self.processWidget.profile.windowsPreferences[self.processWidget.username.text()]
      for i in range(5):
        try:
          out = subprocess.check_output([f"{bin} windowmove --sync {self.processWidget.winID.text()} {pos1} {pos2}"], shell=True)
        except Exception as e:
          self.getWinID()
        else:
          return
      self.processWidget.console.error("tWinManager.restoreWindow: unknow error trying to load position")

  #----------------------------------------------------------------------------------------------------------
  def getWinID(self):
    id, e = self.probeWinID()
    if not id.startswith("ERROR"): self.processWidget.winID.setText(id)
    for i in range(20):
      if self.checkWinID():
        self.processWidget.sigGotWinID.emit(True)
        return
      else:
        self.processWidget.winID.setText("<?>")
        id, e = self.probeWinID()
        if not id.startswith("ERROR"):
          self.processWidget.winID.setText(id)
        time.sleep(0.2)
        
    self.processWidget.sigGotWinID.emit(False)
    if id == "ERROR_LEN0":
      self.msg = f"tWinManager[{self.processWidget.username.text()}].getWinID: failed getting winID, no window with the associated pid {self.pid.text()}"
    elif id == "ERROR_UNMATCHING_NAME":
      self.msg = f"tWinManager[{self.processWidget.username.text()}].getWinID: got winID, but it had the incorrect title"
    elif id == "ERROR_OTHER":
      self.msg = f"tWinManager[{self.processWidget.username.text()}].getWinID: other error<br>{e}"
  
  #----------------------------------------------------------------------------------------------------------
  def probeWinID(self):
    if not self.processWidget.profile.usexdotool.isChecked(): return
    bin = self.processWidget.profile.xdotoolExec.text()
    try:
      out = subprocess.check_output([f"{bin} search --sync --pid {self.processWidget.pid.text()}"], shell=True)
      out = out.decode().strip().split('\n')
      if len(out)==0: return "ERROR_LEN0", None
      for id in out:
        name = subprocess.check_output([f"{bin} getwindowname {id}"], shell=True)
        name = name.decode().strip()
        if name == 'Dungeons and Dragons Online':
          return id, None
      return "ERROR_UNMATCHING_NAME", None
    except Exception as e:
      return "ERROR_OTHER", e
  
    #----------------------------------------------------------------------------------------------------------
  def checkWinID(self):
    if not self.processWidget.profile.usexdotool.isChecked(): return
    bin = self.processWidget.profile.xdotoolExec.text()
    try:
      out = subprocess.check_output([f"{bin} getwindowname {self.processWidget.winID.text()}"], shell=True)
    except:
      return False
    else:
      return True
    
#----------------------------------------------------------------------------------------------------------
def newHeaderLabel(title, width=80):
  hlbl = QLabel(title)
  hlbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
  hlbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  hlbl.setFixedWidth(width)
  return hlbl

#----------------------------------------------------------------------------------------------------------
def newProcessField(title, width=80):
  flbl = QLabel(title)
  flbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
  flbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
  flbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  flbl.setFixedWidth(width)
  return flbl
