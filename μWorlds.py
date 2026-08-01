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
#    <ajackson@bcs.org.uk>), which in turn is based on a lotrolauncher 
#    script by SNy (<SNy@bmx-chemnitz.de>)
#
#
from PyQt6.QtCore import QObject, pyqtSignal
import threading
from helpers.μImageFactory import *
from helpers.χPrint import χPrint
import xml.dom.minidom
from widgets.μCombo import μCombo
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from μWorlds import μWorldList

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  W O R L D
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μWorld(QObject):
  DOWN  = -1
  UNKNOWN = 0
  UP = 1
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, combo, name, chatServer, statusServer, index):
    super().__init__()
    self.name = name
    self.status = μWorld.UNKNOWN
    self.index = index
    self.combo = combo
    self.chatServer = chatServer
    self.statusServer = statusServer
    self.loginServer = None
    self.queueURL = None
    self.nowServing = None
    self.tooltip  = f"<i>Fetching...</i>"
    self.update()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def update(self, checkStatus=False):
    self.combo.setItemText(self.index, self.name)
    if checkStatus: self.checkStatus()

    self.tooltip  = f"<b>{self.name} Server Info:</b><br>"

    if self.status == μWorld.UP:
      self.combo.setItemIcon(self.index, getIcon(P_ICON_CONNECTED_GREEN))
      self.tooltip += f"<b>Status:</b> UP<br>"
    elif self.status == μWorld.DOWN:
      self.combo.setItemIcon(self.index, getIcon(P_ICON_DISCONNECTED_RED))
      self.tooltip += f"<b>Status:</b> DOWN<br>"
    else:
      self.combo.setItemIcon(self.index, getIcon(P_ICON_NONE))
      self.tooltip += f"<b>Status:</b> UNKNOWN<br>"

    self.tooltip += f"<b>chatServer:</b> {self.chatServer}<br>"
    self.tooltip += f"<b>statusServer:</b> {self.statusServer}<br>"
    self.tooltip += f"<b>loginServer:</b> {self.loginServer}<br>"
    self.tooltip += f"<b>queueURL:</b> {self.queueURL if self.queueURL else "?"}<br>"
    self.tooltip += f"<b>nowServing:</b> {self.nowServing if self.nowServing else "?"}<br>"
    # self.setToolTip(tooltip)
    # super().setText(name)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def checkStatus(self):
    threading.Thread(target=self._checkStatus, daemon=True).start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _checkStatus(self):
    try:
      webservice, post = getConnection(self.statusServer)
      webservice.putrequest("GET", post)
      webservice.endheaders()
      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()

      filename = P_DEFAULT_SERVERDIR+self.name+".xml"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.status = μWorld.DOWN
      else:
        doc = xml.dom.minidom.parseString(tempxml)
        try:
          self.nowServing = getNodeText(doc.getElementsByTagName("nowservingqueuenumber")[0].childNodes)
        except:
          self.nowServing = None
        try:
          self.queueURL = getNodeText(doc.getElementsByTagName("queueurls")[0].childNodes).split(";")[0]
        except:
          self.queueURL = None
        self.loginServer = getNodeText(doc.getElementsByTagName("loginservers")[0].childNodes).split(";")[0]
        self.status = μWorld.UP
        self.update()
    except Exception as e:
      self.status = μWorld.DOWN
      χPrint.error("Error trying to check world status", e)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  W O R L D   L I S T 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μWorldList(μCombo):
  _widget  : 'μWorldList'      = None
  worlds  : dict[str, μWorld] = {}
  sigWorldUpdated = pyqtSignal(bool)
  defaultWorlds = ["Cormyr [US]", "Moonsea [EU]", "Shadowdale [US]", "Thrane [US]"]
#   defaultWorlds += ["Argonnessen [Old]", "Cannith [Old]", "Ghallanda [Old]", "Khyber [Old]",
#                    "Orien [Old]", "Sarlona [Old]", "Thelanis [Old]", "Wayfinder [Old]"]
  def __init__(self):
    super().__init__()
    μWorldList._widget            = self
    μWorldList.worlds             = {}
    μWorldList.currentItem        = self.currentItem
    μWorldList.updateWorld        = self.updateWorld
    μWorldList.currentTextChanged = self.currentTextChanged

    for w in self.defaultWorlds:
      μWorldList.worlds[w] = μWorld(self, w,'','',self.count())
      self.addItem(μWorldList.worlds[w])

    self.currentIndexChanged.connect(self.update)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addItem(self, world : μWorld):
    return super().addItem(getIcon(P_ICON_DISCONNECTED_RED), world.name, world)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def currentItem(self):
    return self.currentData()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getSelectedWorld(cls):
    out = cls._widget.currentItem() if cls._widget else None
    return "" if out is None else out.name

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getServerName(cls):
    out = cls._widget.currentItem() if cls._widget else None
    return "" if out is None else out.name.split()[0]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def selectWorld(cls, name):
    if not name or not cls._widget: return
    w = cls.worlds.get(name)
    if w:
      cls._widget.setCurrentIndex(w.index)
    else:
      χPrint.error(f"[μWorld]: world \"{name}\" not found in the list!")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def update(self):
    item = self.currentItem()
    if item: self.setToolTip(item.tooltip)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def updateWorld(self, data : tuple):
    name, chatServer, statusServer = data
    if name in μWorldList.worlds:
      χPrint.info(f"Updating \"{C_SILVER}{name}</font>\" world info...")
      μWorldList.worlds[name].chatServer = chatServer
      μWorldList.worlds[name].statusServer = statusServer
    else:
      χPrint.info(f"Adding \"{C_SILVER}{name}</font>\" world info...")
      μWorldList.worlds[name] = μWorld(self, name, chatServer, statusServer, self.count())
      self.addItem(μWorldList.worlds[name])
    μWorldList.worlds[name].checkStatus()
    self.sigWorldUpdated.emit(True)




