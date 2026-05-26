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
    self.orb.clicked.connect(self.toggle)
    self.orb.ctrlClicked.connect( lambda : self.restart(purge=True))
    self.menuActionToggle.triggered.connect(self.toggle)
    self.menuActionRestart.triggered.connect(self.restart)
    self.menuActionKill.triggered.connect(lambda : self.terminate(force=True))
    self.menuActionConf.triggered.connect(lambda : main.macros.toggle())
    self.menuActionPurge.triggered.connect(lambda : μMilvian.scanBridges(purgeUnknown=True))
    
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
  def getBridges(self) -> dict:
    if not self.isInitialized():  self.initialize()
    if not self.isInitialized():
      μPrint.warning("[cMacrosDaemon] no valid bridges found. Are Dungeon Helper and Milvian plugin running?")
      return {}
    return self.bridges

  #----------------------------------------------------------------------------------------------------------
  def toggle(self):
    if self.status == self.P_STATUS_RUNNING:
      self.terminate()
    else:
      self.launch()

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
  def launch(self):
    from μMacros import μMacroRegistry
    if self.process:
      μPrint.warning("[μMacrosDaemon] already running. Kill it first.")
      return
    bridges = self.getBridges()
    if not bridges: return

    triggers = {}
    for trigger, scripts in μMacroRegistry.consolidatedTriggers.items():
      if trigger == "none": continue
      ft = μMacroRegistry.finalizeScript(scripts, bridges)
      if ft is not None and ft.items: triggers[trigger] = ft

    if not triggers:
      μPrint.warning("[μMacrosDaemon] no macros after finalization. Check active sets and online accounts.")
      return

    toolbarMacros = {k: triggers.pop(k) for k in list(triggers) if k.startswith('toolbar')}
    for hk, ft in triggers.items():
      triggers[hk] = lambda x=ft.items: χHelper.execute(x)
    self.process = χHelper.getShortcutsDaemon(triggers)

    if toolbarMacros:
      μPrint.info(f"[μMacrosDaemon] found {len(toolbarMacros)} toolbar macros")
      μToolbar.clearItems()
      for tb, ft in toolbarMacros.items():
        commands = [cmd for item in ft.items for cmd in item.cmd]
        μToolbar.addItems(μToolbarItem(tb, ft.items, icon=ft.icon, names=ft.names, commands=commands))
      μToolbar.sortLayout()

    if not self.main.processManager.itemExists(self):
      self.main.processManager.addItem(self)
    self.setStatus(self.P_STATUS_RUNNING)
    self.process.start()
    self.pid.setText("R")


