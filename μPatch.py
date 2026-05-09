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
import cProfile
from PyQt6.QtWidgets import QLabel, QTextBrowser, QTextEdit, QComboBox
from PyQt6.QtCore import QRunnable, pyqtSignal, QThreadPool
from μSettings import μSettings
from widgets.μToggler import μToggler
from widgets.μOrb import μOrb, μOrbSmall
import subprocess, re
from typing import TYPE_CHECKING
import threading
from datetime import datetime
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
if TYPE_CHECKING:
   from μMainWindow import μMainWindow

P_TIMESTAMP_FILE=".muddo_patch_timestamp"

class μPatch(μToggler):
  widgetID = "Patcher"
  sigPatchInfo = pyqtSignal(str)
  sigPatchDone = pyqtSignal(bool)

  def __init__(self, main : μMainWindow):
    super().__init__("Patch\n🙵 News", P_ICON_SCROLL)
    self.toggler.setToolTip("Patch client and/or browse news<br><b><i>Last update: NA</i></b>")
    self.main = main
    self.console = main.console
    self.timestamp = QLabel("Last patch: <?>")
    # self.toggler.setToolTip("Last patch: <?>")
    self.log = QTextEdit()
    self.log.setVisible(False)
    self.log.setReadOnly(True)
    self.log.setAcceptRichText(True)
    self.news = QTextBrowser()
    self.news.setReadOnly(True)
    self.news.setSizePolicy( QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    self.btnPatch = μOrbSmall(icon=P_ICON_DOWNLOAD, tooltip="Quick patch.<br><b><i>Ctrl+click</i></b>: calls the original launcher to start the full patch. Use this when the quick patch fails (e.g. the very first patching after installing the game")
    self.btnNews  = μOrbSmall(icon='news-subscribe', tooltip="Fetch and show news from DDO launcher")
    self.comboPatchWhen = QComboBox()
    self.comboPatchWhen.setEnabled(False)
    self.comboPatchWhen.addItem('Never (WIP)')
    self.comboPatchWhen.addItem('Weekly, after maintenance')
    self.comboPatchWhen.addItem('Always')

    self.fileCount = 0
    self.byteCount = 0
    self.readFiles = 0
    self.readBytes = 0
    
    self.setLayout(newVLayout([self.log,
                               newHLayout([self.btnPatch, self.btnNews,"__stretch__", "Auto patch:", self.comboPatchWhen, "__stretch__", self.timestamp]),
                               self.news]))

  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    super().initialize()
    self.btnPatch.clicked.connect(self.patch)
    self.btnPatch.ctrlClicked.connect(self.fullPatch)
    self.btnNews.clicked.connect(self.fetchNews)
    self.sigPatchInfo.connect(self.log.append)
    self.sigPatchDone.connect(self.updateTimestamp)

  #----------------------------------------------------------------------------------------------------------
  def fetchNews(self):
    import xml.etree.ElementTree as ET
    import urllib.request
    import html

    # TODO - this is terrible. Some of the data is already in tServerInfo, but trickling the whole thing
    # through the credentials class is a pain. Maybe move the fetching/parsing of news to a separate class?
    # Need to make the whole thing a static class again...
    newsURL=self.main.credentials.serverInfo.newsFeedURL
    if newsURL == "":
      μPrint.error(f"[cPatch] Error fetching news URL from server config file {P_DEFAULT_SERVERCONFIG}!")
      return
    with urllib.request.urlopen(newsURL) as response:
      newsData = response.read().decode('utf-8')
    
    root = ET.fromstring(newsData)
    htmlParts = []
    for item in root.findall('.//item'):            # adjust if the root structure differs
      title = item.find('title')
      if title is not None and title.text:
        htmlParts.append(f"<h2>{html.unescape(title.text)}")

      link = item.find('link')
      if link is not None and link.text:
        htmlParts.append(f" <a href='{html.unescape(link.text)}' style=\"text-decoration: none;\">🔗</a></h2>")   # as you requested

      desc = item.find('description')
      if desc is not None and desc.text:
        # Convert plain text: preserve line breaks and escape again
        text = html.unescape(desc.text)
        # Replace newlines with <br> if needed
        text = text.replace('\n', '')
        htmlParts.append(f"{text}")

      pub = item.find('pubDate')
      if pub is not None and pub.text:
        date_text = html.unescape(pub.text)
        htmlParts.append(f"<b><i>{date_text}</i></b>")

      # Add a separator between items
      htmlParts.append("<hr>")
    self.news.setHtml("".join(htmlParts))

  #----------------------------------------------------------------------------------------------------------
  def updateTimestamp(self):
    timestampFilename = μSettings.launcher.gamePath()+os.sep+P_TIMESTAMP_FILE
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
    self.toggler.setToolTip(f"Patch client and/or browse news<br><b><i>Last update: {tstamp}</i></b>")
  
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
    μPrint.info(f"Starting {C_SILVER}full launcher</font> for patching...")

  #----------------------------------------------------------------------------------------------------------
  # TODO - add this to process manager 
  def fullLauncherThread(self):
    # self.sigChangeRequest.emit(self.P_STATUS_AUTHENTICATING)

    cmd = f'cd \"{μSettings.launcher.gamePath()}\" ; {μSettings.launcher.command()} DNDLauncher.exe'

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
      μPrint.info("cPatch.fullLauncherThread.run: Error launching, check logs for details!")
      exitCode = 1


#----------------------------------------------------------------------------------------------------------
# TODO reimplement this using threading
#----------------------------------------------------------------------------------------------------------
class tPatcher(QRunnable):
  def __init__(self, patchWidget : μPatch, main : μMainWindow):
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
      timestampFilename = μSettings.launcher.gamePath()+os.sep+P_TIMESTAMP_FILE
      with open(timestampFilename, 'w') as f:
        f.write(f"{datetime.now().strftime("%Y-%m-%d, at %H:%M:%S")}")
    except Exception as e:
      self.main.console.error(f"Error creating file {timestampFilename} for saving timestamp!", e)
    
    self.patchWidget.sigPatchDone.emit(True)
    

  #----------------------------------------------------------------------------------------------------------
  def runTarget(self, target : str):
    # if usingProton:
    if True:
      # Cannot use protonrun here; need to use proton's wine, so we rewire it as follows:
      protonWine = os.path.dirname(μSettings.launcher.protonExec()) + "/dist/bin/wine"
      evars = {'WINEPREFIX': f"{μSettings.launcher.compatData()}/pfx"}
      cmd  = f"\"{protonWine}\" rundll32.exe patchclient.dll,Patch "
      cmd += f"{self.main.credentials.serverInfo.patchServer} "
      cmd += f"--language {μSettings.launcher.language()} "
      cmd += f"--productcode {self.main.credentials.serverInfo.patchProductCode} "
      if μSettings.launcher.useHighRes(): cmd += " --highres "

    out = subprocess.Popen([f"{cmd} {target}"], cwd=μSettings.launcher.gamePath(), env=evars, \
                        stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
    while True:
      line = out.stdout.readline().decode()
      if not line:
        break
      elif line.startswith("Decrypting"):
        pass
      else:
        self.patchWidget.sigPatchInfo.emit(line.strip())