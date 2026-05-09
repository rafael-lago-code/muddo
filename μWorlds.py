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
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from helpers.μImageFactory import *
import xml.dom.minidom

class μWorld(QObject):
  DOWN  = -1
  UNKNOWN = 0
  UP = 1
  
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

  #----------------------------------------------------------------------------------------------------------
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

  #----------------------------------------------------------------------------------------------------------
  def checkStatus(self):
    wc = tWorldChecker(self)
    QtCore.QThreadPool.globalInstance().start(wc)

#----------------------------------------------------------------------------------------------------------
class cWorldList(QComboBox):
  sigWorldUpdated = pyqtSignal(bool)
  defaultWorlds = ["Cormyr [US]", "Moonsea [EU]", "Shadowdale [US]", "Thrane [US]"]
#   defaultWorlds += ["Argonnessen [Old]", "Cannith [Old]", "Ghallanda [Old]", "Khyber [Old]",
#                    "Orien [Old]", "Sarlona [Old]", "Thelanis [Old]", "Wayfinder [Old]"]
  def __init__(self, main):
    super().__init__()
    self.worlds : dict[str, μWorld] = {}
    self.main = main
    self.console = main.console

    for w in self.defaultWorlds:
      self.worlds[w] = μWorld(self, w,'','',self.count())
      self.addItem(self.worlds[w])
    
    self.currentIndexChanged.connect(self.update)

  #----------------------------------------------------------------------------------------------------------
  def addItem(self, world : μWorld):
    return super().addItem(getIcon(P_ICON_NONE), world.name, world)
  
  #----------------------------------------------------------------------------------------------------------
  def currentItem(self):
    return self.currentData()

  #----------------------------------------------------------------------------------------------------------
  def update(self):
    self.setToolTip(self.currentItem().tooltip)

  #----------------------------------------------------------------------------------------------------------
  def updateWorld(self, data : tuple):
    name, chatServer, statusServer = data
    if name in self.worlds.keys():
        self.console.info(f"Updating \"{C_SILVER}{name}</font>\" world info...")
        self.worlds[name].chatServer = chatServer
        self.worlds[name].statusServer = statusServer
    else:
        self.console.info(f"Adding \"{C_SILVER}{name}</font>\" world info...")
        self.worlds[name] = μWorld(self, name, chatServer, statusServer, self.count())
        self.addItem(self.worlds[name])
    self.worlds[name].checkStatus()
    self.sigWorldUpdated.emit(True)


#----------------------------------------------------------------------------------------------------------
class tWorldChecker(QRunnable):
  def __init__(self, world):
    super().__init__()
    self.world = world

  def run(self):
    try:
      webservice, post = getConnection(self.world.statusServer)
      webservice.putrequest("GET", post)
      webservice.endheaders()
      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()

      filename = P_DEFAULT_SERVERDIR+self.world.name+".xml"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.world.status == μWorld.DOWN
      else:
        doc = xml.dom.minidom.parseString(tempxml)
        try:
          self.world.nowServing = getNodeText(doc.getElementsByTagName("nowservingqueuenumber")[0].childNodes)
        except:
          self.world.nowServing = None
        try:
          self.world.queueURL = getNodeText(doc.getElementsByTagName("queueurls")[0].childNodes).split(";")[0]
        except:
          self.world.queueURL = None
        self.world.loginServer = getNodeText(doc.getElementsByTagName("loginservers")[0].childNodes).split(";")[0]
        self.world.status = μWorld.UP
        self.world.update()
    except Exception as e:
      self.world.status = μWorld.DOWN
      self.world.combo.console.error("Error trying to check world status", e)


