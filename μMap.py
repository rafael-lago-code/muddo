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
import os, struct, glob, mmap, math
from PyQt6 import sip
from PyQt6.QtWidgets import QLineEdit, QWidget, QComboBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QSlider, QTextEdit, QVBoxLayout, QHBoxLayout, QProxyStyle, QStyle
from PyQt6.QtGui import QPixmap, QImage, QPainter, QWheelEvent
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QObject, QPointF, pyqtProperty
from helpers.μImageFactory import *
from helpers.util import P_DEFAULT_SHM_DIR
from helpers.μStrings import μString
from helpers.μPrint import μPrint
from widgets.μFloating import μToggler
from widgets.μOrb import μOrbSmall
from widgets.μText import μDisplayLabel
from μSettings import μSetup
from μMilvian import μMilvianMeta, μMilvian
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from μMilvian import μMilvian


P_MAP_DIR = P_DEFAULT_SHM_DIR

P_TYPE_MAIN          = 1
P_TYPE_PLAYER        = 2
P_TYPE_PET           = 3
P_PLAYER_PINS: dict[int, str] = {
  1: "main",
  2: "token_player",
  3: "token_pet",
  4: "token_green",
  5: "token_hireling",
  6: "token_pet_others",
}

P_TYPE_TARGET        = 30
P_TYPE_DISTANT_PARTY = 31
P_EDGE_PINS: dict[int, str] = {
  30: "target",
  31: "distant_party",
}

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# P_ENTITY_PINS
# 100-500: static pins, but with entity context as well. 
# 1000-1200: pure entity pins, stuff that you wouldn't see in the static pin list
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
P_ENTITY_PINS: dict[int, str] = {
  # Block - Teleports
  100: "teleport",
  101: "teleport_red",
  110: "area_yellow",
  111: "area_red",
  120: "airship",
  # Block - Amenities
  200: "shrine",
  201: "shrine_ress",  # extra
  210: "bank",
  215: "auction",
  220: "mailbox",
  225: "crafting",
  230: "patron",
  235: "trainer",
  240: "poi",
  245: "spirit_binder", # extra
  # Block - Vendors
  300: "tavern",
  305: "token_vendor",
  310: "token_pawn",
  315: "collector",
  320: "hireling_vendor",
  # Block - Doors
  350: "door_yellow",
  351: "door_blue",
  352: "door_red",
  353: "door_grey",
  360: "door_raid_yellow",
  # Block - Chalices
  370: "check",
  380: "chalice_raid",
  381: "chalice_raid_blue",
  382: "chalice_raid_grey",
  383: "chalice_raid_red",
  400: "chalice_yellow",
  401: "chalice_blue",
  402: "chalice_grey",
  403: "chalice_red",
  420: "chalice_arc",
  421: "chalice_arc_blue",
  430: "chalice_saga",
  431: "chalice_saga_blue",
  # Block - Challenges
  450: "challenge_blue",
  451: "challenge_grey",
  452: "challenge_red",
  # ─────────────────────────────────────────────────
  # Block - Dungeon Stuff
  # TODO move "chest" to static and shift all indices
  1000: "chest",
  1010: "explorer",
  1015: "soul_stone",
  1020: "crest",
  1021: "crest_socket",
  1025: "token_npc",
  1030: "dimension_door",
  1035: "mysterious_remnants",
  1040: "lostsoul",
  1050: "usable",
  1051: "control_panel",
  1052: "collectible",
  1053: "item_dropped",
  1060: "trap",
  1061: "secret",
  1070: "ladder",
  1071: "door_grey",
  1075: "collectible_taken",
  # Block - Enemies
  1100: "champion_yellow",
  1101: "champion_orange",
  1102: "champion_red",
  1110: "boss_reaper",
  1111: "boss_mini",
  1112: "boss",
  1113: "boss_raids",
  1120: "enemy",
  # Block - Others
  1150: "friendly",
  1160: "breakeable",
  1170: "token_red",
  1180: "token_other",
}

P_STATIC_PINS_SHIFT=500
P_STATIC_PINS_START=600
P_STATIC_PINS_END=999
P_STATIC_PINS = {k+P_STATIC_PINS_SHIFT:v for k,v in P_ENTITY_PINS.items() if k<500}

  # Block - VeryMuchNotInTheEnum
P_STATIC_PINS[1520] = "crest"
P_STATIC_PINS[1521] = "crest_socket"
P_STATIC_PINS[1525] = "token_npc"
P_MAP_PINS: dict[int, str] = P_PLAYER_PINS | P_EDGE_PINS | P_STATIC_PINS | P_ENTITY_PINS


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  L A Y O U T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
# Header: <I4sI64s = uint32 + char[4] + uint32(playerCount) + char[64](areaName) = 76 bytes
_HEADER  = struct.Struct('<I4sI64s')
# Player: <Qfff64s = ulong + 3×float32 (cx,cy,heading) + char[64] = 84 bytes
_PLAYER  = struct.Struct('<Qfff64s')
# Entity/Static: <Qff64sI = ulong + 2×float32 (cx,cy) + char[64] + uint32 = 84 bytes
_ENTITY  = struct.Struct('<Qff64sI')

_MAX_PLAYERS      = 24
_OFF_STATIC_COUNT = _HEADER.size + _MAX_PLAYERS * _PLAYER.size  # 76 + 24*84 = 2092
_OFF_STATIC_START = _OFF_STATIC_COUNT + 4                        # 2096

assert _HEADER.size == 76
assert _PLAYER.size == 84
assert _ENTITY.size == 84
assert _OFF_STATIC_COUNT == 2092
assert _OFF_STATIC_START == 2096


class _RotRelay(QObject):
  def __init__(self, pin): super().__init__(); self._pin = pin
  def _get(self): return self._pin.rotation()
  def _set(self, v): self._pin.setRotation(v)
  rotation = pyqtProperty(float, _get, _set)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   P I N
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMapPin(QGraphicsPixmapItem):
  cache: dict[str, QPixmap] = {}

  def __init__(self, id: int, cx: float, cy: float, name: str,
               pinType: int = 0, heading: float = 0.0):
    super().__init__()
    self.id      = id
    # self.weenie  = weenie
    self.cx      = cx
    self.cy      = cy
    self.name    = name
    self.pinType = pinType
    self.heading = heading
    self._relay      = _RotRelay(self)
    self._rotAnim    = None
    self._selOverlay = None
    self.setZValue(-pinType)
    self.setup()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def pinTypeName(self) -> str:
    return "map/pin_" + P_MAP_PINS.get(self.pinType, "token_red")
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def isStatic(self) -> str:
    return P_STATIC_PINS_START <= self.pinType <= P_STATIC_PINS_END

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setup(self):
    name = self.pinTypeName()
    if name not in μMapPin.cache:
      μMapPin.cache[name] = getPixmap(name).scaled(
        μMap.pinSize, μMap.pinSize,
        Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    self.setPixmap(μMapPin.cache[name])
    self.setToolTip(self.name)
    self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    self.setOffset(-μMap.pinSize / 2, -μMap.pinSize / 2)
    self.setCursor(Qt.CursorShape.PointingHandCursor)
    if self.pinType == P_TYPE_MAIN: self.setRotation(self.heading)  # instant on setup; animated via rotateTo() after

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def paint(self, painter, option, widget=None):
    option.state &= ~QStyle.StateFlag.State_Selected
    super().paint(painter, option, widget)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def itemChange(self, change, value):
    if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
      if value:
        if μMap.runningBridge and not self.isStatic(): μMap.runningBridge.selectEntity(self.id)
        sel_key = 'map/pin_selected'
        if sel_key not in μMapPin.cache:
          μMapPin.cache[sel_key] = getPixmap(sel_key).scaled( μMap.pinSize, μMap.pinSize,
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._selOverlay = QGraphicsPixmapItem(μMapPin.cache[sel_key], self)
        self._selOverlay.setOffset(-μMap.pinSize / 2, -μMap.pinSize / 2)
        self._selOverlay.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)
      elif self._selOverlay:
        self._selOverlay.setParentItem(None)
        self._selOverlay = None
    return super().itemChange(change, value)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def rotateTo(self, heading: float, duration: int):
    current = self.rotation()
    delta = (heading - current) % 360
    if delta > 180: delta -= 360
    target = current + delta
    self.heading = heading
    if self._rotAnim:
      self._rotAnim.stop()
    self._rotAnim = QPropertyAnimation(self._relay, b"rotation")
    self._rotAnim.setDuration(duration)
    self._rotAnim.setStartValue(current)
    self._rotAnim.setEndValue(target)
    self._rotAnim.start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __repr__(self):
    kind = "player" if self.pinType in P_PLAYER_PINS else "entity"
    return f'μMapPin({self.id:#x} {kind} "{self.name}" pin={self.pinType} px=({self.cx:.1f},{self.cy:.1f}))'


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   P A R S E R
#
#       Parses the 'map' binary file written by μMap.dumpEntities() on the C# side.
#       Updates the pins dict in-place: creates new μMapPin for new IDs, updates cx/cy for existing.
#       Returns (ok, seen_ids).
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMapParser:
  def __init__(self):
    self.mapId    : int = 0
    self.ext      : str = ''
    self.areaName : str = ''

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def dataPath() -> str: return f"{μMap.runningBridge.bridgePath}/{μMap.runningBridge.charName.lower()}/map"
  def imagePath(self) -> str: return f"{μMapParser.dataPath()}{self.ext}"

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def load(self, map, path: str = None) -> tuple[bool, set]:

    if μMap.runningBridge is None: return False, set()
    path = path or μMapParser.dataPath()
    if not os.path.exists(path):
      return False, set()
    mm = None
    try:
      with open(path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
      data = mm
      if len(data) < _HEADER.size:
        return False, set()
      old_mapId    = self.mapId
      old_areaName = self.areaName
      (mapId, ext_b, nPlayers, area_b) = _HEADER.unpack_from(data, 0)
      self.mapId    = mapId
      self.ext      = ext_b.rstrip(b'\x00').decode('ascii', errors='replace')
      self.areaName = area_b.rstrip(b'\x00').decode('utf-8', errors='replace')
      seen: set[int] = set()

      # Players — fixed 24-slot block
      poff = _HEADER.size
      for i in range(nPlayers):
        if poff + _PLAYER.size > len(data): break
        (pid, cx, cy, heading, name_b) = _PLAYER.unpack_from(data, poff)
        name = name_b.rstrip(b'\x00').decode('utf-8', errors='replace')
        if pid in map.playerPins:
          p = map.playerPins[pid]
          p.cx, p.cy = cx, cy
          if i == 0 and p.heading != heading:
            p.rotateTo(heading, μSetup.profile.map.refreshInterval())
        else:
          pin_type = P_TYPE_MAIN if i == 0 else (P_TYPE_PET if hex(pid).startswith("0x3") else P_TYPE_PLAYER)
          map.playerPins[pid] = μMapPin(pid, cx, cy, name, pinType=pin_type, heading=heading)
        seen.add(pid)
        poff += _PLAYER.size

      # Static pins — written once per area on C# side
      if len(data) < _OFF_STATIC_COUNT + 4: return True, seen
      (nStatics,) = struct.unpack_from('<I', data, _OFF_STATIC_COUNT)

      if mapId != old_mapId or self.areaName != old_areaName or nStatics != len(map.staticPins):
        for pin in map.staticPins.values():
          if pin.scene() is not None: map._scene.removeItem(pin)
        map.staticPins.clear()
        for i in range(nStatics):
          soff = _OFF_STATIC_START + i * _ENTITY.size
          if soff + _ENTITY.size > len(data): break
          (eid, cx, cy, name_b, pin_type) = _ENTITY.unpack_from(data, soff)
          name = name_b.rstrip(b'\x00').decode('utf-8', errors='replace')
          map.staticPins[i] = μMapPin(eid, cx, cy, name, pinType=pin_type+P_STATIC_PINS_SHIFT)
          μMap.applyPinFilter(map.filter.text(), map.staticPins[i])

      # Entities — after static section
      entity_count_off = _OFF_STATIC_START + nStatics * _ENTITY.size
      if len(data) < entity_count_off + 4: return True, seen
      (nEntities,) = struct.unpack_from('<I', data, entity_count_off)
      if nEntities == 0: return False, set() # skips this refresh frame, no need to remove any pins
      eoff = entity_count_off + 4

      for _ in range(nEntities):
        if eoff + _ENTITY.size > len(data): break
        (eid, cx, cy, name_b, pin_type) = _ENTITY.unpack_from(data, eoff)
        name = name_b.rstrip(b'\x00').decode('utf-8', errors='replace')
        if eid in map.entityPins:
          map.entityPins[eid].cx, map.entityPins[eid].cy = cx, cy
        else:
          map.entityPins[eid] = μMapPin(eid, cx, cy, name, pinType=pin_type)
          μMap.applyPinFilter(map.filter.text(), map.entityPins[eid])

        seen.add(eid)
        eoff += _ENTITY.size
      return True, seen
    except Exception as e:
      μPrint.error(f'[μMap.load] {e}')
      return False, set()
    finally:
      if mm is not None: mm.close()


class _FastTooltipStyle(QProxyStyle):
  def styleHint(self, hint, option=None, widget=None, returnData=None):
    if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay: return 100
    return super().styleHint(hint, option, widget, returnData)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   V I E W
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMapView(QGraphicsView):

  def __init__(self, scene: QGraphicsScene, mapWidget: 'μMap'):
    super().__init__(scene)
    self._map = mapWidget
    self.setStyle(_FastTooltipStyle())
    self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
    self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    self.setRenderHint(QPainter.RenderHint.Antialiasing)
    self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    self.setBackgroundBrush(Qt.GlobalColor.black)
    self.toolbar = QWidget(self)
    self.toolbar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
    self.toolbar.setFixedWidth(48)

  def _getCenter(self): return self.mapToScene(self.viewport().rect().center())
  def _setCenter(self, pt): self.centerOn(pt)
  center = pyqtProperty(QPointF, _getCenter, _setCenter)

  def mousePressEvent(self, event):
    if event.button() == Qt.MouseButton.RightButton:
      self.scene().clearSelection()
    else:
      μMap.centerMode = 'none'
      self._map._scrollTarget = None
      self._map._scrollTimer.stop()
      super().mousePressEvent(event)

  def _repositionToolbar(self):
    self.toolbar.move(self.width() - self.toolbar.width(), self.height() - self.toolbar.height())

  def resizeEvent(self, event):
    super().resizeEvent(event)
    self._repositionToolbar()

  def showEvent(self, event):
    super().showEvent(event)
    self._repositionToolbar()

  def wheelEvent(self, event: QWheelEvent):
    delta = event.angleDelta().y()
    mods  = event.modifiers()
    if mods & Qt.KeyboardModifier.ControlModifier:
      factor = 1.15 if delta > 0 else 1 / 1.15
      self.scale(factor, factor)
    elif mods & Qt.KeyboardModifier.ShiftModifier:
      self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
    else:
      self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   W I D G E T
#
#       Displays the map image from /dev/shm/milvian/map.{ext} with a refresh button.
#       Watches the file for changes and reloads automatically.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMap(μToggler):
  runningBridge : μMilvian = None
  selectedPin   : 'μMapPin | None' = None
  centerMode    : str = 'cartographer'
  upscale = 4
  pinSize = 16*upscale

  def __init__(self, parent=None):
    self.widgetID = "Map"
    super().__init__("Map", P_ICON_MAP)
    self.toggler.setToolTip("Show/Hide Map")
    self.parser = μMapParser()
    self.entityPins: dict[int, μMapPin] = {}
    self.staticPins: dict[int, μMapPin] = {}
    self.playerPins: dict[int, μMapPin] = {}
    self.edgePins: dict[int, μMapPin] = {}
    self._selEdgePin: μMapPin | None = None
    self.setMinimumSize(320, 240)

    self._scene = QGraphicsScene()
    self._bgItem = QGraphicsPixmapItem()
    self._bgItem.setZValue(-10000)
    self._scene.addItem(self._bgItem)
    self.view = μMapView(self._scene, self)
    self._scrollTarget: QPointF = None
    self._scrollTimer = QTimer()
    self._scrollTimer.setInterval(16)
    self._scrollTimer.timeout.connect(self._scrollStep)

    self.btnPrint = μOrbSmall(icon=P_ICON_REFRESH, tooltip='Print entities for debugging')
    self.btnPlay = μOrbSmall(icon=P_ICON_PLAY, tooltip='Request Milvian to start collecting map data')
    self.btnStop = μOrbSmall(icon=P_ICON_STOP, tooltip='Request Milvian to stop collecting map data')
    self._timer = QTimer()
    self._timer.timeout.connect(self.refresh)
    self.btnPrint.clicked.connect(self.printEntities)
    self.btnPlay.clicked.connect(self.startMapsDaemon)
    self.btnStop.clicked.connect(self.stopMapsDaemon)

    self.btnRefresh   = μOrbSmall(icon=P_ICON_REFRESH, tooltip='Reload map view.<br><b><i>Ctrl+click</i></b> restarts map daemon altogether.')
    self.btnCenterMain = μOrbSmall(icon="thick_arrow_up", tooltip='Center on view Cartographer')
    self.btnCenterSelect = μOrbSmall(icon="bullseye", tooltip='Center on view target Object')
    self.btnSelectTarget = μOrbSmall(icon='hand-select', tooltip='Select (in-game) the target object')
    self.btnDetails = μOrbSmall(icon='view-visible', tooltip='Show/Hide Details')
    self.filter = QLineEdit()
    self.lblTargetPin = QLabel()
    self.lblAreaId = QLabel()
    self.lblAreaId.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.lblAreaId.setWordWrap(True)
    self.lblTargetName = QLabel("None")
    self.lblTargetName.setWordWrap(True)
    self.lblTargetName.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.cartographer = QComboBox()
    self.mapOpacity = QSlider(); self.mapOpacity.setRange(0,100); self.mapOpacity.setValue(100)
    self.entityOpacity = QSlider(); self.entityOpacity.setRange(0,100); self.entityOpacity.setValue(100)
    self.staticOpacity = QSlider(); self.staticOpacity.setRange(0,100); self.staticOpacity.setValue(100)
    self.playerOpacity = QSlider(); self.playerOpacity.setRange(0,100); self.playerOpacity.setValue(100)
    self.details = vFrame(μDisplayLabel("Cartographer:"), self.cartographer, " ", μDisplayLabel("Area ID:"), self.lblAreaId, " ",
                          μDisplayLabel("Selection:"), hLayout(self.lblTargetPin, self.lblTargetName),
                              "__stretch__", μDisplayLabel("Opacity:"), hLayout(self.mapOpacity, self.playerOpacity, self.staticOpacity, self.entityOpacity),
                              hLayout("__stretch__", "map", "__stretch__", "party", "__stretch__", "static", "__stretch__", "entities", "__stretch__"), "__stretch__", μDisplayLabel("Search:"), self.filter)
    self.details.setFixedWidth(200)
    self.details.hide()

    self.btnRefresh.clicked.connect(self.refresh)
    self.btnRefresh.ctrlClicked.connect(lambda : self.startMapsDaemon()) # this does restart if it is already running
    self.btnDetails.clicked.connect(lambda: (
      self.details.setVisible(not self.details.isVisible()),
      μSetup.profile and μSetup.profile._state.setValue("map/uiDetailsVisible", self.details.isVisible())))
    self._scene.selectionChanged.connect(self.onSelectionChanged)

    self.cartographer.currentTextChanged.connect(self.startMapsDaemon)
    self.mapOpacity.valueChanged.connect(self.setMapOpacity)
    self.mapOpacity.valueChanged.connect(   lambda v: μSetup.profile and μSetup.profile._state.setValue("map/uiMapOpacity",    v))
    self.entityOpacity.valueChanged.connect(lambda x: self.setPinsOpacity(x/100.0, entity=True))
    self.entityOpacity.valueChanged.connect(lambda v: μSetup.profile and μSetup.profile._state.setValue("map/uiEntityOpacity", v))
    self.staticOpacity.valueChanged.connect(lambda x: self.setPinsOpacity(x/100.0, static=True))
    self.staticOpacity.valueChanged.connect(lambda v: μSetup.profile and μSetup.profile._state.setValue("map/uiStaticOpacity", v))
    self.playerOpacity.valueChanged.connect(lambda x: self.setPinsOpacity(x/100.0, player=True))
    self.playerOpacity.valueChanged.connect(lambda v: μSetup.profile and μSetup.profile._state.setValue("map/uiPlayerOpacity", v))
    μSetup.widget.sigProfileChanged.connect(lambda p, _: self._restoreMapState(p._state))
    self.btnSelectTarget.clicked.connect(self.selectTarget)
    self.btnCenterMain.clicked.connect(lambda: self.setCenterOn('cartographer'))
    self.btnCenterSelect.clicked.connect(lambda: self.setCenterOn('target'))
    self.filter.editingFinished.connect(self.filterPins)

    # toolbar_widget = QWidget(self.view)
    tl = QVBoxLayout()
    tl.addWidget(self.btnCenterMain)
    tl.addWidget(self.btnCenterSelect)
    tl.addWidget(self.btnSelectTarget)
    tl.addSpacing(10)
    tl.addWidget(self.btnDetails)
    tl.addWidget(self.btnRefresh)
    tl.addSpacing(10)
    self.view.toolbar.setLayout(tl)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addLayout(newHLayout([self.view, self.details]))
    self.setLayout(layout)
 
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def toggle(self):
    if self.isVisible():
      self.hide()
      self.stopMapsDaemon()
    else:
      self.show()
      self.startMapsDaemon()
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  #    Select the in-game object associated with the currently targeted pin
  def selectTarget(self):
    if μMap.selectedPin and μMap.runningBridge: 
      if self.selectedPin.isStatic(): return
      μMap.runningBridge.selectEntity(μMap.selectedPin.id)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _restoreMapState(self, state):
    self.mapOpacity.setValue(   int(state.value("map/uiMapOpacity",    100)))
    self.playerOpacity.setValue(int(state.value("map/uiPlayerOpacity", 100)))
    self.staticOpacity.setValue(int(state.value("map/uiStaticOpacity", 100)))
    self.entityOpacity.setValue(int(state.value("map/uiEntityOpacity", 100)))
    self.details.setVisible(state.value("map/uiDetailsVisible", False, type=bool))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def filterPins(self):
    text = self.filter.text()
    for pin in list(self.entityPins.values()) + list(self.staticPins.values()):
      μMap.applyPinFilter(text, pin)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def applyPinFilter(text, pin : μMapPin):
    pin.setVisible(not text or μString(pin.name) == text)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setCenterOn(self, target):
    μMap.centerMode = target
    if target == 'cartographer':
      p = next((pin for pin in self.playerPins.values() if pin.pinType == P_TYPE_MAIN), None)
      if p: self._startScroll(p.cx * μMap.upscale, p.cy * μMap.upscale)
    elif target == 'target':
      if μMap.selectedPin:
        self._startScroll(μMap.selectedPin.cx * μMap.upscale, μMap.selectedPin.cy * μMap.upscale)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setPinSize(cls, size):
    new = size * cls.upscale
    if new != cls.pinSize:
      cls.pinSize = new
      μMapPin.cache.clear()
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setUpscale(cls, size): cls.upscale = size

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setMapSize(cls, width, height):
    cls.mapWidth = width*cls.upscale
    cls.mapHeight = height*cls.upscale

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clear(self, clearCache=False):
    for item in self.playerPins.values(): self._scene.removeItem(item)
    self.playerPins.clear()
    for item in self.entityPins.values(): self._scene.removeItem(item)
    self.entityPins.clear()
    for item in self.staticPins.values(): self._scene.removeItem(item)
    self.staticPins.clear()
    for item in self.edgePins.values(): self._scene.removeItem(item)
    self.edgePins.clear()
    if clearCache: μMapPin.cache.clear()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setMapOpacity(self, val : int):
    self._bgItem.setOpacity(val/100.0)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setPinsOpacity(self, val : float, player = False, static = False, entity = False):
    if player:
      for pin in self.playerPins.values(): pin.setOpacity(val)
      for pin in self.edgePins.values(): pin.setOpacity(val)
    if static:
      for pin in self.staticPins.values(): pin.setOpacity(val)
    if entity:
      for pin in self.entityPins.values(): pin.setOpacity(val)


  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def refresh(self):
    oldPinSize = μMap.pinSize
    oldImageId = self.parser.mapId
    oldAreaName = self.parser.areaName
    μMap.setPinSize(μSetup.profile.map.iconSize())
    ok, seen = self.parser.load(self)

    if self.parser.mapId != oldImageId:
      μMap.centerMode = 'cartographer'
      μPrint.info(f'[μMap] ID changed: {C_ORANGE}{oldAreaName}</font> ➜ {C_ORANGE}{self.parser.areaName}</font>')
      path = self.parser.imagePath()
      pix = QPixmap.fromImage(QImage(path))
      if pix.isNull():
        μPrint.error(f'[μMap] Failed to load {path}')
        μMap.setWindowTitle(f"Map - Unknown")
        self.lblAreaId.setText("")
        self.parser.mapId = -1
        return
      μMap.setUpscale(int(μSetup.profile.map.upscale()/100))
      μMap.setMapSize(pix.width(), pix.height())
      self.setWindowTitle(f"Map - {self.parser.areaName}")
      self.lblAreaId.setText(str(self.parser.mapId))
      self._bgItem.setPixmap(pix.scaled(μMap.mapWidth, μMap.mapHeight,
        Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
      self._scene.setSceneRect(0, 0, μMap.mapWidth, μMap.mapHeight)
      self.view.resetTransform()
      zoom = μSetup.profile.map.mapZoom() / (100 * μMap.upscale)
      self.view.scale(zoom, zoom)

    if not ok: return

    if μMap.pinSize != oldPinSize:
      for pin in self.edgePins.values(): pin.setup()
      for pin in self.playerPins.values(): pin.setup()
      for pin in self.entityPins.values(): pin.setup()
      for pin in self.staticPins.values(): pin.setup()

    for gone_id in set(self.playerPins) - seen:
      self._scene.removeItem(self.playerPins.pop(gone_id))
    for gone_id in set(self.entityPins) - seen:
      self._scene.removeItem(self.entityPins.pop(gone_id))
    for pid in seen:
      pin = self.playerPins.get(pid) or self.entityPins.get(pid)
      if pin is None: continue
      pin.setPos(pin.cx * μMap.upscale, pin.cy * μMap.upscale)
      if pin.scene() is None:
        self._scene.addItem(pin)
    for pin in self.staticPins.values():
      pin.setPos(pin.cx * μMap.upscale, pin.cy * μMap.upscale)
      if pin.scene() is None:
        self._scene.addItem(pin)

    if μMap.centerMode == 'cartographer':
      p = next((pin for pin in self.playerPins.values() if pin.pinType == P_TYPE_MAIN), None)
      if p: self._startScroll(p.cx * μMap.upscale, p.cy * μMap.upscale)
    elif μMap.centerMode == 'target' and μMap.selectedPin:
      self._startScroll(μMap.selectedPin.cx * μMap.upscale, μMap.selectedPin.cy * μMap.upscale)
    self._updateEdgePins()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _startScroll(self, x, y):
    self._scrollTarget = QPointF(x, y)
    if not self._scrollTimer.isActive():
      self._scrollTimer.start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _scrollStep(self):
    if self._scrollTarget is None:
      self._scrollTimer.stop()
      return
    cur = self.view._getCenter()
    dx = self._scrollTarget.x() - cur.x()
    dy = self._scrollTarget.y() - cur.y()
    if dx*dx + dy*dy < 1.0:
      self.view.centerOn(self._scrollTarget)
      self._scrollTarget = None
      self._scrollTimer.stop()
    else:
      self.view.centerOn(cur.x() + dx * 0.12, cur.y() + dy * 0.12)
    self._updateEdgePins()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onSelectionChanged(self):
    all_pins = list(self.playerPins.values()) + list(self.entityPins.values()) + list(self.staticPins.values())
    sel = next((p for p in all_pins if not sip.isdeleted(p) and p.isSelected()), None)
    μMap.selectedPin = sel
    if sel:
      self.lblTargetPin.setPixmap(sel.pixmap().scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
      name = sel.name.split("<br>", 1)
      lbl = "<b>Weenie:</b>" if sel.isStatic() else "<b>Id:</b>"
      self.lblTargetName.setText(f"{lbl} {sel.id}<br><b>Name:</b> {name[0]}{f"<br><i>({name[1]})</i>" if len(name)>1 else ""}")
    else:
      self.lblTargetPin.clear()
      self.lblTargetName.setText("None")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _updateEdgePins(self):
    vr = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
    margin = μMap.pinSize / 2
    inner = vr.adjusted(margin, margin, -margin, -margin)
    main = next((p for p in self.playerPins.values() if p.pinType == P_TYPE_MAIN), None)
    if main is None: return
    mx = main.cx * μMap.upscale
    my = main.cy * μMap.upscale
    seen: set[int] = set()
    for pid, pin in self.playerPins.items():
      if pin.pinType == P_TYPE_MAIN: continue
      px = pin.cx * μMap.upscale
      py = pin.cy * μMap.upscale
      if vr.contains(px, py):
        if pid in self.edgePins:
          self._scene.removeItem(self.edgePins.pop(pid))
        continue
      seen.add(pid)
      if pid not in self.edgePins:
        ep = μMapPin(pid, 0, 0, pin.name, pinType=P_TYPE_DISTANT_PARTY)
        self._scene.addItem(ep)
        self.edgePins[pid] = ep
      ep = self.edgePins[pid]
      μMap.pushToEdge(ep, px, py, mx, my, inner)
    for pid in set(self.edgePins) - seen:
      self._scene.removeItem(self.edgePins.pop(pid))

    sel = μMap.selectedPin
    if sel:
      sx, sy = sel.cx * μMap.upscale, sel.cy * μMap.upscale
    if sel and not vr.contains(sx, sy):
      if self._selEdgePin is None:
        self._selEdgePin = μMapPin(-1, 0, 0, sel.name, pinType=P_TYPE_TARGET)
        self._scene.addItem(self._selEdgePin)
      μMap.pushToEdge(self._selEdgePin, sx, sy, mx, my, inner)
    elif self._selEdgePin is not None:
      self._scene.removeItem(self._selEdgePin)
      self._selEdgePin = None
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def pushToEdge(ep, px, py, ox, oy, inner):
    dx, dy = px - ox, py - oy
    ex, ey = μMap._edgeIntersect(ox, oy, dx, dy, inner)
    ep.setPos(ex, ey)
    ep.setRotation(math.degrees(math.atan2(dx, -dy)) % 360)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def _edgeIntersect(ox, oy, dx, dy, rect) -> tuple[float, float]:
    best_t = float('inf')
    if dx > 0:
      t = (rect.right() - ox) / dx
      if t > 0 and rect.top() <= oy + t * dy <= rect.bottom(): best_t = min(best_t, t)
    elif dx < 0:
      t = (rect.left() - ox) / dx
      if t > 0 and rect.top() <= oy + t * dy <= rect.bottom(): best_t = min(best_t, t)
    if dy > 0:
      t = (rect.bottom() - oy) / dy
      if t > 0 and rect.left() <= ox + t * dx <= rect.right(): best_t = min(best_t, t)
    elif dy < 0:
      t = (rect.top() - oy) / dy
      if t > 0 and rect.left() <= ox + t * dx <= rect.right(): best_t = min(best_t, t)
    if best_t == float('inf'): return ox, oy
    return ox + best_t * dx, oy + best_t * dy

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def printEntities(self):
    self.parser.load(self.entityPins)
    μPrint.info(f'[μMap] imageId={self.parser.mapId} ext={self.parser.ext!r} pins={len(self.entityPins)}')
    for pin in self.entityPins.values():
      μPrint.info(repr(pin))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  #  TODO: add "commander" and "leader" to list of sources
  def startMapsDaemon(self, cartographers = None):
    if μMap.runningBridge: self.stopMapsDaemon()
    bridges = μMilvianMeta.getBridges()

    self.cartographer.currentTextChanged.disconnect()
    self.cartographer.clear()
    if not bridges:
      self.setWindowTitle(f"Map - Unknown")
      self.lblAreaId.setText("")
    else:
      self.cartographer.addItems([b.capitalize() for b in bridges.keys()])
      if cartographers is None:
        cartographers = [s.strip() for s in μSetup.profile.map.cartographers().split(',')]
      elif not isinstance(cartographers, list):
        cartographers = [cartographers]

      for c in cartographers:
        c = c.lower()
        if c in bridges:
          μMap.runningBridge = bridges[c]
          interval = μSetup.profile.map.refreshInterval()
          μMap.runningBridge.drawMap(True, interval)
          self._timer.start(interval)
          self.cartographer.setCurrentText(c.capitalize())
          break
      else:
        μPrint.warning(f"[μMap] Requested Map but no cartographer found: \"{cartographers}\". Select one from the drop-down menu. Edit the list of \"cartographers\" in Settings to suppress this warning.")
    self.cartographer.currentTextChanged.connect(self.startMapsDaemon)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def stopMapsDaemon(self):
    if not μMap.runningBridge: return
    self._timer.stop()
    μMap.runningBridge.drawMap(False)
    μMap.runningBridge = None

    # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def close(self):
    self.stopMapsDaemon()
    super().close()