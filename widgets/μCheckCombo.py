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
from __future__ import annotations
from PyQt6.QtWidgets import QComboBox, QStyle, QStyledItemDelegate
from PyQt6.QtCore import QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from helpers.util import *
from typing import TYPE_CHECKING


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  D E L E G A T E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class _RightIconDelegate(QStyledItemDelegate):
  def paint(self, painter, option, index):
    painter.save()

    # Background
    if option.state & QStyle.StateFlag.State_Selected:
      painter.fillRect(option.rect, option.palette.highlight())
    else:
      painter.fillRect(option.rect, option.palette.base())

    # Check mark (left)
    checked = index.data(Qt.ItemDataRole.UserRole)
    painter.drawText(option.rect.adjusted(4, 0, 0, 0),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     "✓" if checked else " ")

    # Text
    text = index.data(Qt.ItemDataRole.DisplayRole) or ""
    painter.drawText(option.rect.adjusted(20, 0, -24, 0),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

    # Icon (right)
    icon = index.data(Qt.ItemDataRole.DecorationRole)
    if icon and not icon.isNull():
      sz = 16
      icon_rect = option.rect.adjusted(option.rect.width() - sz - 4,
                                       (option.rect.height() - sz) // 2, -4,
                                       (option.rect.height() - sz) // 2)
      icon_rect.setSize(QSize(sz, sz))
      icon.paint(painter, icon_rect)

    painter.restore()

  def sizeHint(self, option, index):
    size = super().sizeHint(option, index)
    size.setHeight(max(size.height(), 24))
    return size


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  C H E C K   C O M B O
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μCheckCombo(QComboBox):
  changed = pyqtSignal()

  def __init__(self, title: str):
    super().__init__()
    self.title = title
    self.blockHide = False
    self.rowModel = QStandardItemModel(self)
    self.setModel(self.rowModel)
    self.header = QStandardItem(f"{title}: None")
    self.rowModel.appendRow(self.header)
    self.view().setItemDelegate(_RightIconDelegate(self))
    self.view().pressed.connect(self.onPressed)
    self.rowModel.itemChanged.connect(self.onItemChanged)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onPressed(self, index: QModelIndex):
    item = self.rowModel.itemFromIndex(index)
    if not item:
      return
    self.blockHide = True
    if index.row() == 0:  # Header
      new_state = not self.areAllChecked()
      for i in range(1, self.rowModel.rowCount()):
        self.rowModel.item(i).setData(new_state, Qt.ItemDataRole.UserRole)
    else:
      current = item.data(Qt.ItemDataRole.UserRole)
      item.setData(not current, Qt.ItemDataRole.UserRole)
    self.refreshHeader()
    self.changed.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def hidePopup(self):
    if self.blockHide:
      self.blockHide = False
      return
    self.setCurrentIndex(0)
    self.refreshHeader()
    super().hidePopup()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setCurrentIndex(self, index):
    super().setCurrentIndex(0)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addCheckItem(self, text: str, checked: bool = True, icon: QIcon = None):
    for i in range(1, self.rowModel.rowCount()):
      if self.rowModel.item(i).text() == text:
        return
    row = QStandardItem(text)
    row.setData(checked, Qt.ItemDataRole.UserRole)
    if icon and not icon.isNull():
      row.setIcon(icon)

    insertPos = self.rowModel.rowCount()
    self.rowModel.itemChanged.disconnect(self.onItemChanged)
    for i in range(1, self.rowModel.rowCount()):
      if text.lower() < self.rowModel.item(i).text().lower():
        insertPos = i
        break
    self.rowModel.insertRow(insertPos, row)
    self.refreshHeader()
    self.rowModel.itemChanged.connect(self.onItemChanged)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getChecked(self) -> list:
    return [self.rowModel.item(i).text()
            for i in range(1, self.rowModel.rowCount())
            if self.rowModel.item(i).data(Qt.ItemDataRole.UserRole)]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def areAllChecked(self) -> bool:
    total = self.rowModel.rowCount() - 1
    return total == 0 or len(self.getChecked()) == total

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onItemChanged(self, item):
    self.refreshHeader()
    self.changed.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def refreshHeader(self):
    checked = self.getChecked()
    nitems  = self.rowModel.rowCount() - 1
    if nitems == 0 or len(checked) == nitems:
      text = f"{self.title}: All"
    elif len(checked) == 1:
      text = f"{self.title}: {checked[0]}"
    elif len(checked) == 0:
      text = f"{self.title}: None"
    else:
      text = f"{self.title}: {len(checked)}/{nitems}"
    self.rowModel.item(0).setText(text)
    self.setCurrentIndex(0)
