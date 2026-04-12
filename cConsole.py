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
from PyQt6.QtWidgets import QTextEdit, QTabWidget
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtCore import QFileSystemWatcher
from helpers.util import *
from widgets.cToggler import cToggler
from datetime import datetime
import sys

# -------------------------------------------------------------------------------------------------------------
class cConsole(cToggler):
  converter = None
  sigInfo  = pyqtSignal(str)
  sigDebug = pyqtSignal(str)
  sigError = pyqtSignal(str)
  sigWarning = pyqtSignal(str)

  def __init__(self, filename : str):
    self.widgetID = "console"
    super().__init__("Log", P_ICON_CONSOLE)
    self.isDebugging = True
    self.logFileName = filename
    self.tabWidget = QTabWidget()
    self.tabWidget.setTabPosition(QTabWidget.TabPosition.East)
    self.tabWidget.setTabsClosable(True)
    self.tabWidget.setTabBarAutoHide(True)
    self.tabs = {}
    
    try:
      os.mkdir(os.path.dirname(filename))
    except: pass
    if os.path.exists(filename):
      try:
        os.rename(filename, filename+".old")
      except: pass
    try:
      self.logFile = open(filename, "w")
    except Exception as e:
      print(f"[FATAL ERROR] Could not open log file {filename} for writing. Aborting...")
      sys.exit(-1)

    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window | 
                        Qt.WindowType.WindowStaysOnTopHint)
    self.setWindowTitle("μDDO Console")

    self.converter = QTextEdit()
    self.content = QTextEdit()
    self.content.setReadOnly(True)
    self.content.setAcceptRichText(True)
    self.tabWidget.addTab(self.content, "Log")

    self.setLayout(newHLayout([self.tabWidget]))

    self.sigInfo.connect(self.printMessage)
    self.sigDebug.connect(self.debugMessage)
    self.sigError.connect(self.errorMessage)
    self.sigWarning.connect(self.warningMessage)
    self.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)

  def prefixStr(self):
    return f'[ {datetime.now().strftime("%Y/%m/%d %H:%M:%S")} ] '
  
  #------------------------------------------------------------------------------------
  def setDebug(self, val):
    self.isDebugging = val

  #------------------------------------------------------------------------------------
  def info(self, message:str):
    self.sigInfo.emit(message)

  #------------------------------------------------------------------------------------
  def error(self, message:str, e:Exception = ""):
    if e:
      self.sigError.emit(message + "<br>  ===> "+str(e))
    else:
      self.sigError.emit(message)
  
  #------------------------------------------------------------------------------------
  def warning(self, message:str, e:Exception = ""):
    if e:
      self.sigWarning.emit(message + "<br>  ===> "+str(e))
    else:
      self.sigWarning.emit(message)

  #------------------------------------------------------------------------------------
  def abort(self, message:str, e:Exception = ""):
    if e:
      self.sigError.emit(message + "<br>  ===> "+str(e))
    else:
      self.sigError.emit(message)
    sys.exit()

  #------------------------------------------------------------------------------------
  def debug(self, message:str):
    self.sigDebug.emit(message)

  #------------------------------------------------------------------------------------
  def getTabIndex(self, name: str) -> int:
    for i in range(self.tabWidget.count()):
        if self.tabWidget.tabText(i) == name:
            return i
    return None
  
  #------------------------------------------------------------------------------------
  def addTab(self, logger) -> bool:
    if self.getTabIndex(logger.name) is None:
      self.tabWidget.addTab(logger, logger.name)
      return True
    else:
      return False
    
  #------------------------------------------------------------------------------------
  def removeTab(self, logger):
    i = self.getTabIndex(logger.name)
    if i is None: 
      self.warning(f"Cannot remove  tab \"{logger.name}\", not found!")
      return
    self.tabWidget.removeTab(i)

  #------------------------------------------------------------------------------------
  def onTabCloseRequested(self, index: int):
      if self.tabWidget.count()>index:
        if self.tabWidget.tabText(index) == "Log":
          self.warning("Main \"Log\" tab cannot be closed by design. Doing nothing.")
          return
        else:
          # cLog's deleteLater method also removes it from the tabWidget
          # I didn't find a cleaner way of doing this, because cLog also has to be
          # able to delete itself via context menu and other toggle button
          self.tabWidget.widget(index).deleteLater()

  #------------------------------------------------------------------------------------
  def printMessage(self, message : str, endLine = True):
    message = C_SILVER+self.prefixStr()+"</font>"+message
    self.content.append(message)
    sbar = self.content.verticalScrollBar()
    sbar.setValue(sbar.maximum())
    self.converter.setText(message)
    self.logFile.writelines(self.converter.toPlainText()+"\n")
    self.logFile.flush()
    self.update()

  #------------------------------------------------------------------------------------
  def errorMessage(self, message:str, e : Exception = None):
    message = C_RED+self.prefixStr()+"</font> 🛑 "+message
    if e: message += '<br>'+str(e)
    self.content.append(message)
    sbar = self.content.verticalScrollBar()
    sbar.setValue(sbar.maximum())
    self.converter.setText(message)
    self.logFile.writelines(self.converter.toPlainText()+"\n")
    self.logFile.flush()
    self.update()

  #------------------------------------------------------------------------------------
  def warningMessage(self, message:str, e : Exception = None):
    message = C_RED+self.prefixStr()+"</font> ⚠ "+message
    if e: message += '<br>'+str(e)
    self.content.append(message)
    sbar = self.content.verticalScrollBar()
    sbar.setValue(sbar.maximum())
    self.converter.setText(message)
    self.logFile.writelines(self.converter.toPlainText()+"\n")
    self.logFile.flush()
    self.update()

  #------------------------------------------------------------------------------------
  def debugMessage(self, message : str):
    if not self.isDebugging: return
    self.logFile.writelines(self.prefixStr()+message+"\n")
    self.logFile.flush()

  #------------------------------------------------------------------------------------
  def close(self) -> bool:
    print(f"Closing log file \"{self.logFileName}\"...")
    self.logFile.close()
    return super().close()
  
  # #------------------------------------------------------------------------------------
  # def addTab(self, filePath: str, name : str):
  #   if filePath in self.tabs:
  #     print(f"Tab for {filePath} already exists.")
  #     return

  #   try:
  #     textEdit = QTextEdit()
  #     textEdit.setReadOnly(True)

  #     if os.path.exists(filePath):
  #       with open(filePath, 'r', encoding='utf-8', errors='replace') as f:
  #         textEdit.setPlainText(f.read())

  #     watcher = QFileSystemWatcher()
  #     watcher.addPath(filePath)
  #     watcher.fileChanged.connect(lambda path: self.updateTabContent(name))

  #     self.tabWidget.addTab(textEdit, name)

  #     self.tabs[name] = {
  #       'filePath': filePath,
  #       'textEdit': textEdit,
  #       'lastPos': 0,
  #       'watcher': watcher
  #     }

  #     self.info(f"Following log for {C_SILVER}{name}</font>...")
  #     self.updateTabContent(name)

  #   except Exception as e:
  #     self.error(f"Failed to add tail tab for {filePath}", e)

  # #------------------------------------------------------------------------------------ 
  # def updateTabContent(self, name: str):
  #     if name not in self.tabs:
  #       return

  #     path     = self.tabs[name]['filePath']
  #     textEdit : QTextEdit = self.tabs[name]['textEdit']

  #     try:
  #       with open(path, 'r', encoding='utf-8', errors='replace') as f:
  #         f.seek(self.tabs[name]['lastPos'])
  #         newContent = f.read()
  #         textEdit.append(newContent)
  #         self.tabs[name]['lastPos'] = f.tell()

  #       textEdit.verticalScrollBar().setValue(textEdit.verticalScrollBar().maximum())

  #     except Exception as e:
  #       self.error(f"Error reading updated file {path}", e)
