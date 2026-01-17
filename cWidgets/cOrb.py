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
from cWidgets.util import *
from PyQt6.QtWidgets import QPushButton, QSizePolicy, QToolTip
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPainterPath, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from cWidgets import cEffects

P_STATUS_NORMAL=0
P_STATUS_HOVERD=1
P_STATUS_COVERD=2
P_STATUS_LCLICK=3
P_STATUS_RCLICK=4
P_STATUS_CCLICK=5
P_STATUS_CRLICK=6
P_STATUS_DISBLD=7
P_STATUS_CHECKD=8

class cOrbTheme_RedMedium():
  _instance = None
  orbSize = QtCore.QSize(80,80)
  iconSize = QtCore.QSize(40,40)

  def __new__(self):
    if self._instance is None:
      self._instance = super().__new__(self)
      BG_RED_PIX = getPixmap(P_BG_REDORB)
      FG_RED_PIX = getPixmap(P_FG_REDORB)
      PRESSED_RED = getPixmap(P_BG_PRESSED_REDORB)

      BG_RED_PIX = BG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
      FG_RED_PIX = FG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
      PRESSED_RED = PRESSED_RED.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)

      self.bgRedLayers = {}
      self.bgRedLayers[P_STATUS_NORMAL] = BG_RED_PIX
      self.bgRedLayers[P_STATUS_HOVERD] = cEffects.tintPixmap(BG_RED_PIX,(200,10,10),1.0)
      self.bgRedLayers[P_STATUS_COVERD] = cEffects.invertPixmap(BG_RED_PIX)
      self.bgRedLayers[P_STATUS_LCLICK] = cEffects.desaturatePixmap(BG_RED_PIX,0.3)
      self.bgRedLayers[P_STATUS_RCLICK] = cEffects.tintPixmap(BG_RED_PIX,(215,120,0),1.0)
      self.bgRedLayers[P_STATUS_CCLICK] = cEffects.tintPixmap(BG_RED_PIX,(215,120,0),1.0)
      self.bgRedLayers[P_STATUS_CRLICK] = cEffects.invertPixmap(BG_RED_PIX)
      self.bgRedLayers[P_STATUS_DISBLD] = cEffects.desaturatePixmap(BG_RED_PIX,1.0)
      self.bgRedLayers[P_STATUS_CHECKD] = PRESSED_RED

      self.fgRedLayers = {}
      self.fgRedLayers[P_STATUS_NORMAL] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_HOVERD] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_COVERD] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_LCLICK] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_RCLICK] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_CCLICK] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_CRLICK] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_DISBLD] = FG_RED_PIX
      self.fgRedLayers[P_STATUS_CHECKD] = QPixmap()

      self.iconEffect = {}
      self.iconEffect[P_STATUS_NORMAL] = cEffects.cNone()
      self.iconEffect[P_STATUS_HOVERD] = cEffects.cTint((215,120,0),0.5)
      self.iconEffect[P_STATUS_COVERD] = cEffects.cNone()
      self.iconEffect[P_STATUS_LCLICK] = cEffects.cTint((215,120,0),0.5)
      self.iconEffect[P_STATUS_RCLICK] = cEffects.cNone()
      self.iconEffect[P_STATUS_CCLICK] = cEffects.cNone()
      self.iconEffect[P_STATUS_CRLICK] = cEffects.cNone()
      self.iconEffect[P_STATUS_DISBLD] = cEffects.cGreyscale()
      self.iconEffect[P_STATUS_CHECKD] = cEffects.cTint((215,120,0),0.5)
      
    return self._instance
  
class cOrbTheme_RedSmall(cOrbTheme_RedMedium):
  _instance = None
  orbSize = QtCore.QSize(32,32)
  iconSize = QtCore.QSize(20,20)


class cOrb(QPushButton):
  ctrlClicked = pyqtSignal()
  rightClicked = pyqtSignal()
  ctrlRightClicked = pyqtSignal()
  theme = None

  @classmethod
  def initTheme(self):
    if self.theme is None:
      self.theme = cOrbTheme_RedMedium()
    return self.theme

  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(*args, **kwargs)
    if title: self.setText(title)
    if icon: self.setIcon(getIcon(icon))
    if tooltip: self.setToolTip(tooltip)
    self._current_state = P_STATUS_NORMAL
    self._is_hovered = False

    self.setEnabled(enabled)

    theme = self.__class__.theme or self.__class__.initTheme()

    self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.setFixedSize(self.theme.orbSize)
    self.setIconSize(self.theme.iconSize)
    self.setMouseTracking(True)

  def setEnabled(self, a0):
    if a0:
      self.normalizeState()
    else:
      self.setState(P_STATUS_DISBLD)
    return super().setEnabled(a0)

  def setChecked(self, a0):
    if a0:
      self.setState(P_STATUS_CHECKD)
    else:
      self.normalizeState()
    return super().setChecked(a0)

  def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = self.theme.bgRedLayers.get(self._current_state, QPixmap())
    fg = self.theme.fgRedLayers.get(self._current_state, QPixmap())

    if not bg.isNull(): painter.drawPixmap(self.rect(), bg)

    self.paintIcon(painter)

    if not fg.isNull(): painter.drawPixmap(self.rect(), fg)

    self.paintText(painter)

    painter.end()
  
  def paintIcon(self, painter : QPainter):
    if self.icon().isNull(): return

    iconEffect = self.theme.iconEffect.get(self._current_state, cEffects.cNone())
    isize = self.theme.iconSize
    osize = self.theme.orbSize
    # Centers the icon respecting iconSize()
    r = QtCore.QRect(int((osize.width()  - isize.width()) / 2.0),
                      int((osize.height() - isize.height()) / 2.0),
                      isize.width(), isize.height())
    pmap = self.icon().pixmap(self.iconSize())
    painter.drawPixmap(r, iconEffect.apply(pmap.scaled(isize, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)))

  def paintText(self, painter : QPainter):
    if not self.text(): return

    text = self.text().replace("&","")
    font = QFont("Linux Libertine Capitals", 12)  # Or use self.font() as base
    font.setBold(True)
    font.setItalic(False)
    painter.setFont(font)
    aFlags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom

    textRect = self.rect().adjusted(5, 0, -5, 0)
    textColour = QColor(255, 255, 255) 
    shadowColour = QColor(0, 0, 0, 200)  # Semi-black
    shadowOffset = QPoint(4, 4)

    outlineColour = QColor(50, 50, 50, 75)  # Semi-black
    painter.setPen(outlineColour)
    for dx in range(-2,3):
      for dy in range(-2,3):
        painter.drawText(QtCore.QRect(textRect.x()+dx, textRect.y()+dy,
                                      textRect.width(), textRect.height()), aFlags, text)
    
    painter.setPen(shadowColour)
    painter.drawText(textRect.translated(shadowOffset), aFlags, text)
    painter.setPen(textColour)      
    painter.drawText(textRect, aFlags, text)


  def enterEvent(self, event):
    if not self.isEnabled(): return
    if self.isChecked(): return
    self._is_hovered = True
    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
      self.setState(P_STATUS_COVERD)
    else:
      self.setState(P_STATUS_HOVERD)
      QToolTip.showText( self.mapToGlobal(self.rect().bottomLeft()),
                         self.toolTip(), self)
    super().enterEvent(event)

  def leaveEvent(self, event):
    if not self.isEnabled(): return
    if self.isChecked(): return
    self._is_hovered = False
    self.setState(P_STATUS_NORMAL)
    super().leaveEvent(event)

  def mousePressEvent(self, event):
    if not self.isEnabled():
      return
    if event.button() == Qt.MouseButton.LeftButton:
      if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        self.ctrlClicked.emit()
        self.setState(P_STATUS_CCLICK)
      else:
        super().mousePressEvent(event)
        self.setState(P_STATUS_LCLICK)
    elif event.button() == Qt.MouseButton.RightButton:
      if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        self.ctrlRightClicked.emit()
        self.setState(P_STATUS_CRLICK)
      else:
        self.rightClicked.emit()
        self.setState(P_STATUS_RCLICK)

  def mouseReleaseEvent(self, event):
    if not self.isEnabled():
      return
    if event.button() == Qt.MouseButton.LeftButton:
      self.normalizeState()
    super().mouseReleaseEvent(event)

  def normalizeState(self):
    # Sets state to hover or normal
    if self._is_hovered:
      self.setState(P_STATUS_HOVERD)
    else:
      self.setState(P_STATUS_NORMAL)

  def setState(self, state):
    self._current_state = state
    self.update()  # Trigger repaint

#-------------------------------------------------------------------------------------------------------------
class cOrbSmall(cOrb):
  theme = None

  @classmethod
  def initTheme(self):
    if self.theme is None:
      self.theme = cOrbTheme_RedSmall()
    return self.theme
  
  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(title, icon, enabled, tooltip, *args, **kwargs)
