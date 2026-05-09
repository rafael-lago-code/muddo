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
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from helpers.util import *
from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#    from cMacrosDaemon import cMacrosDaemon

#---------------------------------------------------------------------------------------------------------------
#
#
#                                         C H E C K   C O M B O
#
#---------------------------------------------------------------------------------------------------------------
class μCheckCombo(QComboBox):
  changed = pyqtSignal()

  def __init__(self, title: str):
    super().__init__()
    self.title = title
    self.blockHide = False
    self.rowModel   = QStandardItemModel(self)
    self.setModel(self.rowModel)
    self.header = QStandardItem(f"{title}: All")
    # self.header.setCheckable(False)
    self.rowModel.appendRow(self.header)
    self.view().pressed.connect(self.onPressed)
    self.rowModel.itemChanged.connect(self.onItemChanged)

  #----------------------------------------------------------------------------------------------------------
  def onPressed(self, index: QModelIndex):
      item = self.rowModel.itemFromIndex(index)
      if not item:
          return

      self.blockHide = True
      if index.row() == 0:  # Header
          toggledState = Qt.CheckState.Unchecked if self.areAllChecked() else Qt.CheckState.Checked
          for i in range(1, self.rowModel.rowCount()):
              ii = self.rowModel.item(i)
              if ii.isCheckable():
                  ii.setCheckState(toggledState)
      else:                 # Individual item
          newState = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
          item.setCheckState(newState)

      # Always update header and notify listeners
      self.refreshHeader()
      self.changed.emit()

  #----------------------------------------------------------------------------------------------------------
  def hidePopup(self):
    if self.blockHide:
      self.blockHide = False
      return
    self.setCurrentIndex(0)
    self.refreshHeader()
    super().hidePopup()

  #----------------------------------------------------------------------------------------------------------
  def setCurrentIndex(self, index):
    super().setCurrentIndex(0)
  
  #----------------------------------------------------------------------------------------------------------
  def addCheckItem(self, text: str, checked: bool = True):
    for i in range(1, self.rowModel.rowCount()):
      if self.rowModel.item(i).text() == text:
        return
    row = QStandardItem(text)
    row.setCheckable(True)
    row.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    insertPos = self.rowModel.rowCount()
    self.rowModel.itemChanged.disconnect(self.onItemChanged)
    for i in range(1, self.rowModel.rowCount()):
        if text.lower() < self.rowModel.item(i).text().lower():
            insertPos = i
            break
    self.rowModel.insertRow(insertPos,row)
    self.refreshHeader()
    self.rowModel.itemChanged.connect(self.onItemChanged)

  #----------------------------------------------------------------------------------------------------------
  def getChecked(self) -> list:
    return [self.rowModel.item(i).text()
            for i in range(1, self.rowModel.rowCount())
            if self.rowModel.item(i).checkState() == Qt.CheckState.Checked]

  #----------------------------------------------------------------------------------------------------------
  def areAllChecked(self) -> bool:
    total = self.rowModel.rowCount() - 1
    return total == 0 or len(self.getChecked()) == total

  #----------------------------------------------------------------------------------------------------------
  def onItemChanged(self, item):
    self.refreshHeader()
    self.changed.emit()

  #----------------------------------------------------------------------------------------------------------
  def refreshHeader(self):
    checked = self.getChecked()
    nitems   = self.rowModel.rowCount() - 1
    if (nitems == 0 or len(checked) == nitems):
      text = f"{self.title}: All"
    elif len(checked) == 1:
      text = f"{self.title}: {checked[0]} Only"
    elif len(checked) == 0:
      text = f"{self.title}: None"
    else:
      text = f"{self.title}: {len(checked)}/{nitems}"
    self.rowModel.item(0).setText(text)
    self.setCurrentIndex(0)