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
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtCore import QRunnable, pyqtSignal, Qt
from util import *
import xml.dom.minidom

class cWorld(QListWidgetItem):
  DOWN  = -1
  UNKNOWN = 0
  UP = 1
  
  def __init__(self, main, name, chatServer, statusServer):
    super().__init__()
    self.status = cWorld.UNKNOWN
    self.main = main
    self.chatServer = chatServer
    self.statusServer = statusServer
    self.loginServer = None
    self.queueURL = None
    self.nowServing = None
    self.name = name
    self.setText(name)

  #----------------------------------------------------------------------------------------------------------
  def setText(self, name, update=False):
    if update: self.updateStatus()

    tooltip  = f"<b>{self.name} Server Info:</b><br>"

    if self.status == cWorld.UP:
      self.setIcon(getIcon(P_ICON_CONNECTED_GREEN))
      tooltip += f"<b>Status:</b> UP<br>"
    elif self.status == cWorld.DOWN:
      self.setIcon(getIcon(P_ICON_DISCONNECTED_RED))
      tooltip += f"<b>Status:</b> DOWN<br>"
    else:
      self.setIcon(getIcon(P_ICON_NONE))
      tooltip += f"<b>Status:</b> UNKNOWN<br>"

    tooltip += f"<b>chatServer:</b> {self.chatServer}<br>"
    tooltip += f"<b>statusServer:</b> {self.statusServer}<br>"
    tooltip += f"<b>loginServer:</b> {self.loginServer}<br>"
    tooltip += f"<b>queueURL:</b> {self.queueURL if self.queueURL else "?"}<br>"
    tooltip += f"<b>nowServing:</b> {self.nowServing if self.nowServing else "?"}<br>"
    self.setToolTip(tooltip)
    super().setText(name)

  #----------------------------------------------------------------------------------------------------------
  def checkStatus(self):
    wc = tWorldChecker(self)
    QtCore.QThreadPool.globalInstance().start(wc)

#----------------------------------------------------------------------------------------------------------
class cWorldList(QListWidget):
  defaultWorlds = ["Argonnessen", "Cannith", "Cormyr", "Ghallanda",
                   "Khyber", "Orien", "Sarlona", "Thelanis", "Wayfinder"]
  def __init__(self, main):
    super().__init__()
    self.worlds = {}
    self.main = main
    self.console = main.console

    for w in self.defaultWorlds:
      self.worlds[w] = cWorld(self.main, w,'','')
      self.addItem(self.worlds[w])

  #----------------------------------------------------------------------------------------------------------
  def updateWorld(self, data : tuple):
    name, chatServer, statusServer = data
    if name in self.worlds.keys():
        self.console.info(f"Updating \"{C_SILVER}{name}</font>\" world info...")
        self.worlds[name].chatServer = chatServer
        self.worlds[name].statusServer = statusServer
    else:
        self.console.info(f"Adding \"{C_SILVER}{name}</font>\" world info...")
        self.worlds[name] = cWorld(self.main, name, chatServer, statusServer)
        self.addItem(self.worlds[name])
    self.worlds[name].checkStatus()

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

      filename = P_DEFAULT_CONFIGDIR+"/Server_"+self.world.text()+".xml"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.world.status == cWorld.DOWN
      else:
        doc = xml.dom.minidom.parseString(tempxml)
        try:
          self.world.nowServing = getText(doc.getElementsByTagName("nowservingqueuenumber")[0].childNodes)
        except:
          self.world.nowServing = None
        try:
          self.world.queueURL = getText(doc.getElementsByTagName("queueurls")[0].childNodes).split(";")[0]
        except:
          self.world.queueURL = None
        self.world.loginServer = getText(doc.getElementsByTagName("loginservers")[0].childNodes).split(";")[0]
        self.world.status = cWorld.UP
        self.world.setText(self.world.text())
    except Exception as e:
      self.world.status = cWorld.DOWN
      self.world.main.console.error("Error trying to check world status", e)


