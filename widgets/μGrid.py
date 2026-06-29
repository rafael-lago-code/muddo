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
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QLayout, QWidget, QGridLayout, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QEvent, QObject, QByteArray
from PyQt6.QtGui import QDrag
import time
import helpers.μEffects as μEffects

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  G R I D
#
#   A grid widget that allows drag-and-drop reordering
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μGrid(QWidget):
  orderChanged = pyqtSignal()
  itemsSwapped = pyqtSignal(object, object)
  columns = 0
  rows = 2
  fillRowsFirst = True
  lastRefreshTime = -1
  refreshSentinel = False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, parent=None):
    super().__init__(parent)
    self.contents: list[QWidget] = []
    self.grid = QGridLayout()
    self.setLayout(self.grid)
    self.setAcceptDrops(True)
    self.draggedWidget = None
    self.originalIndex = -1
    self.lastTargetIndex = -1
    self.lastRefreshTime = time.time_ns()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setColumns(self, columns : int = 0) : self.columns = columns
  def setRows(self, rows : int = 0) : self.rows = rows
  def setFillRowsFirst(self, fillRowsFirst : bool = True) : self.fillRowsFirst = fillRowsFirst

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addWidget(self, widget: QWidget):
    widget.setParent(self)
    self.contents.append(widget)
    widget.installEventFilter(self)

    self._refreshGrid()
    self.orderChanged.emit()

  # def eventFilter(self, watched: QObject, event: QEvent) -> bool:
  #   if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
  #     self._startDrag(watched, event)
  #     return True
  #   return super().eventFilter(watched, event)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
      self.dragStartPos = event.position().toPoint()
      self.draggedWidget = watched if watched in self.contents else None
      if self.draggedWidget:
        self.originalIndex = self.contents.index(self.draggedWidget)

    elif (event.type() == QEvent.Type.MouseMove and 
      event.buttons() & Qt.MouseButton.LeftButton and 
      self.dragStartPos is not None):

      # Start drag only if moved enough
      if (event.position().toPoint() - self.dragStartPos).manhattanLength() > 10:
        self._startDrag(self.draggedWidget, event)
        return True  # consume event
    return False     # does not consume event - it is a click

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _startDrag(self, widget: QWidget, event):
    self.refreshSentinel = True
    self.draggedWidget = widget
    self.originalIndex = self.contents.index(widget)

    drag = QDrag(self)
    mimeData = QMimeData()
    mimeData.setData("application/x-draggablegrid", QByteArray())
    drag.setMimeData(mimeData)

    pixmap = widget.grab()
    drag.setPixmap(μEffects.tint(pixmap,(215,120,0),0.5))
    drag.setHotSpot(event.position().toPoint())

    widget.setWindowOpacity(0.65)

    drag.exec(Qt.DropAction.MoveAction)

    widget.setWindowOpacity(1.0)
    self.draggedWidget = None
    self.originalIndex = -1

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _refreshGrid(self):
    # prevents _refreshGrid spam during drag-and-drop
    if self.refreshSentinel and time.time_ns() - self.lastRefreshTime < 100*1e6: return
    self.lastRefreshTime = time.time_ns()
    
    for i in reversed(range(self.grid.count())):
      item = self.grid.takeAt(i)
      if item and item.widget():
        item.widget().setParent(None)

    for i, widget in enumerate(self.contents):
      row = i // self.columns
      col = i % self.columns
      self.grid.addWidget(widget, row, col)
      widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def dragEnterEvent(self, event):
    if event.mimeData().hasFormat("application/x-draggablegrid"):
      event.acceptProposedAction()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def dragMoveEvent(self, event):
    if not self.draggedWidget or not event.mimeData().hasFormat("application/x-draggablegrid"):
      return

    pos = event.position().toPoint()
    for i, widget in enumerate(self.contents):
      if widget is self.draggedWidget:
        continue
      if widget.geometry().contains(pos):
        self.lastTargetIndex = i
        break

    event.acceptProposedAction()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def dropEvent(self, event):
    self.refreshSentinel = False
    if event.mimeData().hasFormat("application/x-draggablegrid"):
      src = self.originalIndex
      tgt = self.lastTargetIndex
      if src != -1 and tgt != -1 and src != tgt:
        item_a, item_b = self.contents[src], self.contents[tgt]
        self.contents[src], self.contents[tgt] = item_b, item_a
        self._refreshGrid()
        self.itemsSwapped.emit(item_a, item_b)
      self.lastTargetIndex = -1
      event.acceptProposedAction()
      self.orderChanged.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def removeWidget(self, widget: QWidget):
    if widget in self.contents:
      self.contents.remove(widget)
      widget.setParent(None)
      self._refreshGrid()
      self.orderChanged.emit()

  def clear(self):
    for w in list(self.contents):
      self.contents.remove(w)
      w.setParent(None)
    self._refreshGrid()
    self.orderChanged.emit()

  def getWidgets(self):
    return self.contents[:]


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  G R I D   L A Y O U T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μGridLayout(QGridLayout):

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, customFont = None):
    super().__init__()

    self.firstRow = 0
    self.firstColumn = 0
    self.lastRow = 0
    self.lastColumn = 0
    self.customFont = customFont

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def appendRow(self, items):
    if not isinstance(items,list): items = [items]
    r = self.lastRow
    c = self.firstColumn
    ncols = 1
    for i in items: 
      if isinstance(i,str) and i==">":
        ncols += 1
        continue
      elif isinstance(i,str):
        self.addWidget(self.getLabel(i), r, c, 1, ncols)
      elif isinstance(i,QLayout):
        self.addLayout(i, r, c, 1, ncols)
      elif i is not None:
        self.addWidget(i, r, c, 1, ncols)
      c+=ncols
      ncols=1
    self.lastRow += 1
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getLabel(self, text):
    tmp = QLabel(text)
    if self.customFont: tmp.setFont(self.customFont)
    return tmp
  
# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  G R I D   F R A M E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μGridFrame(QFrame):

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, customFont = None):
    super().__init__()
    self._grid = μGridLayout(customFont)
    self.setLayout(self._grid)

  def appendRow(self, *args):
    self._grid.appendRow(list(args))