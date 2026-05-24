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
from μProcess import aProcessItem
from μToolbar import μToolbar, μToolbarItem
from widgets.μOrb import μOrb
from helpers.χHelper import χHelper
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow
from μMilvian import μMilvian

#----------------------------------------------------------------------------------------------------------
class μMacrosDaemon(aProcessItem):
  widgetID = "Macros Daemon"
  process = None
  bridges = {}

  def __init__(self, main : μMainWindow):
    super().__init__()
    self.orb = μOrb("Milvian\nBridge", getIcon('dm_orien'),
                           tooltip="Toggle on/off all shortcuts from all active sets" \
                           "<br><b>Ctrl+Click</b> to purge all shortcuts and restart daemon<br><b><i>Right-click for more options</i></b>")
    self.orb.setCheckable(True)
    # self.orbToggler.setMenu(QMenu("Macros Daemon", self.orbToggler))
    self.menuActionToggle   = self.orb.menu.addAction("Launch Bridges")
    self.menuActionRestart  = self.orb.menu.addAction("Restart Bridges")
    self.menuActionKill     = self.orb.menu.addAction("Kill Bridges")
    self.menuActionPurge    = self.orb.menu.addAction("Purge defunct bridges")
    self.menuActionConf     = self.orb.menu.addAction("Show/Hide setting UI")
    self.menuActionLaunchV2 = self.orb.menu.addAction("Launch v2 (test)")

    self.orb.clicked.connect(self.toggle)
    self.orb.ctrlClicked.connect( lambda : self.restart(purge=True))
    self.menuActionToggle.triggered.connect(self.toggle)
    self.menuActionRestart.triggered.connect(self.restart)
    self.menuActionKill.triggered.connect(lambda : self.terminate(force=True))
    self.menuActionConf.triggered.connect(lambda : main.macros.toggle())
    self.menuActionPurge.triggered.connect(lambda : μMilvian.scanBridges(purgeUnknown=True))
    self.menuActionLaunchV2.triggered.connect(self.launch_v2)
    
    self.profileID.setText("")
    self.worldname.setText("")
    self.username.setText("μDDO")
    # self.updateTooltip()
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnClear.setEnabled(True)
  
  #----------------------------------------------------------------------------------------------------------
  def isInitialized(self):
    return len(self.bridges)>0

  #----------------------------------------------------------------------------------------------------------
  def initialize(self) -> bool:
    if self.isInitialized(): return True
    
    self.bridges = μMilvian.scanBridges(purgeUnknown=False)
    if not self.isInitialized():
      self.main.console.warning("[cMacrosDaemon] failed to initialize cMacrosDaemon")
      return False
    else:
      return True
    
  #----------------------------------------------------------------------------------------------------------
  def getBridges(self, returnMeta=False) -> dict:
    from μMilvian import μMilvianMeta
    if not self.isInitialized():  self.initialize()
    if not self.isInitialized():
      μPrint.warning("[cMacrosDaemon] no valid bridges found. Are Dungeon Helper and Milvian plugin running?")
      return {}
    if returnMeta:
      return self.bridges | {'self': μMilvianMeta.getFocused(), 'any': μMilvianMeta.getAny()}
    else:
      return self.bridges

  #----------------------------------------------------------------------------------------------------------
  def convert(self, consolidated : dict) -> dict:
    bridges = self.getBridges()
    if not bridges: return {}

    parsed = {}
    # first, get rid of "alls" and "selfs":
    for trigger in consolidated.keys():
      if "all" in consolidated[trigger].keys():
        for c in bridges.keys():
          if c in consolidated[trigger].keys():
            consolidated[trigger][c] += consolidated[trigger]["all"]
          else:
            consolidated[trigger][c] = consolidated[trigger]["all"]
        del consolidated[trigger]["all"]
    # winID["self"] = "self"

    for trigger in consolidated.keys():
      parsed[trigger] = []
      for target in consolidated[trigger].keys():
        if target not in bridges.keys(): continue
        if not consolidated[trigger][target]: continue
        action = consolidated[trigger][target]
        if not isinstance(action, list): action = list(action)
        item = lambda t=target,a=action: bridges[t].execute(a)
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

    μPrint.debug(f"  Shortcuts converted to commands:")
    μPrint.debug(f"--------------------------------------------------------")
    for trigger in parsed.keys():
      dbgList = []
      for i in parsed[trigger]:
        if callable(i):
          dbgList.append(f"{i.char}:{i.cmd}")
        else:
          dbgList.append(i)
      μPrint.debug(f"  {trigger} : {dbgList}")
    μPrint.debug(f"--------------------------------------------------------")
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
      μPrint.warning(" Macros Daemon already running through Milvian."+
                                " Try right-click->kill to cleanup state.")
    else:
      consolidatedMacros, meta = self.main.macros.consolidateActiveMacros()
      parsed = self.convert(consolidatedMacros)

      if not parsed:
        μPrint.warning(" Attempting to launch Macros Daemon but no macros found." \
        " Make sure you have macro sets selected and that the relevant accounts are online. No shortcuts daemon" \
        " has been started")
        return
      else:
        toolbarMacros = {k: parsed.pop(k) for k in list(parsed) if k.startswith('toolbar')}

        for hk, script in parsed.items():
          parsed[hk] = lambda x=script: χHelper.execute(x)
        self.process = χHelper.getShortcutsDaemon(parsed)

        if toolbarMacros:
          μPrint.info(f"[cMacrosDaemon] found {len(toolbarMacros.keys())} toolbar macros")
          μToolbar.clearItems()
          for tb, script in toolbarMacros.items():
            m = meta.get(tb, {})
            commands = [cmd for item in script if callable(item) for cmd in item.cmd]
            μToolbar.addItems(μToolbarItem(tb, script,
                                           icon=m.get('icon'),
                                           names=m.get('names', set()),
                                           commands=commands))
          μToolbar.sortLayout()
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
      self.menuActionToggle.setText("Stop")
    else:
      self.orb.setChecked(False)
      self.menuActionToggle.setText("Launch")

  #----------------------------------------------------------------------------------------------------------
  def terminate(self, force=False, remove=False):
    if not self.process: return
    self.process.stop()
    if force: self.cleanup()
    self.setStatus(self.P_STATUS_KILLED)
    self.process = None
    allk = list(self.bridges.keys())
    for k in allk:
      self.bridges[k].close()
      del self.bridges[k]
    self.bridges = {}
    μToolbar.clearItems()
    # if remove: self.clear()

  #----------------------------------------------------------------------------------------------------------
  def restart(self, force=False):
    self.terminate(force)
    self.launch()

  #----------------------------------------------------------------------------------------------------------
  def cleanup(self):
    μPrint.info("Purging all possible shortcuts combinations...")
    μToolbar.clearItems()
    χHelper.forceCleanup()

  #----------------------------------------------------------------------------------------------------------
  def convert_v2(self, consolidated: dict) -> dict:
    from μMilvian import μMilvianMeta
    bridges = self.getBridges()
    if not bridges: return {}

    parsed = {}
    for trigger, actor_map in consolidated.items():
      items = []
      for actor, actions in actor_map.items():
        if not actions:
          continue
        if actor == 'focus':
          item      = lambda a=actions: μMilvianMeta.getFocused().execute(a)
          item.char = 'focus'
          item.cmd  = actions
        elif actor == 'any':
          item      = lambda a=actions: μMilvianMeta.getAny().execute(a)
          item.char = 'any'
          item.cmd  = actions
        elif actor in bridges:
          item      = lambda t=actor, a=actions: bridges[t].execute(a)
          item.char = actor
          item.cmd  = actions
        else:
          μPrint.debug(f'[convert_v2] actor "{actor}" not in bridges, skipping')
          continue
        items.append(item)
      if items:
        parsed[trigger] = items

    μPrint.debug("  [v2] Shortcuts converted:")
    μPrint.debug("--------------------------------------------------------")
    for trigger, items in parsed.items():
      μPrint.debug(f"  {trigger}: {[f'{i.char}:{i.cmd}' for i in items]}")
    μPrint.debug("--------------------------------------------------------")
    return parsed

  #----------------------------------------------------------------------------------------------------------
  def launch_v2(self):
    if self.process:
      μPrint.warning("[v2] Macros Daemon already running. Kill it first.")
      return
    consolidated, meta = self.main.macros.consolidateActiveMacros_v2()
    parsed = self.convert_v2(consolidated)
    if not parsed:
      μPrint.warning("[v2] No macros after consolidation. Check active sets and online accounts.")
      return

    toolbarMacros = {k: parsed.pop(k) for k in list(parsed) if k.startswith('toolbar')}
    for hk, script in parsed.items():
      parsed[hk] = lambda x=script: χHelper.execute(x)
    self.process = χHelper.getShortcutsDaemon(parsed)

    if toolbarMacros:
      μPrint.info(f"[v2] found {len(toolbarMacros)} toolbar macros")
      μToolbar.clearItems()
      for tb, script in toolbarMacros.items():
        m        = meta.get(tb, {})
        commands = [cmd for item in script if callable(item) for cmd in item.cmd]
        μToolbar.addItems(μToolbarItem(tb, script,
                                       icon=m.get('icon'),
                                       names=m.get('names', set()),
                                       commands=commands))
      μToolbar.sortLayout()

    if not self.main.processManager.itemExists(self):
      self.main.processManager.addItem(self)
    self.setStatus(self.P_STATUS_RUNNING)
    self.process.start()
    self.pid.setText("R")


