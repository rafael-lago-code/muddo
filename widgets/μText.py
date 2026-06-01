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

from PyQt6.QtWidgets import QTextEdit, QLabel, QGraphicsDropShadowEffect
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


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  F O N T   D I S P L A Y 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μFontDisplay(QFont):

  def __init__(self, size : int = 12, weight: int = QFont.Weight.Bold):
    super().__init__()
    self.setFamily("Linux Libertine Capitals")
    self.setPointSize(size)
    self.setWeight(weight)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  D I S P L A Y   L A B E L
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μDisplayLabel(QLabel):

  def __init__(self, text: str = "", size: int = 12, weight: int = QFont.Weight.Bold, parent=None):
    super().__init__(text, parent)
    self.setFont(μFontDisplay(size, weight))
    shadow = QGraphicsDropShadowEffect(self)
    shadow.setBlurRadius(6)
    shadow.setOffset(2, 2)
    shadow.setColor(QColor(0, 0, 0, 160))
    self.setGraphicsEffect(shadow)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  J S O N   H I G H L I G H T E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class jsonHighlighter(QSyntaxHighlighter):

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
#   ❖  Y A M L   H I G H L I G H T E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class yamlHighlighter(QSyntaxHighlighter):

  def __init__(self, parent=None):
    super().__init__(parent)

    self.formats = {}

    keyFormat = QTextCharFormat()
    keyFormat.setForeground(QColor("#569cd6"))
    keyFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["key"] = keyFormat

    stringFormat = QTextCharFormat()
    stringFormat.setForeground(QColor("#ce9178"))
    self.formats["string"] = stringFormat

    numberFormat = QTextCharFormat()
    numberFormat.setForeground(QColor("#b5cea8"))
    self.formats["number"] = numberFormat

    boolFormat = QTextCharFormat()
    boolFormat.setForeground(QColor("#c586c0"))
    self.formats["bool"] = boolFormat

    commentFormat = QTextCharFormat()
    commentFormat.setForeground(QColor("#6a9955"))
    commentFormat.setFontItalic(True)
    self.formats["comment"] = commentFormat

    anchorFormat = QTextCharFormat()
    anchorFormat.setForeground(QColor("#dcdcaa"))
    self.formats["anchor"] = anchorFormat

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _applyRegex(self, pattern: str, text: str, fmt, group: int = 0):
    it = QRegularExpression(pattern).globalMatch(text)
    while it.hasNext():
      m = it.next()
      start  = m.capturedStart(group)
      length = m.capturedLength(group)
      self.setFormat(start, length, fmt)

  def highlightBlock(self, text: str):
    self._applyRegex(r'(?m)^\s*([\w\-\.]+)\s*:(?:\s|$)', text, self.formats["key"],    group=1)
    self._applyRegex(r'"(?:[^"\\]|\\.)*"',                text, self.formats["string"])
    self._applyRegex(r"'[^']*'",                          text, self.formats["string"])
    self._applyRegex(r'\b-?\d+(?:\.\d+)?\b',              text, self.formats["number"])
    self._applyRegex(r'\b(true|false|null|yes|no|~)\b',   text, self.formats["bool"])
    self._applyRegex(r'[&\*]\w+',                         text, self.formats["anchor"])
    self._applyRegex(r'#.*$',                             text, self.formats["comment"])


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  F I L T E R   H I G H L I G H T E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class filterHighlighter(QSyntaxHighlighter):

  def __init__(self, parent=None):
    super().__init__(parent)

    self.formats = {}

    fieldFormat = QTextCharFormat()
    fieldFormat.setForeground(QColor("#569cd6"))
    fieldFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["field"] = fieldFormat

    logicFormat = QTextCharFormat()
    logicFormat.setForeground(QColor("#c586c0"))
    logicFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["logic"] = logicFormat

    cmpFormat = QTextCharFormat()
    cmpFormat.setForeground(QColor("#d4d4d4"))
    self.formats["cmp"] = cmpFormat

    funcFormat = QTextCharFormat()
    funcFormat.setForeground(QColor("#dcdcaa"))
    self.formats["func"] = funcFormat

    stringFormat = QTextCharFormat()
    stringFormat.setForeground(QColor("#ce9178"))
    self.formats["string"] = stringFormat

    numberFormat = QTextCharFormat()
    numberFormat.setForeground(QColor("#b5cea8"))
    self.formats["number"] = numberFormat

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _applyRegex(self, pattern: str, text: str, fmt, group: int = 0):
    it = QRegularExpression(pattern, QRegularExpression.PatternOption.CaseInsensitiveOption).globalMatch(text)
    while it.hasNext():
      m = it.next()
      self.setFormat(m.capturedStart(group), m.capturedLength(group), fmt)

  def highlightBlock(self, text: str):
    self._applyRegex(r'\b(name|description|owner|type|equipsto|augments|qualifier|nAugs)\b', text, self.formats["field"])
    self._applyRegex(r'\b(isEquipped|isBound|isLocked)\b',                                   text, self.formats["field"])
    self._applyRegex(r'\b(and|or|not)\b',                                                    text, self.formats["logic"])
    self._applyRegex(r'(==|!=|<=|>=|<|>)',                                                   text, self.formats["cmp"])
    self._applyRegex(r'\b(len|infile)\b(?=\s*\()',                                           text, self.formats["func"])
    self._applyRegex(r'"[^"]*"',                                                             text, self.formats["string"])
    self._applyRegex(r'\b-?\d+(?:\.\d+)?\b',                                                text, self.formats["number"])


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  M A C R O   H I G H L I G H T E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class macroHighlighter(QSyntaxHighlighter):

  def __init__(self, parent=None):
    super().__init__(parent)

    self.formats = {}

    metaFormat = QTextCharFormat()
    metaFormat.setForeground(QColor("#c586c0"))
    metaFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["meta"] = metaFormat

    shorthandFormat = QTextCharFormat()
    shorthandFormat.setForeground(QColor("#4ec9b0"))
    self.formats["shorthand"] = shorthandFormat

    builtinFormat = QTextCharFormat()
    builtinFormat.setForeground(QColor("#dcdcaa"))
    self.formats["builtin"] = builtinFormat

    colonFormat = QTextCharFormat()
    colonFormat.setForeground(QColor("#d4d4d4"))
    colonFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["colon"] = colonFormat

    semicolonFormat = QTextCharFormat()
    semicolonFormat.setForeground(QColor("#808080"))
    self.formats["semicolon"] = semicolonFormat

    stringFormat = QTextCharFormat()
    stringFormat.setForeground(QColor("#ce9178"))
    self.formats["string"] = stringFormat

    numberFormat = QTextCharFormat()
    numberFormat.setForeground(QColor("#b5cea8"))
    self.formats["number"] = numberFormat

    hpspFormat = QTextCharFormat()
    hpspFormat.setForeground(QColor("#b5cea8"))
    hpspFormat.setFontWeight(QFont.Weight.Bold)
    self.formats["hpsp"] = hpspFormat

    braceFormat = QTextCharFormat()
    braceFormat.setForeground(QColor("#9cdcfe"))
    self.formats["brace"] = braceFormat

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _applyRegex(self, pattern: str, text: str, fmt, group: int = 0):
    it = QRegularExpression(pattern, QRegularExpression.PatternOption.CaseInsensitiveOption).globalMatch(text)
    while it.hasNext():
      m = it.next()
      self.setFormat(m.capturedStart(group), m.capturedLength(group), fmt)

  def highlightBlock(self, text: str):
    self._applyRegex(r'"[^"]*"',                                                                                                          text, self.formats["string"])
    self._applyRegex(r'\b(HP|SP)[<>]=?\d*\.?\d+',                                                                                        text, self.formats["hpsp"])
    self._applyRegex(r'\{[^}]+\}',                                                                                                        text, self.formats["brace"])
    self._applyRegex(r'\b(all|self|focus|any|none|etal)\b',                                                                               text, self.formats["meta"])
    self._applyRegex(r'\bb\d+k\d+\b|\btp[mp]\d+\b',                                                                                      text, self.formats["shorthand"])
    self._applyRegex(r'\b(ordered|strategy|sleep|chat|select|enterPortal|closeExplorerJournal|confirmDialog|debug|lootall|interact|macro)\b(?=\s*[,(]|$)', text, self.formats["builtin"])
    self._applyRegex(r'(?<=\w)\s*(:)(?!\s*/)',                                                                                            text, self.formats["colon"],     group=1)
    self._applyRegex(r';',                                                                                                                text, self.formats["semicolon"])
    self._applyRegex(r'\b-?\d+(?:\.\d+)?\b',                                                                                             text, self.formats["number"])


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
    if   self.syntax == "json":   self.highlighter = jsonHighlighter(self.document())
    elif self.syntax == "yaml":   self.highlighter = yamlHighlighter(self.document())
    elif self.syntax == "filter": self.highlighter = filterHighlighter(self.document())
    elif self.syntax == "macro":  self.highlighter = macroHighlighter(self.document())
    else: self.highlighter = None
