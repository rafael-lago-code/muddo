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
import urllib.request
from helpers.μYAML import μYAML
from widgets.μFloating import μToggler
from widgets.μOrb import cOrbTiny, μOrbSmall
from widgets.μMenu import μMenu
from helpers.util import *
from helpers.μImageFactory import *
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QLineEdit, QToolBar, QMenu
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineProfile
import adblock
import os, sys

P_BROWSER_STDERR_LOG = P_DEFAULT_CONFIGDIR + "/logs/browserStdErr.log"

P_BOOKMARK_YAML = P_DEFAULT_CONFIGDIR + "/browserBookmarks.yaml"
P_LANDING_PAGE = "ddowiki.com/page/Home"


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  A D   B L O C K E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χAdBlocker(QWebEngineUrlRequestInterceptor):

  _resourceTypeMap = {
    0:  "document",       # MainFrame     — never block (handled in interceptRequest)
    1:  "subdocument",    # SubFrame
    2:  "stylesheet",     # Stylesheet
    3:  "script",         # Script
    4:  "image",          # Image
    5:  "font",           # FontResource
    6:  "other",          # SubResource
    7:  "object",         # Object
    8:  "xmlhttprequest", # Xhr
    9:  "ping",           # Ping
    10: "other",          # ServiceWorker
    11: "media",          # Media
    12: "other",          # Worker
    13: "image",          # Favicon
  }

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, parent=None):
    super().__init__(parent)
    self.enabled   = True
    self.filterSet = adblock.FilterSet()
    self._loadFilters()
    self.engine    = adblock.Engine(self.filterSet, optimize=True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _loadFilters(self):
    try:
      req = urllib.request.Request(
        "https://easylist.to/easylist/easylist.txt",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
      )
      with urllib.request.urlopen(req, timeout=10) as resp:
        content = resp.read().decode('utf-8')
      try:    self.filterSet.add_filter_list(content)
      except TypeError: self.filterSet.add_filter_list(content, "text")
    except Exception as e:
      print(f"[AdBlocker] failed to load filter list: {e}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def interceptRequest(self, info):
    if not self.enabled: return
    resourceType = -1
    try:    resourceType = int(info.resourceType())
    except: resourceType = getattr(info.resourceType(), 'value', -1)
    if resourceType == 0: return   # never block main frame navigation
    url       = info.requestUrl().toString()
    sourceUrl = info.firstPartyUrl().toString()
    content   = self._resourceTypeMap.get(resourceType, "other")
    try:
      result  = self.engine.check_network_urls(url, sourceUrl, content)
    except AttributeError:
      try:    result = self.engine.check_network_url(url, sourceUrl, content)
      except: return
    blocked = getattr(result, 'matched', None) or getattr(result, 'blocked', None)
    if blocked: info.block(True)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setEnabled(self, enabled):
    self.enabled = enabled


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  μ B R O W S E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μBrowser(μToggler):

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self, parent=None):
    super().__init__("Wiki", "compass")
    self.urlHistory = []
    self.currentPage = -1
    self._navigating = False
    os.makedirs(os.path.dirname(P_BROWSER_STDERR_LOG), exist_ok=True)
    self._stderrLog = open(P_BROWSER_STDERR_LOG, "w")
    self._origStderr = os.dup(2)
    os.dup2(self._stderrLog.fileno(), 2)
    sys.stderr = os.fdopen(self._origStderr, "w", closefd=False)

    self.webview = None
    self.adblocker = χAdBlocker()
    QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.adblocker)

    self.btnBack = μOrbSmall(icon="thick_arrow_left",    tooltip="Back. <br><b><i>Right-click</i></b> or <b><i>Ctrl-click</i></b> or : show backward history")
    self.btnForward = μOrbSmall(icon="thick_arrow_right",    tooltip="Forward.<br><b><i>Right-click</i></b> or <b><i>Ctrl-click</i></b> or : show forward history")
    self.btnRefresh = μOrbSmall(icon="view-refresh",    tooltip="Refresh Page")
    self.cbAdblocker = μOrbSmall(icon="shield",    tooltip="Toggles the Ad-Blocker OFF")
    self.btnBookmark = μOrbSmall(icon="bookmarks",    tooltip="Bookmark current page.<br><b><i>Right-click</i></b> or <b><i>Ctrl-click</i></b> or : show bookmarked items")
    self.btnWiki = μOrbSmall(icon="curled-scroll",    tooltip=f"Return do the default landing page:<br><b><i>{P_LANDING_PAGE}</i></b>")
    self.cbAdblocker.setCheckable(True)

    self.urlEdit = QLineEdit()
    self.toolbar = QToolBar()
    self.toolbar.addWidget(self.btnBack)
    self.toolbar.addWidget(self.btnForward)
    self.toolbar.addWidget(self.btnBookmark)
    self.toolbar.addWidget(self.btnRefresh)
    self.toolbar.addWidget(self.urlEdit)
    self.toolbar.addWidget(self.cbAdblocker)
    self.toolbar.addWidget(self.btnWiki)

    self.urlEdit.setText(P_LANDING_PAGE)
    
    self.urlEdit.returnPressed.connect(lambda : self.gotoHistory(self.urlEdit.text()))
    self.btnWiki.clicked.connect(lambda : self.gotoHistory(P_LANDING_PAGE))
    self.btnBack.clicked.connect(lambda : self.gotoHistory(self.currentPage-1))
    self.btnForward.clicked.connect(lambda : self.gotoHistory(self.currentPage+1))
    self.btnBookmark.clicked.connect(self.bookmarkPage)
    # self.btnRefresh.clicked.connect(self.webview.reload)
    self.cbAdblocker.setChecked(True)
    self.cbAdblocker.toggled.connect(self.toggleAdblock)

    QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(lambda : self.urlEdit.setFocus())

    self.btnForward.rightReleased.disconnect()
    self.btnBack.rightReleased.disconnect()
    self.btnBookmark.rightReleased.disconnect()
    self.btnBack.rightReleased.connect(self.showBackMenu)
    self.btnForward.rightReleased.connect(self.showForwardMenu)
    self.btnBookmark.rightReleased.connect(self.showBookmarkMenu)
    self.btnBack.ctrlRightReleased.connect(self.showBackMenu)
    self.btnForward.ctrlRightReleased.connect(self.showForwardMenu)
    self.btnBookmark.ctrlRightReleased.connect(self.showBookmarkMenu)
    self.loadBookmarks()
    # self.webview.urlChanged.connect(self._onUrlChanged)
    # self.webview.loadFinished.connect(self._onLoadFinished)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setVisible(self, value: bool):
    if value and self.webview is None:
      self.webview = QWebEngineView()
      self.setLayout(vLayout(self.toolbar, self.webview))
      self.btnRefresh.clicked.connect(self.webview.reload)
      self.webview.urlChanged.connect(self._onUrlChanged)
      self.webview.loadFinished.connect(self._onLoadFinished)
      self.gotoHistory(P_LANDING_PAGE)
    super().setVisible(value)


  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _onUrlChanged(self, url):
    urlStr = url.toString()
    self.urlEdit.setText(urlStr)
    if self._navigating:
      self._navigating = False
      return
    self.gotoHistory(urlStr)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _onLoadFinished(self, ok):
    if not ok or not self.urlHistory: return
    title = self.webview.page().title()
    if title:
      url, _ = self.urlHistory[self.currentPage]
      self.urlHistory[self.currentPage] = (url, title)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def showBackMenu(self, e : QEvent):
    import widgets.μOrb as μOrb
    menu = QMenu("History - Back", self.btnBack)
    for i, (url, title) in enumerate(self.urlHistory):
      if i >= self.currentPage: break
      menu.addAction(title or url, lambda checked=False, idx=i: self.gotoHistory(idx))
    menu.exec(self.btnBack.mapToGlobal(e.pos()))
    self.btnBack.setState(μOrb.P_STATUS_RCLICK)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def showForwardMenu(self, e : QEvent):
    import widgets.μOrb as μOrb
    menu = QMenu("History - Forward", self.btnForward)
    for i, (url, title) in enumerate(self.urlHistory):
      if i <= self.currentPage: continue
      menu.addAction(title or url, lambda checked=False, idx=i: self.gotoHistory(idx))
    menu.exec(self.btnForward.mapToGlobal(e.pos()))
    self.btnForward.setState(μOrb.P_STATUS_RCLICK)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def gotoHistory(self, data):
    if isinstance(data, str):
      url = data if data.startswith("http") else "https://" + data
      self.urlHistory = self.urlHistory[:self.currentPage + 1]
      self.urlHistory.append((url, ""))
      index = len(self.urlHistory) - 1
    else:
      index = data

    if not 0 <= index < len(self.urlHistory): return
    self.currentPage = index
    url, _ = self.urlHistory[index]
    self._navigating = True
    self.webview.load(QUrl(url))
    self.urlEdit.setText(url)
    self.btnBack.setEnabled(self.currentPage > 0)
    self.btnForward.setEnabled(self.currentPage < len(self.urlHistory) - 1)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def toggleAdblock(self, state):
    self.adblocker.setEnabled(state)
    self.cbAdblocker.setChecked(state)
    self.cbAdblocker.setToolTip("Toggles the Ad-Blocker " + "ON" if not state else "OFF")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def bookmarkPage(self):
    title = self.webview.page().title()
    url   = self.webview.url().toString()
    db = μYAML(P_BOOKMARK_YAML)
    if not isinstance(db.raw, list): db.raw = []
    for bm in db.raw:
      if bm["url"] == url: return
    db.raw.append({"title": title, "url": url})
    db.save()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def loadBookmarks(self):
    db = μYAML(P_BOOKMARK_YAML)
    self._bookmarks = db.raw if isinstance(db.raw, list) else []

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def showBookmarkMenu(self, e : QEvent):
    import widgets.μOrb as μOrb
    self.loadBookmarks()
    menu = μMenu("Bookmarks", self.btnBookmark)
    for i, bm in enumerate(self._bookmarks):
      closeBtn = cOrbTiny(icon=P_ICON_SMPLX)
      menu.addAction(text = bm["title"] or bm["url"],
        callback = lambda checked=False, url=bm["url"]: self.gotoHistory(url),
        button = closeBtn,
        buttonCallback = lambda checked=False, idx=i, m=menu: (self._deleteBookmark(idx), m.close()))
    if not self._bookmarks:
      menu.addAction("(no bookmarks)").setEnabled(False)
    menu.exec(self.btnBookmark.mapToGlobal(e.pos()))
    self.btnBookmark.setState(μOrb.P_STATUS_RCLICK)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def _deleteBookmark(self, index):
    db = μYAML(P_BOOKMARK_YAML)
    if not isinstance(db.raw, list) or index >= len(db.raw): return
    db.raw.pop(index)
    db.save()


# # 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
# #   ❖  M A I N   W I N D O W
# # 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
# class MainWindow(QMainWindow):

#   # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#   def __init__(self):
#     super().__init__()
#     self.setWindowTitle("μDDO's Mini-Browser")
#     self.setGeometry(100, 100, 1200, 800)

#     self.browser = μBrowser()
#     self.setCentralWidget(self.browser)


# if __name__ == "__main__":
#   app = QApplication(sys.argv)
#   window = MainWindow()
#   window.show()
#   sys.exit(app.exec())
