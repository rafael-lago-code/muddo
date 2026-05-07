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
from helpers.cImageFactory import getPixmap
from helpers.cPrint import cPrint
from helpers.util import *
from helpers import cEffects
from widgets.cFloating import cFloating
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
    self.trigger = toolbar
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
  grid = None

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(cls):
    cSettings.toolbar._macroNCols.valueChanged.connect(cls.grid.setColumns)
    cSettings.toolbar._macroNRows.valueChanged.connect(cls.grid.setRows)
    cSettings.toolbar._macroFillRowFirst.stateChanged.connect(cls.grid.setFillRowsFirst)
    cSettings.toolbar._macroNCols.valueChanged.connect(cls.sortLayout)
    cSettings.toolbar._macroNRows.valueChanged.connect(cls.sortLayout)
    cSettings.toolbar._macroFillRowFirst.stateChanged.connect(cls.sortLayout)
    cls.grid.itemsSwapped.connect(cls.onItemsSwapped)
    cls.widget.setVisible(False)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def onItemsSwapped(cls, item_a, item_b):
    if isinstance(item_a, cToolbarItem) and isinstance(item_b, cToolbarItem):
      cls.main.macros.swapTriggers(item_a.trigger, item_b.trigger)

  #----------------------------------------------------------------------------------------------------------
  def __init__(self, main):
    cToolbar.main = main
    cToolbar._instantiateWidget(main)
    super().__init__(main)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def _instantiateWidget(cls, main):
    cls.widget = cFloating("Toolbar", main)
    cls.grid = cGrid(cls.widget)

    cls.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    cls.widget.setTitleBarWidget(QWidget())
    cls.widget.setLayout(newVLayout([cls.grid]))
    # cls.widget.setBackground({})
    # theme = {d: f"ornate_frame_{d}" for d in ['NW', 'N', 'NE', 'W', 'E', 'SW', 'S', 'SE']}
    theme : dict[str, QPixmap]= {}
    for d in ['NW', 'N', 'NE', 'W', 'E', 'SW', 'S', 'SE']:
      pm = getPixmap(f"ornate_frame_{d}")
      pm = pm.scaled(int(pm.width()*0.25), int(pm.height()*0.25), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
      theme[d] = cEffects.cBrightContrast(-0.2,2.0).apply(cEffects.cOpacity(0.75).apply(pm))
    cls.widget.setBackground(theme)

    main.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, cls.widget)
    cls.widget.setFloating(True)
    cls.widget.setVisible(False)

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
    cls.clearLayout()
    cls.widget.setVisible(False)

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
    cls.widget.setVisible(True)
    nrows = cSettings.toolbar.macroNRows()
    ncols = cSettings.toolbar.macroNCols()
    macroFillMissing = cSettings.toolbar.macroFillMissing()
    fillRowsFirst= cSettings.toolbar.macroFillRowFirst()

    cls.grid.setColumns(ncols)
    cls.grid.setRows(ncols)
    cls.grid.setFillRowsFirst(fillRowsFirst)
    cls.items.sort(key=lambda item: item.index())

    if macroFillMissing and cls.items:
      indexed = {item.index(): item for item in cls.items}
      slots = [indexed.get(i) or cToolbarItem(str(i), {}, icon=QIcon(), enabled=False)
               for i in range(1, max(indexed) + 1)]
    else:
      slots = cls.items

    for item in slots:
      cls.grid.addWidget(item)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def clearLayout(cls):
    cls.grid.clear()
    cls.widget.setVisible(False)




    


