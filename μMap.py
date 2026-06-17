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
import os, struct, glob, mmap
from dataclasses import dataclass
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QVBoxLayout, QHBoxLayout, QProxyStyle, QStyle
from PyQt6.QtGui import QPixmap, QPainter, QWheelEvent
from PyQt6.QtCore import Qt, QTimer
from helpers.μImageFactory import *
from helpers.util import P_DEFAULT_SHM_DIR
from helpers.μPrint import μPrint
from widgets.μFloating import μToggler
from widgets.μOrb import μOrbSmall
from μSettings import μSettings
from μMilvian import μMilvianMeta, μMilvian
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from μMilvian import μMilvian


P_MAP_DIR = P_DEFAULT_SHM_DIR
P_PIN_TYPE_MAP: dict[int, str] = {
    1: "map/pin_auction",
    2: "map/pin_bank",
    3: "map/pin_challenge_blue",
    4: "map/pin_door_yellow",
    6: "map/pin_mailbox",
    7: "map/pin_crafting",
    8: "map/pin_teleport",
    9: "map/pin_patron",
   10: "map/pin_airship",
   11: "map/pin_shrine_ress",
   12: "map/pin_shrine",
   13: "map/pin_tavern",
   14: "map/pin_door_grey",
   15: "map/pin_door_blue",
   16: "map/pin_door_red",
   17: "map/pin_area_yellow",
   18: "map/pin_area_red",
   19: "map/pin_door_raid_yellow",
   20: "map/pin_dimension_door",
  100: "map/pin_chalice_yellow",
  101: "map/pin_chalice_blue",
  102: "map/pin_chalice_grey",
  103: "map/pin_chalice_red",
  110: "map/pin_chalice_raid",
  111: "map/pin_chalice_raid_blue",
  112: "map/pin_chalice_raid_grey",
  113: "map/pin_chalice_raid_red",
  120: "map/pin_chalice_arc",
  121: "map/pin_chalice_arc_blue",
  130: "map/pin_chalice_saga",
  131: "map/pin_chalice_saga_blue",
  201: "map/pin_token_vendor",
  202: "map/pin_token_pawn",
  203: "map/pin_collector",
  204: "map/pin_hireling_vendor",
  205: "map/pin_spirit_binder",
  210: "map/pin_trainer",
  300: "map/pin_poi",
  301: "map/pin_breakeable",
  302: "map/pin_crest",
  303: "map/pin_crest_socket",
  304: "map/pin_chest",
  305: "map/pin_secret",
  306: "map/pin_mysterious_remnants",
  307: "map/pin_lostsoul",
  308: "map/pin_usable",
  309: "map/pin_control_panel",
  310: "map/pin_explorer",
  311: "map/pin_collectible",
  312: "map/pin_ladder",
  313: "map/pin_item_dropped",
  314: "map/pin_collectible_taken",
  315: "map/pin_soul_stone",
  400: "map/pin_enemy",
  401: "map/pin_friendly",
  402: "map/pin_token_other",
  403: "map/pin_champion_yellow",
  404: "map/pin_champion_orange",
  405: "map/pin_champion_red",
  410: "map/pin_boss_reaper",
  411: "map/pin_boss_mini",
  412: "map/pin_boss",
  413: "map/pin_boss_raids",
  1000: "map/pin_token_red",
}


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  L A Y O U T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
# Header: <I4sI = uint32 + char[4] + uint32(playerCount) = 12 bytes
_HEADER  = struct.Struct('<I4sI')
# Player: <Qfff64s = ulong + 3×float32 (cx,cy,heading) + char[64] = 84 bytes
_PLAYER  = struct.Struct('<Qfff64s')
# Entity: <QffIiq64s64sI = ulong + 2×float32 (cx,cy) + uint32 + int32 + int64 + char[64] + char[64] + uint32 = 164 bytes
_ENTITY  = struct.Struct('<QffIiq64s64sI')

assert _HEADER.size == 12
assert _PLAYER.size == 84
assert _ENTITY.size == 164


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   E N T I T Y
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
@dataclass
class μMapPlayer:
  id      : int
  cx      : float
  cy      : float
  heading : float
  name    : str

  def __repr__(self):
    return f'μMapPlayer({self.id:#x} "{self.name}" px=({self.cx:.1f},{self.cy:.1f}) h={self.heading:.1f}°)'

@dataclass
class μMapEntity:
  id           : int
  cx           : float
  cy           : float
  weenieType   : int
  mapNoteLevel : int   # int32
  mapNoteType  : int   # int64
  mapNoteStr   : str
  name         : str
  pinType      : int

  def __repr__(self):
    return f'μMapEntity({self.id:#x} "{self.name}" pin={self.pinType} wt={self.weenieType:#x} px=({self.cx:.1f},{self.cy:.1f}) lvl={self.mapNoteLevel} type={self.mapNoteType:#x} str="{self.mapNoteStr}")'


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P
#
#       Parses the 'map' binary file written by μMap.dumpEntities() on the C# side.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMapParser:
  def __init__(self):
    self.map_image_id : int   = 0
    self.ext          : str   = ''
    self.players      : list[μMapPlayer] = []
    self.entities     : list[μMapEntity] = []

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def dataPath() -> str: return f"{μMap.runningBridge.bridgePath}/{μMap.runningBridge.charName.lower()}/map"
  def imagePath(self) -> str: return f"{μMapParser.dataPath()}{self.ext}"

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def load(self, path: str = None) -> bool:
    path = path or μMapParser.dataPath()
    if not os.path.exists(path):
      return False
    mm = None
    try:
      with open(path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
      data = mm
      if len(data) < _HEADER.size:
        return False
      (map_image_id, ext_b, player_count) = _HEADER.unpack_from(data, 0)
      self.map_image_id = map_image_id
      self.ext          = ext_b.rstrip(b'\x00').decode('ascii', errors='replace')
      self.players  = []
      self.entities = []
      off = _HEADER.size
      for _ in range(player_count):
        if off + _PLAYER.size > len(data): return True
        (pid, cx, cy, heading, name_b) = _PLAYER.unpack_from(data, off)
        name = name_b.rstrip(b'\x00').decode('utf-8', errors='replace')
        self.players.append(μMapPlayer(id=pid, cx=cx, cy=cy, heading=heading, name=name))
        off += _PLAYER.size
      if off + 4 > len(data): return True
      (entity_count,) = struct.unpack_from('<I', data, off)
      off += 4
      for _ in range(entity_count):
        if off + _ENTITY.size > len(data): break
        (eid, cx, cy, weenie_type, note_level, note_type, note_str_b, name_b, pin_type) = _ENTITY.unpack_from(data, off)
        name     = name_b.rstrip(b'\x00').decode('utf-8', errors='replace')
        note_str = note_str_b.rstrip(b'\x00').decode('utf-8', errors='replace')
        self.entities.append(μMapEntity(id=eid, cx=cx, cy=cy, weenieType=weenie_type,
          mapNoteLevel=note_level, mapNoteType=note_type, mapNoteStr=note_str, name=name, pinType=pin_type))
        off += _ENTITY.size
      return True
    except Exception as e:
      μPrint.error(f'[μMap.load] {e}')
      return False
    finally:
      if mm is not None: mm.close()


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   P I N
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMapPinItem(QGraphicsPixmapItem):
  cache: dict[str, QPixmap] = {}
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getPin(cls, data: μMapPlayer | μMapEntity) -> QPixmap:
    pinType = μMapPinItem.getPinType(data)
    if pinType not in cls.cache:
      cls.cache[pinType] = getPixmap(pinType).scaled(μMap.pinSize, μMap.pinSize, Qt.AspectRatioMode.KeepAspectRatio,
                                                        Qt.TransformationMode.SmoothTransformation)
    return cls.cache[pinType]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, data : μMapPlayer | μMapEntity):
    super().__init__(μMapPinItem.getPin(data))
    self.setToolTip(data.name)
    self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    self.setOffset(-μMap.pinSize / 2, -μMap.pinSize / 2)
    if isinstance(data, μMapPlayer):     z = 3
    elif data.pinType in P_PIN_TYPE_MAP: z = 2
    else:                                z = 1
    self.setZValue(z)
    self.setCursor(Qt.CursorShape.PointingHandCursor)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getPinType(data):
    if isinstance(data, μMapPlayer):
      return "map/pin_token_pet" if hex(data.id).startswith("0x3") else "map/pin_token_player"
    return P_PIN_TYPE_MAP.get(data.pinType, "map/pin_token_red")


class _FastTooltipStyle(QProxyStyle):
  def styleHint(self, hint, option=None, widget=None, returnData=None):
    if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay: return 100
    return super().styleHint(hint, option, widget, returnData)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A P   V I E W
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMapView(QGraphicsView):
  def __init__(self, scene: QGraphicsScene):
    super().__init__(scene)
    self.setStyle(_FastTooltipStyle())
    self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
    self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    self.setRenderHint(QPainter.RenderHint.Antialiasing)
    self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

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
  upscale = 4
  pinSize = 16*upscale

  def __init__(self, parent=None):
    super().__init__("Map", P_ICON_MAP)
    self.toggler.setToolTip("Show Map")
    self.parser = μMapParser()
    self.pinItems: dict[int, μMapPinItem] = {}
    self.setMinimumSize(768, 640)

    self._scene = QGraphicsScene()
    self._bgItem = QGraphicsPixmapItem()
    self._bgItem.setZValue(0)
    self._scene.addItem(self._bgItem)
    self._view = μMapView(self._scene)

    self.btnRefresh = μOrbSmall(icon=P_ICON_REFRESH, tooltip='Reload map image from disk')
    self.btnPrint = μOrbSmall(icon=P_ICON_REFRESH, tooltip='Print entities for debugging')
    self.btnPlay = μOrbSmall(icon=P_ICON_PLAY, tooltip='Request Milvian to start collecting map data')
    self.btnStop = μOrbSmall(icon=P_ICON_STOP, tooltip='Request Milvian to stop collecting map data')
    self._timer = QTimer()
    self._timer.timeout.connect(self.refresh)
    self.btnRefresh.clicked.connect(self.refresh)
    self.btnPrint.clicked.connect(self.printEntities)
    self.btnPlay.clicked.connect(self.launchMapsDaemon)
    self.btnStop.clicked.connect(self.stopMapsDaemon)

    toolbar = QHBoxLayout()
    toolbar.addWidget(self.btnRefresh)
    toolbar.addWidget(self.btnPrint)
    toolbar.addWidget(self.btnPlay)
    toolbar.addWidget(self.btnStop)
    toolbar.addStretch()

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addLayout(toolbar)
    layout.addWidget(self._view)
    self.setLayout(layout)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setPinSize(cls, size):
    cls.pinSize = size*cls.upscale
    μMapPinItem.cache.clear()
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
    for item in self.pinItems.values(): self._scene.removeItem(item)
    self.pinItems.clear()
    if clearCache: μMapPinItem.cache.clear()
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def refresh(self):
    self.clear()
    self.parser.load()
    path = self.parser.imagePath()
    pix = QPixmap(path)
    if pix.isNull():
      μPrint.error(f'[μMap] Failed to load {path}')
      return
    firstLoad = self._bgItem.pixmap().isNull()
    μMap.setUpscale(int(μSettings.profile.map.upscale()/100))
    μMap.setMapSize(pix.width(), pix.height())
    self._bgItem.setPixmap(pix.scaled(μMap.mapWidth, μMap.mapHeight,
      Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    self._scene.setSceneRect(0, 0, μMap.mapWidth, μMap.mapHeight)
    if firstLoad:
      self._view.resetTransform()
      zoom = μSettings.profile.map.mapZoom()/(100*μMap.upscale)
      self._view.scale(zoom, zoom)
    self.plotEntities()
    mainPlayer = self.parser.players[0]
    self._view.centerOn(mainPlayer.cx * μMap.upscale, mainPlayer.cy * μMap.upscale)


  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def plotEntities(self):
    seen: set[int] = set()
    μMap.setPinSize(μSettings.profile.map.iconSize())
    for p in self.parser.players:
      self.plotPin(p)
      seen.add(p.id)
    for e in self.parser.entities:
      self.plotPin(e)
      seen.add(e.id)
    dead = set(self.pinItems) - seen
    for pid in dead:
      self._scene.removeItem(self.pinItems.pop(pid))
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def plotPin(self, data : μMapPlayer | μMapEntity):
    if data.id in self.pinItems:
      self.pinItems[data.id].setPos(data.cx * μMap.upscale, data.cy * μMap.upscale)
    else:
      item = μMapPinItem(data)
      item.setPos(data.cx * μMap.upscale, data.cy * μMap.upscale)
      self._scene.addItem(item)
      self.pinItems[data.id] = item

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def printEntities(self):
    self.parser.load()
    μPrint.info(f'[μMap] imageId={self.parser.map_image_id} ext={self.parser.ext!r} players={len(self.parser.players)} entities={len(self.parser.entities)}')
    for p in self.parser.players:
      μPrint.info(repr(p))
    for e in self.parser.entities:
      μPrint.info(repr(e))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  #  TODO: add "commander" and "leader" to list of sources
  def launchMapsDaemon(self):
    if μMap.runningBridge: self.stopMapsDaemon()
    bridges = μMilvianMeta.getBridges()

    sources = [s.strip() for s in μSettings.profile.map.sourceBridge().split(',')]
    for s in sources:
      if s in bridges:
        μMap.runningBridge = bridges[s]
        interval = μSettings.profile.map.refreshInterval()
        μMap.runningBridge.drawMap(True, interval)
        self._timer.start(interval)
        return
    else:
      μPrint.warning(f"[μMap] Requested Map but none of the preferred bridges found: \"{sources}\". Edit the list in Settings")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def stopMapsDaemon(self):
    if not μMap.runningBridge: return
    self._timer.stop()
    μMap.runningBridge.drawMap(False)
    μMap.runningBridge = None
