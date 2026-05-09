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
from helpers.μImageFactory import *

# -----------------------------------------------------------------------------
class μCanvas(QWidget):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setObjectName("floatingCanvas")
    self.setAutoFillBackground(False)
    self._bg_colour = QColor(27, 30, 32, 240)
    self._bg_images = {}

  def setBackground(self, images: dict):
    self._bg_colour = None
    self._bg_images = {}
    for key, val in images.items():
      if key == 'colour':
        self._bg_colour = val if isinstance(val, QColor) else QColor(val)
      else:
        self._bg_images[key] = val if isinstance(val, QPixmap) else getPixmap(val)
    self.update()

  def paintEvent(self, event):
    painter = QPainter(self)
    W, H = self.width(), self.height()

    left_w   = max((self._bg_images[k].width()  for k in ('NW', 'W', 'SW') if k in self._bg_images), default=0)
    right_w  = max((self._bg_images[k].width()  for k in ('NE', 'E', 'SE') if k in self._bg_images), default=0)
    top_h    = max((self._bg_images[k].height() for k in ('NW', 'N', 'NE') if k in self._bg_images), default=0)
    bottom_h = max((self._bg_images[k].height() for k in ('SW', 'S', 'SE') if k in self._bg_images), default=0)

    cx = left_w
    cy = top_h
    cw = W - left_w - right_w
    ch = H - top_h - bottom_h

    if self._bg_colour:
      painter.fillRect(0, 0, W, H, self._bg_colour)

    def draw(key, x, y, w, h):
      pix = self._bg_images.get(key)
      if pix and w > 0 and h > 0:
        painter.drawPixmap(QRect(x, y, w, h), pix)

    draw('NW',     0,           0,            left_w,   top_h)
    draw('N',      cx,          0,            cw,       top_h)
    draw('NE',     W - right_w, 0,            right_w,  top_h)
    draw('W',      0,           cy,           left_w,   ch)
    draw('center', cx,          cy,           cw,       ch)
    draw('E',      W - right_w, cy,           right_w,  ch)
    draw('SW',     0,           H - bottom_h, left_w,   bottom_h)
    draw('S',      cx,          H - bottom_h, cw,       bottom_h)
    draw('SE',     W - right_w, H - bottom_h, right_w,  bottom_h)

    painter.end()

# -----------------------------------------------------------------------------
class μBar(QWidget):

  _BAR_H = 24

  def __init__(self, title: str, parent=None):
    super().__init__(parent)
    from widgets.μOrb import cOrbTiny

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
class μFloating(QDockWidget):
  widgetID = "floatingWidget"
  _state = QSettings(P_DEFAULT_CONF)

  def __init__(self, title="", parent=None):
    super().__init__(title, parent)
    self.setObjectName(self.widgetID)
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    self.setStyleSheet("QDockWidget { border: none; }")
    self._pending_bg = None

    self._titleBar = μBar(title, self)
    self._titleBar.btnClose.clicked.connect(self.hide)
    self.setTitleBarWidget(self._titleBar)

  def setWindowTitle(self, title: str):
    super().setWindowTitle(title)
    self._titleBar.setTitle(title)

  def setBackground(self, images: dict):
    self._pending_bg = images
    if isinstance(self.widget(), μCanvas):
      self.widget().setBackground(images)

  def setLayout(self, layout):
    content = μCanvas()
    content.setStyleSheet("QWidget#floatingCanvas { border: none; }")
    content.setLayout(layout)
    self.setWidget(content)
    if self._pending_bg is not None:
      content.setBackground(self._pending_bg)

  def initialize(self):
    pass
