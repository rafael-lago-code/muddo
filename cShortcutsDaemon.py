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
from PyQt6.QtCore import QRunnable
from cProcess import aProcessItem
from XHelper import XHelper
import subprocess
import os, time
from cWidgets.util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cDDO import cDDO
   from cMainWindow import cMainWindow

P_POST_FOCUS_DELAY = "delay_0.5"

#----------------------------------------------------------------------------------------------------------
class cShortcutsDaemon(aProcessItem):
  def __init__(self, main : cMainWindow):
    super().__init__(main)
    self.key = "scd_"+self.profile.name
    self.daemon = None
    
    self.profileID.setText(self.profile.name)
    self.worldname.setText("")
    self.username.setText("Shortcuts Daemon")
    self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnRemove.setEnabled(True)

    self.sigGotPID.connect(self.updateTooltip)

  #----------------------------------------------------------------------------------------------------------
  def convert(self, consolidated : dict) -> dict:
    parsed = {}
    winID = {}
    for i in self.main.processManager.items.values():
      if i.__class__.__name__ == "cDDO":
        winID[i.username.text()] = i.winID.text()

    self.main.console.debugMessage(f"  Converting shortcuts to backend; winID of active accounts:")
    self.main.console.debugMessage(f"--------------------------------------------------------")
    for k in winID.keys():
      self.main.console.debugMessage(f"  {k}: {winID[k]}")
    self.main.console.debugMessage(f"--------------------------------------------------------")

    # first, get rid of "alls" and "selfs":
    for hk in consolidated.keys():
      if "all" in consolidated[hk].keys():
        for t in winID:
          if t in consolidated[hk].keys():
            consolidated[hk][t] += consolidated[hk]["all"]
          else:
            consolidated[hk][t] = consolidated[hk]["all"]
        del consolidated[hk]["all"]
    winID["self"] = "%WINID_SELF"

    for hk in consolidated.keys():
      parsed[hk] = ""
      for target in consolidated[hk].keys():
        if target not in winID.keys(): continue
        if not consolidated[hk][target]: continue

        parsed[hk] += f" focus_{winID[target]} {P_POST_FOCUS_DELAY} {" ".join(consolidated[hk][target])}"
      if parsed[hk]:
        parsed[hk] = f" {parsed[hk]}"
      else:
        del parsed[hk]

    self.main.console.debugMessage(f"  Shortcuts converted to commands:")
    self.main.console.debugMessage(f"--------------------------------------------------------")
    for hk in parsed.keys():
      self.main.console.debugMessage(f"  {hk} : {parsed[hk]}")
    self.main.console.debugMessage(f"--------------------------------------------------------")
    return parsed
    
  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    parsed = self.convert(self.main.shortcuts.consolidateActiveShortcuts())
    xh = XHelper()
    xh.sigDebugPrinted.connect(self.main.console.debugMessage)
    for hk, script in parsed.items():
      parsed[hk] = lambda x=script : xh.sendKeystrokes(x)

    try:
      self.daemon = xh.getShortcutsDaemon(parsed)
    except Exception as e:
      print(e)
    self.daemon.start()
    self.setStatus("running")
    self.btnToggle.setIcon(getIcon(P_ICON_SKULL))
    self.status = self.P_STATUS_RUNNING
    self.pid.setText("R")

  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.daemon:
      self.btnToggle.setEnabled(False)
      self.daemon.stop()
      # XHelper().forceCleanup()
      self.daemon = None
      self.setStatus("killed")
    else:
      self.launch()

    # exec = tSCDExecutable(self, parsed)
    # QtCore.QThreadPool.globalInstance().start(exec)

    # pidw = tDHPIDWatcher(self, dhexec)
    # QtCore.QThreadPool.globalInstance().start(pidw)

  #----------------------------------------------------------------------------------------------------------
  def updateTooltip(self):
    if self.pid.text().isdecimal():
      text = "<b>Running</b>"
    else:
      text = "<i>Not running</i>"
    self.setToolTip(text)
  
