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
from __future__ import annotations
import builtins

class _autoList:
  def __init__(self, parent, key):
    self._d, self._k = parent, key
  def append(self, value):
    lst = dict.get(self._d, self._k)
    if lst is None:
      lst = []
      dict.__setitem__(self._d, self._k, lst)
    lst.append(value)
  def __bool__(self):  return False
  def __iter__(self):  return iter([])
  def __len__(self):   return 0
  def __repr__(self):  return 'None'


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  D I C T I O N A R Y
#
#     A non-panic version of the dictionary. μDict[key] returns None instead fo BREAKING YOUR APP if it doesn't 
#     have the key and and μDict[key].append creates a list if the key does not exist (if it exists but is not a 
#     a list, it breaks, so be consistent)
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μDict(dict):

  def __getitem__(self, key):
    v = self.get(key, None)
    if v is None: return _autoList(self, key)
    return v

  def str(self, key, default=None) -> builtins.str | None:
    v = self.get(key)
    return builtins.str(v) if v is not None else default

  def int(self, key, default=None) -> builtins.int | None:
    v = self.get(key)
    try:    return builtins.int(v) if v is not None else default
    except: return default

  def float(self, key, default=None) -> builtins.float | None:
    v = self.get(key)
    try:    return builtins.float(v) if v is not None else default
    except: return default

  def bool(self, key, default=None) -> builtins.bool | None:
    v = self.get(key)
    if v is None: return default
    if isinstance(v, builtins.bool): return v
    if isinstance(v, builtins.str):  return v.lower() not in ('false', '0', 'no', '')
    return builtins.bool(v)
