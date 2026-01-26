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
from __future__ import annotations
from PyQt6.QtCore import QRunnable
import subprocess
import time
from cWidgets.util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cDDO import cDDO


class tWinManager(QRunnable):
  def __init__(self, ddo : cDDO, cmd):
    super().__init__()
    self.ddo = ddo
    self.cmd = cmd
    self.bin = ddo.frozenProfile.xdotoolExec.text()
    self.msg = ""
  
  #----------------------------------------------------------------------------------------------------------
  def run(self):
    if not self.ddo.frozenProfile.usexdotool.isChecked(): return
    if self.cmd == "getWinID":
      self.getWinID()
    elif self.cmd == "restoreWindow":
      self.restoreWindow()
    elif self.cmd == "saveWindow":
      self.saveWindow()

  #----------------------------------------------------------------------------------------------------------
  def saveWindow(self):
    e = None
    for i in range(5):
      try:
        out = subprocess.check_output([f"{self.bin} getwindowgeometry {self.ddo.winID.text()}"], shell=True)
        out = out.decode().strip().split('\n')
        pos = out[1].split()[1].split(',')
        self.ddo.frozenProfile.windowsPreferences[self.ddo.username.text()] = (int(pos[0]), int(pos[1]))
        self.ddo.frozenProfile.save()
      except Exception as e:
        self.getWinID()
      else:
        return
    self.ddo.console.error("tWinManager.saveWindow: unknow error trying to save position info", e)

  #----------------------------------------------------------------------------------------------------------
  # restoreWindow
  #    Tries to restore window preferences. It always checks the WinID again because these change 
  #    every now and then, which is weird. It will loop a few times until it gets a valid winID.
  def restoreWindow(self):
    if self.ddo.username.text() in self.ddo.frozenProfile.windowsPreferences.keys():
      pos1, pos2 = self.ddo.frozenProfile.windowsPreferences[self.ddo.username.text()]
      for i in range(5):
        try:
          out = subprocess.check_output([f"{self.bin} windowmove --sync {self.ddo.winID.text()} {pos1} {pos2}"], shell=True)
        except Exception as e:
          self.getWinID()
        else:
          return
      self.ddo.console.error("tWinManager.restoreWindow: unknow error trying to load position")

  #----------------------------------------------------------------------------------------------------------
  def getWinID(self):
    id, e = self.probeWinID()
    if not id.startswith("ERROR"): self.ddo.winID.setText(id)
    for i in range(20):
      if self.checkWinID():
        self.ddo.sigGotWinID.emit(True)
        return
      else:
        self.ddo.winID.setText("")
        id, e = self.probeWinID()
        if not id.startswith("ERROR"):
          self.ddo.winID.setText(id)
        time.sleep(0.2)
        
    self.ddo.sigGotWinID.emit(False)
    if id == "ERROR_LEN0":
      self.msg = f"tWinManager[{self.ddo.username.text()}].getWinID: failed getting winID, no window with the associated pid {self.pid.text()}"
    elif id == "ERROR_UNMATCHING_NAME":
      self.msg = f"tWinManager[{self.ddo.username.text()}].getWinID: got winID, but it had the incorrect title"
    elif id == "ERROR_OTHER":
      self.msg = f"tWinManager[{self.ddo.username.text()}].getWinID: other error<br>{e}"
  
  #----------------------------------------------------------------------------------------------------------
  def probeWinID(self):
    worldPrefix = self.ddo.world.name.split(" ")[0]
    try:
      out = subprocess.check_output([f"{self.bin} search --sync --pid {self.ddo.pid.text()}"], shell=True)
      out = out.decode().strip().split('\n')
      if len(out)==0: return "ERROR_LEN0", None
      for id in out:
        name = subprocess.check_output([f"{self.bin} getwindowname {id}"], shell=True)
        name = name.decode().strip()
        if name == 'Dungeons and Dragons Online' or worldPrefix in name:
          return id, None
      return "ERROR_UNMATCHING_NAME", None
    except Exception as e:
      return "ERROR_OTHER", e
  
    #----------------------------------------------------------------------------------------------------------
  def checkWinID(self):
    try:
      out = subprocess.check_output([f"{self.bin} getwindowname {self.ddo.winID.text()}"], shell=True)
    except:
      return False
    else:
      return True
    