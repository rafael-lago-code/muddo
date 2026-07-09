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
import sys
from PyQt6.QtWidgets import QMenu
from PyQt6.QtWidgets import QWidgetAction, QWidget, QHBoxLayout, QToolButton, QPushButton, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QSizePolicy

class μMenu(QMenu):
  def addAction(self, text: str, callback, icon = None, button : QPushButton = None,
                buttonCallback = None, parent = None) -> QAction:

    newAction = QAction(text, self)
    newAction.triggered.connect(callback)
    if icon: newAction.setIcon(icon)

    widget = QWidget(self)
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setSpacing(8)

    menuText = QToolButton(widget)
    menuText.setDefaultAction(newAction)
    menuText.setAutoRaise(True)
    menuText.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    menuText.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    menuText.setStyleSheet("""
        QToolButton {
            background: transparent;
            border: none;
            text-align: left;
            padding: 4px 10px;
        }
        QToolButton:hover {
            background: palette(highlight);
            color: palette(highlighted-text);
        }
    """)

    layout.addWidget(menuText, 1)
    if button:
      if buttonCallback: button.clicked.connect(buttonCallback)
      layout.addWidget(button, 0)

    widgetAction = QWidgetAction(self)
    widgetAction.setDefaultWidget(widget)
    super().addAction(widgetAction)