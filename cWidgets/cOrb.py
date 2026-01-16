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
from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal
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

class cOrb(QPushButton):
    ctrlClicked = pyqtSignal()
    rightClicked = pyqtSignal()
    ctrlRightClicked = pyqtSignal()

    def __init__(self, title = None, icon = None, enabled = True, tooltip = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        if title: self.setText(title)
        if icon: self.setIcon(getIcon(icon))
        if tooltip: self.setToolTip(tooltip)
        self._current_state = P_STATUS_NORMAL
        self._is_hovered = False

        self.setEnabled(enabled)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setFixedSize(80,80)
        self.setIconSize(QtCore.QSize(40,40))
        
        # Initialize layer dictionaries
        _bg = getPixmap(P_BG_REDORB)
        _fg = getPixmap(P_FG_REDORB)
        self.bg = {P_STATUS_NORMAL: _bg,
                   P_STATUS_HOVERD: cEffects.tintPixmap(_bg,(200,10,10),1.0),
                   P_STATUS_COVERD: cEffects.invertPixmap(_bg),
                   P_STATUS_LCLICK: cEffects.desaturatePixmap(_bg,0.3),
                   P_STATUS_RCLICK: cEffects.tintPixmap(_bg,(215,120,0),1.0),
                   P_STATUS_CCLICK: cEffects.tintPixmap(_bg,(215,120,0),1.0),
                   P_STATUS_CRLICK: cEffects.invertPixmap(_bg),
                   P_STATUS_DISBLD: cEffects.desaturatePixmap(_bg,1.0),
                   P_STATUS_CHECKD: _bg}
        self.fg = {P_STATUS_NORMAL: _fg,
                   P_STATUS_HOVERD: _fg,
                   P_STATUS_COVERD: _fg,
                   P_STATUS_LCLICK: _fg,
                   P_STATUS_RCLICK: _fg,
                   P_STATUS_CCLICK: _fg,
                   P_STATUS_CRLICK: _fg,
                   P_STATUS_DISBLD: _fg,
                   P_STATUS_CHECKD: QPixmap()}
        self.iconEffects = {P_STATUS_NORMAL: cEffects.cNone(),
                            P_STATUS_HOVERD: cEffects.cNone(),
                            P_STATUS_COVERD: cEffects.cNone(),
                            P_STATUS_LCLICK: cEffects.cNone(),
                            P_STATUS_RCLICK: cEffects.cNone(),
                            P_STATUS_CCLICK: cEffects.cNone(),
                            P_STATUS_CRLICK: cEffects.cNone(),
                            P_STATUS_DISBLD: cEffects.cGreyscale(),
                            P_STATUS_CHECKD: cEffects.cNone()}
        self.setMouseTracking(True)
        
    def setLayers(self, state, bg=None, fg=None):
        if bg:
            self.bg[state] = getPixmap(bg)
        if fg:
            self.fg[state] = getPixmap(fg)

    def setEnabled(self, a0):
        if not a0:
          self._setState("disabled")
        return super().setEnabled(a0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg = self.bg.get(self._current_state, QPixmap())
        fg = self.fg.get(self._current_state, QPixmap())
        ie = self.iconEffects.get(self._current_state, cEffects.cNone())
        
        if not bg.isNull():
            painter.drawPixmap(self.rect(), bg.scaled(
                self.size(), 
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        
        if not self.icon().isNull():
            
            isize = self.iconSize()
            bsize = self.size()
            # Centers the icon respecting iconSize()
            r = QtCore.QRect(int((bsize.width()  - isize.width() )/2.0),
                             int((bsize.height() - isize.height())/2.0),
                             isize.width(), isize.height())
            pmap = self.icon().pixmap(self.iconSize())
            painter.drawPixmap(r, ie.apply(pmap.scaled(isize,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation)))
        
        if not fg.isNull():
            painter.drawPixmap(self.rect(), fg.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        
        if self.text():
            painter.setPen(self.palette().buttonText().color())
            painter.setFont(self.font())
            text_rect = self.rect().adjusted(5, 0, -5, 0)
            # painter.drawText(text_rect,  Qt.AlignmentFlag.AlignCenter , self.text())
            painter.drawText(text_rect,  Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self.text())

        painter.end()
    
    def enterEvent(self, event):
        if not self.isEnabled(): return
        self._is_hovered = True
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
          self._setState(P_STATUS_COVERD)
        else:
          self._setState(P_STATUS_HOVERD)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if not self.isEnabled(): return
        self._is_hovered = False
        self._setState(P_STATUS_NORMAL)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if not self.isEnabled(): return
        if event.button() == Qt.MouseButton.LeftButton:
          if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.ctrlClicked.emit()
            self._setState(P_STATUS_CCLICK)
          else:
            super().mousePressEvent(event)
            self._setState(P_STATUS_LCLICK)
        elif event.button() == Qt.MouseButton.RightButton:
          if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.ctrlRightClicked.emit()
            self._setState(P_STATUS_CRLICK)
          else:
            self.rightClicked.emit()
            self._setState(P_STATUS_RCLICK)
        
    
    def mouseReleaseEvent(self, event):
        if not self.isEnabled(): return
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_hovered:
                self._setState(P_STATUS_HOVERD)
            else:
                self._setState(P_STATUS_NORMAL)
        super().mouseReleaseEvent(event)
    
    def _setState(self, state):
        if state != self._current_state:
            self._current_state = state
            self.update()  # Trigger repaint

# # Usage Example
# if __name__ == "__main__":
#     import sys
#     from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
    
#     app = QApplication(sys.argv)
    
#     window = QWidget()
#     layout = QVBoxLayout(window)
    
#     # Create custom button
#     button = cOrb("Click Me!")
#     button.setFixedSize(200, 80)
    
#     # Define colors/images for each state (simplified example)
#     # In reality, you'd load actual images
#     colors = {
#         P_STATUS_NORMAL: ('#3498db', '#2980b9', '#1c6ea4'),
#         P_STATUS_HOVERD: ('#5dade2', '#3498db', '#2e86c1'),
#         P_STATUS_LCLICK: ('#21618c', '#1b4f72', '#154360'),
#     }
    
#     # Set up layers for each state
#     for state, (bg_color, middle_color, fg_color) in colors.items():
#         button.setLayerImages(state, bg_color, middle_color, fg_color)
    
#     layout.addWidget(button)
#     window.show()
    
#     sys.exit(app.exec())