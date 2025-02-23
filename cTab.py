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
#    <ajackson@bcs.org.uk>), which in turn is based on a script by SNy
#    (<SNy@bmx-chemnitz.de>)
#
#
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLayout
from util import *

class cTab(QWidget):

  def __init__(self, title : str):
    super().__init__()
    self.toggler = QPushButton(" "+title)
    self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_RIGHT))
    self.toggler.setFixedHeight(36)
    self.toggler.setCheckable(True)

    self.toggler.clicked.connect(self.toggle)
    self.setVisible(False)
    
  def toggle(self):
    if self.toggler.isChecked():
      self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_DOWN))
      self.setVisible(True)
    else:
      self.setVisible(False)
      self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_RIGHT))

  def setVisible(self, value : bool):
    super().setVisible(value)
    self.toggler.setChecked(value)


