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
from __future__ import annotations
from io import BufferedReader
from PyQt6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from helpers.μImageFactory import *
from helpers.μPrint import μPrint
from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#    from cMacrosDaemon import cMacrosDaemon

P_ITEM_COLUMNS = ["Name", "Owner", "Type", "Equips To", "Binding", "👤", "🔒"]
P_ITEM_UKNOWN_ICON = None

# Augments logic is based on which colors they accept
#----------------------------------------------------------------
#  1<<0 = 1:  colorless
#  1<<1 = 2:  red
#  1<<2 = 4:  yellow
#  1<<3 = 8:  blue
#  1<<4 = 16: orange
#  1<<5 = 32: purple
#  1<<6 = 64: green
#  1<<30    : sun
#  1<<31    : moon
#  So an orange slot = (orange | red | yellow | colorless) = 1 + 2 + 4 + 16 = 23
P_ITEM_AUGMENTS_NAME = {1:     "Colorless",
                        3:     "Red",
                        5:     "Yellow",
                        9:     "Blue",
                        23:    "Orange",
                        43:    "Purple",
                        77:    "Green",
                        1<<21: "Sentient",
                        1<<30: "Sun",
                        1<<31: "Moon"}
P_ITEM_AUGMENTS_ICON = {1:     "⚪",  # ◆
                        3:     "🛑",  # 🟥 🔴
                        5:     "🟨",  # 🟡
                        9:     "🔷",  # 🔵 🟦
                        23:    "🔶",  # 🟧 🟠
                        43:    "🟣",  # 🟪
                        77:    "🟩",  # 🟢
                        1<<21: "💎",   # More or less arbitrary choice, I hope it doesn't conflict with anything in the future
                        1<<30: "☀️",
                        1<<31: "🌙"}
P_ITEM_BINDING_NAME = {0: "∞",
                       1: "?1?",
                       2: "BtC",
                       3: "BtA",
                       4: "BtCoE",
                       5: "BtAoE",
                       6: "BtC" # kinda bugged, it is bound to character on acquire and on equip
}


P_ITEM_EQUIPPED_SLOT_BASE = 3*0x40000000-1 # don't ask, I don't know
P_ITEM_EQUIPPED_SLOT = {
      1<<1 : "Goggles",
      1<<2 : "Cloak",
      1<<3 : "Ring (Right)",
      1<<4 : "Bracers",
      1<<5 : "Ring (Left)",
      1<<6 : "Helm",
      1<<7 : "Armor",
      1<<8 : "Trinket",
      1<<9 : "Necklace",
      1<<10: "Gloves",
      1<<11: "Belt",
      1<<12: "Boot",
      1<<13: "Main Weapon",
      1<<14: "Secondary Weapon",
      1<<15: "Arrow",
      1<<16: "Quiver",
      1<<17: "Runearm",
      1<<18: "Cosmetic Weapon1?",
      1<<19: "Cosmetic Weapon2",
      1<<20: "?1<<20?",
      1<<21: "Cosmetic Armor",
      1<<22: "Cosmetic Helmet",
      1<<23: "?1<<23?",
      1<<24: "Cosmetic Cloak",
      3229614081: "Pet Armor",
      3229614082: "Pet Collar",
      3254779905: "?3254779905?",
    }

P_STATUS_UNKNOWN = 0
P_STATUS_IDLE    = 1
P_STATUS_BUSY_REFRESH   = 2
P_STATUS_BUSY_DISSOLVE  = 3
P_STATUS_BUSY_SELL      = 4
P_STATUS_BUSY_TRADE     = 5
P_STATUS_BUSY_STORE     = 6
P_STATUS_BUSY_FEEDJEWEL = 7

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            I T E M   D A T A
#
#                                  
#---------------------------------------------------------------------------------------------------------------
class μItemData(QTableWidgetItem):
  _id = 0
  _name = ""
  _ownerID = 0
  _ownerName = ""
  _container = ""
  _weenieID = 0
  _type = ""
  _quantity = 0
  _qualifier = ""
  _valueCopper = 0
  _hardness = 0
  _durability = 0
  _iconId = 0
  _icon = None
  _description = ""
  _minLevel = 0
  _material = 0
  _isJunk = 0
  _isLocked = 0
  _isSellable = 0
  _isMinorArtifact = 0
  _setBonus1 = 0
  _setBonus2 = 0
  _currentSlot = 0
  _binding = 0
  _equipsTo = ""
  _augments = []
  _effects = {}

  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def readString(f) -> str:
    count = int.from_bytes(f.read(2), byteorder='little', signed=False)
    return f.read(count).decode('utf-8')

  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def readIcon(f) -> QImage:
    import numpy as np
    # bg_color=(210, 180, 140)
    bg_color=(74, 119, 157)
    width  = int.from_bytes(f.read(4), byteorder='little', signed=False)
    height = int.from_bytes(f.read(4), byteorder='little', signed=False)
    count  = int.from_bytes(f.read(4), byteorder='little', signed=False)
    rawData = f.read(count)
    if width == 0 or height == 0 or count != width*height*4:
      return None

    arr = np.frombuffer(rawData, dtype=np.uint8).reshape(height, width, 4).copy()
    arr[:, :, [0, 2]] = arr[:, :, [2, 0]] # inverts red and blue channels
    bg_arr = np.full((height, width, 4), [*bg_color, 255], dtype=np.uint8)
    alpha = arr[:, :, 3:4] / 255.0        # Normalize alpha to 0-1
    result = (bg_arr[:, :, :3] * (1 - alpha) + arr[:, :, :3] * alpha).astype(np.uint8)
    result = np.dstack([result, np.full((height, width), 255, dtype=np.uint8)])

    # img = Image.frombytes('RGBA', (width, height), rawData)
    qimage = QImage(result, width, height, QImage.Format.Format_RGBA8888)
    return qimage

  #----------------------------------------------------------------------------------------------------------
  def __init__(self):
      global P_ITEM_UKNOWN_ICON
      P_ITEM_UKNOWN_ICON = getIcon(P_MUDDO_DIR+'/images/ddo_themes/skill_icons/item_placeholder.png')
      super().__init__()

  #----------------------------------------------------------------------------------------------------------
  def digest(self):
    self.setText(f"{self._name} {" ".join(self.augments(iconsOnly=True))}")
    self.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    ttip = ""
    if self._description: ttip += f"<i>\"{self._description.replace('\n','<br>')}\"</i><br><br>"
    if self._qualifier: ttip += f"<b>Qualifier:</b> {self._qualifier}<br>"
    if self._quantity and self._quantity>1: ttip += f"<b>Quantity:</b> {self._quantity}<br>"
    if self._minLevel: ttip += f"<b>Minimum Level:</b> {self._minLevel}<br>"
    if self._augments: ttip += f"<b>Augments:</b><br> ● {'<br> ● '.join(self.augments())} <br>"
    if self._effects: ttip += "<b>Effects:</b><br>" + "<br>".join([f" ● {k}: {v}" for k,v in self._effects.items()]) + "<br>"
    if self._material: ttip += f"<b>Material:</b> {self._material}<br>"
    if self._hardness: ttip += f"<b>Hardness:</b> {self._hardness}<br>"
    if self._valueCopper: ttip += f"<b>Value:</b> {self._valueCopper}CC<br>"
    if self._qualifier: ttip += f"<b>Instance ID:</b> {self._id}<br>"
    if ttip == "": ttip = f"<i>(no description)</i>"
    self.setIcon(self.icon())
    self.setToolTip(ttip)
    self.setData(Qt.ItemDataRole.UserRole, self._name)
  
#----------------------------------------------------------------------------------------------------------
  def icon(self) -> QIcon:
    if self._icon:
      return QIcon(QPixmap(self._icon))
    else:
      return P_ITEM_UKNOWN_ICON

  #----------------------------------------------------------------------------------------------------------
  def slot(self):
    if int(self._currentSlot) >= P_ITEM_EQUIPPED_SLOT_BASE:
      return P_ITEM_EQUIPPED_SLOT.get(int(self._currentSlot)-P_ITEM_EQUIPPED_SLOT_BASE, f"?{self._currentSlot-P_ITEM_EQUIPPED_SLOT_BASE}?")
    else:
      # Tab / Row / Col
      return (self._currentSlot//20, (self._currentSlot % 20) // 5, (self._currentSlot % 20) % 5)

  #----------------------------------------------------------------------------------------------------------
  def owner(self):
    return self._ownerName.split()[0]

  #----------------------------------------------------------------------------------------------------------
  def binding(self):
    return P_ITEM_BINDING_NAME.get(self._binding, f"?{self._binding}?")
  
  #----------------------------------------------------------------------------------------------------------
  def augments(self, textOnly=False, iconsOnly=False):
    copyVals = self._augments.copy()
    text=[]
    icons=[]
    while copyVals:
      v = copyVals.pop(-1)
      if v == 0: pass
      elif v in P_ITEM_AUGMENTS_NAME:
        text  += [P_ITEM_AUGMENTS_NAME[v]] if textOnly else [f"{P_ITEM_AUGMENTS_NAME[v]} {P_ITEM_AUGMENTS_ICON[v]} "]
        icons += [P_ITEM_AUGMENTS_ICON[v]]
      else:
        text  += [f"?{v}?"]
        icons += [f"?{v}?"]
    return icons if iconsOnly else text
  
  #----------------------------------------------------------------------------------------------------------
  def readFromBin(self, file : BufferedReader):
    self._id          = int.from_bytes(file.read(8), byteorder='little', signed=False)
    self._name        = μItemData.readString(file) # f.read(count).decode('utf-8')
    self._ownerID     = int.from_bytes(file.read(8), byteorder='little', signed=False)
    self._ownerName   = μItemData.readString(file)
    self._weenieID    = int.from_bytes(file.read(8), byteorder='little', signed=False)
    self._type        = μItemData.readString(file)
    self._quantity    = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._qualifier   = μItemData.readString(file)
    self._valueCopper = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._hardness    = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._durability  = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._iconId      = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._icon        = μItemData.readIcon(file)
    self._description = μItemData.readString(file)
    self._minLevel    = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._material    = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._isJunk      = int.from_bytes(file.read(1), byteorder='little', signed=False)
    self._isLocked    = int.from_bytes(file.read(1), byteorder='little', signed=False)
    self._isSellable  = int.from_bytes(file.read(1), byteorder='little', signed=False)
    self._isMinorArtifact = int.from_bytes(file.read(1), byteorder='little', signed=False)
    self._setBonus1   = μItemData.readString(file)
    self._setBonus2   = μItemData.readString(file)
    self._currentSlot = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._binding     = int.from_bytes(file.read(4), byteorder='little', signed=False)
    self._equipsTo    = μItemData.readString(file)

    self._augments = []
    self._effects  = {}
    
    count = int.from_bytes(file.read(2), byteorder='little', signed=False)
    for _ in range(count):
      self._augments.append(int.from_bytes(file.read(4), byteorder='little', signed=False))

    count = int.from_bytes(file.read(2), byteorder='little', signed=False)
    for _ in range(count):
      countKey = int.from_bytes(file.read(2), byteorder='little', signed=False)
      key = file.read(countKey).decode('utf-8')
      countVal = int.from_bytes(file.read(2), byteorder='little', signed=False)
      self._effects[key] = file.read(countVal).decode('utf-8')
    return self

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            I T E M   T A B L E
#
#                                  
#---------------------------------------------------------------------------------------------------------------
class μItemsTable(QTableWidget):
  itemsById = {}
  staleData = {}

  def __init__(self, parent):
    super().__init__(0, 7, parent)
    self.setColumnWidth(0, 300)
    self.setColumnWidth(1, 100)
    self.setColumnWidth(2, 100)
    self.setColumnWidth(3, 100)
    self.setColumnWidth(4, 50)
    self.setColumnWidth(5, 10)
    self.setColumnWidth(6, 10)
    self.setHorizontalHeaderLabels(P_ITEM_COLUMNS)
    self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    self.setIconSize(QtCore.QSize(36,36))
    self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

  #----------------------------------------------------------------------------------------------------------
  def getColumnWidget(self, item, col: str) -> QTableWidgetItem:
    if col == "Name": return item

    if col == "Owner":
      return newCell(item.owner())
    elif col == "Type":
      return newCell(item._type)
    elif col == "Equips To":
      return newCell(item._equipsTo)
    elif col == "Binding":
      return newCell(item.binding())
    elif col == "👤":
      text = item.slot()
      cell = newCell("" if isinstance(text, tuple) else "✓")
      ttip = ""
      if isinstance(text, tuple):
        ttip = f"<b>In Backpack</b><br> ● Tab {text[0]}<br> ● Row {text[1]}<br> ● Col {text[2]}"
      else:
        ttip = f"<b>Equipped</b><br> ● {text}"
      cell.setToolTip(ttip)
      cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      return cell
    elif col == "🔒":
      return newCell("✓" if item._isLocked == 1 else "", 1 if item._isLocked == 1 else 0)
    else:
      return newCell(f"Unknown Column <{col}>")
  
  #----------------------------------------------------------------------------------------------------------
  def append(self, item : μItemData):
    self.setSortingEnabled(False)

    if item._id in self.itemsById:
      oldItem = self.itemsById[item._id]
      crow = oldItem.row()
      try: self.staleData[item.owner()].remove(oldItem)
      except: pass
    else:
      crow = self.rowCount()
      self.insertRow(crow)

    for i, col in enumerate(P_ITEM_COLUMNS):
        self.setItem(crow, i, self.getColumnWidget(item, col))
    self.itemsById[item._id] = item

    self.setSortingEnabled(True)
  
  #----------------------------------------------------------------------------------------------------------
  def clearStale(self, charName : str):
    npurged = 0
    for item in list(self.staleData[charName]):
      try: del self.itemsById[item._id]
      except: pass
      try:
        self.removeRow(item.row())
        npurged += 1
      except RuntimeError:
        pass  # item was already replaced/deleted by Qt via setItem in append()
    self.staleData[charName] = []
    if (npurged): μPrint.info(f"[cItemsTable] cleaned {npurged} stale items from {C_ORANGE}{charName}</font>")

  #----------------------------------------------------------------------------------------------------------
  def clearAll(self):
    self.setRowCount(0)
    self.itemsById = {}
    self.staleData = {}