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
#

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  P R I N T
#                                  
#   This is a static class. Don't instantiate it.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μPrint():
  info    = lambda x : print(x)
  debug   = lambda x : print(x)
  warning = lambda x,e=None : print(x + (f"\n{e}" if e else ""))
  error   = lambda x,e=None : print(x + (f"\n{e}" if e else ""))
  console = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def attachConsole(cls, console):
    cls.console = console
    cls.info    = console.info
    cls.error   = console.error
    cls.debug   = console.debug
    cls.warning = console.warning
    cls.info(f"Console attached to {cls.__name__}")
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def deattachConsole(cls):
    cls.console = None
    cls.info    = lambda x : print(x)
    cls.debug   = lambda x : print(x)
    cls.warning = lambda x,e=None : print(x + (f"\n{e}" if e else ""))
    cls.error   = lambda x,e=None : print(x + (f"\n{e}" if e else ""))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def fillRight(text, length: int, char: str = " ") -> str:
    s = str(text)
    if len(s) >= length: return s[:length]
    return s + char * (length - len(s))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def fillLeft(text, length: int, char: str = " ") -> str:
    s = str(text)
    if len(s) >= length: return s[:length]
    return char * (length - len(s)) + s

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def fillCenter(text, length: int, char: str = " ") -> str:
    s = str(text)
    if len(s) >= length: return s[:length]
    total = length - len(s)
    left  = total // 2
    right = total - left
    return char * left + s + char * right

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def fill(text, length: int, char: str = " ", align : str = "l") -> str:
    if align == "r": return μPrint.fillLeft(text, length, char)
    if align == "l": return μPrint.fillRight(text, length, char)
    if align == "c": return μPrint.fillCenter(text, length, char)