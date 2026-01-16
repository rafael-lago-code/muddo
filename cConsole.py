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
from PyQt6.QtWidgets import QTextEdit, QWidget
from PyQt6.QtCore import pyqtSignal, Qt
from cWidgets.util import *
from cWidgets.cToggler import cToggler
from datetime import datetime
import sys

# -------------------------------------------------------------------------------------------------------------
class cConsole(cToggler):
  converter = None
  sigInfo  = pyqtSignal(str)
  sigDebug = pyqtSignal(str)
  sigError = pyqtSignal(str)

  def __init__(self, filename : str):
    self.widgetID = "console"
    super().__init__("Log", P_ICON_CONSOLE)
    self.isDebugging = True
    self.logFileName = filename
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
    self.setLayout(newHLayout([self.content]))

    self.sigInfo.connect(self.printMessage)
    self.sigDebug.connect(self.debugMessage)
    self.sigError.connect(self.errorMessage)

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
    message = C_RED+self.prefixStr()+"</font>"+message
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
