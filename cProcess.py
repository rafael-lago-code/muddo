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
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import pyqtSignal
from cWidgets.cToggler import cToggler
from collections import OrderedDict
import subprocess
from cWidgets.util import *
from cWidgets.cOrb import cOrbSmall
from XHelper import XHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

class cProcessManager(cToggler):

  def __init__(self, main : cMainWindow):
    self.widgetID = "processManager"
    super().__init__("Process\nManager", P_ICON_PROPERTIES)
    self.main = main
    self.console = main.console
    self.items : OrderedDict[str, aProcessItem] = OrderedDict()
    pal = QPalette()
    self.colour1 = pal.color(QPalette.ColorRole.Window)
    self.colour2 = pal.color(QPalette.ColorRole.AlternateBase)

    header = QWidget()
    header.setLayout(newHLayout([newHeaderLabel("PID", 50), newHeaderLabel("WinID"),\
                     newHeaderLabel("World"), newHeaderLabel("Profile"), "Username"]))

    self.btnStartAll   = cOrbSmall(icon=P_ICON_PLAY,      tooltip="Starts all processes which are not yet already running")
    self.btnKillAll    = cOrbSmall(icon=P_ICON_SKULL_RED, tooltip="Left click: terminates all running processes<br>Ctrl+Left click or Right click: force termination (SIGKILL) all processes")
    self.btnSaveAll    = cOrbSmall(icon=P_ICON_SAVEALL,   tooltip="Saves all windows positions")
    self.btnRestoreAll = cOrbSmall(icon=P_ICON_UNDO,      tooltip="Restores all previously saved windows positions")
    self.btnRemoveAll  = cOrbSmall(icon=P_ICON_CLEARALL,  tooltip="Left click: clear all processes<br>Ctrl+Left click or Right click: kill and clear all processes")
    self.btnMuteAll    = cOrbSmall(icon=P_ICON_MUTE,      tooltip="Toggles audio on/off for all processes")
    self.btnCaptureOrphans = cOrbSmall(icon=getIcon(P_MUDDO_DIR+'/images/chain.png'), tooltip="Attempts to find running instances of DDO and capture them"\
                                     " into our own process manager.\n<b><i>WARNING</i></b>: this will not try to guess which"\
                                     " profile (if any) was used to launch the original DDO instance!")
    
    self.btnCaptureOrphans.clicked.connect(self.main.captureOrphan)
    self.btnStartAll.clicked.connect(self.startAll)
    self.btnKillAll.clicked.connect(self.killAll)
    self.btnKillAll.ctrlClicked.connect(lambda : self.killAll(force=True))
    self.btnKillAll.rightClicked.connect(lambda : self.killAll(force=True))
    self.btnSaveAll.clicked.connect(self.saveWindowAll)
    self.btnRestoreAll.clicked.connect(self.restoreWindowAll)
    self.btnRemoveAll.clicked.connect(self.removeAll)
    self.btnRemoveAll.ctrlClicked.connect(lambda : self.removeAll(True))
    self.btnRemoveAll.rightClicked.connect(lambda : self.removeAll(True))

    # buttons = QWidget()
    # buttons.setLayout()
    
    self.content = newVLayout([header])
    self.setLayout(newVLayout([self.content, newHLayout([self.btnCaptureOrphans,"__stretch__", "All processes: ", self.btnStartAll,\
      self.btnKillAll, self.btnSaveAll, self.btnRestoreAll, self.btnRemoveAll, self.btnMuteAll]),
                    "__stretch__"]))
    

  #----------------------------------------------------------------------------------------------------------
  def removeItem(self, item : aProcessItem, kill=False):
    if kill and item.status == item.P_STATUS_RUNNING:
      try:
        item.kill()
      except Exception as e:
        self.console.error(f"cProcessManager.cleanItem: error killing \"{item.key}\"", e)
    elif item.status == item.P_STATUS_RUNNING:
      return
    
    try:
      self.layout().removeWidget(item)
      del self.items[item.key]
    except Exception as e:
      self.console.error(f"cProcessManager.cleanItem: unknown error removing item \"{item.key}\"", e)

    item.deleteLater()
    self.main.processManager.resetColour()


  #----------------------------------------------------------------------------------------------------------
  def removeAll(self, kill=False):
    allItems  = set(self.items.values())
    for i in allItems: 
      self.removeItem(i,kill)

  #----------------------------------------------------------------------------------------------------------
  def startAll(self):
    for u in self.items.keys(): 
      if u.startswith("dh_"): continue
      if self.items[u].status == aProcessItem.P_STATUS_RUNNING:
        self.items[u].launch()

  #----------------------------------------------------------------------------------------------------------
  def killAll(self, force=False):
    for u in self.items.keys(): 
      if u.startswith("dh_"): continue
      self.items[u].kill(force)
    
  #----------------------------------------------------------------------------------------------------------
  def saveWindowAll(self):
    for u in self.items.keys(): self.items[u].saveWindow()
  
  #----------------------------------------------------------------------------------------------------------
  def restoreWindowAll(self):
    for u in self.items.keys(): self.items[u].restoreWindow()

  #----------------------------------------------------------------------------------------------------------
  def addItem(self, p : aProcessItem):
    self.btnKillAll.setEnabled(True)
    self.btnSaveAll.setEnabled(True)
    self.btnRestoreAll.setEnabled(True)
    self.btnRemoveAll.setEnabled(True)
    self.items[p.key] = p
    self.setColour(p)
    self.content.addWidget(p)

  #----------------------------------------------------------------------------------------------------------
  def isPIDManaged(self, pid : str) -> bool:
    for i in self.items.values():
      if i.pid.text() == pid: return True
    return False
  
  #----------------------------------------------------------------------------------------------------------
  def setColour(self,p : aProcessItem):
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
class aProcessItem(QWidget):
  sigRunning = pyqtSignal(bool)
  sigGotPID = pyqtSignal(bool)
  sigTerminated = pyqtSignal(bool)

  P_STATUS_ERROR   = -1
  P_STATUS_UNKNOWN = 0
  P_STATUS_AUTHENTICATING    = 1
  P_STATUS_QUEUEING   = 2
  P_STATUS_RUNNING = 3
  P_STATUS_KILLED  = 4

  def __init__(self, main : cMainWindow):
    super().__init__()
    self.main = main
    self.console = main.console
    self.status = self.P_STATUS_UNKNOWN
    self.profile = main.profile() # yes, we freeze the profile here!
    self.key = ""
    
    self.pid = newProcessField("", 50)
    self.winID = newProcessField("")
    self.profileID = newProcessField("")
    self.worldname = newProcessField("")
    self.username = QLabel()

    self.btnToggle  = cOrbSmall(icon=P_ICON_PLAY,  tooltip="Toggles launch/terminate process.<br>Right click or ctrl click to force kill (SIGKILL)")
    self.btnSave    = cOrbSmall(icon=P_ICON_SAVE,  tooltip="Save this windows's position")
    self.btnRestore = cOrbSmall(icon=P_ICON_UNDO,  tooltip="Restore previously saved windows position")
    self.btnRemove  = cOrbSmall(icon=P_ICON_TRASH, tooltip="Left click: Removes this process from the list of processes.<br>Right click or ctrl click: force kill and remove")
    self.btnMute    = cOrbSmall(icon=P_ICON_MUTE,  tooltip="Toggles audio on/off for this process")
    self.btnToggle.clicked.connect(self.toggle)
    self.btnToggle.rightClicked.connect(lambda : self.toggle(True))
    self.btnToggle.ctrlClicked.connect(lambda : self.toggle(True))
    self.btnSave.clicked.connect(self.saveWindow)
    self.btnRestore.clicked.connect(self.restoreWindow)
    self.btnRemove.clicked.connect(self.remove)
    self.btnRemove.ctrlClicked.connect(lambda : self.remove(True))
    self.btnRemove.rightClicked.connect(lambda : self.remove(True))
    self.btnMute.clicked.connect(self.audioToggle)

    self.sigTerminated.connect(lambda : self.setStatus(aProcessItem.P_STATUS_KILLED))
    
    self.setLayout(newHLayout([self.pid, self.winID, self.worldname, self.profileID, 
                              self.username, self.btnToggle, self.btnSave, self.btnRestore,
                              self.btnRemove, self.btnMute]))
  
  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def remove(self, kill=False):
    self.main.processManager.removeItem(self, kill)
  
  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def audioToggle(self):
    if XHelper().isPIDMuted(self.pid):
      self.console.info(f"{C_SILVER}Muting</font> {self.pid}...")
      XHelper().unmutePID(self.pid)
      self.btnMute.setIcon(getIcon(P_ICON_UNMUTE))
    else:
      self.console.info(f"{C_SILVER}Unmuting</font> {self.pid}...")
      XHelper().mutePID(self.pid)
      self.btnMute.setIcon(getIcon(P_ICON_MUTE))

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, status):
    if status == "running" or status == aProcessItem.P_STATUS_RUNNING: 
      self.status = aProcessItem.P_STATUS_RUNNING
      self.btnSave.setEnabled(True)
      self.btnRestore.setEnabled(True)
      self.btnToggle.setEnabled(True)
      self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
      self.btnRemove.setEnabled(True)
    elif status == "killed" or status == aProcessItem.P_STATUS_KILLED:
      self.pid.setText("")
      self.winID.setText("")
      self.btnSave.setEnabled(False)
      self.btnRestore.setEnabled(False)
      self.btnToggle.setEnabled(True)
      self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
      self.status = self.P_STATUS_UNKNOWN
    elif status == "error" or status == aProcessItem.P_STATUS_ERROR:
      self.username.setText(f"C_RED{self.username.text()}[E]</font>")
      self.btnSave.setEnabled(False)
      self.btnRestore.setEnabled(False)
      self.btnToggle.setEnabled(False)
      self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
      self.status = self.P_STATUS_UNKNOWN


  # #----------------------------------------------------------------------------------------------------------
  # def clean(self):
  #   # this should be called when the job has already died (i.e. user closed the window)
  #   self.pid.setText("")
  #   self.winID.setText("")
  #   self.btnSave.setEnabled(False)
  #   self.btnRestore.setEnabled(False)
  #   self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
  #   self.status = self.P_STATUS_UNKNOWN

  #----------------------------------------------------------------------------------------------------------
  def kill(self, force=False):
    if not force and not self.pid.text().isdigit(): return
    if self.worldname.text():
      self.console.info(f"Killing {C_SILVER}{self.username.text()}</font> in {C_SILVER}{self.worldname.text()}</font>...")
    else:
      self.console.info(f"Killing {C_SILVER}{self.username.text()}</font>, PID={C_SILVER}{self.pid.text()}</font>...")
    signal = "-9" if force else "-15"
    try:
      out = subprocess.check_output([f"kill {signal} {self.pid.text()}"], shell=True)
    except Exception as e:
      self.console.error(f"aProcessItem.kill: unknown error killing (signal: {signal})process with PID {self.pid.text()}", e)
      self.status = self.P_STATUS_ERROR
    else:
      self.setStatus(aProcessItem.P_STATUS_KILLED)
  
  #----------------------------------------------------------------------------------------------------------
  def toggle(self, force=False):
    if self.status == self.P_STATUS_RUNNING:
      self.kill(force)
    else:
      self.launch()

