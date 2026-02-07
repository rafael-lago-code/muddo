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
from cWidgets.util import *
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from ..cConsole import cConsole

# -------------------------------------------------------------------------------------------------------------
class cLog(QTextEdit):
  printInfo    = lambda x : print(x)
  printDebug   = lambda x : print(x)
  printWarning = lambda x,e=None : print(x + f"\n{e}" if e else "")
  printError   = lambda x,e=None : print(x + f"\n{e}" if e else "")
  console      = None

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def attachConsole(self, console):
    self.console  : cConsole = console
    self.printInfo = console.info
    self.printError = console.error
    self.printDebug = console.debug
    self.printWarning = console.warning
    self.printInfo("Console attached to cLog")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def deattachConsole(self):
    self.console      = None
    self.printInfo    = lambda x : print(x)
    self.printError   = lambda x : print(x)
    self.printDebug   = lambda x : print(x)
    self.printWarning = lambda x : print(x)

  # -------------------------------------------------------------------------------------------------------------
  def __init__(self, filePath: str, name : str):
    if not os.path.exists(filePath):
      self.printError(f"Error trying to create cLog \"{name}\": {filePath} does not exist!")
      return None
    elif self.console.getTabIndex(name) is not None:
      self.printError(f"Error trying to create cLog \"{name}\": tab with this name already exists!")
      return None

    super().__init__()
    self.name = name
    self.filePath = filePath
    self.setReadOnly(True)
    self.watcher = QFileSystemWatcher()
    self.watcher.addPath(filePath)
    self.lastPos = 0
    if not self.console.addTab(self):
      self.printError(f"Error trying to add tab to cConsole \"{self.name}\": name already exists!")
      self.deleteLater()
      return None

    self.watcher.fileChanged.connect(self.onFileUpdated)
    if self.onFileUpdated():
      self.printInfo(f"Following log for {C_SILVER}{self.name}</font>...")
    
  #------------------------------------------------------------------------------------ 
  def onFileUpdated(self) -> bool:
    try:
      with open(self.filePath, 'r', encoding='utf-8', errors='replace') as f:
        f.seek(self.lastPos)
        newContent = f.read()
        self.append(newContent)
        self.lastPos = f.tell()

      self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    except Exception as e:
      self.printError(f"Error reading updated file {self.filePath}", e)

  #------------------------------------------------------------------------------------ 
  def deleteLater(self):
    self.printInfo(f"Stopped following log for {C_SILVER}{self.name}</font>...")
    self.watcher.removePath(self.filePath)
    self.watcher.deleteLater()
    self.console.removeTab(self)
    self.name = None
    super().deleteLater()
