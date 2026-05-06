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
from helpers.cImageFactory import *
from PyQt6.QtWidgets import QPushButton, QSizePolicy, QToolTip, QApplication
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QMouseEvent, QShortcut, QKeySequence
from PyQt6.QtCore import QSize, Qt, pyqtSignal, QPoint, QEvent
from PyQt6.QtWidgets import QMenu, QWidget
from helpers import cEffects

P_STATUS_NORMAL=0
P_STATUS_HOVERD=1
P_STATUS_COVERD=2
P_STATUS_LCLICK=3
P_STATUS_RCLICK=4
P_STATUS_CCLICK=5
P_STATUS_CRLICK=6
P_STATUS_DISBLD=7
P_STATUS_CHECKD=8
P_STATUS_CHECKD_HOVERD=9

P_COLOUR_GOLD=(215,120,0)
P_COLOUR_RED=(200,10,10)

P_COLOUR_HIGHLIGHT=P_COLOUR_GOLD
P_COLOUR_ORB_GLOW=P_COLOUR_RED

#-------------------------------------------------------------------------------------------------------------
class cOrbTheme_RedMedium():
  _instance = None
  orbSize = QtCore.QSize(80,80)
  iconSize = QtCore.QSize(40,40)
  font = QFont("Linux Libertine Capitals", 12, QFont.Weight.Bold, False)

  def __new__(self):
    if self._instance is None:
      self._instance = super().__new__(self)
      BG_RED_PIX = getPixmap(P_BG_REDORB)
      FG_RED_PIX = getPixmap(P_FG_REDORB)
      PRESSED_RED = getPixmap(P_BG_PRESSED_REDORB)

      BG_RED_PIX  = BG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      FG_RED_PIX  = FG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      PRESSED_RED = PRESSED_RED.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      ICON_EFFECT = cEffects.cTint(P_COLOUR_HIGHLIGHT,0.5)
      TEXT_EFFECT = cEffects.cTint(P_COLOUR_HIGHLIGHT,0.2)

      self._instance.setBg(BG_RED_PIX, PRESSED_RED)
      self._instance.setFg(FG_RED_PIX, cEffects.opacity(FG_RED_PIX,0.6))
      self._instance.setIconEffect(ICON_EFFECT)
      self._instance.setTextEffect(TEXT_EFFECT)

    return self._instance

  #---------------------------------------------------------------------------------------------------------
  def setBg(self, bg, pressed):
    self.bg = {}
    self.bg[P_STATUS_NORMAL] = bg
    self.bg[P_STATUS_HOVERD] = cEffects.tint(bg,P_COLOUR_ORB_GLOW,1.0)
    self.bg[P_STATUS_COVERD] = cEffects.tint(bg,P_COLOUR_HIGHLIGHT,0.3)
    self.bg[P_STATUS_LCLICK] = cEffects.desaturate(bg,0.3)
    self.bg[P_STATUS_RCLICK] = cEffects.tint(bg,P_COLOUR_HIGHLIGHT,1.0)
    self.bg[P_STATUS_CCLICK] = cEffects.tint(bg,P_COLOUR_HIGHLIGHT,1.0)
    self.bg[P_STATUS_CRLICK] = cEffects.invert(bg)
    self.bg[P_STATUS_DISBLD] = cEffects.desaturate(bg,1.0)
    self.bg[P_STATUS_CHECKD] = pressed
    self.bg[P_STATUS_CHECKD_HOVERD] = pressed
  
  #---------------------------------------------------------------------------------------------------------
  def setIconEffect(self, iconEffect):
    self.iconEffect = {}
    self.iconEffect[P_STATUS_NORMAL] = cEffects.cNone()
    self.iconEffect[P_STATUS_HOVERD] = iconEffect
    self.iconEffect[P_STATUS_COVERD] = cEffects.cNone()
    self.iconEffect[P_STATUS_LCLICK] = iconEffect
    self.iconEffect[P_STATUS_RCLICK] = cEffects.cNone()
    self.iconEffect[P_STATUS_CCLICK] = cEffects.cNone()
    self.iconEffect[P_STATUS_CRLICK] = cEffects.cNone()
    self.iconEffect[P_STATUS_DISBLD] = cEffects.cGreyscale()
    self.iconEffect[P_STATUS_CHECKD] = iconEffect
    self.iconEffect[P_STATUS_CHECKD_HOVERD] = iconEffect

  #---------------------------------------------------------------------------------------------------------
  def setTextEffect(self, textEffect):
    self.textEffect = {}
    self.textEffect[P_STATUS_NORMAL] = cEffects.cNone()
    self.textEffect[P_STATUS_HOVERD] = textEffect
    self.textEffect[P_STATUS_COVERD] = cEffects.cNone()
    self.textEffect[P_STATUS_LCLICK] = textEffect
    self.textEffect[P_STATUS_RCLICK] = cEffects.cNone()
    self.textEffect[P_STATUS_CCLICK] = cEffects.cNone()
    self.textEffect[P_STATUS_CRLICK] = cEffects.cNone()
    self.textEffect[P_STATUS_DISBLD] = cEffects.cGreyscale()
    self.textEffect[P_STATUS_CHECKD] = textEffect
    self.textEffect[P_STATUS_CHECKD_HOVERD] = textEffect
  
  #---------------------------------------------------------------------------------------------------------
  def setFg(self, fg, pressed):
    self.fg = {}
    self.fg[P_STATUS_NORMAL] = fg
    self.fg[P_STATUS_HOVERD] = fg
    self.fg[P_STATUS_COVERD] = fg
    self.fg[P_STATUS_LCLICK] = fg
    self.fg[P_STATUS_RCLICK] = fg
    self.fg[P_STATUS_CCLICK] = fg
    self.fg[P_STATUS_CRLICK] = fg
    self.fg[P_STATUS_DISBLD] = fg
    self.fg[P_STATUS_CHECKD] = pressed
    self.fg[P_STATUS_CHECKD_HOVERD] = cEffects.tint(fg,P_COLOUR_HIGHLIGHT,0.3)

#-------------------------------------------------------------------------------------------------------------
class cOrbTheme_RedSmall(cOrbTheme_RedMedium):
  _instance = None
  orbSize = QtCore.QSize(32,32)
  iconSize = QtCore.QSize(20,20)

#-------------------------------------------------------------------------------------------------------------
class cTheme_DialogClose(cOrbTheme_RedMedium):
  _instance = None
  orbSize = QtCore.QSize(24,24)
  iconSize = QtCore.QSize(14,14)

#-------------------------------------------------------------------------------------------------------------
class cTheme_Checkbox(cOrbTheme_RedMedium):
  _instance = None
  orbSize = QtCore.QSize(21,21)
  iconSize = QtCore.QSize(18,18)

  def __new__(self):
    if self._instance is None:
      self._instance = super().__new__(self)
      BG_RED_PIX  = getPixmap(P_BG_REDBOX)
      FG_RED_PIX  = getPixmap(P_FG_REDBOX)
      PRESSED_RED = getPixmap(P_BG_PRESSED_REDBOX)

      BG_RED_PIX  = BG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      FG_RED_PIX  = FG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      PRESSED_RED = PRESSED_RED.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      ICON_EFFECT = cEffects.cNone()
      TEXT_EFFECT = cEffects.cTint(P_COLOUR_HIGHLIGHT,0.2)

      self._instance.setBg(BG_RED_PIX, PRESSED_RED)
      self._instance.setFg(FG_RED_PIX, cEffects.opacity(FG_RED_PIX,0.5))
      self._instance.setIconEffect(ICON_EFFECT)
      self._instance.setTextEffect(TEXT_EFFECT)

    return self._instance
  
#-------------------------------------------------------------------------------------------------------------
class cTheme_Toolbar(cOrbTheme_RedMedium):
  _instance = None
  orbSize = QtCore.QSize(38,38)
  iconSize = QtCore.QSize(30,30)

  def __new__(self):
    if self._instance is None:
      self._instance = super().__new__(self)
      BG_RED_PIX  = getPixmap(P_BG_REDFRAME)
      FG_RED_PIX  = getPixmap(P_FG_REDFRAME)
      PRESSED_RED = getPixmap(P_BG_REDFRAME)

      BG_RED_PIX  = BG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      FG_RED_PIX  = FG_RED_PIX.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      PRESSED_RED = PRESSED_RED.scaled(self.orbSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
      ICON_EFFECT = cEffects.cNone()
      TEXT_EFFECT = cEffects.cTint(P_COLOUR_HIGHLIGHT,0.2)

      self._instance.setBg(BG_RED_PIX, PRESSED_RED)
      self._instance.setFg(FG_RED_PIX, QPixmap())
      self._instance.setIconEffect(ICON_EFFECT)
      self._instance.setTextEffect(TEXT_EFFECT)

    return self._instance
  
#-------------------------------------------------------------------------------------------------------------
#
#                                                  O R B
#
#-------------------------------------------------------------------------------------------------------------
class cOrb(QPushButton):
  ctrlClicked = pyqtSignal(QMouseEvent)
  rightClicked = pyqtSignal(QMouseEvent)
  ctrlRightClicked = pyqtSignal(QMouseEvent)
  ctrlReleased = pyqtSignal(QMouseEvent)
  rightReleased = pyqtSignal(QMouseEvent)
  ctrlRightReleased = pyqtSignal(QMouseEvent)
  theme = None

  @classmethod
  def getTheme(cls):
    if cls.theme is None:
      cls.theme = cOrbTheme_RedMedium()
    return cls.theme
  
  def setIconSize(self, size):
    self.theme.iconSize = size
    return super().setIconSize(size)
  
  #----------------------------------------------------------------------------------------------------------
  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(*args, **kwargs)
    if title: self.setText(title)
    if icon: self.setIcon(getIcon(icon))
    if tooltip: self.setToolTip(tooltip)
    self._current_state = P_STATUS_NORMAL
    self._isHovered = False
    self.setEnabled(enabled)
    self.textRendered = None
    self.iconRendered = None
    self.menu = QMenu(title, self)
    
    ctrlTrigger = QShortcut(QKeySequence(Qt.Key.Key_Control), self)
    ctrlTrigger.activated.connect(lambda : self._setCtrlPressed(True))

    theme = self.__class__.getTheme()

    self.setFont(theme.font)
    QApplication.instance().installEventFilter(self)

    self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.setFixedSize(self.theme.orbSize)
    self.setIconSize(self.theme.iconSize)
    self.setMouseTracking(True)
    self.rightReleased.connect(self.showMenu)
  
  #----------------------------------------------------------------------------------------------------------
  def setIcon(self, a0):
    self.iconRendered = None
    super().setIcon(a0)
  
  #----------------------------------------------------------------------------------------------------------
  def setText(self, a0):
    self.textRendered = None
    super().setText(a0)

  #----------------------------------------------------------------------------------------------------------
  def setMenu(self, menu : QMenu):
    self.menu = menu
    menu.aboutToHide.connect(self.normalizeState)

  #----------------------------------------------------------------------------------------------------------
  def showMenu(self, e : QEvent):
    if len(self.menu.actions())>0:
      self.menu.exec(self.mapToGlobal(e.pos()))
      self.setState(P_STATUS_RCLICK)      
 
  #----------------------------------------------------------------------------------------------------------
  def setEnabled(self, a0):
    if a0:
      self.normalizeState()
    else:
      self.setState(P_STATUS_DISBLD)
    return super().setEnabled(a0)
  
  #-------------------------------------------------------------------------------------------------------------
  def _setCtrlPressed(self, b):
    self._ctrlPressed = b

  #-------------------------------------------------------------------------------------------------------------
  def setChecked(self, a0):
    super().setChecked(a0)
    self.normalizeState()

  #-------------------------------------------------------------------------------------------------------------
  def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = self.theme.bg.get(self._current_state, QPixmap())
    fg = self.theme.fg.get(self._current_state, QPixmap())

    if not bg.isNull(): painter.drawPixmap(self.rect(), bg)

    self.paintIcon(painter)

    if not fg.isNull(): painter.drawPixmap(self.rect(), fg)

    self.paintText(painter)

    painter.end()

  #-------------------------------------------------------------------------------------------------------------
  def paintIcon(self, painter : QPainter):
    if self.icon().isNull(): return
    if not self.iconRendered:
      self.iconRendered = self.icon().pixmap(self.iconSize()).scaled(self.theme.iconSize,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

    # Centers the icon respecting iconSize()
    r = QtCore.QRect(int((self.theme.orbSize.width()  - self.theme.iconSize.width()) / 2.0),
                     int((self.theme.orbSize.height() - self.theme.iconSize.height()) / 2.0),
                          self.theme.iconSize.width(), self.theme.iconSize.height())
    iconEffect = self.theme.iconEffect.get(self._current_state, cEffects.cNone())
    painter.drawPixmap(r, iconEffect.apply(self.iconRendered))
    

  #-------------------------------------------------------------------------------------------------------------
  def paintText(self, painter : QPainter):
    if not self.text(): return
    if not self.textRendered:
      self.textRendered = QPixmap(self.size())
      self.textRendered.fill(Qt.GlobalColor.transparent)
      textPainter = QPainter(self.textRendered)

      text = self.text().replace("&","")
      textPainter.setFont(self.font())
      aFlags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom

      textRect = self.rect().adjusted(5, 0, -5, 0)
      textColour = QColor(255, 255, 255) 
      shadowColour = QColor(0, 0, 0, 200)  # Semi-black
      shadowOffset = QPoint(4, 4)

      outlineColour = QColor(50, 50, 50, 75)  # Semi-black
      textPainter.setPen(outlineColour)
      for dx in range(-2,3):
        for dy in range(-2,3):
          textPainter.drawText(QtCore.QRect(textRect.x()+dx, textRect.y()+dy,
                                        textRect.width(), textRect.height()), aFlags, text)
      
      textPainter.setPen(shadowColour)
      textPainter.drawText(textRect.translated(shadowOffset), aFlags, text)
      textPainter.setPen(textColour)      
      textPainter.drawText(textRect, aFlags, text)
      textPainter.end()
    textEffect = self.theme.textEffect.get(self._current_state, cEffects.cNone())
    painter.drawPixmap(self.rect(), textEffect.apply(self.textRendered))

  #-------------------------------------------------------------------------------------------------------------
  def enterEvent(self, event):
    if not self.isEnabled(): return
    self._isHovered = True
    if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
      self.setState(P_STATUS_COVERD)
    elif self.isChecked():
      self.setState(P_STATUS_CHECKD_HOVERD)
    else:
      self.setState(P_STATUS_HOVERD)
    if self.toolTip():
      QToolTip.showText( self.mapToGlobal(self.rect().bottomLeft()),
                        self.toolTip(), self)
    super().enterEvent(event)
  
  #-------------------------------------------------------------------------------------------------------------
  def mouseMoveEvent(self, a0):
    if self.underMouse():
      if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
        self.setState(P_STATUS_COVERD)
      elif self.isChecked():
        self.setState(P_STATUS_CHECKD_HOVERD)
      else:
        self.setState(P_STATUS_HOVERD)
    return super().mouseMoveEvent(a0)
  
  #-------------------------------------------------------------------------------------------------------------
  def leaveEvent(self, event):
    if not self.isEnabled(): return
    self._isHovered = False
    self.normalizeState()
    super().leaveEvent(event)

  #-------------------------------------------------------------------------------------------------------------
  def mousePressEvent(self, event):
    if not self.isEnabled(): return
    if event.button() == Qt.MouseButton.LeftButton:
      if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        self.setState(P_STATUS_CCLICK)
        self.ctrlClicked.emit(event)
      else:
        self.setState(P_STATUS_LCLICK)
        super().mousePressEvent(event)
    elif event.button() == Qt.MouseButton.RightButton:
      if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        self.setState(P_STATUS_CRLICK)
        self.ctrlRightClicked.emit(event)
      else:
        self.setState(P_STATUS_RCLICK)
        self.rightClicked.emit(event)

  #-------------------------------------------------------------------------------------------------------------
  def mouseReleaseEvent(self, event):
    if not self.isEnabled(): return
    if event.button() == Qt.MouseButton.LeftButton:
      if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        self.ctrlReleased.emit(event)
      else:
        super().mouseReleaseEvent(event)
    elif event.button() == Qt.MouseButton.RightButton:
      if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        self.ctrlRightReleased.emit(event)
      else:
        self.rightReleased.emit(event)
    self.normalizeState()

  #-------------------------------------------------------------------------------------------------------------
  def normalizeState(self):
    # Sets state to hover or normal or checked
    if self.isChecked():
      if self._isHovered:
        self.setState(P_STATUS_CHECKD_HOVERD)
      else:
        self.setState(P_STATUS_CHECKD)
    elif self._isHovered:
      self.setState(P_STATUS_HOVERD)
    else:
      self.setState(P_STATUS_NORMAL)

  #-------------------------------------------------------------------------------------------------------------
  def setState(self, state):
    self._current_state = state
    self.update()  # Trigger repaint

#-------------------------------------------------------------------------------------------------------------
#
#                                              O R B S M A L L
#
#-------------------------------------------------------------------------------------------------------------
class cOrbSmall(cOrb):
  theme = None

  @classmethod
  def getTheme(cls):
    if cls.theme is None:
      cls.theme = cOrbTheme_RedSmall()
    return cls.theme
  
  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(title, icon, enabled, tooltip, *args, **kwargs)


#-------------------------------------------------------------------------------------------------------------
#
#                                              O R B T I N Y
#
#-------------------------------------------------------------------------------------------------------------
class cOrbTiny(cOrb):
  theme = None

  @classmethod
  def getTheme(cls):
    if cls.theme is None:
      cls.theme = cTheme_DialogClose()
    return cls.theme
  
  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(title, icon, enabled, tooltip, *args, **kwargs)

#-------------------------------------------------------------------------------------------------------------
#
#                                              B O X S M A L L
#
#-------------------------------------------------------------------------------------------------------------
class cBox(cOrb):
  theme = None

  @classmethod
  def getTheme(cls):
    if cls.theme is None:
      cls.theme = cTheme_Checkbox()
    return cls.theme
  
  def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(title, icon, enabled, tooltip, *args, **kwargs)


#-------------------------------------------------------------------------------------------------------------
#
#                                              O R B C H E C K
#
#-------------------------------------------------------------------------------------------------------------
class cOrbCheck(QWidget):
  orb : cOrbSmall = None
  label : QLabel  = None

  @classmethod
  def getTheme(cls):
    if cls.orb.theme is None:
      cls.orb.theme = cOrbTheme_RedSmall()
    return cls.orb.theme
  
  def __init__(self, title = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.orb = cOrbSmall("")
    self.label = QLabel(title)
    self.orb.setCheckable(True)
    self.orb.setChecked(True)

    self.setText    = self.label.setText
    self.isChecked  = self.orb.isChecked
    self.stateChanged = self.orb.clicked
    self.clicked = self.orb.clicked
    self.setEnabled(enabled)
    self.setToolTip(tooltip)
    self.setLayout(newHLayout([self.orb, self.label]))

    self.updateStatus()
    self.stateChanged.connect(self.updateStatus)
  
  def updateStatus(self):
    if self.orb.isChecked():
      self.orb.setIcon(getIcon(P_ICON_CHECKMARK))
    else:
      self.orb.setIcon(QIcon())
  
  def setEnabled(self, a0):
    self.orb.setEnabled(a0)
    self.label.setEnabled(a0)
    super().setEnabled(a0)

  def setChecked(self, a0 : bool):
    if a0:
      self.orb.setIcon(getIcon(P_ICON_CHECKMARK))
    else:
      self.orb.setIcon(QIcon())
    self.orb.setChecked(a0)

  # def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
    # super().__init__(title, icon, enabled, tooltip, *args, **kwargs)

#-------------------------------------------------------------------------------------------------------------
#
#                                              C H E C K B O X
#
#-------------------------------------------------------------------------------------------------------------
class cBoxCheck(QWidget):
  box : cBox = None
  label : QLabel  = None
  toggled = pyqtSignal(bool)

  @classmethod
  def getTheme(cls):
    if cls.box.theme is None:
      cls.box.theme = cTheme_Checkbox()
    return cls.box.theme
  
  def __init__(self, title = None, enabled = True, tooltip = "", *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.box = cBox("")
    self.label = QLabel(title)
    self.box.setCheckable(True)
    self.box.setChecked(True)
    # self.box.theme.iconSize = QSize(16,16)
    self.box.setIconSize(QSize(14,14))

    self.setText    = self.label.setText
    self.isChecked  = self.box.isChecked
    self.stateChanged = self.box.clicked
    self.clicked = self.box.clicked
    self.setEnabled(enabled)
    self.setToolTip(tooltip)
    self.setLayout(newHLayout([self.box, self.label]))

    self.updateStatus()
    self.stateChanged.connect(self.updateStatus)
    self.toggled = self.stateChanged
  
  def updateStatus(self):
    if self.box.isChecked():
      self.box.setIcon(getIcon(P_ICON_SMPLCHECK))
    else:
      self.box.setIcon(QIcon())
  
  def setEnabled(self, a0):
    self.label.setEnabled(a0)
    super().setEnabled(a0)
    self.box.setEnabled(a0)

  def setChecked(self, a0 : bool):
    if a0:
      self.box.setIcon(getIcon(P_ICON_SMPLCHECK))
    else:
      self.box.setIcon(QIcon())
    self.box.setChecked(a0)
