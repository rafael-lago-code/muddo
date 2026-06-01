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
import os, urllib.request
from helpers.μYAML import μYAML
from PyQt6.QtWidgets import (QDialog, QFileDialog, QInputDialog,
                              QLabel, QLineEdit, QListWidget, QListWidgetItem,
                              QMessageBox, QPushButton, QSizePolicy, QTabWidget,
                              QWidget, QHBoxLayout, QVBoxLayout, QApplication)
from PyQt6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QSize
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
from widgets.μOrb import μOrbSmall

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
P_USER_ICONS_DIR  = P_DEFAULT_CONFIGDIR + "/icons"
P_BUILTIN_ICONS_DIR = P_MUDDO_DIR + "/images/custom-icons"
P_RECENT_FILE     = P_DEFAULT_CONFIGDIR + "/recentIcons.yaml"
P_ICON_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg"}
P_PREVIEW_SIZE    = QSize(64, 64)
P_THUMB_SIZE      = QSize(24, 24)
P_RECENT_MAX      = 10
P_GRID_SIZE = QSize(P_THUMB_SIZE.width() + 16, P_THUMB_SIZE.height() + 24)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def scanIcons(directory: str) -> list[str]:
  results = []
  for root, _, files in os.walk(directory):
    for f in sorted(files):
      if os.path.splitext(f)[1].lower() in P_ICON_EXTENSIONS:
        results.append(os.path.join(root, f))
  return results

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def loadRecent() -> list[str]:
  try:
    paths = μYAML(P_RECENT_FILE).raw or []
    return [p for p in paths if os.path.isfile(p)][:P_RECENT_MAX]
  except Exception:
    return []

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def saveRecent(path: str):
  recent = loadRecent()
  recent = [p for p in recent if p != path]
  recent.insert(0, path)
  recent = recent[:P_RECENT_MAX]
  try:
    os.makedirs(P_DEFAULT_CONFIGDIR, exist_ok=True)
    μYAML.dump(recent, P_RECENT_FILE)
  except Exception as e:
    μPrint.error("[cIconSelectDialog] could not save recent icons", e)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def makeItem(path: str) -> QListWidgetItem:
  px = getPixmap(path)
  if px.isNull():
    px = QPixmap(P_THUMB_SIZE)
    px.fill(Qt.GlobalColor.gray)
  else:
    px = px.scaled(P_THUMB_SIZE, Qt.AspectRatioMode.KeepAspectRatio,
                   Qt.TransformationMode.SmoothTransformation)
  item = QListWidgetItem(getIcon(px), os.path.basename(path))
  item.setData(Qt.ItemDataRole.UserRole, path)
  item.setToolTip(path)
  return item

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def makeIconList() -> QListWidget:
  lw = QListWidget()
  lw.setViewMode(QListWidget.ViewMode.IconMode)
  lw.setIconSize(P_THUMB_SIZE)
  lw.setGridSize(P_GRID_SIZE)
  lw.setUniformItemSizes(True)
  lw.setResizeMode(QListWidget.ResizeMode.Adjust)
  lw.setMovement(QListWidget.Movement.Static)
  lw.setWordWrap(True)
  return lw


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  I C O N   S E L E C T   D I A L O G
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μIconSelectDialog(QDialog):
  def __init__(self, current: str = None, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Select Icon")
    self.setMinimumSize(700, 480)
    self._selected = current

    os.makedirs(P_USER_ICONS_DIR, exist_ok=True)

    self.preview = QLabel()
    self.preview.setFixedSize(P_PREVIEW_SIZE)
    self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.preview.setStyleSheet("border: 1px solid #555;")
    self.meta = QLabel()
    self.meta.setWordWrap(True)
    self.meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.meta.setFixedWidth(100)

    self.filter = QLineEdit()
    self.filter.setClearButtonEnabled(True)

    self.tabs = QTabWidget()
    self.listBuiltin = makeIconList()
    self.listUser    = makeIconList()
    self.listRecent  = makeIconList()
    self.tabs.addTab(self.listRecent,  "Recent")
    self.tabs.addTab(self.listUser,    "User")
    self.tabs.addTab(self.listBuiltin, "Built-in")

    # --- url fetch bar (hidden until needed) ---
    self.urlBar = QWidget()
    self.urlEdit = QLineEdit()
    self.urlFetch = QPushButton("Fetch")
    urlRow = newHLayout(["URL:", self.urlEdit, self.urlFetch])
    urlRow.setContentsMargins(0, 0, 0, 0)
    self.urlBar.setLayout(urlRow)
    self.urlBar.setVisible(False)

    self.btnFile  = μOrbSmall(icon=P_ICON_HARDDISK,  tooltip="Select image from a local file")
    self.btnURL   = μOrbSmall(icon=P_ICON_DOWNLOAD,  tooltip="Download image from a url and save it locally")
    self.btnPaste = μOrbSmall(icon=P_ICON_PASTE,     tooltip="Paste from clipboard")
    self.btnOk     = μOrbSmall(icon=P_ICON_CHECKMARK, tooltip="Accept")
    self.btnCancel = μOrbSmall(icon=P_ICON_CLEAR,     tooltip="Cancel")

    root = QVBoxLayout(self)
    root.addLayout(newHLayout([newVLayout(["Preview:", self.preview, self.meta, "__stretch__"]), 
                               newVLayout([self.filter, self.tabs])]))
    root.addWidget(self.urlBar)
    root.addLayout(newHLayout([self.btnFile, self.btnURL, self.btnPaste, "__stretch__", self.btnOk, self.btnCancel]))

    # --- populate ---
    self.populateList(self.listBuiltin, scanIcons(P_BUILTIN_ICONS_DIR))
    self.populateList(self.listUser,    scanIcons(P_USER_ICONS_DIR))
    self.populateList(self.listRecent,  loadRecent())

    if current:
      self.setPreview(current)

    # --- connections ---
    for lw in (self.listBuiltin, self.listUser, self.listRecent):
      lw.currentItemChanged.connect(self.onItemChanged)
      lw.itemDoubleClicked.connect(self.onAccept)

    self.btnFile.clicked.connect(self.fromFile)
    self.btnURL.clicked.connect(self.toggleUrlBar)
    self.urlFetch.clicked.connect(self.fromURL)
    self.btnPaste.clicked.connect(self.fromPaste)
    self.btnOk.clicked.connect(self.onAccept)
    self.btnCancel.clicked.connect(self.reject)
    self.filter.textChanged.connect(self.applyFilter)
    self.tabs.currentChanged.connect(lambda _: self.applyFilter(self.filter.text()))

    QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(self.fromPaste)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def currentList(self) -> QListWidget:
    return self.tabs.currentWidget()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def applyFilter(self, text: str):
    lw = self.currentList()
    if not isinstance(lw, QListWidget):
      return
    needle = text.lower()
    for i in range(lw.count()):
      item = lw.item(i)
      item.setHidden(needle not in item.text().lower())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def populateList(self, lw: QListWidget, paths: list[str]):
    lw.clear()
    for p in paths:
      lw.addItem(makeItem(p))
    if lw is self.currentList():
      self.applyFilter(self.filter.text())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onItemChanged(self, current: QListWidgetItem, _prev):
    if current:
      path = current.data(Qt.ItemDataRole.UserRole)
      self._selected = path
      self.setPreview(path)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def setPreview(self, path: str):
    px = getPixmap(path)
    if not px.isNull():
      self.preview.setPixmap(px.scaled(P_PREVIEW_SIZE,
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation))
      self.meta.setText(f"{os.path.basename(path)}\n{px.width()}×{px.height()} px\n{path}")
    else:
      self.preview.setText("(no preview)")
      self.meta.setText("")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def fromFile(self):
    path, _ = QFileDialog.getOpenFileName(
      self, "Select icon", "",
      "Images (*.png *.svg *.jpg *.jpeg);;All files (*)")
    if path:
      self._selected = path
      self.setPreview(path)
      self.refreshRecent(path)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def toggleUrlBar(self):
    self.urlBar.setVisible(not self.urlBar.isVisible())
    if self.urlBar.isVisible():
      self.urlEdit.setFocus()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def fromURL(self):
    url = self.urlEdit.text().strip()
    if not url:
      return
    fname = os.path.basename(url.split("?")[0]) or "icon.png"
    dest = os.path.join(P_USER_ICONS_DIR, fname)
    try:
      urllib.request.urlretrieve(url, dest)
    except Exception as e:
      QMessageBox.critical(self, "Download failed", str(e))
      return
    self.urlBar.setVisible(False)
    self.urlEdit.clear()
    self._selected = dest
    self.setPreview(dest)
    self.refreshRecent(dest)
    self.populateList(self.listUser, scanIcons(P_USER_ICONS_DIR))
    self.tabs.setCurrentWidget(self.listUser)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def fromPaste(self):
    img = QApplication.clipboard().image()
    if img.isNull():
      QMessageBox.information(self, "Paste", "No image found in clipboard.")
      return
    name, ok = QInputDialog.getText(self, "Save pasted image", "File name (without extension):")
    if not ok or not name.strip():
      return
    dest = os.path.join(P_USER_ICONS_DIR, name.strip() + ".png")
    if not img.save(dest, "PNG"):
      QMessageBox.critical(self, "Save failed", f"Could not save to {dest}")
      return
    self._selected = dest
    self.setPreview(dest)
    self.refreshRecent(dest)
    self.populateList(self.listUser, scanIcons(P_USER_ICONS_DIR))
    self.tabs.setCurrentWidget(self.listUser)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def refreshRecent(self, path: str):
    saveRecent(path)
    self.populateList(self.listRecent, loadRecent())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def onAccept(self):
    if self._selected:
      saveRecent(self._selected)
    self.accept()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def selectedPath(self) -> str | None:
    return self._selected
