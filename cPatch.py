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
#    This software is heavily based on PyLotRO (credits to AJackson
#    <ajackson@bcs.org.uk>), which in turn is based on a script by SNy
#    (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from cTab import cTab
import subprocess
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMainWindow import cMainWindow
   from cWorlds import cWorld

class cPatch(cTab):

  def __init__(self, main : cMainWindow):
    super().__init__("Patch")
    self.patchClient = "patchclient.dll"
    self.btnPatch = QPushButton("Patch Now")
    self.main = main
    self.console = main.console
    
    v = QVBoxLayout()
    v.addWidget(QLabel("TODO"))
    v.addWidget(self.btnPatch)
    self.btnPatch.clicked.connect(self.patch)
    
    self.setLayout(v)
  
  #----------------------------------------------------------------------------------------------------------
  def patch(self):
    
    cmd  = f"cd {self.main.settings.gameDir.text()}; "
    cmd += f"\"{self.main.settings.launcherBinary.text()}\" run "
    cmd += f"\"C:/windows/system32/rundll32.exe {self.patchClient},Patch "
    cmd += f"{self.main.credentials.serverInfo.patchServer} "
    cmd += f"--language {self.main.settings.languageList.currentText()} "
    cmd += f"--productcode {self.main.credentials.serverInfo.patchProductCode} --filesonly "
    if self.main.settings.useHighRes.isChecked(): cmd += " --highres "
    cmd += "\""
    
    self.console.info(cmd)
    out = subprocess.check_output([cmd], shell=True)

  #----------------------------------------------------------------------------------------------------------
  def readOutput(self):
    pass
		# line = QByteArray2str(self.process.readAllStandardOutput())
		# self.uiLog.txtLog.append(line)
		# self.progressMonitor.parseOutput(line)

  #----------------------------------------------------------------------------------------------------------
  def readErrors(self):
    pass
		# self.uiLog.txtLog.append(QByteArray2str(self.process.readAllStandardError()))
    


