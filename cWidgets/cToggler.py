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
from PyQt6.QtWidgets import QWidget, QPushButton
from cWidgets.cFloating import cFloating
from cWidgets.cOrb import cOrb
from cWidgets.util import *

class cToggler(cFloating):

  def __init__(self, title : str, icon):
    super().__init__()
    self.toggler = cOrb(title, icon)
    self.toggler.setCheckable(True)

    self.toggler.clicked.connect(self.toggle)
    self.setVisible(False)
    
  def toggle(self):
    if self.toggler.isChecked():
      # self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_DOWN))
      self.setVisible(True)
    else:
      # self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_UP))
      self.setVisible(False)

  def setVisible(self, value : bool):
    self.toggler.setChecked(value)
    # if value:
      # self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_DOWN))
    # else:
      # self.toggler.setIcon(getIcon(P_ICON_TRIANGLE_UP))
    super().setVisible(value)


