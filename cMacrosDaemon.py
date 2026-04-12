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
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from cProcess import aProcessItem
from widgets.cOrb import cOrb
from helpers.XHelper import XHelper
from helpers.util import *
from helpers.cPrint import cPrint
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow
from cMilvian import cMilvian

P_POST_FOCUS_DELAY = "delay_0.01"

#----------------------------------------------------------------------------------------------------------
class cMacrosDaemon(aProcessItem):
  def __init__(self, main : cMainWindow):
    super().__init__()
    self.key = "Macros Daemon"
    self.process = None
    self.milvianProc = None

    self.orb = cOrb("Macros\nDaemon", P_ICON_GEARLOOP,
                           tooltip="Toggle on/off all shortcuts from all active sets" \
                           "<br><b>Ctrl+Click</b> to purge all shortcuts and restart daemon<br><b><i>Right-click for more options</i></b>")
    self.orb.setCheckable(True)
    # self.orbToggler.setMenu(QMenu("Macros Daemon", self.orbToggler))
    self.actionToggle  = self.orb.menu.addAction("Launch Daemon")
    self.actionRestart = self.orb.menu.addAction("Restart Daemon")
    self.actionKill    = self.orb.menu.addAction("Kill Daemon")
    self.actionConf    = self.orb.menu.addAction("Show/Hide setting UI")

    self.orb.clicked.connect(self.toggle)
    self.orb.ctrlClicked.connect( lambda : self.restart(purge=True))
    self.actionToggle.triggered.connect(self.toggle)
    self.actionRestart.triggered.connect(self.restart)
    self.actionKill.triggered.connect(lambda : self.terminate(force=True))
    self.actionConf.triggered.connect(lambda : main.macros.toggle())
    
    self.profileID.setText("")
    self.worldname.setText("")
    self.username.setText("μDDO")
    # self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnClear.setEnabled(True)

  #----------------------------------------------------------------------------------------------------------
  def convert(self, consolidated : dict) -> dict:
    parsed = {}
    if not self.milvianProc: self.milvianProc = cMilvian.getFromDir(purgeUnknown=False)
    if len(self.milvianProc) == 0:
      self.main.console.warning("Attempted to start Macro Daemon, but no valid bridges found. Are Dungeon Helper and Milvian plugin running?")
      return {}

    # first, get rid of "alls" and "selfs":
    for trigger in consolidated.keys():
      if "all" in consolidated[trigger].keys():
        for c in self.milvianProc.keys():
          if c in consolidated[trigger].keys():
            consolidated[trigger][c] += consolidated[trigger]["all"]
          else:
            consolidated[trigger][c] = consolidated[trigger]["all"]
        del consolidated[trigger]["all"]
    # winID["self"] = "self"

    for trigger in consolidated.keys():
      parsed[trigger] = []
      for target in consolidated[trigger].keys():
        if target not in self.milvianProc.keys(): continue
        if not consolidated[trigger][target]: continue
        action = consolidated[trigger][target]
        if not isinstance(action, list): action = list(action)
        item = lambda t=target,a=action: self.milvianProc[t].sendList(a)
        item.char = target
        item.cmd = action
        parsed[trigger].append(item)
        # for k in consolidated[trigger][target]:
        #   if k.startswith("sleep") or k.startswith("focus") or k.startswith("point") or k.startswith("click"):
        #     parsed[trigger].append(k)
        #   else:
        #     item = lambda t=target,x=k: self.milvianProc[t].sendInputAction(x)
        #     item.char = target
        #     item.cmd = k
        #     parsed[trigger].append(item)

      if not parsed[trigger]:
        del parsed[trigger]

    self.main.console.debugMessage(f"  Shortcuts converted to commands:")
    self.main.console.debugMessage(f"--------------------------------------------------------")
    for trigger in parsed.keys():
      dbgList = []
      for i in parsed[trigger]:
        if callable(i):
          dbgList.append(f"{i.char}:{i.cmd}")
        else:
          dbgList.append(i)
      self.main.console.debugMessage(f"  {trigger} : {dbgList}")
    self.main.console.debugMessage(f"--------------------------------------------------------")
    return parsed

  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.status == self.P_STATUS_RUNNING:
      self.terminate()
    else:
      self.launch()

  #----------------------------------------------------------------------------------------------------------
  def launch(self):
    if self.process:
      cPrint.warning(" Attempting to launch Macros Daemon when one is already running."+
                                " Try right-click->kill to cleanup state.")
    else:
      parsed = self.convert(self.main.macros.consolidateActiveMacros())
      if not parsed:
        cPrint.warning(" Attempting to launch Macros Daemon but no macros found." \
        " Make you have macro sets selected and that the relevant accounts are online before starting" \
        " the Macros Daemon")
        return
      else:
        xh = XHelper()
        for hk, script in parsed.items():
          parsed[hk] = lambda x=script : xh.execute(x)
        self.process = xh.getShortcutsDaemon(parsed)
    if not self.main.processManager.itemExists(self):
      self.main.processManager.addItem(self)
    self.setStatus(self.P_STATUS_RUNNING)
    self.process.start()
    self.pid.setText("R")

  #----------------------------------------------------------------------------------------------------------
  def setStatus(self, status):
    super().setStatus(status)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnAudio.setEnabled(False)
    if status == aProcessItem.P_STATUS_RUNNING:
      self.orb.setChecked(True)
      self.actionToggle.setText("Stop")
    else:
      self.orb.setChecked(False)
      self.actionToggle.setText("Launch")

  #----------------------------------------------------------------------------------------------------------
  def terminate(self, force=False, remove=False):
    if not self.process: return
    self.process.stop()
    if force: self.cleanup()
    self.setStatus(self.P_STATUS_KILLED)
    self.process = None
    allk = list(self.milvianProc.keys())
    for k in allk:
      self.milvianProc[k].close()
      del self.milvianProc[k]
    self.milvianProc = None
    # if remove: self.clear()

  #----------------------------------------------------------------------------------------------------------
  def restart(self, force=False):
    self.terminate(force)
    self.launch()

  #----------------------------------------------------------------------------------------------------------
  def cleanup(self):
    cPrint.info("Purging all possible shortcuts combinations...")
    XHelper().forceCleanup()

  
