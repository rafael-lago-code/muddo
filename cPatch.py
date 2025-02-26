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
#    <ajackson@bcs.org.uk>), which in turn is based on a lotrolauncher 
#    script by SNy (<SNy@bmx-chemnitz.de>)
#
#
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QRunnable, pyqtSignal, QThreadPool
from cTab import cTab
import subprocess
from typing import TYPE_CHECKING
from datetime import datetime
from util import *
if TYPE_CHECKING:
   from cMainWindow import cMainWindow
   from cWorlds import cWorld

P_TIMESTAMP_FILE=".muddo_patch_timestamp"

class cPatch(cTab):
  sigPatchInfo = pyqtSignal(str)
  sigPatchDone = pyqtSignal(bool)

  def __init__(self, main : cMainWindow):
    super().__init__("Patch")
    self.btnPatch = QPushButton(getIcon(P_ICON_DOWNLOAD), "Patch Now")
    self.btnPatch.setIconSize(P_DEFAULT_ICON_SIZE)
    self.btnPatch.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    self.main = main
    self.console = main.console
    self.timestamp = QLabel("Last patch: <?>")
    self.log = QTextEdit()
    self.log.setVisible(False)
    self.log.setReadOnly(True)
    self.log.setAcceptRichText(True)

    self.fileCount = 0
    self.byteCount = 0
    self.readFiles = 0
    self.readBytes = 0
    
    self.btnPatch.clicked.connect(self.patch)
    self.sigPatchInfo.connect(self.log.append)
    self.sigPatchDone.connect(self.updateTimestamp)
    self.main.settings.gameDir.textChanged.connect(self.updateTimestamp)

    if self.main.settings.gameDir.text(): self.updateTimestamp()

    self.setLayout(newVLayout([self.log,\
                               newHLayout([self.timestamp, self.btnPatch])]))
    
  #----------------------------------------------------------------------------------------------------------
  def updateTimestamp(self):
    timestampFilename = self.main.settings.gameDir.text()+os.sep+P_TIMESTAMP_FILE
    if os.path.exists(timestampFilename):
      try:
        with open(timestampFilename, 'r') as f:
          tstamp = f.readline()
      except Exception as e:
        self.main.console.error(f"Error opening file {timestampFilename} for reading timestamp!", e)
        tstamp = "Last update: <?>"
    else:
      tstamp = "Last update: never"
    self.timestamp.setText(f"Last update: {tstamp}")
  
  #----------------------------------------------------------------------------------------------------------
  def patch(self):
    self.log.clear()
    self.log.setVisible(True)
    proc = tPatcher(self, self.main)
    QThreadPool.globalInstance().start(proc)

#----------------------------------------------------------------------------------------------------------
class tPatcher(QRunnable):
  def __init__(self, patchWidget : cPatch, main : cMainWindow):
    super().__init__()
    self.main = main
    self.patchWidget = patchWidget

  #----------------------------------------------------------------------------------------------------------
  def run(self):
    self.patchWidget.sigPatchInfo.emit(f"{C_SILVER}<b>------------------------------------------<br>\
                                       [*] Launching files patcher...<br>------------------------------------------</b></font>")
    self.runTarget("--filesonly")
    self.patchWidget.sigPatchInfo.emit(f"{C_SILVER}<b>------------------------------------------<br>\
                                       [*] Launching data patcher...<br>------------------------------------------</b></font>")
    self.runTarget("--dataonly")
    self.patchWidget.sigPatchInfo.emit(f"{C_SILVER}<b>------------------------------------------<br>\
                                       [*] Patching completed!<br>------------------------------------------</b></font>")

    try:
      timestampFilename = self.main.settings.gameDir.text()+os.sep+P_TIMESTAMP_FILE
      with open(timestampFilename, 'w') as f:
        f.write(f"{datetime.now().strftime("%Y-%m-%d, at %H:%M:%S")}")
    except Exception as e:
      self.main.console.error(f"Error creating file {timestampFilename} for saving timestamp!", e)
    
    self.patchWidget.sigPatchDone.emit(True)
    

  #----------------------------------------------------------------------------------------------------------
  def runTarget(self, target : str):
    # if usingProton:
    if True:
      protonWine = os.path.dirname(self.main.settings.launcherBinary.text()) + "/dist/bin/wine"
      evars = {'WINEPREFIX': f"{self.main.settings.protonPrefix}/pfx"}
      cmd  = f"\"{protonWine}\" rundll32.exe patchclient.dll,Patch "
      cmd += f"{self.main.credentials.serverInfo.patchServer} "
      cmd += f"--language {self.main.settings.languageList.currentText()} "
      cmd += f"--productcode {self.main.credentials.serverInfo.patchProductCode} "
      if self.main.settings.useHighRes.isChecked(): cmd += " --highres "
    
    out = subprocess.Popen([f"{cmd} {target}"], cwd=self.main.settings.gameDir.text(), env=evars, \
                        stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
    while True:
      line = out.stdout.readline().decode()
      if not line:
        break
      elif line.startswith("Decrypting"):
        pass
      else:
        self.patchWidget.sigPatchInfo.emit(line.strip())