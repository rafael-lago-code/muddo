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
from cWidgets.util import *

class cFloating(QWidget):
  # Default constants
  P_RECT = QRect(100,100,300,200)
  P_POS_X = 100
  P_POS_Y = 100
  P_SIZE_W = 300
  P_SIZE_H = 200
  widgetID = "floatingWidget"
  
  def __init__(self):
    super().__init__()
    self.settings = QSettings(P_DEFAULT_CONF)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                        Qt.WindowType.Window | 
                        Qt.WindowType.WindowStaysOnTopHint)
    self.setWindowOpacity(0.9)
    # self.setGeometry(self.P_POS_X, self.P_POS_Y, self.P_SIZE_W, self.P_SIZE_H)
    self.loadState()
  
  def loadState(self):
    rect = self.settings.value(f"{self.widgetID}/geometry", self.P_RECT)
    self.setGeometry(rect)

  def saveState(self):
    self.settings.setValue(f"{self.widgetID}/geometry",  self.geometry())
  
  def closeEvent(self, event):
    self.saveState()
    super().closeEvent(event)
