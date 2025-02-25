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
#    <ajackson@bcs.org.uk>), which in turn is based on a lotrolauncher 
#    script by SNy (<SNy@bmx-chemnitz.de>)
#
#
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLayout
from util import *

class cCollapsible(QWidget):

  def __init__(self, title : str):
    super().__init__()
    self.tag = QPushButton(title)
    self.tag.setFlat(True)
    self.tag.setIcon(getIcon(P_ICON_TRIANGLE_DOWN))
    self.tag.setStyleSheet("text-align:left;")

    self.tag.clicked.connect(self.toggle)
    
    self.body = QWidget()
    
    h = QHBoxLayout()
    h.addWidget(self.tag)
    h.addStretch()
    v = QVBoxLayout()
    v.addLayout(h)
    v.addWidget(self.body)
    self.setLayout(v)

  def toggle(self):
    if self.body.isVisible():
      self.setCollapsed(True)
    else:
      self.setCollapsed(False)

  def isCollapsed(self):
    return not self.body.isVisible()
  
  def setCollapsed(self, value : bool):
    if value:
      self.tag.setIcon(getIcon(P_ICON_TRIANGLE_RIGHT))
      self.body.hide()
    else:
      self.tag.setIcon(getIcon(P_ICON_TRIANGLE_DOWN))
      self.body.show()

  def addWidget(self, w : QWidget):
    l = self.body.layout()
    l.addWidget(w)
  
  def addLayout(self, w : QLayout):
    l = self.body.layout()
    l.addLayout(w)

    


