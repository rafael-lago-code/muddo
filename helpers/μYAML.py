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
import os
import yaml


def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

class _BlockDumper(yaml.Dumper):
    pass

_BlockDumper.add_representer(str, _str_representer)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖ Y A M L 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μYAML:

  def __init__(self, path: str):
    self.path = path
    self.raw  = {}
    if os.path.exists(path):
      with open(path, 'r', encoding='utf-8') as f:
        self.raw = yaml.safe_load(f) or {}

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def save(self, block: bool = False):
    μYAML.dump(self.raw, self.path, block=block)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def dump(data, path: str, block: bool = False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dumper = _BlockDumper if block else yaml.Dumper
    with open(path, 'w', encoding='utf-8') as f:
      yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, Dumper=dumper)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def get(self, path: str, default=None):
    return self._get_recursive(self.raw, path.split('/'), default)

  @staticmethod
  def _get_recursive(d, keys, default):
    if not isinstance(d, dict) or keys[0] not in d:
      return default
    return d[keys[0]] if len(keys) == 1 else μYAML._get_recursive(d[keys[0]], keys[1:], default)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def parseText(text):
    return yaml.safe_load(text) or {}

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def set(self, path: str, value):
    self._set_recursive(self.raw, path.split('/'), value)

  @staticmethod
  def _set_recursive(d, keys, value):
    if len(keys) == 1:
      d[keys[0]] = value
      return
    if keys[0] not in d or not isinstance(d[keys[0]], dict):
      d[keys[0]] = {}
    μYAML._set_recursive(d[keys[0]], keys[1:], value)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def lookup(self, field: str, value) -> str | None:
    for key, entry in self.raw.items():
      if isinstance(entry, dict) and entry.get(field) == value:
        return str(key)
    return None
