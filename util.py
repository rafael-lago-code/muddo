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
import os
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6 import QtCore
from http.client import HTTPConnection, HTTPSConnection
import ssl

C_SILVER = "<font style=\"color:#828282\">"
C_RED = "<font style=\"color:#ff5555\">"
C_GREEN = "<font style=\"color:#6aff83\">"
C_BLUE = "<font style=\"color:#43b7ff\">" 

# P_DEFAULT_WORKDIR    = os.environ['HOME'] + "/.local/share/muDDO"
P_DEFAULT_CONFIGDIR  = os.environ['HOME'] + "/.config/muDDO"
P_DEFAULT_WORKDIR    = P_DEFAULT_CONFIGDIR
P_DEFAULT_CONFIGFILE = P_DEFAULT_CONFIGDIR + "/settings.json"

P_DEFAULT_ICON_EXTENSION=".svg"
P_ICON_UNDO      = "edit-undo"
P_ICON_SORT      = "view-sort"
P_ICON_OPEN      = "document-open"
P_ICON_OPENFOLDER= "document-open-folder"
P_ICON_SAVE      = "document-save"
P_ICON_SAVEALL   = "document-save-all"
P_ICON_SAVEAS    = "document-save-as"
P_ICON_ADD       = "list-add"
P_ICON_REMOVE    = "list-remove"
P_ICON_REFRESH   = "view-refresh"
P_ICON_QUESTION  = "dontknow"
P_ICON_PLAY      = "media-playback-start"
P_ICON_PAUSE     = "media-playback-pause"
P_ICON_STOP      = "media-playback-stop"
P_ICON_FILTER    = "view-filter"
P_ICON_EXIT      = "application-exit"
P_ICON_CONFIRM   = "dialog-ok-apply"
P_ICON_CONFIGURE = "configure"
P_ICON_PROPERTIES= "document-properties"
P_ICON_CLEAR     = "edit-clear"
P_ICON_CANCEL    = "dialog-cancel"
P_ICON_CLOSE     = "window-close"
P_ICON_AUTO      = "autocorrection"
P_ICON_TRIANGLE_UP    = "draw-triangle3"
P_ICON_TRIANGLE_DOWN  = "draw-triangle4"
P_ICON_TRIANGLE_LEFT  = "draw-triangle1"
P_ICON_TRIANGLE_RIGHT = "draw-triangle2"
P_DEFAULT_ICON_PATHS  = [os.path.dirname(os.path.abspath(__file__))+'/images/breeze-dark-icons/',
                         '/usr/share/icons/breeze-dark',
                         '/usr/share/icons/breeze',
                         '/usr/share/icons/Adwaita',
                         '/usr/share/icons/gnome',
                         '/usr/share/icons/Humanity-Dark',
                         '/usr/share/icons/Humanity']

P_CERTFILE = None
P_CERTCTX = None

#@TODO write this properly to search/detect the correct icon scheme...
_iconScheme = {}
for i in [P_ICON_UNDO, P_ICON_SORT, P_ICON_OPEN, P_ICON_OPENFOLDER, P_ICON_SAVE, P_ICON_SAVEALL, P_ICON_SAVEAS,
          P_ICON_ADD, P_ICON_REMOVE, P_ICON_REFRESH, P_ICON_QUESTION, P_ICON_PLAY, P_ICON_PAUSE, P_ICON_STOP,
          P_ICON_FILTER, P_ICON_EXIT, P_ICON_CONFIRM, P_ICON_CONFIGURE, P_ICON_PROPERTIES, P_ICON_CLEAR, P_ICON_CANCEL,
          P_ICON_CLOSE, P_ICON_AUTO, P_ICON_TRIANGLE_UP, P_ICON_TRIANGLE_DOWN, P_ICON_TRIANGLE_LEFT, P_ICON_TRIANGLE_RIGHT]:
  for d in P_DEFAULT_ICON_PATHS:
    for s in ["64", "32", "16"]:
      if os.path.exists(d+"/actions/"+s+"/"+i+P_DEFAULT_ICON_EXTENSION):
        _iconScheme[i] = d+"/actions/"+s+"/"+i+P_DEFAULT_ICON_EXTENSION
        break
    else:
      continue
    break

#----------------------------------------------------------------------------------------------------------
P_CERTFILE = os.path.dirname(__file__)+"/certificates/ca_cert2025.pem"
P_CERTCTX = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
if not os.access(P_CERTFILE, os.R_OK):
  P_CERTFILE = None
else:
  P_CERTCTX.verify_mode = ssl.CERT_REQUIRED
  P_CERTCTX.load_verify_locations(P_CERTFILE)
  P_CERTCTX.set_ciphers('DEFAULT@SECLEVEL=1')
        
#----------------------------------------------------------------------------------------------------------  
def quickQLabel(text :  str):
  lbl = QLabel(text)
  lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
  return lbl

#----------------------------------------------------------------------------------------------------------  
def getPixmap(name:str) -> QIcon:
  return QPixmap(_iconScheme[name])

#----------------------------------------------------------------------------------------------------------  
def getIcon(name:str) -> QIcon:
  return QIcon(getPixmap(name))

#----------------------------------------------------------------------------------------------------------  
def getConnection(urlIn):
  if urlIn.upper().find("HTTP://") >= 0:
    url = urlIn[7:].split("/")[0]
    post = urlIn[7:].replace(url, "")
    return HTTPConnection(url), post
  else:
    url = urlIn[8:].split("/")[0]
    post = urlIn[8:].replace(url, "")
    return HTTPSConnection(url, context=P_CERTCTX), post
    
#----------------------------------------------------------------------------------------------------------
def getText(nodelist):
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE or node.nodeType == node.CDATA_SECTION_NODE:
			rc = rc + node.data
	return rc

  
