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
from PyQt6.QtWidgets import QLabel, QTextEdit, QComboBox
from PyQt6.QtCore import QRunnable, pyqtSignal, QThreadPool
from widgets.cToggler import cToggler
from widgets.cOrb import cOrb, cOrbSmall
import subprocess
from typing import TYPE_CHECKING
import threading
from datetime import datetime
from helpers.util import *
from helpers.cPrint import cPrint
if TYPE_CHECKING:
   from cMainWindow import cMainWindow

P_TIMESTAMP_FILE=".muddo_patch_timestamp"

class cPatch(cToggler):
  sigPatchInfo = pyqtSignal(str)
  sigPatchDone = pyqtSignal(bool)

  def __init__(self, main : cMainWindow):
    self.widgetID = "patch"
    super().__init__("Patch", P_ICON_DOWNLOAD)
    self.toggler.setToolTip("Patch Client<br><b><i>Last update: NA</i></b>")
    self.main = main
    self.console = main.console
    self.timestamp = QLabel("Last patch: <?>")
    self.toggler.setToolTip("Last patch: <?>")
    self.log = QTextEdit()
    self.log.setVisible(False)
    self.log.setReadOnly(True)
    self.log.setAcceptRichText(True)

    self.btnPatch = cOrbSmall(icon=P_ICON_DOWNLOAD, tooltip="Quick patch.<br>Ctrl+click: calls the original launcher to start the full patch. Use this when the quick patch fails (e.g. the very first patching after installing the game")
    self.comboPatchWhen = QComboBox()
    self.comboPatchWhen.setEnabled(False)
    self.comboPatchWhen.addItem('Never (WIP)')
    self.comboPatchWhen.addItem('Weekly, after maintenance')
    self.comboPatchWhen.addItem('Always')

    self.fileCount = 0
    self.byteCount = 0
    self.readFiles = 0
    self.readBytes = 0
    
    self.setLayout(newVLayout([self.log, newHLayout([self.btnPatch, "__stretch__", "Auto patch:", self.comboPatchWhen, "__stretch__", self.timestamp]), "__stretch__"]))

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    self.btnPatch.clicked.connect(self.patch)
    self.btnPatch.ctrlClicked.connect(self.fullPatch)
    self.sigPatchInfo.connect(self.log.append)
    self.sigPatchDone.connect(self.updateTimestamp)

  #----------------------------------------------------------------------------------------------------------
  def updateTimestamp(self):
    timestampFilename = self.main.profile().launcher.gamePath()+os.sep+P_TIMESTAMP_FILE
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
    self.toggler.setToolTip(f"Patch Client<br><b><i>Last update: {tstamp}</i></b>")
  
  #----------------------------------------------------------------------------------------------------------
  def getLogFilename(self):
    return f"{P_DEFAULT_LOGSDIR}/fullpatcher.txt"
  
  #----------------------------------------------------------------------------------------------------------
  def patch(self):
    self.log.clear()
    self.log.setVisible(True)
    proc = tPatcher(self, self.main)
    QThreadPool.globalInstance().start(proc)

  #----------------------------------------------------------------------------------------------------------
  def fullPatch(self):
    # if self.status == aProcessItem.P_STATUS_RUNNING: return
    t = threading.Thread(target=self.fullLauncherThread, daemon=True)
    t.start()
    cPrint.info(f"Starting {C_SILVER}full launcher</font> for patching...")

  #----------------------------------------------------------------------------------------------------------
  # TODO - add this to process manager 
  def fullLauncherThread(self):
    # self.sigChangeRequest.emit(self.P_STATUS_AUTHENTICATING)

    cmd = (
        f'cd "{self.main.profile().gameDir.text()}" && '
        f'STEAM_ROOT="{self.main.profile().steamRoot.text()}" '
        f'PROTON_LOG=1 '
        f'STEAM_COMPAT_DATA_PATH="{self.main.profile().compatData.text()}" '
        f'STEAM_COMPAT_CLIENT_INSTALL_PATH="{self.main.profile().compatData.text()}" '
        f'"{self.main.profile().protonExec.text()}" run "DNDLauncher.exe"'
    )
    print(cmd)

    logFile = open(self.getLogFilename(), "w")
    proc = subprocess.Popen(
        cmd,
        shell=True,                     # Needed for env var prefix + cd + &&
        stdout=logFile,
        stderr=subprocess.STDOUT,       # Merge stderr → stdout → log
        start_new_session=True,         # New session → survives Python exit
        close_fds=True,
        env=os.environ.copy(),          # Inherit + your vars are in cmd
    )
    if proc:
      # self.sigChangeRequest.emit(self.P_STATUS_RUNNING)
      exitCode = proc.wait()
    else:
      cPrint.info("cPatch.fullLauncherThread.run: Error launching, check logs for details!")
      exitCode = 1

    # this locks until the launcher process ends, and it is intentional!
    # If it does end, then it was closed by the user (or some error...)
    # if exitCode==137:
    #   self.sigChangeRequest.emit(self.P_STATUS_KILLED)
    # elif exitCode in (1,2,126,127):
    #   self.sigChangeRequest.emit(self.P_STATUS_ERROR)
    # else:
    #   self.sigChangeRequest.emit(self.P_STATUS_TERMINATED)


#----------------------------------------------------------------------------------------------------------
# TODO reimplement this using threading
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
      timestampFilename = self.main.profile().gameDir.text()+os.sep+P_TIMESTAMP_FILE
      with open(timestampFilename, 'w') as f:
        f.write(f"{datetime.now().strftime("%Y-%m-%d, at %H:%M:%S")}")
    except Exception as e:
      self.main.console.error(f"Error creating file {timestampFilename} for saving timestamp!", e)
    
    self.patchWidget.sigPatchDone.emit(True)
    

  #----------------------------------------------------------------------------------------------------------
  def runTarget(self, target : str):
    # if usingProton:
    if True:
      protonWine = os.path.dirname(self.main.profile().protonExec.text()) + "/dist/bin/wine"
      evars = {'WINEPREFIX': f"{self.main.profile().compatData.text()}/pfx"}
      cmd  = f"\"{protonWine}\" rundll32.exe patchclient.dll,Patch "
      cmd += f"{self.main.credentials.serverInfo.patchServer} "
      cmd += f"--language {self.main.profile().languageCombo.currentText()} "
      cmd += f"--productcode {self.main.credentials.serverInfo.patchProductCode} "
      if self.main.profile().useHighRes.isChecked(): cmd += " --highres "

    out = subprocess.Popen([f"{cmd} {target}"], cwd=self.main.profile().gameDir.text(), env=evars, \
                        stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
    while True:
      line = out.stdout.readline().decode()
      if not line:
        break
      elif line.startswith("Decrypting"):
        pass
      else:
        self.patchWidget.sigPatchInfo.emit(line.strip())