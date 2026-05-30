#!/usr/bin/env python3
from __future__ import annotations

import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSpinBox, QLabel, QFrame
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QMouseEvent, QPixmap, QPainterPath


DRAG_THRESHOLD   = 5
RECT_SELECT_COLOR = QColor(100, 160, 255)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S T Y L E S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class NodeStyle:
  radius               = 22
  width                = None
  height               = None
  fg                   = None
  border_width         = 2.0
  selected_border_width = 3.5
  text_color           = QColor(255, 255, 255)
  color_disconnected   = QColor(200,  50,  50)
  color_receives       = QColor( 50, 180, 100)
  color_incoming       = QColor( 70, 130, 210)
  color_highlight      = QColor(255, 160,  40)
  color_selected       = QColor(255, 220,  50)

  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
class EdgeStyle:
  width          = 2.0
  arrow_size     = 12.0
  color          = QColor(100, 100, 100)
  dragging_color = QColor(255, 120,   0)
  dragging_width = 2.5

  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  N O D E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μNode(QWidget):
  sigSelected = pyqtSignal(bool)
  sigConnected = pyqtSignal(object)
  sigReceiveConnection = pyqtSignal(object)
  sigDisconnected = pyqtSignal()
  sigConnectionChanged = pyqtSignal()
  sigDoubleClicked = pyqtSignal()

  def __init__(self, center: QPointF = None, label: str = None, parent=None, bg : QPixmap = None, style: NodeStyle = None,
               allowOutgoing: bool = True, allowIncoming: bool = True):
    super().__init__(parent)
    self.label = label
    self.bg = bg
    self._preparedBG = None
    self.hovered = False
    self.selected = False
    self.center: QPointF = center
    self.allowOutgoing = allowOutgoing
    self.allowIncoming = allowIncoming
    self.style = style if style is not None else NodeStyle()
    self._applyStyle()
    if bg is not None:
      self.setBg(bg)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _applyStyle(self):
    s = self.style
    fg, radius, width, height = s.fg, s.radius, s.width, s.height

    if radius is not None:
      self._shape = 'circle'
      self._radius = radius
      self._width = radius * 2
      self._height = radius * 2
      self._pixmap = self.cropCircle(fg, radius) if fg is not None else None
    elif fg is not None:
      self._shape = 'rect'
      if width is not None:
        h = height if height is not None else width
        scaled = fg.scaled(width, h,
          Qt.AspectRatioMode.KeepAspectRatio,
          Qt.TransformationMode.SmoothTransformation)
        self._pixmap = scaled
        self._width = scaled.width()
        self._height = scaled.height()
      else:
        self._pixmap = fg
        self._width = fg.width()
        self._height = fg.height()
      self._radius = max(self._width, self._height) // 2
    elif width is not None:
      self._shape = 'rect'
      self._width = width
      self._height = height if height is not None else width
      self._radius = max(self._width, self._height) // 2
      self._pixmap = None
    else:
      self._shape = 'circle'
      self._radius = NodeStyle.radius
      self._width = NodeStyle.radius * 2
      self._height = NodeStyle.radius * 2
      self._pixmap = None
    self._prepareBg()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _prepareBg(self):
    if self.bg is None:
      self._preparedBG = None
    elif self._shape == 'circle':
      self._preparedBG = μNode.cropCircle(self.bg, self._radius)
    else:
      self._preparedBG = self.bg.scaled(self._width, self._height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setBg(self, bg: QPixmap | None):
    self.bg = bg
    self._prepareBg()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setStyle(self, style: NodeStyle):
    self.style = style
    self._applyStyle()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def cropCircle(image: QPixmap, radius: int) -> QPixmap:
    diameter = radius * 2
    result = QPixmap(diameter, diameter)
    result.fill(QColor(0, 0, 0, 0))

    p = QPainter(result)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0.0, 0.0, float(diameter), float(diameter))
    p.setClipPath(path)

    x = (diameter - image.width()) / 2
    y = (diameter - image.height()) / 2
    p.drawPixmap(int(x), int(y), image)
    p.end()
    return result

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setSelected(self, value: bool):
    if self.selected != value:
      self.selected = value
      self.sigSelected.emit(value)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def colour(self, edges: list[μEdge], is_dragging: bool) -> QColor:
    s = self.style
    if self.hovered and is_dragging:
      return s.color_highlight

    receives_arrow = any(e.target is self for e in edges)
    has_outgoing   = any(e.source is self and e.target is not None for e in edges)

    if receives_arrow and not has_outgoing:
      return s.color_incoming
    if receives_arrow or has_outgoing:
      return s.color_receives
    return s.color_disconnected

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def draw(self, edges: list[μEdge], is_dragging: bool, painter: QPainter):
    s = self.style
    colour = self.colour(edges, is_dragging)
    border_pen = (QPen(s.color_selected, s.selected_border_width)
                  if self.selected else QPen(colour.darker(140), s.border_width))

    if self._preparedBG is not None:
      bx = int(self.center.x() - self._preparedBG.width() / 2)
      by = int(self.center.y() - self._preparedBG.height() / 2)
      painter.drawPixmap(bx, by, self._preparedBG)

    if self._shape == 'circle':
      if self._pixmap is not None:
        px = int(self.center.x() - self._pixmap.width() / 2)
        py = int(self.center.y() - self._pixmap.height() / 2)
        painter.drawPixmap(px, py, self._pixmap)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
      else:
        painter.setPen(border_pen)
        painter.setBrush(QBrush(colour))
      painter.drawEllipse(self.center, self._radius, self._radius)
    else:
      rect = QRectF(
        self.center.x() - self._width / 2,
        self.center.y() - self._height / 2,
        self._width, self._height,
      )
      if self._pixmap is not None:
        px = int(self.center.x() - self._pixmap.width() / 2)
        py = int(self.center.y() - self._pixmap.height() / 2)
        painter.drawPixmap(px, py, self._pixmap)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
      else:
        painter.setPen(border_pen)
        painter.setBrush(QBrush(colour))
      painter.drawRect(rect)

    painter.setPen(QPen(s.text_color))
    text_rect = QRectF(
      self.center.x() - self._width / 2,
      self.center.y() - self._height / 2,
      self._width, self._height,
    )
    if self.label:
      painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.label)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def containsPoint(self, pos: QPointF) -> bool:
    dx = pos.x() - self.center.x()
    dy = pos.y() - self.center.y()
    if self._shape == 'circle':
      return dx * dx + dy * dy <= (self._radius + 4) ** 2
    return abs(dx) <= self._width / 2 + 4 and abs(dy) <= self._height / 2 + 4

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def edgeBoundaryPoint(self, direction: QPointF) -> QPointF:
    dx, dy = direction.x(), direction.y()
    if abs(dx) < 0.001 and abs(dy) < 0.001:
      return QPointF(self.center)
    if self._shape == 'circle':
      length = math.hypot(dx, dy)
      ux, uy = dx / length, dy / length
      return QPointF(self.center.x() + ux * self._radius, self.center.y() + uy * self._radius)
    hw = self._width / 2
    hh = self._height / 2
    tx = abs(hw / dx) if abs(dx) > 0.001 else float('inf')
    ty = abs(hh / dy) if abs(dy) > 0.001 else float('inf')
    t = min(tx, ty)
    return QPointF(self.center.x() + dx * t, self.center.y() + dy * t)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E D G E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μEdge:
  def __init__(self, source: μNode, target: μNode | None, style: EdgeStyle = None):
    self.source = source
    self.target = target
    self.style = style if style is not None else EdgeStyle()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setTarget(self, new_target: μNode | None):
    old_target = self.target
    if old_target is new_target:
      return
    self.target = new_target
    if old_target is not None:
      old_target.sigConnectionChanged.emit()
    if new_target is not None:
      self.source.sigConnected.emit(new_target)
      new_target.sigReceiveConnection.emit(self.source)
    else:
      self.source.sigDisconnected.emit()
    self.source.sigConnectionChanged.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def draw(self, painter: QPainter):
    if self.target is None:
      return
    s = self.style
    p1 = self.source.center
    p2 = self.target.center

    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    length = math.hypot(dx, dy)
    if length < 1:
      return
    ux, uy = dx / length, dy / length

    start = self.source.edgeBoundaryPoint(QPointF(dx, dy))
    end   = self.target.edgeBoundaryPoint(QPointF(-dx, -dy))

    painter.setPen(QPen(s.color, s.width))
    painter.drawLine(start, end)

    ax = end.x() - ux * s.arrow_size
    ay = end.y() - uy * s.arrow_size
    px = -uy * s.arrow_size * 0.45
    py =  ux * s.arrow_size * 0.45
    triangle = [end, QPointF(ax + px, ay + py), QPointF(ax - px, ay - py)]
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(s.color))
    painter.drawPolygon(triangle)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  N E T W O R K   W I D G E T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μNetwork(QWidget):
  def __init__(self, parent=None, allowCycles=True):
    super().__init__(parent)
    self.allowCycles = allowCycles
    self.setMinimumSize(500, 500)

    self._nodeCount = 0
    self.nodes: list[μNode] = []
    self.edges: list[μEdge] = []

    self._dragEdge: μEdge | None = None
    self._dragCurrentPos: QPointF | None = None
    self._pressPos: QPointF | None = None
    self._pressNode: μNode | None = None
    self._dragStarted = False
    self._rectSelecting = False
    self._rectCurrent: QPointF | None = None

    self.nodeStyle = NodeStyle()
    self.edgeStyle = EdgeStyle()
    self.setMouseTracking(True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setNodeStyle(self, **kwargs): self.nodeStyle = NodeStyle(**kwargs)
  def setEdgeStyle(self, **kwargs): self.edgeStyle = EdgeStyle(**kwargs)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def add(self, node: μNode | None = None):
    if node is None:
      node = μNode(QPointF(0, 0), style=self.nodeStyle)
    else:
      node.setStyle(self.nodeStyle)
    self.nodes.append(node)
    self._nodeCount = len(self.nodes)
    self.recomputePositions()
    self.resetEdges()
    self.update()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def recomputePositions(self):
    n = self._nodeCount
    if n == 0:
      return
    cx = self.width() / 2
    cy = self.height() / 2
    ring_radius = min(cx, cy) - self.nodeStyle.radius - 30
    for i, node in enumerate(self.nodes):
      angle = -math.pi / 2 + 2 * math.pi * i / n
      node.center = QPointF(cx + ring_radius * math.cos(angle), cy + ring_radius * math.sin(angle))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def resetEdges(self):
    self.edges.clear()

  def clearEdges(self, node: μNode, outgoing: bool = True, incoming: bool = False):
    self.edges = [e for e in self.edges
                  if not (outgoing and e.source is node)
                  and not (incoming and e.target is node)]
    self.update()

  def connectNodes(self, a: μNode, b: μNode):
    self.edges.append(μEdge(a, b, self.edgeStyle))
    self.update()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clear(self):
    self.edges.clear()
    self.nodes.clear()
    self._nodeCount  = 0
    self._dragEdge   = None
    self._pressNode  = None
    self.update()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def resizeEvent(self, event):
    super().resizeEvent(event)
    self.recomputePositions()
    self.update()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getNodeAt(self, pos: QPointF) -> μNode | None:
    for node in self.nodes:
      if node.containsPoint(pos):
        return node
    return None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _edgeForSource(self, node: μNode) -> μEdge | None:
    for edge in self.edges:
      if edge.source is node:
        return edge
    return None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _setHovered(self, node: μNode | None):
    for n in self.nodes:
      n.hovered = (n is node)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _wouldCreateCycle(self, source: μNode, target: μNode) -> bool:
    visited = set()
    current = target
    while current is not None and current not in visited:
      if current is source:
        return True
      visited.add(current)
      edge = self._edgeForSource(current)
      current = edge.target if edge is not None else None
    return False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _trySetTarget(self, edge: μEdge, target: μNode | None):
    if target is not None:
      if not edge.source.allowOutgoing: return
      if not target.allowIncoming:      return
      if not self.allowCycles and self._wouldCreateCycle(edge.source, target):
        return
    edge.setTarget(target)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clearSelection(self):
    for n in self.nodes:
      n.setSelected(False)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def mouseDoubleClickEvent(self, event: QMouseEvent):
    if event.button() == Qt.MouseButton.LeftButton:
      node = self.getNodeAt(QPointF(event.position()))
      if node is not None:
        node.sigDoubleClicked.emit()
    super().mouseDoubleClickEvent(event)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def mousePressEvent(self, event: QMouseEvent):
    if event.button() == Qt.MouseButton.LeftButton:
      pos = QPointF(event.position())
      self._pressPos = pos
      self._pressNode = self.getNodeAt(pos)
      self._dragStarted = False
    super().mousePressEvent(event)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def mouseMoveEvent(self, event: QMouseEvent):
    pos = QPointF(event.position())
    hovered = self.getNodeAt(pos)
    self._setHovered(hovered)

    if self._pressPos is not None and not self._dragStarted and not self._rectSelecting:
      dx = pos.x() - self._pressPos.x()
      dy = pos.y() - self._pressPos.y()
      if dx * dx + dy * dy > DRAG_THRESHOLD ** 2:
        if self._pressNode is not None:
          self._dragStarted = True
          if self._pressNode.allowOutgoing:
            edge = self._edgeForSource(self._pressNode)
            if edge is None:
              edge = μEdge(self._pressNode, None, self.edgeStyle)
              self.edges.append(edge)
            self._dragEdge = edge
            self._dragCurrentPos = pos
        else:
          self._rectSelecting = True
          self._rectCurrent = pos

    if self._dragEdge is not None:
      self._dragCurrentPos = pos

    if self._rectSelecting:
      self._rectCurrent = pos

    self.update()
    super().mouseMoveEvent(event)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def mouseReleaseEvent(self, event: QMouseEvent):
    if event.button() != Qt.MouseButton.LeftButton:
      super().mouseReleaseEvent(event)
      return

    if self._rectSelecting and self._pressPos is not None and self._rectCurrent is not None:
      ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
      rect = QRectF(self._pressPos, self._rectCurrent).normalized()
      if not ctrl:
        self.clearSelection()
      for node in self.nodes:
        if rect.contains(node.center):
          node.setSelected(True)
    elif self._dragStarted and self._dragEdge is not None:
      target = self.getNodeAt(QPointF(event.position()))
      if self._pressNode is not None and self._pressNode.selected:
        selected = [n for n in self.nodes if n.selected]
        for node in selected:
          edge = self._edgeForSource(node)
          if edge is None:
            continue
          if target is not None and target is not node:
            self._trySetTarget(edge, target)
          elif target is None:
            self._trySetTarget(edge, None)
      else:
        if target is not None and target is not self._dragEdge.source:
          self._trySetTarget(self._dragEdge, target)
        elif target is None:
          self._trySetTarget(self._dragEdge, None)
    elif not self._dragStarted:
      ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
      node = self._pressNode
      if node is not None:
        if ctrl:
          node.setSelected(not node.selected)
        else:
          was_selected = node.selected
          self.clearSelection()
          node.setSelected(not was_selected)
      else:
        self.clearSelection()

    self._dragEdge = None
    self._dragCurrentPos = None
    self._pressPos = None
    self._pressNode = None
    self._dragStarted = False
    self._rectSelecting = False
    self._rectCurrent = None
    self._setHovered(None)
    self.update()
    super().mouseReleaseEvent(event)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def paintEvent(self, event):
    super().paintEvent(event)
    if self._nodeCount == 0:
      return

    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    self.drawEdges(painter)
    self.drawNodes(painter)
    self._drawSelectionRect(painter)

    painter.end()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def drawEdges(self, painter: QPainter):
    for edge in self.edges:
      if edge is self._dragEdge:
        continue
      edge.draw(painter)

    if self._dragEdge is not None and self._dragCurrentPos is not None:
      s = self.edgeStyle
      pen = QPen(s.dragging_color, s.dragging_width, Qt.PenStyle.DashLine)
      painter.setPen(pen)
      src = self._dragEdge.source
      dx = self._dragCurrentPos.x() - src.center.x()
      dy = self._dragCurrentPos.y() - src.center.y()
      start = src.edgeBoundaryPoint(QPointF(dx, dy))
      painter.drawLine(start, self._dragCurrentPos)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _drawSelectionRect(self, painter: QPainter):
    if not self._rectSelecting or self._pressPos is None or self._rectCurrent is None:
      return
    rect = QRectF(self._pressPos, self._rectCurrent).normalized()
    fill = QColor(RECT_SELECT_COLOR)
    fill.setAlpha(30)
    painter.setPen(QPen(RECT_SELECT_COLOR, 1, Qt.PenStyle.DashLine))
    painter.setBrush(QBrush(fill))
    painter.drawRect(rect)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def drawNodes(self, painter: QPainter):
    font = QFont("sans-serif", 11, QFont.Weight.Bold)
    painter.setFont(font)
    is_dragging = self._dragEdge is not None
    for node in self.nodes:
      node.draw(self.edges, is_dragging, painter)
