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
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout
from cWidgets.util import *
from cWidgets.cToggler import cToggler

class cNews(cToggler):

  def __init__(self, main):
    self.widgetID = "news"
    self.main = main
    super().__init__("News", P_ICON_NOTES)
    self.context = QTextEdit()
    self.context.setReadOnly(True)
    self.context.setAcceptRichText(True)
    self.context.setText("TODO")

    v = QVBoxLayout()
    v.addWidget(self.context)
    self.setLayout(v)
  
    #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    pass




    


