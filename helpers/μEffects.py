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
import math
from PyQt6.QtGui import QPixmap, QColor, qGray, QImage, QPainter
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from helpers.μImageFactory import *

P_EFFECT_NONE = 0
P_EFFECT_GREY = 1
P_EFFECT_BLUR = 2
P_EFFECT_TINT = 3
P_EFFECT_DSAT = 4
P_EFFECT_SEPI = 5
P_EFFECT_INVT = 6
P_EFFECT_OPAC = 7
P_EFFECT_BCON = 8
P_EFFECT_DSHD = 9

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   N O N E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cNone():
  def __init__(self, pre=None):
    self.pre = pre
  def apply(self, target):
    if isinstance(target,str):     return getPixmap(target)
    if isinstance(target,QPixmap): return target
    if isinstance(target,QImage):  return target

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   G R E Y S C A L E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cGreyscale(cNone):
  def __init__(self, pre=cNone()):
    self.pre = pre

  def apply(self, target):
    return greyscale(self.pre.apply(target))

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   D E S A T U R A T E 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cDesaturate(cNone):
  def __init__(self, amount, pre=cNone()):
    self.pre = pre
    self.amount = amount

  def apply(self, target):
    return desaturate(self.pre.apply(target), self.amount)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   T I N T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cTint(cNone):
  def __init__(self, tintColour: QColor, strength: float, pre=cNone()):
    self.pre = pre
    self.tintColour = tintColour
    self.strength = strength

  def apply(self, target):
    return tint(self.pre.apply(target), self.tintColour, self.strength)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   I N V E R T
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cInvert(cNone):
  def __init__(self, pre=cNone()):
    self.pre = pre

  def apply(self, target):
    return invert(self.pre.apply(target))

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   B L U R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cBlur(cNone):
  def __init__(self, radius: float, pre=cNone()):
    self.pre = pre
    self.radius = radius

  def apply(self, target):
    return blur(self.pre.apply(target), self.radius)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   O P A C I T Y
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cOpacity(cNone):
  def __init__(self, amount, pre=cNone()):
    self.amount = amount
    self.pre = pre

  def apply(self, target):
    return opacity(self.pre.apply(target), self.amount)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   B R I G H T N E S S   C O N T R A S T 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cBrightContrast(cNone):
  def __init__(self, brightness: float = 0.0, contrast: float = 1.0, pre=cNone()):
    self.pre = pre
    self.brightness = brightness
    self.contrast = contrast

  def apply(self, target):
    return brightContrast(self.pre.apply(target), self.brightness, self.contrast)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  E F F E C T   -   D R O P   S H A D O W
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class cDropShadow(cNone):
  def __init__(self, dx: int = 4, dy: int = 4, radius: float = 4.0,
               color: QColor = None, shadow_opacity: float = 0.6, pre=cNone()):
    self.pre = pre
    self.dx = dx
    self.dy = dy
    self.radius = radius
    self.color = color
    self.shadow_opacity = shadow_opacity

  def apply(self, target):
    return dropShadow(self.pre.apply(target), self.dx, self.dy, self.radius, self.color, self.shadow_opacity)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def greyscale(target):
  return desaturate(target, 1.0)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def desaturate(target, amount: float):
  if isinstance(target, QPixmap):
    return QPixmap.fromImage(desaturate(target.toImage(), amount))
  for x in range(target.width()):
    for y in range(target.height()):
      color = target.pixelColor(x, y)
      gray = qGray(color.red(), color.green(), color.blue())
      r = int(color.red()   * (1 - amount) + gray * amount)
      g = int(color.green() * (1 - amount) + gray * amount)
      b = int(color.blue()  * (1 - amount) + gray * amount)
      target.setPixelColor(x, y, QColor(r, g, b, color.alpha()))
  return target

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def tint(target, tintColour, strength: float):
  if isinstance(target, QPixmap):
    return QPixmap.fromImage(tint(target.toImage(), tintColour, strength))
  if isinstance(tintColour, QColor):
    tintColour = (tintColour.red(), tintColour.green(), tintColour.blue())
  for x in range(target.width()):
    for y in range(target.height()):
      color = target.pixelColor(x, y)
      r = int(color.red()   * (1 - strength) + tintColour[0] * strength)
      g = int(color.green() * (1 - strength) + tintColour[1] * strength)
      b = int(color.blue()  * (1 - strength) + tintColour[2] * strength)
      target.setPixelColor(x, y, QColor(r, g, b, color.alpha()))
  return target

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def invert(target):
  if isinstance(target, QPixmap):
    return QPixmap.fromImage(invert(target.toImage()))
  target.invertPixels(QImage.InvertMode.InvertRgb)
  return target

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def opacity(target, amount: float):
  if isinstance(target, QPixmap):
    return QPixmap.fromImage(opacity(target.toImage(), amount))
  for x in range(target.width()):
    for y in range(target.height()):
      color = target.pixelColor(x, y)
      color.setAlpha(int(color.alpha() * amount))
      target.setPixelColor(x, y, color)
  return target

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def blur(target, radius: float):
  as_image = isinstance(target, QImage)
  pix = QPixmap.fromImage(target) if as_image else target

  scene = QGraphicsScene()
  item = QGraphicsPixmapItem(pix)
  effect = QGraphicsBlurEffect()
  effect.setBlurRadius(radius)
  item.setGraphicsEffect(effect)
  scene.addItem(item)

  result = QImage(pix.size(), QImage.Format.Format_ARGB32)
  result.fill(Qt.GlobalColor.transparent)
  painter = QPainter(result)
  scene.render(painter, source=QRectF(0, 0, pix.width(), pix.height()))
  painter.end()

  return result if as_image else QPixmap.fromImage(result)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def brightContrast(target, brightness: float, contrast: float):
  if isinstance(target, QPixmap):
    return QPixmap.fromImage(brightContrast(target.toImage(), brightness, contrast))
  b = int(brightness * 255)
  for x in range(target.width()):
    for y in range(target.height()):
      color = target.pixelColor(x, y)
      r  = max(0, min(255, int((color.red()   - 128) * contrast + 128 + b)))
      g  = max(0, min(255, int((color.green() - 128) * contrast + 128 + b)))
      bl = max(0, min(255, int((color.blue()  - 128) * contrast + 128 + b)))
      target.setPixelColor(x, y, QColor(r, g, bl, color.alpha()))
  return target

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def dropShadow(target, dx: int = 3, dy: int = 3, radius: float = 3.0, color: QColor = None, opacity: float = 0.6):
  if isinstance(target, QPixmap):
    return QPixmap.fromImage(dropShadow(target.toImage(), dx, dy, radius, color, opacity))
  if color is None:
    color = QColor(0, 0, 0)

  target = target.convertToFormat(QImage.Format.Format_ARGB32)
  w, h = target.width(), target.height()
  sr, sg, sb = color.red(), color.green(), color.blue()

  # Fill shadow colour, mask by target alpha via DestinationIn
  shadow_pix = QPixmap(w, h)
  shadow_pix.fill(QColor(sr, sg, sb, int(255 * opacity)))
  mask_painter = QPainter(shadow_pix)
  mask_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
  mask_painter.drawImage(0, 0, target)
  mask_painter.end()

  shadow = blur(shadow_pix.toImage(), radius)

  result = QImage(w, h, QImage.Format.Format_ARGB32)
  result.fill(Qt.GlobalColor.transparent)
  painter = QPainter(result)
  painter.drawImage(dx, dy, shadow)
  painter.drawImage(0, 0, target)
  painter.end()
  return result
