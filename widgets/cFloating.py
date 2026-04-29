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
from PyQt6.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QPainter, QFont, QColor, QPixmap
from PyQt6.QtCore import QSettings, QRect, QSize, Qt
from helpers.util import *

# -----------------------------------------------------------------------------
class cFloatingTitleBar(QWidget):

  _BAR_H = 24

  def __init__(self, title: str, parent=None):
    super().__init__(parent)
    from widgets.cOrb import cOrbTiny

    self._font  = QFont("Linux Libertine Capitals", 12, QFont.Weight.Normal, False)
    self.setTitle(title)

    src_left   = getPixmap(P_MUDDO_DIR + "/images/ui_elements/title_grey_left.png")
    src_middle = getPixmap(P_MUDDO_DIR + "/images/ui_elements/title_grey_middle.png")
    src_right  = getPixmap(P_MUDDO_DIR + "/images/ui_elements/title_grey_right.png")

    h = self._BAR_H

    # Scale left/right to bar height, keep aspect ratio → width adjusts
    self._pix_left  = src_left.scaledToHeight(h,  Qt.TransformationMode.SmoothTransformation)
    self._pix_right = src_right.scaledToHeight(h, Qt.TransformationMode.SmoothTransformation)
    # Middle is stored at native resolution; we stretch it in paintEvent
    self._pix_middle_src = src_middle

    self.btnClose = cOrbTiny(icon=P_ICON_SMPLX)
    self.btnClose.setFixedSize(h, h)

    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addStretch()
    layout.addWidget(self.btnClose)

    self.setFixedHeight(h)
    self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

  def setTitle(self, title: str):
    self._title = title.replace("&", "").replace("\n", " ").replace("\r", "").lower()
    self.update()

  def paintEvent(self, event):
    painter = QPainter(self)
    w, h = self.width(), self.height()
    lw  = self._pix_left.width()
    rw  = self._pix_right.width()
    bw  = self.btnClose.width()

    # left cap
    painter.drawPixmap(0, 0, self._pix_left)

    # right cap (sits immediately left of the close button)
    painter.drawPixmap(w - rw, 0, self._pix_right)

    # middle — stretched to fill the space between caps and button
    mid_w = w - lw - rw
    if mid_w > 0:
      mid_pix = self._pix_middle_src.scaled(
        mid_w, h,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
      )
      painter.drawPixmap(lw, 0, mid_pix)

      painter.setFont(self._font)
      painter.setPen(QColor(255, 255, 255))
      painter.drawText(QRect(lw, 0, mid_w, h), Qt.AlignmentFlag.AlignCenter, self._title)

    painter.end()


# -----------------------------------------------------------------------------
class cFloating(QDockWidget):
  widgetID = "floatingWidget"
  _state = QSettings(P_DEFAULT_CONF)

  def __init__(self, title="", parent=None):
    super().__init__(title, parent)
    self.setObjectName(self.widgetID)
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    self.setStyleSheet("QDockWidget { border: none; }")

    self._titleBar = cFloatingTitleBar(title, self)
    self._titleBar.btnClose.clicked.connect(self.hide)
    self.setTitleBarWidget(self._titleBar)

  def setWindowTitle(self, title: str):
    super().setWindowTitle(title)
    self._titleBar.setTitle(title)

  def setLayout(self, layout):
    content = QWidget()
    content.setObjectName("floatingContent")
    content.setStyleSheet("QWidget#floatingContent { background: rgba(27, 30, 32, 240); border: none; }")
    content.setLayout(layout)
    self.setWidget(content)

  def initialize(self):
    pass
