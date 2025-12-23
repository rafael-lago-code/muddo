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
from cWidgets.util import *
from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent


class cButton(QPushButton):
    ctrlClicked = pyqtSignal()
    rightClicked = pyqtSignal()
    ctrlRightClicked = pyqtSignal()

    def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        if title: self.setText(title)
        if icon: self.setIcon(getIcon(icon))
        if tooltip: self.setToolTip(tooltip)
        self.setEnabled(enabled)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

    def mousePressEvent(self, event: QMouseEvent):
      if event.button() == Qt.MouseButton.LeftButton:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
          self.ctrlClicked.emit()
        else:
          super().mousePressEvent(event)
      elif event.button() == Qt.MouseButton.RightButton:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
          self.ctrlRightClicked.emit()
        else:
          self.rightClicked.emit()

class cLauncherButton(cButton):
  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(title, icon, enabled, tooltip, *args, **kwargs)
    self.setFixedHeight(60)
    self.setFixedWidth(120)
    self.setIconSize(QtCore.QSize(36,36))