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
from PyQt6.QtCore import pyqtSignal
from cWidgets.util import *
from datetime import datetime
import sys

# -------------------------------------------------------------------------------------------------------------
class cConsole(QTextEdit):
  converter = None
  sigInfo  = pyqtSignal(str)
  sigDebug = pyqtSignal(str)
  sigError = pyqtSignal(str)

  def __init__(self, filename : str):
    super().__init__()
    self.setReadOnly(True)
    self.setAcceptRichText(True)
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
    self.converter = QTextEdit()

    self.sigInfo.connect(self.printMessage)
    self.sigDebug.connect(self.debugMessage)
    self.sigError.connect(self.errorMessage)

    # self.setStyleSheet("""
    #     * {
    #         selection-background-color: #4f4f4f; /* light gray */
    #         selection-color: #ff6c6e;
    #     }
    #     QMenu::item:selected {
    #         background: #4f4f4f;
    #         color: #ff6c6e;
    #     }
    #     QLineEdit, QTextEdit, QPlainTextEdit, QAbstractItemView {
    #         selection-background-color: #4f4f4f;
    #         selection-color: #ff6c6e;
    #     }
    # """)

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
    self.append(message)
    sbar = self.verticalScrollBar()
    sbar.setValue(sbar.maximum())
    self.converter.setText(message)
    self.logFile.writelines(self.converter.toPlainText()+"\n")
    self.logFile.flush()
    self.update()

  #------------------------------------------------------------------------------------
  def errorMessage(self, message:str, e : Exception = None):
    message = C_RED+self.prefixStr()+"</font>"+message
    if e: message += '<br>'+str(e)
    self.append(message)
    sbar = self.verticalScrollBar()
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
    self.print(f"Closing log file \"{self.logFileName}\"...")
    self.logFile.close()
    return super().close()
