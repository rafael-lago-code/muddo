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
from PyQt6.QtGui import QPainter, QPixmap, QColor, qGray, QImage
from PyQt6.QtWidgets import QWidget, QGraphicsBlurEffect
from PyQt6.QtCore import Qt, QRect
from helpers.util import *

P_EFFECT_NONE = 0
P_EFFECT_GREY = 1
P_EFFECT_BLUR = 2
P_EFFECT_TINT = 3
P_EFFECT_DSAT = 4
P_EFFECT_SEPI = 5
P_EFFECT_INVT = 6
P_EFFECT_OPAC = 7

class cNone():
  def __init__(self, pre=None):
    self.pre = pre
  def apply(self, target):
    if isinstance(target,str):     return getPixmap(target)
    if isinstance(target,QPixmap): return target
    if isinstance(target,QImage):  return target

class cGreyscale(cNone):
  def __init__(self, pre=cNone()):
    self.pre = pre
  
  def apply(self, target):
    target = self.pre.apply(target)
    if isinstance(target,str):     return greyscalePixmap(getPixmap(target))
    if isinstance(target,QPixmap): return greyscalePixmap(target)
    if isinstance(target,QImage):  return greyscaleImage(target)

class cDesaturate(cNone):
  def __init__(self, amount, pre=cNone()):
    self.pre = pre
    self.amount = amount
  
  def apply(self, target):
    target = self.pre.apply(target)
    if isinstance(target,QPixmap): return desaturatePixmap(target, self.amount)
    if isinstance(target,QImage):  return desaturateImage(target, self.amount)

class cTint(cNone):
  def __init__(self, tintColour : QColor, strength : float, pre=cNone()):
    self.pre = pre
    self.tintColour = tintColour
    self.strength = strength
  
  def apply(self, target):
    target = self.pre.apply(target)
    if isinstance(target,QPixmap): return tintPixmap(target, self.tintColour, self.strength)
    if isinstance(target,QImage):  return tintImage(target, self.tintColour, self.strength)

class cInvert(cNone):
  def __init__(self, pre=cNone()):
    self.pre = pre
  
  def apply(self, target):
    target = self.pre.apply(target)
    if isinstance(target,QPixmap): return invertPixmap(target)
    if isinstance(target,QImage):  return invertImage(target)

class cOpacity(cNone):
  def __init__(self, amount, pre = cNone):
    self.amount = amount
    self.pre = pre
  
  def apply(self, target):
    target = self.pre.apply(target)
    if isinstance(target,QPixmap): return opacityPixmap(target, self.amount)
    if isinstance(target,QImage):  return opacityImage(target, self.amount)

def greyscaleImage(image : QImage) -> QImage:
  return desaturateImage(image, 1.0)

def desaturateImage(image : QImage, amount : float) -> QImage:
  for x in range(image.width()):
    for y in range(image.height()):
      color = image.pixelColor(x, y)
      gray = qGray(color.red(), color.green(), color.blue())
      r = int(color.red()   * (1 - amount) + gray * amount)
      g = int(color.green() * (1 - amount) + gray * amount)
      b = int(color.blue()  * (1 - amount) + gray * amount)
      image.setPixelColor(x, y, QColor(r,g,b,color.alpha()))
  return image

def tintImage(image : QImage, tintColour, strength : float) -> QImage:
  if isinstance(tintColour, QColor): tintColour = (tintColour.red(), tintColour.green(), tintColour.blue())
  for x in range(image.width()):
    for y in range(image.height()):
      color = image.pixelColor(x, y)
      r = int(color.red()   * (1 - strength) + tintColour[0] * strength)
      g = int(color.green() * (1 - strength) + tintColour[1] * strength)
      b = int(color.blue()  * (1 - strength) + tintColour[2] * strength)
      image.setPixelColor(x, y, QColor(r,g,b,color.alpha()))
  return image

def invertImage(image : QImage) -> QImage:
  image.invertPixels(QImage.InvertMode.InvertRgb)
  return image

def opacityImage(image : QImage, opacity : float) -> QImage:
  for x in range(image.width()):
    for y in range(image.height()):
      color = image.pixelColor(x, y)
      color.setAlpha(int(color.alpha() * opacity))
      image.setPixelColor(x, y, color)
  return image

def blurImage(image : QImage, radius : float) -> QImage:
  pass
  # temp_widget = QWidget()
  # temp_widget.setFixedSize(image.size())
  
  # blur_effect = QGraphicsBlurEffect()
  # blur_effect.setBlurRadius(radius)
  # temp_widget.setGraphicsEffect(blur_effect)
  
  # result = QPixmap(pixmap.size())
  # result.fill(Qt.GlobalColor.transparent)
  
  # painter = QPainter(result)
  # blur_effect.draw(painter)
  # painter.drawPixmap(QRect(pixmap.size().height(), pixmap.size().width()), pixmap)
  # painter.end()
  
  # return result

def greyscalePixmap(pixmap : QPixmap) -> QPixmap:
  return QPixmap.fromImage(greyscaleImage(pixmap.toImage()))

def desaturatePixmap(pixmap : QPixmap, amount : float) -> QPixmap:
  return QPixmap.fromImage(desaturateImage(pixmap.toImage(), amount))

def tintPixmap(pixmap : QPixmap, tintColour : QColor, strength : float) -> QPixmap:
  return QPixmap.fromImage(tintImage(pixmap.toImage(), tintColour, strength))

def invertPixmap(pixmap : QPixmap) -> QPixmap:
  return QPixmap.fromImage(invertImage(pixmap.toImage()))

def opacityPixmap(pixmap : QPixmap, opacity : float) -> QPixmap:
  return QPixmap.fromImage(opacityImage(pixmap.toImage(), opacity))

def blurPixmap(pixmap : QPixmap, radius : float) -> QPixmap:
  return QPixmap.fromImage(blurImage(pixmap.toImage(), radius))


















