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
from PyQt6.QtCore import QRunnable, pyqtSignal
from util import *
import os
import xml.dom.minidom
import urllib

class tAccount(QRunnable):
  P_STATUS_ERROR = -1
  P_STATUS_UNKNOWN = 0
  P_STATUS_DONE = 1
  P_STATUS_AUTHENTICATING = 3
  P_STATUS_QUEUEING = 4

  def __init__(self, main, username, world):
    super().__init__()
    self.main = main
    self.console = main.console
    self.username = username
    self.world = world
    self.serverInfo = main.credentials.serverInfo
    self.ticket = None
    self.status = self.P_STATUS_UNKNOWN
    self.subscription = None

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    self.status = self.P_STATUS_AUTHENTICATING
    if self.authenticate():
      self.main.sigAuthenticatedUser.emit(self.username)
    else:
      self.status = self.P_STATUS_ERROR
      return
    
    self.status = self.P_STATUS_QUEUEING
    if not self.wait():
      self.status = self.P_STATUS_ERROR
      return

  
  #----------------------------------------------------------------------------------------------------------
  def authenticate(self):
    SM_TEMPLATE = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
    <soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" \
    xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" \
    xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
    <soap:Body><LoginAccount xmlns=\"http://www.turbine.com/SE/GLS\"><username>%s</username>\
    <password>%s</password><additionalInfo></additionalInfo></LoginAccount></soap:Body></soap:Envelope>"

    password = self.main.credentials.accounts[self.username]
    SoapMessage = SM_TEMPLATE%(self.username, password)
    webresp = None

    try:
      msg = SoapMessage.encode()
      webservice, post = getConnection(self.serverInfo.authServer)

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

      filename = P_DEFAULT_WORKDIR+os.sep+"GLSAuthServer_"+self.username+".xml"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.console.error(f"Failed to fetch information from \"{self.serverInfo.authServer}\"")
        return False
      else:
        doc = xml.dom.minidom.parseString(tempxml)
        self.ticket = getText(doc.getElementsByTagName("Ticket")[0].childNodes)
        for nodes in doc.getElementsByTagName("GameSubscription"):
          game = ""
          # status = ""
          subscription = ""
          # desc = ""

          for node in nodes.childNodes:
            if node.nodeName == "Game":
              game = getText(node.childNodes)
            # elif node.nodeName == "Status":
              # status = getText(node.childNodes)
            elif node.nodeName == "Name":
              subscription = getText(node.childNodes)
            # elif node.nodeName == "Description":
              # desc = getText(node.childNodes)

          if game == "DDO":
            self.subscription = subscription
            break

        #   self.messError = "No Error"
        #   self.authSuccess = True
        # else:
        #   self.console.error(f"Game account \"{self.username}\" not associated with user account - please visit games website and check account details")
    except ssl.SSLError as e:
      self.console.error("SSL error occured in HTTPS connection", e)
      return False
    except Exception as e:
      if webresp and webresp.status == 500:
        self.console.error("Account details incorrect", e)
      else:
        self.console.error(f"Server not found - may be down.\n{webresp and webresp.status or "N/A"}", e)
      return False
    else:
      if self.subscription is None:
        self.console.error(f"Game account \"{C_SILVER}{self.username}</font>\" not associated with user account - please visit games website and check account details")
        return False
      self.console.info(f"Authenticated \"{C_SILVER}{self.username}</font>\"!")
      return True

  #----------------------------------------------------------------------------------------------------------
  def queue(self):
    number  = None
    serving = None
    try:
      webservice, post = getConnection(self.serverInfo.worldQueueURL)

      argComplete = self.serverInfo.worldQueueParam.replace("{0}", self.subscription).replace("{1}",
        urllib.parse.quote(self.ticket)).replace("{2}", urllib.parse.quote(self.world.queueURL))

      msg = argComplete.encode()
      webservice.putrequest("POST", post)
      webservice.putheader("Content-type", "application/x-www-form-urlencoded")
      webservice.putheader("Content-length", f"{len(msg)}")
      webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount")
      webservice.endheaders()
      webservice.send(msg)

      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()
      filename = P_DEFAULT_CONFIGDIR+os.sep+"WorldQueue_"+self.username+".xml"

      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml != "":
        doc = xml.dom.minidom.parseString(tempxml)
        if getText(doc.getElementsByTagName("HResult")[0].childNodes) == "0x00000000":
          number  = getText(doc.getElementsByTagName("QueueNumber")[0].childNodes)
          serving = getText(doc.getElementsByTagName("NowServingNumber")[0].childNodes)

    except Exception as e:
      self.console.error(f"Error checking the queue for \"{C_SILVER}{self.username}</font>\"<br>"+\
                         f"(number,serving) = ({number},{serving})<br>"+\
                         f"queueURL={self.world.queueURL}",e)
    return (number, serving)

  #----------------------------------------------------------------------------------------------------------
  def wait(self):
    (number, serving) = self.queue()
    if number and serving:
      self.main.sigQueuedUser.emit(self.username)
    while number > serving:
      if number is None or serving is None:
        self.console.error(f"Something went wrong while queueing for account \"{C_SILVER}{self.username}</font>\"")
        return False
    self.console.info(f"Queueing done for \"{C_SILVER}{self.username}</font>\", joining server...")
    self.main.sigQueuedUserDone.emit(self.username)
    return True
      


