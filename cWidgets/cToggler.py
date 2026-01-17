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
    if self.isVisible():
      self.saveState()
      self.hide()
      self.toggler.setChecked(False)
    else:
      # there is a bug preventing the loading the position of the window, if it
      # "thinks" that it didn't change, so we need to force some crap here.
      self.move(QPoint(10,10))
      self.show()
      self.loadState()
      self.toggler.setChecked(True)
      # self.setVisible(True)      

  def setVisible(self, value : bool):
    self.toggler.setChecked(value)
    super().setVisible(value)
  


