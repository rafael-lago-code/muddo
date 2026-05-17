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
from PyQt6.QtCore import QFileSystemWatcher
from helpers.util import *
from helpers.μPrint import μPrint

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  L O G 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μLog(QTextEdit):

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, filePath: str, name : str):
    super().__init__()
    if not os.path.exists(filePath):
      μPrint.error(f"Error trying to create cLog \"{name}\": {filePath} does not exist!")
      return None
    elif μPrint.console.getTabIndex(name) is not None:
      μPrint.error(f"Error trying to create cLog \"{name}\": tab with this name already exists!")
      return None

    self.name = name
    self.filePath = filePath
    self.setReadOnly(True)
    self.watcher = QFileSystemWatcher()
    self.watcher.addPath(filePath)
    self.lastPos = 0
    if not μPrint.console.addTab(self):
      μPrint.error(f"Error trying to add tab to cConsole \"{self.name}\": name already exists!")
      self.deleteLater()
      return None

    self.watcher.fileChanged.connect(self.onFileUpdated)
    if self.onFileUpdated():
      μPrint.info(f"Following log for {C_SILVER}{self.name}</font>...")
    
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onFileUpdated(self) -> bool:
    try:
      with open(self.filePath, 'r', encoding='utf-8', errors='replace') as f:
        f.seek(self.lastPos)
        newContent = f.read()
        self.append(newContent)
        self.lastPos = f.tell()

      self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    except Exception as e:
      μPrint.error(f"Error reading updated file {self.filePath}", e)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def deleteLater(self):
    if self.name is None: return
    μPrint.info(f"Stopped following log for {C_SILVER}{self.name}</font>...")
    self.name = None
    try:
      self.watcher.fileChanged.disconnect(self.onFileUpdated)
      self.watcher.removePath(self.filePath)
      self.watcher.deleteLater()
    except RuntimeError:
      pass
    μPrint.console.removeTab(self)
    super().deleteLater()
