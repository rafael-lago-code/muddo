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
from PyQt6.QtCore import QObject, pyqtSignal
from μSettings import μSetup
from helpers.μPrint import μPrint
from helpers.util import *
import os, time, threading
import xml.dom.minidom

P_DDO_LAUNCHERCONFIG='ddo.launcherconfig'

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  S E R V E R   I N F O
#                                  
#   This is a hybrid class. Don't instantiate it unless you know what you're doing.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μServerInfo(QObject):
  _instance     : 'μServerInfo' = None
  sigServerInfo        = pyqtSignal(bool)
  sigFetchedGLS        = pyqtSignal(bool)
  sigFetchedWorld      = pyqtSignal(tuple)
  sigFetchedWorldsInfo = pyqtSignal(bool)
  sigFetchedQueueInfo  = pyqtSignal(bool)
  P_STATUS_ERROR   = -1
  P_STATUS_WORKING = 0
  P_STATUS_UNKNOWN = 1
  P_STATUS_DONE    = 2

  authServer               = ""
  patchServer              = ""
  launchConfigServer       = ""
  realmList                = []
  urlGLSDataCenter         = ""
  gameName                 = ""
  gameClientFilename       = ""
  gameClientArgTemplate    = ""
  gameClientAuthServerURL  = ""
  gameClientGLSTicketLifetime = ""
  newsFeedURL              = ""
  newsStyleSheetURL        = ""
  patchProductCode         = ""
  worldQueueURL            = ""
  worldQueueParam          = ""
  status                   = P_STATUS_UNKNOWN

  def __init__(self):
    super().__init__()
    μServerInfo._instance = self
    μServerInfo.sigServerInfo        = self.sigServerInfo
    μServerInfo.sigFetchedGLS        = self.sigFetchedGLS
    μServerInfo.sigFetchedWorld      = self.sigFetchedWorld
    μServerInfo.sigFetchedWorldsInfo = self.sigFetchedWorldsInfo
    μServerInfo.sigFetchedQueueInfo  = self.sigFetchedQueueInfo

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def collect(cls):
    threading.Thread(target=cls._instance.run, daemon=True).start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def run(self):
    μServerInfo.status = μServerInfo.P_STATUS_WORKING

    gamePath = μSetup.launcher.gamePath()
    gameConfig = gamePath+os.sep+P_DDO_LAUNCHERCONFIG
    for i in range(4):
      if os.path.exists(gameConfig):
        break
      gamePath = os.path.dirname(gamePath)
      gameConfig = gamePath+os.sep+P_DDO_LAUNCHERCONFIG
    
    if not os.path.exists(gameConfig):
      raise Exception(f"tServerInfo.init: could not find {P_DDO_LAUNCHERCONFIG} in directory \"{gamePath}\"")
    else:
      try:
        doc = xml.dom.minidom.parse(gameConfig)

        nodes = doc.getElementsByTagName("appSettings")[0].childNodes
        for node in nodes:
          if node.nodeType == node.ELEMENT_NODE:
            if node.getAttribute("key") == "Launcher.DataCenterService.GLS":
              μServerInfo.urlGLSDataCenter = node.getAttribute("value")
            elif node.getAttribute("key") == "DataCenter.GameName":
              μServerInfo.gameName = node.getAttribute("value")
        
      except Exception as e:
        self.sigFetchedGLS.emit(False)
        μServerInfo.status = μServerInfo.P_STATUS_ERROR
        μPrint.error("Error fetching GLSData", e)
      else:
        self.sigFetchedGLS.emit(True)
        μPrint.info("Fetched GLSData")
    
    if self.getGLSData():
      if self.getQueue():
        μServerInfo.status = μServerInfo.P_STATUS_DONE
        μPrint.info("Finished gathering server data")
        return
    self.status = self.P_STATUS_ERROR
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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

        μServerInfo.authServer = getNodeText(doc.getElementsByTagName("AuthServer")[0].childNodes)
        μServerInfo.patchServer = getNodeText(doc.getElementsByTagName("PatchServer")[0].childNodes)
        μServerInfo.launchConfigServer = getNodeText(doc.getElementsByTagName("LauncherConfigurationServer")[0].childNodes)

        μServerInfo.realmList = []

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
          μServerInfo.realmList.append((name, urlChatServer, urlStatusServer))
          self.sigFetchedWorld.emit((name, urlChatServer, urlStatusServer))

    except Exception as e:
      μPrint.error("Error fetching worlds data", e)
      self.sigFetchedWorldsInfo.emit(False)
      return False
    else:
      μPrint.info("Fetched worlds data")
      time.sleep(1)
      self.sigFetchedWorldsInfo.emit(True)
      return True
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getQueue(self) -> bool:
    try:
      webservice, post = getConnection(self.launchConfigServer)
      webservice.putrequest("GET", post)
      webservice.endheaders()
      webresp = webservice.getresponse()
      tempxml = webresp.read().decode()

      with open(P_DEFAULT_SERVERCONFIG, "w") as f:
        f.write(tempxml)

      if tempxml == "":
        self.loadSuccess = False
      else:
        doc = xml.dom.minidom.parseString(tempxml)

        nodes = doc.getElementsByTagName("appSettings")[0].childNodes
        for node in nodes:
          if node.nodeType == node.ELEMENT_NODE:
            if node.getAttribute("key") == "GameClient.WIN64.Filename":
              μServerInfo.gameClientFilename = node.getAttribute("value")
            elif node.getAttribute("key") == "GameClient.WIN32.ArgTemplate": #there isn't one for WIN64!
              μServerInfo.gameClientArgTemplate = node.getAttribute("value")
            elif node.getAttribute("key") == "GameClient.Arg.authserverurl":
              μServerInfo.gameClientAuthServerURL = node.getAttribute("value")
            elif node.getAttribute("key") == "GameClient.Arg.glsticketlifetime":
              μServerInfo.gameClientGLSTicketLifetime = node.getAttribute("value")
            elif node.getAttribute("key") == "URL.NewsFeed":
              μServerInfo.newsFeedURL = node.getAttribute("value")
            elif node.getAttribute("key") == "URL.NewsStyleSheet":
              μServerInfo.newsStyleSheetURL = node.getAttribute("value")
            elif node.getAttribute("key") == "Patching.ProductCode":
              μServerInfo.patchProductCode = node.getAttribute("value")
            elif node.getAttribute("key") == "WorldQueue.LoginQueue.URL":
              μServerInfo.worldQueueURL = node.getAttribute("value")
            elif node.getAttribute("key") == "WorldQueue.TakeANumber.Parameters":
              μServerInfo.worldQueueParam = node.getAttribute("value")
    except Exception as e:
      μPrint.error("Error fetching queue info", e)
      self.sigFetchedQueueInfo.emit(False)
      return False
    else:
      self.sigFetchedQueueInfo.emit(True)
      μPrint.info("Fetched queue info")
      return True



