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
from μMilvian import μMilvian, μMilvianMeta

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M I L V I A N   B R I D G E
#
#   This is just giving some UI to start/stop the bridges.
#   
#   This is a hybrid class.
#   One instance lives in cMainWindow. __init__ creates the widgets, the rest is supposed to be done
#   via class methods
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMilvianBridge(aProcessItem):
  widgetID = "Milvian Bridge"
  process  = None
  _widget  = None   # singleton instance reference

  def __init__(self, main : μMainWindow):
    super().__init__()
    μMilvianBridge._widget = self
    self.orb = μOrb("Milvian\nBridge", getIcon('dm_orien'),
                           tooltip="Toggle on/off all shortcuts from all active sets" \
                           "<br><b>Ctrl+Click</b> to purge all shortcuts and restart daemon<br><b><i>Right-click for more options</i></b>")
    self.orb.setCheckable(True)
    self.menuActionToggle   = self.orb.menu.addAction("Launch Bridges")
    self.menuActionRestart  = self.orb.menu.addAction("Restart Bridges")
    self.menuActionKill     = self.orb.menu.addAction("Kill Bridges")
    self.menuActionPurge    = self.orb.menu.addAction("Purge defunct bridges")
    self.menuActionConf     = self.orb.menu.addAction("Show/Hide setting UI")
    self.orb.clicked.connect(μMilvianBridge.toggle)
    self.orb.ctrlClicked.connect(lambda: μMilvianBridge.restart(purge=True))
    self.menuActionToggle.triggered.connect(μMilvianBridge.toggle)
    self.menuActionRestart.triggered.connect(μMilvianBridge.restart)
    self.menuActionKill.triggered.connect(lambda: μMilvianBridge.terminate(force=True))
    self.menuActionConf.triggered.connect(lambda: main.macros.toggle())
    self.menuActionPurge.triggered.connect(lambda: μMilvian.scanBridges(purgeUnknown=True))

    self.profileID.setText("")
    self.worldname.setText("")
    self.username.setText("μDDO")
    self.btnToggle.setEnabled(True)
    self.btnSave.setEnabled(False)
    self.btnRestore.setEnabled(False)
    self.btnClear.setEnabled(True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def toggle(cls):
    if cls._widget and cls._widget.status == aProcessItem.P_STATUS_RUNNING:
      cls.terminate()
    else:
      cls.launch()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def terminate(cls, force=False, remove=False):
    if not cls.process: return
    cls.process.stop()
    if force: cls.cleanup()
    if cls._widget: cls._widget.setStatus(aProcessItem.P_STATUS_KILLED)
    cls.process = None
    μMilvianMeta.closeBridges()
    μToolbar.clearItems()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def restart(cls, force=False, purge=False):
    cls.terminate(force or purge)
    cls.launch()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def cleanup(cls):
    μPrint.info("Purging all possible shortcuts combinations...")
    μToolbar.clearItems()
    χHelper.forceCleanup()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def launch(cls):
    from μMacros import μMacroRegistry
    if cls.process:
      μPrint.warning("[μMilvianBridge] already running. Kill it first.")
      return
    bridges = μMilvianMeta.getBridges()
    if not bridges: return

    triggers = {}
    μMacroRegistry.consolidateAll()
    for trigger, scripts in μMacroRegistry.consolidatedTriggers.items():
      if trigger == "none": continue
      ft = μMacroRegistry.finalizeScript(scripts, bridges)
      if ft is not None and ft.items: triggers[trigger] = ft

    if not triggers:
      μPrint.warning("[μMilvianBridge] no macros after finalization. Check active sets and online accounts.")
      return

    toolbarMacros = {k: triggers.pop(k) for k in list(triggers) if k.startswith('toolbar')}
    for hk, ft in triggers.items():
      triggers[hk] = lambda x=ft.items: χHelper.execute(x)
    cls.process = χHelper.getShortcutsDaemon(triggers)

    if toolbarMacros:
      μPrint.info(f"[μMilvianBridge] found {len(toolbarMacros)} toolbar macros")
      μToolbar.clearItems()
      for tb, ft in toolbarMacros.items():
        commands = [cmd for item in ft.items for cmd in item.cmd]
        μToolbar.addItems(μToolbarItem(tb, ft.items, icon=ft.icon, names=ft.names, commands=commands))
      μToolbar.sortLayout()

    if cls._widget:
      if not cls.main.processManager.itemExists(cls._widget):
        cls.main.processManager.addItem(cls._widget)
      cls._widget.setStatus(aProcessItem.P_STATUS_RUNNING)
      cls._widget.pid.setText("R")
    cls.process.start()


