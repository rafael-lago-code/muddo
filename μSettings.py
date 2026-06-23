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
from PyQt6.QtWidgets import QComboBox, QTabWidget, QStackedWidget
from PyQt6.QtCore import pyqtSignal
from widgets.μCombo import μCheckCombo, μCombo
from μSettingsProfile import μSettingsProfile
from helpers.μPrint import μPrint
from widgets.μOrb import μOrbSmall
from helpers.μImageFactory import *
from widgets.μFloating import μToggler
import os, glob, shutil
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μMainWindow import μMainWindow

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  S E T T I N G S
#
#   This is a hybrid class.
#   One instance lives in cMainWindow. __init__ calls cSettings.setup. Most of the time just use it as a
#   static class, use cSettings.widget for the instance.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μSetup(μToggler):
  widget : μSetup = None
  sigProfileChanged = pyqtSignal(μSettingsProfile, str)
  widgetID = "Setup"
  lastProfile : str = ""
  profiles : dict[str, μSettingsProfile] = {}
  tabs        = None  # QTabWidget
  stacks      = []    # [QStackedWidget x5] — Launcher/XAudio/Plugins/Toolbar/Map
  profileList = None  # QComboBox
  profileMain = None  # QComboBox
  profile = None


  SECTION_NAMES = ["Launcher", "X && Audio", "Plugins", "Toolbar", "Map"]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setup(cls, widget : μSetup):
    cls.widget = widget
    cls.profileMain = μCombo()
    cls.profileMain.setMinimumWidth(200)
    cls.profileList = μCombo()
    cls.profileList.setEditable(True)
    cls.profileList.setMinimumWidth(200)
    cls.stacks = [QStackedWidget() for _ in cls.SECTION_NAMES]
    cls.tabs = QTabWidget()
    cls.tabs.setStyleSheet("""
      QTabWidget::pane { background: rgba(40, 40, 40, 120); border: none; }
      QTabBar::tab {
          background: rgba(40, 40, 40, 120);
          color: white;
          padding: 4px 8px;
          border: none;
      }
      QTabBar::tab:selected {
          background: rgba(84, 19, 8, 220);
      }
      QTabBar::tab:hover:!selected {
          background: rgba(80, 80, 80, 180);
      }
    """)
    for name, stack in zip(cls.SECTION_NAMES, cls.stacks):
      cls.tabs.addTab(stack, name)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def addProfile(cls, name):
    if cls.profiles.get(name): return
    try:
      newProfile = μSettingsProfile(name)
      cls.profiles[name] = newProfile
      for stack, w in zip(cls.stacks, newProfile.sectionWidgets()):
        stack.addWidget(w)
      cls.profileList.addItem(name)
      cls.profileMain.addItem(name)
    except Exception as e:
      μPrint.error(f"[cSettings] failed to load profile \"{name}\". Skipping it...", e)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWidget(cls) -> μSetup:
    return cls.widget

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def syncProfileLists(cls, source="setup"):
    try:
      cls.profileList.currentIndexChanged.disconnect()
      cls.profileMain.currentIndexChanged.disconnect()
    except: pass

    if source=="setup":
      name = cls.profileList.currentText()
      idx = cls.profileList.currentIndex()
      cls.profileMain.setCurrentIndex(idx)
    else:
      name = cls.profileMain.currentText()
      idx = cls.profileMain.currentIndex()
      cls.profileList.setCurrentIndex(idx)

    cls.profileList.currentIndexChanged.connect(lambda : cls.syncProfileLists("setup"))
    cls.profileMain.currentIndexChanged.connect(lambda : cls.syncProfileLists("main"))

    if not name: return
    if name in cls.profiles.keys():
      μSetup.switchProfile(name)
    else:
      μPrint.warning(f"Trying to change to profile \"{name}\", but it was not found! Doing nothing instead...")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def switchProfile(cls, name):
    cls.profile   = cls.profiles[name]
    cls.launcher  = cls.profiles[name].launcher
    cls.xsettings = cls.profiles[name].xsettings
    cls.plugins   = cls.profiles[name].plugins
    cls.session   = cls.profiles[name].session
    cls.toolbar   = cls.profiles[name].toolbar
    cls.map       = cls.profiles[name].map

    idx = cls.stacks[0].indexOf(cls.profiles[name].wLauncher)
    for stack in cls.stacks:
      stack.setCurrentIndex(idx)
    # cls.main.patch.updateTimestamp()
    cls.widget.sigProfileChanged.emit(cls.profiles[name], cls.lastProfile)
    cls.lastProfile = name

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, main : μMainWindow):
    super().__init__("&Setup", P_ICON_GEARSTACK, main)
    self.toggler.setToolTip("Toggle Setup UI")
    self.main = main
    μSetup.setup(self)

    profileLbl = QLabel("Profile: ")
    profileLbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

    self.btnDuplicateProfile = μOrbSmall(icon=P_ICON_DUPDOC, tooltip="Duplicate current settings and profile into a new one.<br>You can rename it directly from the ComboBox after creating it.")
    self.btnRemoveProfile = μOrbSmall(icon=P_ICON_TRASH, tooltip="Delete current profile and its associated files (main settings remain untouched)")

    self.setLayout(newVLayout([self.tabs, newHLayout(["__stretch__", "Profile: ", self.profileList, self.btnDuplicateProfile,
                               self.btnRemoveProfile, "__stretch__"])]))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def _confPath(name):
    return P_DEFAULT_CONFIGDIR + os.sep + f"profile_{name}.conf"

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def initialize(self):
    self.load()
    super().initialize()
    self.tabs.insertTab(0, self.main.credentials, "Accounts")
    self.tabs.setCurrentIndex(0)
    self.btnDuplicateProfile.clicked.connect(self.duplicateProfile)
    self.btnRemoveProfile.clicked.connect(self.removeProfile)
    self.profileList.currentIndexChanged.connect(lambda : μSetup.syncProfileLists("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : μSetup.syncProfileLists("main"))
    self.profileList.lineEdit().editingFinished.connect(self.renameProfile)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _selectProfile(self, name):
    try:
      self.profileList.currentIndexChanged.disconnect()
      self.profileMain.currentIndexChanged.disconnect()
    except: pass
    idx = self.profileList.findText(name)
    self.profileList.setCurrentIndex(-1)
    self.profileList.setCurrentIndex(idx)
    self.profileMain.setCurrentIndex(-1)
    self.profileMain.setCurrentIndex(idx)
    self.profileList.currentIndexChanged.connect(lambda : μSetup.syncProfileLists("settings"))
    self.profileMain.currentIndexChanged.connect(lambda : μSetup.syncProfileLists("main"))
    μSetup.switchProfile(name)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def removeProfile(self):
    name = μSetup.lastProfile
    if not name: return
    try:
      profile = μSetup.profiles.pop(name, None)
      if profile:
        for stack, w in zip(μSetup.stacks, profile.sectionWidgets()):
          stack.removeWidget(w)
      for combo in [self.profileList, self.profileMain]:
        idx = combo.findText(name)
        if idx >= 0: combo.removeItem(idx)
      os.remove(self._confPath(name))
      μPrint.info(f"[cSettings] removed profile \"{name}\"")
    except Exception as e:
      μPrint.error(f"[cSettings] failed to remove profile \"{name}\"", e)
    if self.profileList.count() > 0:
      self._selectProfile(self.profileList.itemText(0))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def duplicateProfile(self):
    src = μSetup.lastProfile
    if not src: return
    dst = f"copyOf_{src}"
    try:
      shutil.copy2(self._confPath(src), self._confPath(dst))
      μSetup.addProfile(dst)
      self._selectProfile(dst)
      μPrint.info(f"[cSettings] duplicated \"{src}\" → \"{dst}\"")
    except Exception as e:
      μPrint.error(f"[cSettings] failed to duplicate profile \"{src}\"", e)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def renameProfile(self):
    newName = self.profileList.lineEdit().text().strip()
    oldName = μSetup.lastProfile
    if not newName or newName == oldName: return
    if newName in μSetup.profiles: return
    try:
      shutil.move(self._confPath(oldName), self._confPath(newName))
      profile = μSetup.profiles.pop(oldName)
      μSetup.profiles[newName] = profile
      for combo in [self.profileList, self.profileMain]:
        idx = combo.findText(oldName)
        if idx >= 0: combo.setItemText(idx, newName)
      μSetup.lastProfile = newName
      μSetup.profile.name = newName
      μPrint.info(f"[cSettings] renamed \"{oldName}\" → \"{newName}\"")
    except Exception as e:
      μPrint.error(f"[cSettings] failed to rename profile \"{oldName}\"", e)
      self.profileList.lineEdit().setText(oldName)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def load(self):
    self.lastProfile  = self._state.value("lastProfile", "")         # goes in the "General" section of the settings file
    try:
      files = glob.glob(P_DEFAULT_CONFIGDIR+os.sep+"profile_*.conf")
      files = [ os.path.splitext(os.path.basename(f))[0][8:].strip() for f in files ]
      try:
        self.profileList.currentIndexChanged.disconnect()
        self.profileMain.currentIndexChanged.disconnect()
      except: pass

      self.profileList.clear()
      self.profileMain.clear()
      for p in files:
        if p != "": μSetup.addProfile(p)
      self.profileList.currentIndexChanged.connect(lambda : μSetup.syncProfileLists("settings"))
      self.profileMain.currentIndexChanged.connect(lambda : μSetup.syncProfileLists("main"))

      lpIdx = self.profileList.findText(self.lastProfile)
      if lpIdx == -1:
        self.profileList.setCurrentIndex(0)
        self.profileMain.setCurrentIndex(0)
        μPrint.warning(f"[cSettings] last profile \"{self.lastProfile}\" was not found. Loading \"{self.profileMain.itemText(0)}\" instead...")
      else:
        self.profileList.setCurrentIndex(-1)
        self.profileList.setCurrentIndex(lpIdx)
        self.profileMain.setCurrentIndex(-1)
        self.profileMain.setCurrentIndex(lpIdx)

    except Exception as e:
      μPrint.error(f"[cSettings] error loading settings from \"{C_SILVER}{self._state.fileName()}</font>\"", e)
    else:
      μPrint.info(f"[cSettings] loaded from \"{C_SILVER}{self._state.fileName()}</font>\"")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def save(self):
    try:
      self._state.setValue("lastProfile", self.profileList.currentText())                  # goes in the "General" section of the settings file
    except Exception as e:
      μPrint.error(f"[cSettings] could not create \"{C_SILVER}{self._state.fileName()}</font>\" to store settings!",e)
    else:
      μPrint.info(f"[cSettings] saved in \"{C_SILVER}{self._state.fileName()}</font>\"")
