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
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSettings, QPoint, QSize, Qt, QRect
import time
from helpers.util import *

class cFloating(QWidget):
  # Default constants
  P_RECT = QRect(100,100,300,200)
  P_POS_X = 100
  P_POS_Y = 100
  P_SIZE_W = 300
  P_SIZE_H = 200
  widgetID = "floatingWidget"
  _state = QSettings(P_DEFAULT_CONF)
  
  def __init__(self, parent = None):
    super().__init__(parent)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                        Qt.WindowType.Window | 
                        Qt.WindowType.WindowStaysOnTopHint)
    self.setWindowOpacity(0.9)
    # self.setGeometry(self.P_POS_X, self.P_POS_Y, self.P_SIZE_W, self.P_SIZE_H)
    self.loadState()
  
  def loadState(self):
    setting = QSettings(P_DEFAULT_CONF)
    self.loadGeometry()
    self.setVisible(setting.value(f"{self.widgetID}/visible") == "true")
  
  def loadGeometry(self):
    setting = QSettings(P_DEFAULT_CONF)
    rect = setting.value(f"{self.widgetID}/geometry", self.P_RECT)
    # there is a bug preventing the loading the position of the window, if it
    # "thinks" that it didn't change, so we need to force some crap here.
    self.move(QPoint(10,10))
    self.setGeometry(rect)

  def saveState(self):
    self._state.setValue(f"{self.widgetID}/geometry",  self.geometry())
    self._state.setValue(f"{self.widgetID}/visible",  self.isVisible())

  def show(self):
    if self.isVisible(): return
    # self.loadState()
    self.setVisible(True)

  def hide(self):
    if not self.isVisible(): return
    # self.saveState()
    self.setVisible(False)

  def setVisible(self, value : bool):
    super().setVisible(value)
    if value: self.loadGeometry()
    else:     self.saveState()
  
  def closeEvent(self, event):
    self.saveState()
    super().closeEvent(event)
