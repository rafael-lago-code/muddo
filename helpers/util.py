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
import re
from PyQt6.QtWidgets import QLabel, QPushButton, QSizePolicy, QFrame, QHBoxLayout, QSplitter, \
                            QVBoxLayout, QLayout, QFrame
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QImage
from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6 import QtCore
from http.client import HTTPConnection, HTTPSConnection
import ssl, json, yaml

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  D E F A U L T S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
C_SILVER = "<font style=\"color:#828282\">"
C_RED = "<font style=\"color:#ff6969\">"
C_ORANGE = "<font style=\"color:#ffa744\">"
C_GREEN = "<font style=\"color:#6aff83\">"
C_BLUE = "<font style=\"color:#43b7ff\">" 

# P_DEFAULT_WORKDIR    = os.environ['HOME'] + "/.local/share/muDDO"
P_MUDDO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P_DEFAULT_CONFIGDIR  = os.environ['HOME'] + "/.config/muDDO"
P_DEFAULT_MACRODIR   = P_DEFAULT_CONFIGDIR + "/macros"
P_DEFAULT_MACROEXT = ".macro"
P_DEFAULT_FILTERSDIR   = P_DEFAULT_CONFIGDIR + "/filters"
P_DEFAULT_FILTEREXT = ".filter"
P_DEFAULT_WORKDIR    = P_DEFAULT_CONFIGDIR
P_DEFAULT_CONFIGFILE = P_DEFAULT_CONFIGDIR + "/settings.json"

P_DEFAULT_SERVERDIR   = P_DEFAULT_CONFIGDIR+"/serverInfo/"
P_DEFAULT_SERVERCONFIG= P_DEFAULT_SERVERDIR+"/dndlauncher.server.xml"
P_DEFAULT_LOGSDIR     = P_DEFAULT_CONFIGDIR+"/logs/"

P_DEFAULT_CONF    = "muDDO/settings"
P_DEFAULT_SHM_DIR = "/dev/shm/milvian/"

P_CERTFILE = None
P_CERTCTX = None

P_DEFAULT_BG = QColor(27, 30, 32, 240)
P_EXTENDED_SETTINGS_FILE = os.path.join(P_DEFAULT_CONFIGDIR, "extendedSettings.yaml")

DB_ITEM_COLS = ["id","storage_type","name","owner_id","owner_name","weenie_id","type",
                "quantity","qualifier","value_copper","hardness","durability","icon_id",
                "description","min_level","material","is_junk","is_locked","is_minor_artifact",
                "is_sellable","set_bonus_1","set_bonus_2","current_slot","binding","equips_to",
                "augments","effects"]



# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  C E R T I F I C A T E   D E T E C T I O N
#
#    Probably outdated strategy, called at the first "import"...
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
P_CERTFILE = os.path.dirname(__file__)+"/../certificates/ca_cert2025.pem"
P_CERTCTX = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
if not os.access(P_CERTFILE, os.R_OK):
  P_CERTFILE = None
else:
  P_CERTCTX.verify_mode = ssl.CERT_REQUIRED
  P_CERTCTX.load_verify_locations(P_CERTFILE)
  P_CERTCTX.set_ciphers('DEFAULT@SECLEVEL=1')


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def loadExtendedSettings() -> dict:
  try:
    with open(P_EXTENDED_SETTINGS_FILE, "r") as f:
      return yaml.safe_load(f) or {}
  except Exception:
    return {}

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────  
def newRQLabel(text :  str):
  lbl = QLabel(text)
  lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
  return lbl

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newHLine():
  hline = QFrame()
  hline.setFrameStyle(QFrame.Shadow.Raised)
  hline.setFrameShape(QFrame.Shape.HLine)
  return hline

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newHLayout(objects : list, font=None) -> QHBoxLayout:
  return stackToLayout(QHBoxLayout(), objects, font)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newVLayout(objects : list, font=None) -> QVBoxLayout:
  return stackToLayout(QVBoxLayout(), objects, font)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newHFrame(objects : list, font=None) -> QFrame:
  f = QFrame()
  f.setLayout(stackToLayout(QHBoxLayout(), objects, font))
  return f

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newVFrame(objects : list, font=None) -> QFrame:
  f = QFrame()
  f.setLayout(stackToLayout(QVBoxLayout(), objects, font))
  return f

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def hLayout(*objects, font=None) -> QHBoxLayout:
  return stackToLayout(QHBoxLayout(), list(objects), font)

def vLayout(*objects, font=None) -> QVBoxLayout:
  return stackToLayout(QVBoxLayout(), list(objects), font)

def hFrame(*objects, font=None) -> QFrame:
  f = QFrame()
  f.setLayout(stackToLayout(QHBoxLayout(), list(objects), font))
  return f

def vFrame(*objects, font=None) -> QFrame:
  f = QFrame()
  f.setLayout(stackToLayout(QVBoxLayout(), list(objects), font))
  return f

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newVSplitter(objects : list, font=None) -> QSplitter:
  f = QSplitter(Qt.Orientation.Vertical)
  appendWidget(f, objects, font)
  return f

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def newHSplitter(objects : list, font=None) -> QSplitter:
  f = QSplitter(Qt.Orientation.Horizontal)
  appendWidget(f, objects, font)
  return f

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def appendWidget(container, objects : list, font=None) -> QLayout:
  for v in objects:
    if isinstance(v, str):
      lbl = QLabel(v)
      if font: lbl.setFont(font)
      container.addWidget(lbl)
    else:
      container.addWidget(v)
  return container

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def stackToLayout(layout : QLayout, objects : list, font=None) -> QLayout:
  for v in objects:
    if isinstance(v, str):
      if v == "__stretch__":
        layout.addStretch()
      elif v == "__separator__" or v == "__line__":
        t = QFrame()
        t.setFixedHeight(2)
        if isinstance(layout, QHBoxLayout):
          t.setFrameShape(QFrame.Shape.VLine)
        else:
           t.setFrameShape(QFrame.Shape.HLine)
        t.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(t)
      else:
        lbl = QLabel(v)
        if font: lbl.setFont(font)
        layout.addWidget(lbl)
    elif issubclass(v.__class__, QLayout):
      layout.addLayout(v)
    else:
      layout.addWidget(v)
  return layout

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def getArrow():
  fs = QLabel().font().pointSize()
  return f"&nbsp;&nbsp;&nbsp;<span style='font-size:{fs+4}pt'>▾</span>"

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def getConnection(urlIn, timeout=15):
  if urlIn.upper().find("HTTP://") >= 0:
    url = urlIn[7:].split("/")[0]
    post = urlIn[7:].replace(url, "")
    return HTTPConnection(url, timeout=timeout), post
  else:
    url = urlIn[8:].split("/")[0]
    post = urlIn[8:].replace(url, "")
    return HTTPSConnection(url, context=P_CERTCTX, timeout=timeout), post
    
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
def getNodeText(nodelist):
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE or node.nodeType == node.CDATA_SECTION_NODE:
			rc = rc + node.data
	return rc

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
def newHeaderLabel(title, width=80):
  hlbl = QLabel(title)
  hlbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
  hlbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  hlbl.setFixedWidth(width)
  return hlbl

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
def newProcessField(title, width=80):
  flbl = QLabel(title)
  flbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
  flbl.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
  flbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
  flbl.setFixedWidth(width)
  return flbl

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
def newCell(text, data=None):
  from PyQt6.QtCore import Qt
  from PyQt6.QtWidgets import QTableWidgetItem
  cell = QTableWidgetItem(str(text))
  cell.setData(Qt.ItemDataRole.UserRole, data if data else text)
  return cell

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
def pathLinux2Windows(linuxPath : str):
  tmp = linuxPath.split('/')
  tmp = tmp[tmp.index('drive_c')+1:]
  return "C:\\" + "\\".join(tmp)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
def getPrefix(linuxPath : str):
  tmp = linuxPath.split('/')
  return "/".join(tmp[0:tmp.index('drive_c')])

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
class setBGColour(QObject):
  def __init__(self, viewport, color: QColor):
    super().__init__(viewport)
    self._color = color
    viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    viewport.installEventFilter(self)

  def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.Paint:
      p = QPainter(obj)
      p.fillRect(obj.rect(), self._color)
      p.end()
    return False

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────----------------------
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