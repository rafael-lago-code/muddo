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
from widgets.cFloating import cFloating
from widgets.cOrb import cOrb
from helpers.util import *

class cToggler(cFloating):

  def __init__(self, title : str, icon, parent = None):
    self.toggler = cOrb(title, icon)
    self.toggler.setCheckable(True)
    super().__init__(parent)

    self.toggler.clicked.connect(self.toggle)
    self.setVisible(False)
    
  def toggle(self):
    if self.isVisible():
      self.hide()
    else:
      self.show()
  
  # def show(self):
  #   # there is a bug preventing the loading the position of the window, if it
  #   # "thinks" that it didn't change, so we need to force some crap here.
  #   if self.isVisible(): return
  #   self.move(QPoint(10,10))
  #   self.loadState()
  #   self.setVisible(True)

  # def hide(self):
  #   if not self.isVisible(): return
  #   self.setVisible(False)
  #   self.saveState()

  def setVisible(self, value : bool):
    self.toggler.setChecked(value)
    super().setVisible(value)
  


