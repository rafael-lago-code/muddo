# coding=utf-8
###########################################################################
# Name:   μDDO
# Author: Rafael Lago
# Date:   February 2025
#
# Support classes for the Linux based launcher
# for the game Dungeons & Dragons Online
#
# Based on PyLotRO by AJackson <ajackson@bcs.org.uk>
# Based on a script by SNy <SNy@bmx-chemnitz.de>
#
# (C) 2025 Rafael Lago
#
# This file is part of PyLotRO
#
# μDDO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# μDDO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with μDDO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtCore import Qt
from util import *
import xml.dom.minidom

class cWorld(QListWidgetItem):
  DOWN  = -1
  UNKNOWN = 0
  UP = 1
  
  def __init__(self, name, chatServer, statusServer):
    super().__init__()
    self.status = cWorld.UNKNOWN
    self.chatServer = chatServer
    self.statusServer = statusServer
    self.loginServer = None
    self.queueURL = None
    self.nowServing = None
    self.setText(name)

  #----------------------------------------------------------------------------------------------------------
  def setText(self, name, update=False):
    if update: self.updateStatus()

    if self.status == cWorld.UP:
      self.setForeground(QBrush(Qt.GlobalColor.green))
      self.setFont(QFont(self.font().families(), italic=False))
    elif self.status == cWorld.DOWN:
      self.setForeground(QBrush(Qt.GlobalColor.red))
      self.setFont(QFont(self.font().families(), italic=False))
    else:
      self.setForeground(QBrush())
      self.setFont(QFont(self.font().families(), italic=True))
    super().setText(name)

  #----------------------------------------------------------------------------------------------------------
  def checkStatus(self):
    try:
      webservice, post = getConnection(self.statusServer)
      webservice.putrequest("GET", post)
      webservice.endheaders()

      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()

      filename = P_DEFAULT_CONFIGDIR+"/Server_"+self.text()+".config"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.status == cWorld.DOWN
      else:
        doc = xml.dom.minidom.parseString(tempxml)
        try:
          self.nowServing = getText(doc.getElementsByTagName("nowservingqueuenumber")[0].childNodes)
        except:
          self.nowServing = None
        try:
          self.queueURL = getText(doc.getElementsByTagName("queueurls")[0].childNodes).split(";")[0]
        except:
          self.queueURL = None
        self.loginServer = getText(doc.getElementsByTagName("loginservers")[0].childNodes).split(";")[0]
        self.status = cWorld.UP
    except Exception as e:
      self.status = cWorld.DOWN
      raise e

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
      self.worlds[w] = cWorld(w,'','')
      self.addItem(self.worlds[w])

  #----------------------------------------------------------------------------------------------------------
  def updateWorld(self, data : tuple):
    (name, chatServer, statusServer) = data
    if name in self.worlds.keys():
        self.console.info(f"Updating \"{name}\" world info...")
        self.worlds[name].chatServer = chatServer
        self.worlds[name].statusServer = statusServer
    else:
        self.console.info(f"Adding \"{name}\" world info...")
        self.worlds[name] = cWorld(name, chatServer, statusServer)
        self.addItem(self.worlds[name])

  # #----------------------------------------------------------------------------------------------------------
  # def populate(self, realmList : dict):
  #   for r in realmList:
  #     self.updateWorld(r)
  #     try:
  #       self.worlds[r[0]].checkStatus()
  #     except Exception as e:
  #       self.console.error(f"Failure populating {r[0]}", e)


