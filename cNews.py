# coding=utf-8
###########################################################################
# Name:   μDDO
# Author: Rafael Lago
# Date:   February 2025
#
# Support classes for the Linux based launcher
# for the game Dungeons & Dragons Online
#
# Based on PyLotRO by AJackson <ajackson@bcs.org.uk>
# Based on a script by SNy <SNy@bmx-chemnitz.de>
#
# (C) 2025 Rafael Lago
#
# This file is part of PyLotRO
#
# μDDO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# μDDO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with μDDO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################

from PyQt6.QtWidgets import QWidget, QTextEdit, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy
from util import *
from cCollapsible import cCollapsible

class cNews(cCollapsible):

  def __init__(self):
    super().__init__("News")
    
    self.context = QTextEdit()
    self.context.setReadOnly(True)
    self.context.setAcceptRichText(True)
    self.context.setText("TODO")

    v = QVBoxLayout()
    v.addWidget(self.context)
    self.body.setLayout(v)




    


