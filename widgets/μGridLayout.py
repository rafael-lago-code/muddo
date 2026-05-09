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
from PyQt6.QtWidgets import QGridLayout
from helpers.util import *

class μGridLayout(QGridLayout):

  def __init__(self):
    super().__init__()

    self.firstRow = 0
    self.firstColumn = 0
    self.lastRow = 0
    self.lastColumn = 0

  def appendRow(self, items):
    if not isinstance(items,list): items = [items]
    r = self.lastRow
    c = self.firstColumn
    ncols = 1
    for i in items: 
      if isinstance(i,str) and i==">":
        ncols += 1
        continue
      elif isinstance(i,str):
        self.addWidget(QLabel(i), r, c, 1, ncols)
      elif isinstance(i,QLayout):
        self.addLayout(i, r, c, 1, ncols)
      elif i is not None:
        self.addWidget(i, r, c, 1, ncols)
      c+=ncols
      ncols=1
    self.lastRow += 1
  
  # def appendColumn(self, items):
  #   if not isinstance(items,list): items = [items]
  #   c = self.lastColumn
  #   r = self.firstRow
  #   for i in items: 
  #     if isinstance(i,str):
  #       i = QLabel(i)
  #     elif i is not None:
  #       self.addWidget(i, r, c)
  #     r+=1
  #   self.lastColumn += 1



    


