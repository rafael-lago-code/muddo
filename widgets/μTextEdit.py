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

from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import pyqtSignal, QEvent, Qt, QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  F O N T   C O N S O L E
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μFontMono(QFont):

  def __init__(self, size : int = 10, weight: int = QFont.Weight.Normal):
    super().__init__()
    self.setFamily("Consolas, Courier New, DejaVu Sans Mono, monospace")
    self.setStyleHint(QFont.StyleHint.Monospace)      # Important fallback
    self.setFixedPitch(True)                          # Forces fixed width
    self.setPointSize(size)
    self.setWeight(weight)

  # def createMonospaceFont(size: int = 12, weight: int = QFont.Weight.Normal) -> QFont:
  #     font = QFont()
      
  #     # Try common monospace fonts in order of preference
  #     font.setFamily("Consolas, Courier New, DejaVu Sans Mono, monospace")
      
  #     font.setStyleHint(QFont.StyleHint.Monospace)      # Important fallback
  #     font.setFixedPitch(True)                          # Forces fixed width
  #     font.setPointSize(size)
  #     font.setWeight(weight)
      
  #     return font

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  J S O N   H I G H L I G H T E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class JsonHighlighter(QSyntaxHighlighter):

  def __init__(self, parent=None):
    super().__init__(parent)

    self.formats = {}

    # Key format (blue)
    keyFormat = QTextCharFormat()
    keyFormat.setForeground(QColor("#569cd6"))
    keyFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["key"] = keyFormat

    # String format (green)
    stringFormat = QTextCharFormat()
    stringFormat.setForeground(QColor("#ce9178"))
    self.formats["string"] = stringFormat

    # Number format (orange)
    numberFormat = QTextCharFormat()
    numberFormat.setForeground(QColor("#b5cea8"))
    self.formats["number"] = numberFormat

    # Boolean & null (purple)
    boolFormat = QTextCharFormat()
    boolFormat.setForeground(QColor("#c586c0"))
    self.formats["bool"] = boolFormat

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _applyRegex(self, pattern: str, text: str, fmt, length_adjust: int = 0):
    it = QRegularExpression(pattern).globalMatch(text)
    while it.hasNext():
      m = it.next()
      self.setFormat(m.capturedStart(), m.capturedLength() + length_adjust, fmt)

  def highlightBlock(self, text: str):
    self._applyRegex(r'"([^"\\]|\\.)*"',       text, self.formats["string"])
    self._applyRegex(r'"([^"\\]|\\.)*"\s*:',   text, self.formats["key"],    length_adjust=-1)
    self._applyRegex(r'\b-?\d+\.?\d*\b',       text, self.formats["number"])
    self._applyRegex(r'\b(true|false|null)\b',  text, self.formats["bool"])

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  T E X T   E D I T
#
#   QTextEdit with an editingFinished signal, emitted on focus out.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μTextEdit(QTextEdit):
  editingFinished = pyqtSignal()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, parent=None, syntax: str = 'none'):
    super().__init__(parent)
    self.syntax = syntax.lower()
    self.setSyntax(self.syntax)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def focusOutEvent(self, event: QEvent):
    super().focusOutEvent(event)
    self.editingFinished.emit()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setSyntax(self, syntax: str):
    self.syntax = syntax.lower()
    # if self.highlighter: self.highlighter.setDocument(None)
    if self.syntax == "json": self.highlighter = JsonHighlighter(self.document())
    else: self.highlighter = None
