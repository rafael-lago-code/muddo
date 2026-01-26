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
import os
from PyQt6.QtWidgets import QLabel, QPushButton, QSizePolicy, QFrame, QHBoxLayout,\
                            QVBoxLayout, QLayout, QFrame
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6 import QtCore
from http.client import HTTPConnection, HTTPSConnection
import ssl
import json

C_SILVER = "<font style=\"color:#828282\">"
C_RED = "<font style=\"color:#ff5555\">"
C_ORANGE = "<font style=\"color:#ffa744\">"
C_GREEN = "<font style=\"color:#6aff83\">"
C_BLUE = "<font style=\"color:#43b7ff\">" 

# P_DEFAULT_WORKDIR    = os.environ['HOME'] + "/.local/share/muDDO"
P_MUDDO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P_DEFAULT_CONFIGDIR  = os.environ['HOME'] + "/.config/muDDO"
P_DEFAULT_MACRODIR   = P_DEFAULT_CONFIGDIR + "/macros/"
P_DEFAULT_WORKDIR    = P_DEFAULT_CONFIGDIR
P_DEFAULT_CONFIGFILE = P_DEFAULT_CONFIGDIR + "/settings.json"

P_DEFAULT_CONF = "muDDO/muddo"

P_DEFAULT_ICON_SIZE=QtCore.QSize(28,28)
P_DEFAULT_ICON_EXTENSION=".svg"
P_ICON_NONE      = "none"
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
P_ICON_MUTE      = "audio-volume-muted"
P_ICON_UNMUTE    = "audio-on"
P_ICON_PLAY      = "media-playback-start"
P_ICON_PAUSE     = "media-playback-pause"
P_ICON_STOP      = "media-playback-stop"
P_ICON_FILTER    = "view-filter"
P_ICON_EXIT      = "dungeon-exit"
P_ICON_CONFIRM   = "dialog-ok-apply"
P_ICON_CONFIGURE = "configure"
P_ICON_PROPERTIES= "document-properties"
P_ICON_CLEAR     = "edit-clear"
P_ICON_CANCEL    = "dialog-cancel"
P_ICON_CLOSE     = "window-close"
P_ICON_AUTO      = "autocorrection"
P_ICON_COMPASS   = "compass"
P_ICON_LOCKOPEN  = "document-decrypt"
P_ICON_LOCKCLOSE = "document-encrypted"
P_ICON_EDIT      = "document-edit"
P_ICON_SCROLL    = "curled-scroll"
P_ICON_NEWDOC    = "document-new"
P_ICON_STAR      = "draw-star"
P_ICON_BROOM     = "edit-clear-all"
P_ICON_CLEARALL  = "edit-clear-red"
P_ICON_SHRED     = "edit-delete-shred"
P_ICON_TRASH     = "edit-delete"
P_ICON_REDX      = "paint-none"
P_ICON_PROCSTOP  = "process-stop"
P_ICON_NOTES     = "view-pim-notes"
P_ICON_DOWNLOAD  = "edit-download"
P_ICON_CONSOLE   = "console"
P_ICON_LOGIN     = "login"
P_ICON_GEARLOOP  = "gear-loop"
P_ICON_GEARHIER  = "gears-hierarchy"
P_ICON_GEARSTACK = "gears-stack"

P_ICON_TRIANGLE_UP    = "draw-triangle3"
P_ICON_TRIANGLE_DOWN  = "draw-triangle4"
P_ICON_TRIANGLE_LEFT  = "draw-triangle1"
P_ICON_TRIANGLE_RIGHT = "draw-triangle2"

P_ICON_D20   = "dice-d20-white"
P_ICON_GEAR  = "gear-white"
P_ICON_SKULL = "human-skull-white"
P_ICON_SKULL_RED = "human-skull-red"
P_ICON_LOCKOPEN_GREEN = "document-decrypt-green"
P_ICON_LOCKCLOSE_RED  = "document-encrypted-red"
P_ICON_CONNECTED_GREEN = "network-connect-green"
P_ICON_DISCONNECTED_RED  = "network-disconnect-red"
P_ICON_SKULL = "human-skull-white"

P_FG_REDORB = "orb_fg"
P_BG_REDORB = "redorb_bg"
P_BG_PRESSED_REDORB = "redorb_pressed"

P_DEFAULT_ICON_PATHS  = [P_MUDDO_DIR+'/images/custom-icons/',
                         P_MUDDO_DIR+'/images/breeze-dark-icons/',
                         P_MUDDO_DIR+'/images/',
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
for icon in dir():
  if icon.startswith("P_ICON") or icon.startswith("P_BG") or icon.startswith("P_FG"):
    icon = vars()[icon]
    for e in [P_DEFAULT_ICON_EXTENSION, ".png"]:
      for d in P_DEFAULT_ICON_PATHS:
        if os.path.exists(d+icon+e):
          _iconScheme[icon] = d+icon+e
          break
        elif os.path.exists(d+"/actions/"+icon+e):
          _iconScheme[icon] = d+"/actions/"+icon+e
          break
        else:
          for s in ["64", "32", "16"]:
            if os.path.exists(d+"/actions/"+s+"/"+icon+e):
              _iconScheme[icon] = d+"/actions/"+s+"/"+icon+e
              break
          else:
            continue
          break


#----------------------------------------------------------------------------------------------------------
P_CERTFILE = os.path.dirname(__file__)+"/../certificates/ca_cert2025.pem"
P_CERTCTX = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
if not os.access(P_CERTFILE, os.R_OK):
  P_CERTFILE = None
else:
  P_CERTCTX.verify_mode = ssl.CERT_REQUIRED
  P_CERTCTX.load_verify_locations(P_CERTFILE)
  P_CERTCTX.set_ciphers('DEFAULT@SECLEVEL=1')
        
#----------------------------------------------------------------------------------------------------------  
def newRQLabel(text :  str):
  lbl = QLabel(text)
  lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
  return lbl

#----------------------------------------------------------------------------------------------------------  
def newHLine():
  hline = QFrame()
  hline.setFrameStyle(QFrame.Shadow.Raised)
  hline.setFrameShape(QFrame.Shape.HLine)
  return hline

#------------------------------------------------------------------------------------
def newHLayout(objects : list) -> QHBoxLayout:
  return stackToLayout(QHBoxLayout(),objects)

#------------------------------------------------------------------------------------
def newVLayout(objects : list) -> QVBoxLayout:
  return stackToLayout(QVBoxLayout(),objects)

#------------------------------------------------------------------------------------
def newHFrame(objects : list) -> QHBoxLayout:
  f = QFrame()
  f.setLayout(stackToLayout(QHBoxLayout(),objects))
  return f

#------------------------------------------------------------------------------------
def newVFrame(objects : list) -> QHBoxLayout:
  f = QFrame()
  f.setLayout(stackToLayout(QVBoxLayout(),objects))
  return f

#------------------------------------------------------------------------------------
def stackToLayout(layout : QLayout, objects : list) -> QLayout:
  for v in objects:
    if isinstance(v,str):
      if v == "__stretch__":
        layout.addStretch()
      else:
        layout.addWidget(QLabel(v))
    elif issubclass(v.__class__,QLayout):
      layout.addLayout(v)
    else:
      layout.addWidget(v)
  return layout

#----------------------------------------------------------------------------------------------------------  
def getArrow():
  fs = QLabel().font().pointSize()
  return f"&nbsp;&nbsp;&nbsp;<span style='font-size:{fs+4}pt'>▾</span>"

#----------------------------------------------------------------------------------------------------------  
def getPixmap(a0 : str) -> QPixmap:
  if isinstance(a0, str):
    if a0 in _iconScheme.keys():
      return QPixmap(_iconScheme[a0])
    elif os.path.exists(a0):
      return QPixmap(a0)
    else:
      return QPixmap()
  if isinstance(a0, QIcon):
    return a0.pixmap(a0.actualSize())
  elif isinstance(a0, QPixmap):
     return a0
  else:
    return QPixmap()

#----------------------------------------------------------------------------------------------------------  
def getIcon(a0) -> QIcon:
  if isinstance(a0, QIcon):
    return a0
  elif isinstance(a0, QPixmap):
     return QIcon(a0)
  elif isinstance(a0, str):
     return QIcon(getPixmap(a0))
  else:
    return QIcon()

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

#----------------------------------------------------------------------------------------------------------
def newToolbarButton(icon, tooltip, connection):
  btn = QPushButton()
  btn.setIcon(getIcon(icon))
  btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  btn.setEnabled(False)
  btn.setToolTip(tooltip)
  btn.clicked.connect(connection)
  return btn

#----------------------------------------------------------------------------------------------------------
def newHeaderLabel(title, width=80):
  hlbl = QLabel(title)
  hlbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
  hlbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  hlbl.setFixedWidth(width)
  return hlbl

#----------------------------------------------------------------------------------------------------------
def newProcessField(title, width=80):
  flbl = QLabel(title)
  flbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
  flbl.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
  flbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  flbl.setFixedWidth(width)
  return flbl
  
#----------------------------------------------------------------------------------------------------------
def pathLinux2Windows(linuxPath : str):
  tmp = linuxPath.split('/')
  tmp = tmp[tmp.index('drive_c')+1:]
  return "C:\\" + "\\".join(tmp)

#----------------------------------------------------------------------------------------------------------
def getPrefix(linuxPath : str):
  tmp = linuxPath.split('/')
  return "/".join(tmp[0:tmp.index('drive_c')])

#----------------------------------------------------------------------------------------------------------
# This encoder is originally taken from
#   https://gist.github.com/jannismain/e96666ca4f059c3e5bc28abb711b5c92
# with some minor modifications
class muJSONEncoder(json.JSONEncoder):
    CONTAINER_TYPES = (list, tuple, dict)
    MAX_WIDTH = 1024
    MAX_ITEMS = 100
    
    def __init__(self, *args, **kwargs):
        # using this class without indentation is pointless
        kwargs["indent"] = 2
        kwargs["separators"]=(', ',': ')
        super().__init__(*args, **kwargs)
        self.indentation_level = 0

    def encode(self, o):
        if isinstance(o, (list, tuple)):
            return self._encode_list(o)
        if isinstance(o, dict):
            return self._encode_object(o)
        return json.dumps(
            o,
            skipkeys=self.skipkeys,
            ensure_ascii=self.ensure_ascii,
            check_circular=self.check_circular,
            allow_nan=self.allow_nan,
            sort_keys=self.sort_keys,
            indent=self.indent,
            separators=(self.item_separator, self.key_separator),
            default=self.default if hasattr(self, "default") else None,
        )

    def _encode_list(self, o):
        if self._put_on_single_line(o):
            return "[" + ", ".join(self.encode(el) for el in o) + "]"
        self.indentation_level += 1
        output = [self.indent_str + self.encode(el) for el in o]
        self.indentation_level -= 1
        return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"

    def _encode_object(self, o):
        if not o:
            return "{}"

        # ensure keys are converted to strings
        o = {str(k) if k is not None else "null": v for k, v in o.items()}

        if self.sort_keys:
            o = dict(sorted(o.items(), key=lambda x: x[0]))

        if self._put_on_single_line(o):
            return (
                "{ "
                + ", ".join(
                    f"{self.encode(k)}: {self.encode(el)}" for k, el in o.items()
                )
                + " }"
            )

        self.indentation_level += 1
        output = [
            f"{self.indent_str}{self.encode(k)}: {self.encode(v)}" for k, v in o.items()
        ]
        self.indentation_level -= 1

        return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"

    def iterencode(self, o, **kwargs):
        """Required to also work with `json.dump`."""
        return self.encode(o)

    def _put_on_single_line(self, o):
        return (
            self._primitives_only(o)
            and len(o) <= self.MAX_ITEMS
            and len(str(o)) - 2 <= self.MAX_WIDTH
        )

    def _primitives_only(self, o: list | tuple | dict):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self) -> str:
        if isinstance(self.indent, int):
            return " " * (self.indentation_level * self.indent)
        elif isinstance(self.indent, str):
            return self.indentation_level * self.indent
        else:
            raise ValueError(
                f"indent must either be of type int or str (is: {type(self.indent)})"
            )