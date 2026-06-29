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
from PyQt6.QtWidgets import QComboBox, QLineEdit, QStyle, QStyleOptionComboBox, QStylePainter, QStyledItemDelegate
from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from helpers.util import *


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  D E L E G A T E S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class _IconRightDelegate(QStyledItemDelegate):
  def paint(self, painter, option, index):
    painter.save()

    if option.state & QStyle.StateFlag.State_Selected:
      painter.fillRect(option.rect, option.palette.highlight())
    else:
      painter.fillRect(option.rect, option.palette.base())

    text = index.data(Qt.ItemDataRole.DisplayRole) or ""
    painter.drawText(option.rect.adjusted(4, 0, -24, 0),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

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


class _CheckIconRightDelegate(_IconRightDelegate):
  def paint(self, painter, option, index):
    painter.save()

    if option.state & QStyle.StateFlag.State_Selected:
      painter.fillRect(option.rect, option.palette.highlight())
    else:
      painter.fillRect(option.rect, option.palette.base())

    checked = index.data(Qt.ItemDataRole.UserRole)
    painter.drawText(option.rect.adjusted(4, 0, 0, 0),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     "✓" if checked else " ")

    text = index.data(Qt.ItemDataRole.DisplayRole) or ""
    painter.drawText(option.rect.adjusted(20, 0, -24, 0),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

    icon = index.data(Qt.ItemDataRole.DecorationRole)
    if icon and not icon.isNull():
      sz = 16
      icon_rect = option.rect.adjusted(option.rect.width() - sz - 4,
                                       (option.rect.height() - sz) // 2, -4,
                                       (option.rect.height() - sz) // 2)
      icon_rect.setSize(QSize(sz, sz))
      icon.paint(painter, icon_rect)

    painter.restore()


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  ζ C O M B O   R I G H T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μCombo(QComboBox):
  def __init__(self):
    super().__init__()
    self.view().setItemDelegate(_IconRightDelegate(self))

  def paintEvent(self, event):
    painter = QStylePainter(self)
    opt = QStyleOptionComboBox()
    self.initStyleOption(opt)
    icon = self.itemIcon(self.currentIndex())
    opt.currentIcon = QIcon()
    opt.iconSize    = QSize(0, 0)
    painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)
    painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)
    if not icon.isNull():
      content_rect = self.style().subControlRect(
        QStyle.ComplexControl.CC_ComboBox, opt,
        QStyle.SubControl.SC_ComboBoxEditField, self)
      sz = 16
      x = content_rect.right() - sz - 2
      y = content_rect.center().y() - sz // 2
      painter.setClipping(False)
      icon.paint(painter, QRect(x, y, sz, sz))


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  μ C H E C K   C O M B O
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μCheckCombo(μCombo):
  changed = pyqtSignal()

  def __init__(self, title: str = None):
    super().__init__()
    self.title     = title
    self.blockHide = False
    self.rowModel  = QStandardItemModel(self)
    self.setModel(self.rowModel)
    self.header = QStandardItem("")
    self.rowModel.appendRow(self.header)
    self.view().setItemDelegate(_CheckIconRightDelegate(self))
    self.view().pressed.connect(self.onPressed)
    self.rowModel.itemChanged.connect(self.onItemChanged)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onPressed(self, index: QModelIndex):
    item = self.rowModel.itemFromIndex(index)
    if not item:
      return
    self.blockHide = True
    if index.row() == 0:  # Header — toggle all
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
    prefix  = f"{self.title}: " if self.title is not None else ""
    checked = self.getChecked()
    nitems  = self.rowModel.rowCount() - 1
    if nitems == 0 or len(checked) == nitems:
      text = f"{prefix}All"
    elif len(checked) == 1:
      text = f"{prefix}{checked[0]}"
    elif len(checked) == 0:
      text = f"{prefix}None"
    else:
      text = f"{prefix}{len(checked)}/{nitems}"
    self.rowModel.item(0).setText(text)
    self.setCurrentIndex(0)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#
#   ❖  μ A D V A N C E D   C O M B O
#
#     μCheckCombo with a filter QLineEdit that appears once item count reaches minShowFilter (default 10)
#     Meant for comboboxes which can have hilariously long number of items.
#
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
_AC_FILTER_ROW = 1
_AC_ITEMS_START = 2

class μAdvancedCombo(μCheckCombo):
  def __init__(self, title: str = None, minShowFilter: int = 10):
    super().__init__(title)
    self._minShowFilter = minShowFilter

    filterItem = QStandardItem("")
    filterItem.setFlags(Qt.ItemFlag.NoItemFlags)
    self.rowModel.itemChanged.disconnect(self.onItemChanged)
    self.rowModel.insertRow(_AC_FILTER_ROW, filterItem)
    self.rowModel.itemChanged.connect(self.onItemChanged)

    self._filterEdit = QLineEdit()
    self._filterEdit.setPlaceholderText("🔍 filter...")
    self._filterEdit.setClearButtonEnabled(True)
    self.view().setIndexWidget(self.rowModel.index(_AC_FILTER_ROW, 0), self._filterEdit)
    self._filterEdit.textChanged.connect(self._applySearch)
    self.view().setRowHidden(_AC_FILTER_ROW, True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _applySearch(self, text: str):
    text = text.lower()
    for i in range(_AC_ITEMS_START, self.rowModel.rowCount()):
      item = self.rowModel.item(i)
      self.view().setRowHidden(i, bool(text) and text not in item.text().lower())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def hidePopup(self):
    self._filterEdit.clear()
    super().hidePopup()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onPressed(self, index: QModelIndex):
    if index.row() == _AC_FILTER_ROW:
      return
    if index.row() == 0:
      self.blockHide = True
      new_state = not self.areAllChecked()
      for i in range(_AC_ITEMS_START, self.rowModel.rowCount()):
        self.rowModel.item(i).setData(new_state, Qt.ItemDataRole.UserRole)
      self.refreshHeader()
      self.changed.emit()
      return
    self.blockHide = True
    item = self.rowModel.itemFromIndex(index)
    item.setData(not item.data(Qt.ItemDataRole.UserRole), Qt.ItemDataRole.UserRole)
    self.refreshHeader()
    self.changed.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def addCheckItem(self, text: str, checked: bool = True, icon: QIcon = None):
    for i in range(_AC_ITEMS_START, self.rowModel.rowCount()):
      if self.rowModel.item(i).text() == text:
        return
    row = QStandardItem(text)
    row.setData(checked, Qt.ItemDataRole.UserRole)
    if icon and not icon.isNull():
      row.setIcon(icon)

    insertPos = self.rowModel.rowCount()
    self.rowModel.itemChanged.disconnect(self.onItemChanged)
    for i in range(_AC_ITEMS_START, self.rowModel.rowCount()):
      if text.lower() < self.rowModel.item(i).text().lower():
        insertPos = i
        break
    self.rowModel.insertRow(insertPos, row)
    nitems = self.rowModel.rowCount() - _AC_ITEMS_START
    self.view().setRowHidden(_AC_FILTER_ROW, nitems < self._minShowFilter)
    self.refreshHeader()
    self.rowModel.itemChanged.connect(self.onItemChanged)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def getChecked(self) -> list:
    return [self.rowModel.item(i).text()
            for i in range(_AC_ITEMS_START, self.rowModel.rowCount())
            if self.rowModel.item(i).data(Qt.ItemDataRole.UserRole)]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def areAllChecked(self) -> bool:
    total = self.rowModel.rowCount() - _AC_ITEMS_START
    return total == 0 or len(self.getChecked()) == total

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def refreshHeader(self):
    prefix  = f"{self.title}: " if self.title is not None else ""
    checked = self.getChecked()
    nitems  = self.rowModel.rowCount() - _AC_ITEMS_START
    if nitems == 0 or len(checked) == nitems:
      text = f"{prefix}All"
    elif len(checked) == 1:
      text = f"{prefix}{checked[0]}"
    elif len(checked) == 0:
      text = f"{prefix}None"
    else:
      text = f"{prefix}{len(checked)}/{nitems}"
    self.rowModel.item(0).setText(text)
    self.setCurrentIndex(0)
