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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QRunnable, pyqtSignal, Qt
from cCollapsible import cCollapsible
from tAccount import tAccount
from collections import OrderedDict
import subprocess
import os, time
from util import *

class cProcessManager(cCollapsible):

  def __init__(self, main):
    super().__init__("Process Manager")
    self.main = main
    self.console = main.console
    self.items = OrderedDict()
    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)

    PIDHeader = QLabel("PID")
    winIDLabelHeader = QLabel("WinID")
    worldLabelHeader = QLabel("World")
    usernameHeader = QLabel("Username")
    PIDHeader.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    winIDLabelHeader.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    worldLabelHeader.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
    PIDHeader.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    winIDLabelHeader.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    worldLabelHeader.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    PIDHeader.setFixedWidth(50)
    winIDLabelHeader.setFixedWidth(80)
    worldLabelHeader.setFixedWidth(80)

    h = QHBoxLayout()
    h.addWidget(PIDHeader)
    h.addWidget(winIDLabelHeader)
    h.addWidget(worldLabelHeader)
    h.addWidget(usernameHeader)

    header = QWidget()
    header.setLayout(h)

    self.btnStart   = cProcessManager.newButton(P_ICON_PLAY,  "Start all non-running processes", self.startAll)
    self.btnKill    = cProcessManager.newButton(P_ICON_CLOSE, "Force-kill all running processes", self.killAll)
    self.btnSave    = cProcessManager.newButton(P_ICON_SAVE,  "Save all windows position", self.saveWindowAll)
    self.btnRestore = cProcessManager.newButton(P_ICON_UNDO,  "Restore all previously saved windows positions", self.restoreWindowAll)
    self.btnClear   = cProcessManager.newButton(P_ICON_CLEAR, "Clears all processes", self.clearAll)

    h = QHBoxLayout()
    h.addWidget(quickQLabel("All processes: "))
    h.addWidget(self.btnStart)
    h.addWidget(self.btnSave)
    h.addWidget(self.btnRestore)
    h.addWidget(self.btnClear)
    h.addWidget(self.btnKill)

    buttons = QWidget()
    buttons.setLayout(h)

    self.content = QVBoxLayout()
    self.content.addWidget(header)

    v = QVBoxLayout()
    v.addLayout(self.content)
    v.addWidget(buttons)
    self.body.setLayout(v)

  #----------------------------------------------------------------------------------------------------------
  def clear(self, u):
    item = self.items[u]
    self.layout().removeWidget(item)
    del self.items[u]
    del item
    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)
    for u in self.items.keys():
      self.setColour(self.items[u])

  #----------------------------------------------------------------------------------------------------------
  def clearAll(self):
    allUsernames = set(self.items.keys())
    for u in allUsernames:
      self.clear(u)

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
  def addProcess(self, p):
    self.btnKill.setEnabled(True)
    self.btnSave.setEnabled(True)
    self.btnRestore.setEnabled(True)
    self.btnClear.setEnabled(True)
    self.items[p.account.username] = p
    self.setColour(p)
    self.content.addWidget(p)
  
  #----------------------------------------------------------------------------------------------------------
  def setColour(self,p):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, self.colour2)
    p.setAutoFillBackground(True)
    p.setPalette(pal)
    tmp = self.colour2
    self.colour2 = self.colour1
    self.colour1 = tmp
  
  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def newButton(icon, tooltip, connection):
    btn = QPushButton()
    btn.setIcon(getIcon(icon))
    btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    btn.setEnabled(False)
    btn.setToolTip(tooltip)
    btn.clicked.connect(connection)
    return btn
  
class cProcessItem(QWidget):
  sigGotPID = pyqtSignal(bool)
  sigGotWinID = pyqtSignal(bool)

  P_STATUS_UNKNOWN = 0
  P_STATUS_RUNNING = 1
  P_STATUS_KILLED = 2

  def __init__(self, main, username, world):
    super().__init__()
    self.main = main
    self.account = tAccount(main, username, world)
    self.console = main.console
    self.status = self.P_STATUS_UNKNOWN
    
    self.PIDLabel = QLabel("NA")
    self.winIDLabel = QLabel("NA")
    self.worldLabel = QLabel(self.account.world.name)
    self.usernameLabel = QLabel(self.account.username)
    self.PIDLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.winIDLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.worldLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.usernameLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.PIDLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    self.winIDLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    self.worldLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
    self.PIDLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.winIDLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.worldLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.PIDLabel.setFixedWidth(50)
    self.winIDLabel.setFixedWidth(80)
    self.worldLabel.setFixedWidth(80)
    self.btnToggle  = cProcessManager.newButton(P_ICON_PLAY,      "Toggle (kill/start) process", self.toggle)
    self.btnDetails = cProcessManager.newButton(P_ICON_PROPERTIES,"Prints full commandline with all arguments", self.details)
    self.btnSave    = cProcessManager.newButton(P_ICON_SAVE,      "Save this windows's position", self.saveWindow)
    self.btnRestore = cProcessManager.newButton(P_ICON_UNDO,      "Restore previously saved windows position", self.restoreWindow)
    self.btnClear   = cProcessManager.newButton(P_ICON_CLEAR,     "Toggle (kill/start) process",  self.clear)
    
    h1 = QHBoxLayout()
    h1.addWidget(self.PIDLabel)
    h1.addWidget(self.winIDLabel)
    h1.addWidget(self.worldLabel)
    h1.addWidget(self.usernameLabel)
    h1.addWidget(self.btnToggle)
    h1.addWidget(self.btnSave)
    h1.addWidget(self.btnRestore)
    h1.addWidget(self.btnClear)
    h1.addWidget(self.btnDetails)

    self.setLayout(h1)
    QtCore.QThreadPool.globalInstance().start(self.account)

  
  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    self.btnToggle.setEnabled(True)
    self.btnDetails.setEnabled(True)
    self.btnClear.setEnabled(True)

    self.console.info(f"Launching {C_SILVER}{self.account.username}</font> in {C_SILVER}{self.account.world.name}</font>...")
    outFilename = P_DEFAULT_CONFIGDIR+os.sep+self.account.world.name+"_"+self.account.username+".out"
    if os.path.exists(outFilename): os.rename(outFilename,outFilename+".old")

    arg = self.parseArguments()
    gameExec = self.main.settings.gameExec.text()
    gameDir = os.path.dirname(gameExec)
    gameDir = os.path.dirname(gameDir)
    gameExec = 'x64/dndclient64.exe' #TODO this needs to be done properly, not hard-coded...

    cmd  = f"cd \"{gameDir}\" ; "
    cmd += f"STEAM_ROOT=\"{self.main.settings.steamRoot.text()}\" PROTON_LOG=1 "
    cmd += f"STEAM_COMPAT_DATA_PATH=\"{self.main.settings.protonPrefix}\" "
    cmd += f"STEAM_COMPAT_CLIENT_INSTALL_PATH=\"{self.main.settings.protonPrefix}\" "
    cmd += f"\"{self.main.settings.protonExec}\" run "
    cmd += f"{gameExec} "
    cmd += f"{arg} &> {outFilename}"

    exec = tGameExecutable(cmd)
    QtCore.QThreadPool.globalInstance().start(exec)
    pidw = tPIDWatcher(self, gameExec)
    QtCore.QThreadPool.globalInstance().start(pidw)
    self.sigGotPID.connect(self.autoRestore)
    self.sigGotPID.connect(self.btnSave.setEnabled)
    self.sigGotPID.connect(self.btnRestore.setEnabled)

    self.btnToggle.setIcon(getIcon(P_ICON_STOP))
    self.status = self.P_STATUS_RUNNING
  
  #----------------------------------------------------------------------------------------------------------
  def clear(self):
    self.main.processManager.clear(self.account.username)

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
    time.sleep(2.0)
    self.restoreWindow()

  
#----------------------------------------------------------------------------------------------------------
  def kill(self):
    self.console.info(f"Killing {C_SILVER}{self.account.username}</font> in {C_SILVER}{self.account.world.name}</font>...")
    try:
      out = subprocess.check_output([f"kill -9 {self.PIDLabel.text()}"], shell=True)
    except Exception as e:
      self.console.error(f"cProcessItem.kill: unknown error killing process with PID {self.PIDLabel.text()}", e)

    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
    self.status = self.P_STATUS_KILLED
  
  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.status == self.P_STATUS_RUNNING:
      self.kill()
    else:
      username = self.account.username
      world = self.account.world
      del self.account
      self.account = tAccount(self.main, username, world)
      QtCore.QThreadPool.globalInstance().start(self.account)

  #----------------------------------------------------------------------------------------------------------
  def details(self):
    arg = self.parseArguments()
    self.console.info(f"<br>Arguments for {C_SILVER}{self.account.username}</font>:")
    self.console.info(f"--------------------------------------------------------------")
    self.console.info(arg)
    self.console.info(f"--------------------------------------------------------------")

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
    if not self.main.settings.useHighRes.isEnabled():
      arg += " --HighResOutOfDate"
    return arg

#----------------------------------------------------------------------------------------------------------
class tGameExecutable(QRunnable):
  def __init__(self, exec):
    super().__init__()
    self.exec = exec
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    os.system(self.exec)

#----------------------------------------------------------------------------------------------------------
class tPIDWatcher(QRunnable):
  def __init__(self, processWidget, gameExec):
    super().__init__()
    self.processWidget = processWidget
    self.gameExec = gameExec
    self.subscription = processWidget.account.subscription
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    for i in range(100):
      out = subprocess.check_output([f"ps a -o pid,command | grep {self.processWidget.account.subscription}"], shell=True)
      for line in out.decode().strip().split('\n'):
        line = line.split()
        if line[1] == self.gameExec:
          self.processWidget.PIDLabel.setText(line[0])
          self.processWidget.sigGotPID.emit(True)
          return True
        time.sleep(0.1)
    self.processWidget.console.error("cProcessItem.getPID: could not get PID, process may not be running anymore...")
    self.processWidget.sigGotPID.emit(False)
    return False
  
#----------------------------------------------------------------------------------------------------------
class tWinManager(QRunnable):
  def __init__(self, processWidget, cmd):
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
  # saveWindow
  def saveWindow(self):
    if not self.processWidget.main.settings.usexdotool.isChecked(): return
    bin = self.processWidget.main.settings.xdotoolExec.text()
    for i in range(5):
      try:
        out = subprocess.check_output([f"{bin} getwindowgeometry {self.processWidget.winIDLabel.text()}"], shell=True)
        out = out.decode().strip().split('\n')
        pos = out[1].split()[1].split(',')
        self.processWidget.main.windowsPreferences[self.processWidget.account.username] = (int(pos[0]), int(pos[1]))
        self.processWidget.main.saveWindowsPreferences()
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
    if not self.processWidget.main.settings.usexdotool.isChecked(): return
    bin = self.processWidget.main.settings.xdotoolExec.text()
    self.processWidget.main.loadWindowsPreferences()
    if self.processWidget.account.username in self.processWidget.main.windowsPreferences.keys():
      pos1, pos2 = self.processWidget.main.windowsPreferences[self.processWidget.account.username]
      for i in range(5):
        try:
          out = subprocess.check_output([f"{bin} windowmove --sync {self.processWidget.winIDLabel.text()} {pos1} {pos2}"], shell=True)
        except Exception as e:
          self.getWinID()
        else:
          return
      self.processWidget.console.error("tWinManager.restoreWindow: unknow error trying to load position")

  #----------------------------------------------------------------------------------------------------------
  def getWinID(self):
    id, e = self.probeWinID()
    if not id.startswith("ERROR"): self.processWidget.winIDLabel.setText(id)
    for i in range(20):
      if self.checkWinID():
        self.processWidget.sigGotWinID.emit(True)
        return
      else:
        self.processWidget.winIDLabel.setText("<?>")
        id, e = self.probeWinID()
        if not id.startswith("ERROR"):
          self.processWidget.winIDLabel.setText(id)
        time.sleep(0.2)
        
    self.processWidget.sigGotWinID.emit(False)
    if id == "ERROR_LEN0":
      self.msg = f"tWinManager[{self.processWidget.account.username}].getWinID: failed getting winID, no window with the associated pid {self.PIDLabel.text()}"
    elif id == "ERROR_UNMATCHING_NAME":
      self.msg = f"tWinManager[{self.processWidget.account.username}].getWinID: got winID, but it had the incorrect title"
    elif id == "ERROR_OTHER":
      self.msg = f"tWinManager[{self.processWidget.account.username}].getWinID: other error<br>{e}"
  
  #----------------------------------------------------------------------------------------------------------
  def probeWinID(self):
    if not self.processWidget.main.settings.usexdotool.isChecked(): return
    bin = self.processWidget.main.settings.xdotoolExec.text()
    print(f"========================================================= {bin}")
    try:
      out = subprocess.check_output([f"{bin} search --sync --pid {self.processWidget.PIDLabel.text()}"], shell=True)
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
    if not self.processWidget.main.settings.usexdotool.isChecked(): return
    bin = self.processWidget.main.settings.xdotoolExec.text()
    try:
      out = subprocess.call([f"{bin} getwindowname {self.processWidget.winIDLabel.text()}"], shell=True)
    except:
      return False
    else:
      return True
    
