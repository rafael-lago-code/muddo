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
# This file is part of μDDO
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
from PyQt6.QtCore import QRunnable, pyqtSignal
from util import *
import os
import xml.dom.minidom

class tAccount(QRunnable):
  sigUserAuthenticated = pyqtSignal(bool)
  sigAuthenticationFinished = pyqtSignal(bool)
  
  P_STATUS_ERROR = -1
  P_STATUS_WORKING = 0
  P_STATUS_UNKNOWN = 1
  P_STATUS_DONE = 2

  def __init__(self, main, username):
    super().__init__()
    self.main = main
    self.console = main.console
    self.username = username
    self.url = main.login.serverInfo.authServer
    self.ticket = None
    self.status = self.P_STATUS_UNKNOWN

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    self.status = self.P_STATUS_WORKING
    SM_TEMPLATE = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
    <soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" \
    xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" \
    xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
    <soap:Body><LoginAccount xmlns=\"http://www.turbine.com/SE/GLS\"><username>%s</username>\
    <password>%s</password><additionalInfo></additionalInfo></LoginAccount></soap:Body></soap:Envelope>"

    password = self.main.login.accounts[self.username]
    SoapMessage = SM_TEMPLATE%(self.username, password)
    webresp = None


    try:
      msg = SoapMessage.encode()
      webservice, post = getConnection(self.url)

      webservice.putrequest("POST", post)
      webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
      webservice.putheader("Content-length", "%d" % len(msg))
      webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount")
      webservice.endheaders()
      webservice.send(msg)

      webresp = webservice.getresponse()

      self.gameList = []

      self.ticket = ""
      tempxml = webresp.read().decode()

      filename = P_DEFAULT_WORKDIR + os.sep + self.username + "_GLSAuthServer.config"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.console.error(f"Failed to fetch information from \"{self.url}\"")
      else:
        doc = xml.dom.minidom.parseString(tempxml)
        self.ticket = getText(doc.getElementsByTagName("Ticket")[0].childNodes)
        # for nodes in doc.getElementsByTagName("GameSubscription"):
        #   game = ""
        #   status = ""
        #   name = ""
        #   desc = ""

        #   for node in nodes.childNodes:
        #     if node.nodeName == "Game":
        #       game = getText(node.childNodes)
        #     elif node.nodeName == "Status":
        #       status = getText(node.childNodes)
        #     elif node.nodeName == "Name":
        #       name = getText(node.childNodes)
        #     elif node.nodeName == "Description":
        #       desc = getText(node.childNodes)

        #   if game == "DDO":
        #     activeAccount = True
        #     # self.gameList.append(Game(name, desc))
        #     self.gameList.append((name, desc))

        # if activeAccount:
        #   self.messError = "No Error"
        #   self.authSuccess = True
        # else:
        #   self.console.error(f"Game account \"{self.username}\" not associated with user account - please visit games website and check account details")
    except ssl.SSLError as e:
      self.status = self.P_STATUS_ERROR
      self.console.error("SSL error occured in HTTPS connection", e)
    except Exception as e:
      self.status = self.P_STATUS_ERROR
      if webresp and webresp.status == 500:
        self.console.error("Account details incorrect", e)
      else:
        self.console.error(f"Server not found - may be down.\n{webresp and webresp.status or "N/A"}", e)
    self.console.info(f"Authenticated {C_SILVER}{self.username}</font>!")
    self.status = self.P_STATUS_DONE

