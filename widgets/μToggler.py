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
from PyQt6.QtCore import QPoint
from widgets.μFloating import μFloating
from widgets.μOrb import μOrb
from helpers.util import *

class μToggler(μFloating):

  def __init__(self, title : str, icon, parent = None):
    self.toggler = μOrb(title, icon)
    self.toggler.setCheckable(True)
    super().__init__(title, parent)
    self.toggler.clicked.connect(self.toggle)
    self.visibilityChanged.connect(self.toggler.setChecked)
    self.setVisible(False)

  def toggle(self):
    if self.isVisible():
      self.hide()
    else:
      self.show()

  def setVisible(self, value : bool):
    self.toggler.setChecked(value)
    super().setVisible(value)
