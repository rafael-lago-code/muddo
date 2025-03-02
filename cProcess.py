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
from tAuthenticator import tAuthenticator
from collections import OrderedDict
import subprocess
import os, time
from util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow
   from cDDO import cDDO
   from cWorlds import cWorld

class cProcessManager(cTab):

  def __init__(self, main : cMainWindow):
    super().__init__("Process Manager")
    self.main = main
    self.console = main.console
    self.items : OrderedDict[str, cDDO] = OrderedDict()
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
    buttons.setLayout(newHLayout(["__stretch__", "All processes: ", self.btnStart,\
      self.btnKill, self.btnSave, self.btnRestore, self.btnClear]))
    
    self.content = newVLayout([header])
    self.setLayout(newVLayout([self.content, buttons]))
    

  #----------------------------------------------------------------------------------------------------------
  def removeProcess(self, item : aProcessItem):
    try:
      item.kill()
      item.sigTerminated.disconnect()
      self.layout().removeWidget(item)
      del self.items[item.key]
    except Exception as e:
      self.console.error(f"cProcessManager.removeItem: unknown error removing item \"{item.key}\"", e)

    item.deleteLater()
    self.main.processManager.resetColour()

  #----------------------------------------------------------------------------------------------------------
  def removeAll(self):
    allItems = set(self.items.values())
    for i in allItems: self.removeProcess(i)

  #----------------------------------------------------------------------------------------------------------
  def startAll(self):
    for u in self.items.keys(): 
      if self.items[u].status == cDDO.P_STATUS_RUNNING:
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
  def addProcess(self, p : cDDO):
    self.btnKill.setEnabled(True)
    self.btnSave.setEnabled(True)
    self.btnRestore.setEnabled(True)
    self.btnClear.setEnabled(True)
    self.items[p.key] = p
    self.setColour(p)
    self.content.addWidget(p)
  
  #----------------------------------------------------------------------------------------------------------
  def setColour(self,p : cDDO):
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
    
    self.pid = newProcessField("NA", 50)
    self.winID = newProcessField("NA")
    self.profileID = newProcessField("")
    self.worldname = newProcessField("")
    self.username = QLabel()

    self.btnToggle  = newToolbarButton(P_ICON_PLAY,  "Toggle (kill/start) process", self.toggle)
    self.btnSave    = newToolbarButton(P_ICON_SAVE,  "Save this windows's position", self.saveWindow)
    self.btnRestore = newToolbarButton(P_ICON_UNDO,  "Restore previously saved windows position", self.restoreWindow)
    self.btnRemove  = newToolbarButton(P_ICON_TRASH, "Removes this process from the list of processes",  self.remove)

    self.sigTerminated.connect(self.clean)
    
    self.setLayout(newHLayout([self.pid, self.winID, self.worldname, self.profileID, 
                              self.username, self.btnToggle, self.btnSave, self.btnRestore,
                              self.btnRemove]))
  
  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def remove(self):
    self.main.processManager.removeProcess(self)
  
  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def restoreWindow(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def clean(self):
    # this should be called when the job has already died (i.e. user closed the window)
    self.pid.setText("NA")
    self.winID.setText("NA")
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnToggle.setIcon(getIcon(P_ICON_PLAY))
    self.status = self.P_STATUS_UNKNOWN

  #----------------------------------------------------------------------------------------------------------
  def kill(self):
    if self.pid.text() == "NA": return
    self.console.info(f"Killing {C_SILVER}{self.username.text()}</font> in {C_SILVER}{self.worldname.text()}</font>...")
    try:
      out = subprocess.check_output([f"kill -9 {self.pid.text()}"], shell=True)
    except Exception as e:
      self.console.error(f"cDDO.kill: unknown error killing process with PID {self.pid.text()}", e)

    self.clean()
    self.status = self.P_STATUS_KILLED
  
  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.status == self.P_STATUS_RUNNING:
      self.kill()
    else:
      self.launch()

