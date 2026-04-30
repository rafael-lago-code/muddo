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
from PyQt6.QtWidgets import QGridLayout, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QPainter, QPixmap, QColor
from PyQt6.QtCore import Qt, QPoint
from cSettings import cSettings
from helpers.cPrint import cPrint
from helpers.util import *
from helpers import cEffects
from widgets.cOrb import cOrb, cTheme_Toolbar
from widgets.cGrid import cGrid

#----------------------------------------------------------------------------------------------------------
class cToolbarItem(cOrb):
  theme = None

  @classmethod
  def getTheme(cls):
    if cls.theme is None:
      cls.theme = cTheme_Toolbar()
    return cls.theme

  def __init__(self, toolbar, script, enabled=True, icon=None, names=frozenset(), commands=[]):
    title = toolbar.replace("_","").replace("toolbar", "")
    resolved_icon = QIcon(icon) if icon else QIcon('/home/soul/share/μddo/images/ddo_themes/skill_icons/placeholder.png')
    tooltip = ", ".join(sorted(names)) if names else "<i><no description></i>"
    super().__init__(title, resolved_icon, enabled, tooltip=tooltip)
    self.names    = names
    self.commands = commands
    for step in script:
      self.clicked.connect(lambda checked=False, s=step: s())
  
  def index(self):
    return int(self.text())

  def paintText(self, painter):
    if not self.text(): return
    if not self.textRendered:
      self.textRendered = QPixmap(self.size())
      self.textRendered.fill(Qt.GlobalColor.transparent)
      textPainter = QPainter(self.textRendered)

      text = self.text().replace("&", "")
      textPainter.setFont(self.font())
      aFlags = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
      textRect = self.rect().adjusted(4, 4, -4, -4)

      outlineColour = QColor(50, 50, 50, 75)
      textPainter.setPen(outlineColour)
      for dx in range(-2, 3):
        for dy in range(-2, 3):
          textPainter.drawText(
            textRect.adjusted(dx, dy, dx, dy), aFlags, text)

      textPainter.setPen(QColor(0, 0, 0, 200))
      textPainter.drawText(textRect.translated(QPoint(1, 1)), aFlags, text)
      textPainter.setPen(QColor(255, 255, 255))
      textPainter.drawText(textRect, aFlags, text)
      textPainter.end()

    textEffect = self.theme.textEffect.get(self._current_state, cEffects.cNone())
    painter.drawPixmap(self.rect(), textEffect.apply(self.textRendered))


#---------------------------------------------------------------------------------------------------------------
#
#
#                                            T O O L B A R
#                                  
#   This is a hybrid class.
#   One instance lives in cMainWindow. __init__ calls cSettings.setup.
#   Anyone can add items via class method "addItems"
#---------------------------------------------------------------------------------------------------------------
class cToolbar(QWidget):
  widgetID = "Toolbar"
  items : list[cToolbarItem] = []
  widget = None

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(cls):
    cSettings.toolbar._macroNCols.valueChanged.connect(cls.widget.setColumns)
    cSettings.toolbar._macroNRows.valueChanged.connect(cls.widget.setRows)
    cSettings.toolbar._macroFillRowFirst.stateChanged.connect(cls.widget.setFillRowsFirst)
    cSettings.toolbar._macroNCols.valueChanged.connect(cls.sortLayout)
    cSettings.toolbar._macroNRows.valueChanged.connect(cls.sortLayout)
    cSettings.toolbar._macroFillRowFirst.stateChanged.connect(cls.sortLayout)

  #----------------------------------------------------------------------------------------------------------
  def __init__(self, main):
    cToolbar._instantiateWidget(main)
    super().__init__(main)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def _instantiateWidget(cls, main):
    cls.widget = cGrid(main)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def addItems(cls, newItems):
    if isinstance(newItems, (list,tuple)):
      for i in newItems: cls.items.append(i)
    else:
      cls.items.append(newItems)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def clearItems(cls):
    cls.items.clear()

  # # #----------------------------------------------------------------------------------------------------------
  # @classmethod
  # def TESTITEMS(cls):
  #   for i in range(10):
  #     cls.addItems(cToolbarItem(str(i), {}, icon=QIcon(), enabled=True))
  #   cls.sortLayout()
  
  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def sortLayout(cls):
    cls.clearLayout()
    nrows = cSettings.toolbar.macroNRows()
    ncols = cSettings.toolbar.macroNCols()
    macroFillMissing = cSettings.toolbar.macroFillMissing()
    fillRowsFirst= cSettings.toolbar.macroFillRowFirst()

    cls.widget.setColumns(ncols)
    cls.widget.setRows(ncols)
    cls.widget.setFillRowsFirst(fillRowsFirst)
    cls.items.sort(key=lambda item: item.index())

    if macroFillMissing and cls.items:
      indexed = {item.index(): item for item in cls.items}
      slots = [indexed.get(i) or cToolbarItem(str(i), {}, icon=QIcon(), enabled=False)
               for i in range(1, max(indexed) + 1)]
    else:
      slots = cls.items

    for item in slots:
      cls.widget.addWidget(item)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def clearLayout(cls):
    cls.widget.clear()




    


