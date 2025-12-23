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
from __future__ import annotations
from PyQt6.QtCore import QRunnable
from PyQt6.QtCore import pyqtSignal
from cWidgets.util import *
import os
import xml.dom.minidom
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

P_DDO_LAUNCHERCONFIG='ddo.launcherconfig'

class tServerInfo(QRunnable):
  sigServerInfo = pyqtSignal(bool)
  P_STATUS_ERROR = -1
  P_STATUS_WORKING = 0
  P_STATUS_UNKNOWN = 1
  P_STATUS_DONE = 2

  def __init__(self, main : cMainWindow):
    super().__init__()
    self.main = main
    self.console = main.console
    self.authServer = ""
    self.patchServer = ""
    self.launchConfigServer = ""
    self.realmList = []

    self.gameClientFilename = ""
    self.gameClientArgTemplate = ""
    self.newsFeedURL = ""
    self.newsStyleSheetURL = ""
    self.patchProductCode = ""
    self.worldQueueURL = ""
    self.worldQueueParam = ""

    self.status = self.P_STATUS_UNKNOWN

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    self.status = self.P_STATUS_WORKING

    gameDir = self.main.profile().gameDir.text()
    gameConfig = gameDir+os.sep+P_DDO_LAUNCHERCONFIG
    for i in range(4):
      if os.path.exists(gameConfig):
        break
      gameDir = os.path.dirname(gameDir)
      gameConfig = gameDir+os.sep+P_DDO_LAUNCHERCONFIG
    
    if not os.path.exists(gameConfig):
      raise Exception(f"tServerInfo.init: could not find {P_DDO_LAUNCHERCONFIG} in directory \"{gameDir}\"")
    else:
      try:
        doc = xml.dom.minidom.parse(gameConfig)

        nodes = doc.getElementsByTagName("appSettings")[0].childNodes
        for node in nodes:
          if node.nodeType == node.ELEMENT_NODE:
            if node.getAttribute("key") == "Launcher.DataCenterService.GLS":
              self.urlGLSDataCenter = node.getAttribute("value")
            elif node.getAttribute("key") == "DataCenter.GameName":
              self.gameName = node.getAttribute("value")
        
      except Exception as e:
        self.main.credentials.sigFetchedGLS.emit(False)
        self.status = self.P_STATUS_ERROR
        self.console.error("Error fetching GLSData", e)
      else:
        self.main.credentials.sigFetchedGLS.emit(True)
        self.console.info("Fetched GLSData")
    
    if self.getGLSData():
      if self.getQueue():
        self.status = self.P_STATUS_DONE
        self.console.info("Finished gathering server data")
        return 
    self.status = self.P_STATUS_ERROR
  
  #----------------------------------------------------------------------------------------------------------
  def getGLSData(self):
    SM_TEMPLATE = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
<soap:Body><GetDatacenters xmlns=\"http://www.turbine.com/SE/GLS\"><game>%s</game>\
</GetDatacenters></soap:Body></soap:Envelope>"
    SoapMessage = SM_TEMPLATE%(self.gameName)

    try:
      msg = SoapMessage.encode()
      webservice, post = getConnection(self.urlGLSDataCenter)

      webservice.putrequest("POST", post)
      webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
      webservice.putheader("Content-length", f"{len(msg)}")
      webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/GetDatacenters")
      webservice.endheaders()
      webservice.send(msg)

      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()
      filename = P_DEFAULT_WORKDIR+"/GLSDataCenter.xml"
      
      with open(filename, "w") as f:
        f.write(tempxml)
      
      if tempxml == "":
        self.loadSuccess = False
      else:
        doc = xml.dom.minidom.parseString(tempxml)

        self.authServer = getText(doc.getElementsByTagName("AuthServer")[0].childNodes)
        self.patchServer = getText(doc.getElementsByTagName("PatchServer")[0].childNodes)
        self.launchConfigServer = getText(doc.getElementsByTagName("LauncherConfigurationServer")[0].childNodes)

        self.realmList = []

        name = ""
        urlChatServer = ""
        urlStatusServer = ""

        for node in doc.getElementsByTagName("World"):
          for realm in node.childNodes:
            if realm.nodeName == "Name":
              name = realm.firstChild.nodeValue
            elif realm.nodeName == "ChatServerUrl":
              urlChatServer = realm.firstChild.nodeValue
            elif realm.nodeName == "StatusServerUrl":
              urlStatusServer = realm.firstChild.nodeValue
          self.realmList.append((name, urlChatServer, urlStatusServer))
          self.main.credentials.sigFetchedWorld.emit((name, urlChatServer, urlStatusServer))
          
    except Exception as e:
      self.console.error("Error fetching worlds data", e)
      self.main.credentials.sigFetchedWorldsInfo.emit(False)
      return False
    else:
      self.main.credentials.sigFetchedWorldsInfo.emit(True)
      self.console.info("Fetched worlds data")
      return True
  
  #----------------------------------------------------------------------------------------------------------
  def getQueue(self) -> bool:
    try:
      webservice, post = getConnection(self.launchConfigServer)
      webservice.putrequest("GET", post)
      webservice.endheaders()
      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()

      filename = P_DEFAULT_WORKDIR+"/dndlauncher.server.xml"
      with open(filename, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.loadSuccess = False
      else:
        doc = xml.dom.minidom.parseString(tempxml)

        nodes = doc.getElementsByTagName("appSettings")[0].childNodes
        for node in nodes:
          if node.nodeType == node.ELEMENT_NODE:
            if node.getAttribute("key") == "GameClient.WIN64.Filename":
              self.gameClientFilename = node.getAttribute("value")
            elif node.getAttribute("key") == "GameClient.WIN32.ArgTemplate": #there isn't one for WIN64!
              self.gameClientArgTemplate = node.getAttribute("value")
            elif node.getAttribute("key") == "GameClient.Arg.authserverurl":
              self.gameClientAuthServerURL = node.getAttribute("value")
            elif node.getAttribute("key") == "GameClient.Arg.glsticketlifetime":
              self.gameClientGLSTicketLifetime = node.getAttribute("value")
            elif node.getAttribute("key") == "URL.NewsFeed":
              self.newsFeedURL = node.getAttribute("value")
            elif node.getAttribute("key") == "URL.NewsStyleSheet":
              self.newsStyleSheetURL = node.getAttribute("value")
            elif node.getAttribute("key") == "Patching.ProductCode":
              self.patchProductCode = node.getAttribute("value")
            elif node.getAttribute("key") == "WorldQueue.LoginQueue.URL":
              self.worldQueueURL = node.getAttribute("value")
            elif node.getAttribute("key") == "WorldQueue.TakeANumber.Parameters":
              self.worldQueueParam = node.getAttribute("value")

        self.loadSuccess = True
    except Exception as e:
      self.console.error("Error fetching queue info", e)
      self.main.credentials.sigFetchedQueueInfo.emit(False)
      return False
    else:
      self.main.credentials.sigFetchedQueueInfo.emit(True)
      self.console.info("Fetched queue info")
      return True



