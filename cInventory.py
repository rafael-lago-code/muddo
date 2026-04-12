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
from PyQt6.QtWidgets import QAbstractItemView, QCheckBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from widgets.cOrb import cOrbSmall, cOrb
from helpers.util import *
from widgets.cToggler import cToggler
from PIL import Image

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
                        1<<21: "💎",   # More or less arbitrary, I hope it doesn't conflict with anything in the future
                        1<<30: "☀️",
                        1<<31: "🌙"}
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

#----------------------------------------
class itemData(QTableWidgetItem):
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
    _isTrash = 0
    _isLocked = 0
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
      count = int.from_bytes(f.read(2), byteorder='little', signed=False) # don't need, but it is saved there
      rawData = f.read(count)
      total_pixels = count // 4         # 4 bytes/channels per pixel
      width = int(total_pixels ** 0.5)  # Square root
      height = width                    # should be 36 for the normal icon
      
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
      if self._description: ttip += f"<i>\"{self._description}\"</i><br><br>"
      if self._qualifier: ttip += f"<b>Qualifier:</b> {self._qualifier}<br>"
      if self._quantity and self._quantity>1: ttip += f"<b>Quantity:</b> {self._quantity}<br>"
      if self._minLevel: ttip += f"<b>Minimum Level:</b> {self._minLevel}<br>"
      if self._augments: ttip += f"<b>Augments:</b><br> ● {'<br> ● '.join(self.augments())} <br>"
      if self._effects: ttip += "<b>Effects:</b><br>" + "<br>".join([f" ● {k}: {v}" for k,v in self._effects.items()]) + "<br>"
      if self._material: ttip += f"<b>Material:</b> {self._material}<br>"
      if self._hardness: ttip += f"<b>Hardness:</b> {self._hardness}<br>"
      if self._valueCopper: ttip += f"<b>Value:</b> {self._valueCopper}CC<br>"
      if ttip == "": ttip = f"<i>(no description)</i>"
      self.setIcon(self.icon())
      self.setToolTip(ttip)
      self.setData(Qt.ItemDataRole.UserRole, self._name)
    
    #----------------------------------------------------------------------------------------------------------
    def getColumnWidget(self, col: str) -> QTableWidgetItem:
      if col == "Name": return self

      if col == "Owner":
        return newCell(self._ownerName)
      elif col == "Type":
        return newCell(self._type)
      elif col == "Equips To":
        return newCell(self._equipsTo)
      elif col == "Binding":
        return newCell(self.binding())
      elif col == "👤":
        text = self.slot()
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
        return newCell("✓" if self._isLocked == 1 else "", 1 if self._isLocked == 1 else 0)
      else:
        return newCell(f"Unknown Column <{col}>")

    #----------------------------------------------------------------------------------------------------------
    def icon(self) -> QIcon:
      if self._icon:
        return QIcon(QPixmap(self._icon))
      else:
        return P_ITEM_UKNOWN_ICON

    #----------------------------------------------------------------------------------------------------------
    def slot(self):
      textSlot = ""
      if int(self._currentSlot) >= P_ITEM_EQUIPPED_SLOT_BASE:
        return P_ITEM_EQUIPPED_SLOT.get(int(self._currentSlot)-P_ITEM_EQUIPPED_SLOT_BASE, f"?{self._currentSlot-P_ITEM_EQUIPPED_SLOT_BASE}?")
      else:
        # Tab / Row / Col
        return (self._currentSlot//20, (self._currentSlot % 20) // 5, (self._currentSlot % 20) % 5)

    #----------------------------------------------------------------------------------------------------------
    def binding(self):
      if self._binding == 0: return "∞"
      elif self._binding == 1: return "?1?"
      elif self._binding == 2: return "BtC"
      elif self._binding == 3: return "BtA"
      elif self._binding == 4: return "BtCoE"
      elif self._binding == 5: return "BtAoE"
      elif self._binding == 6: return "BtC" # kinda bugged, it is bound to character on acquire and on equip
      else: return f"?{self._binding}?"
    
    #----------------------------------------------------------------------------------------------------------
    def augments(self, textOnly=False, iconsOnly=False):
      copyVals = self._augments.copy()
      text=[]
      icons=[]
      while copyVals:
        v = copyVals.pop(-1)
        if v == 0: pass
        elif v in P_ITEM_AUGMENTS_NAME:
          text += [P_ITEM_AUGMENTS_NAME[v]] if textOnly else [f"{P_ITEM_AUGMENTS_NAME[v]} {P_ITEM_AUGMENTS_ICON[v]} "]
          icons += [P_ITEM_AUGMENTS_ICON[v]]
        else:
          text += [f"?{v}?"]
          icons += [f"?{v}?"]
      return icons if iconsOnly else text

#----------------------------------------------------------------------------------------------------------
class cStorageManager(cToggler):
  def __init__(self, main):
    self.widgetID = "StorageManager"
    self.main = main
    super().__init__("Storage\nManager", P_ICON_CHEST)
    self.toggler.setToolTip("Toggle StorageManager UI<br><b><i>NOT IMPLEMENTED</i></b>")
    self.table = QTableWidget(0, 7)
    self.table.setColumnWidth(0, 300)
    self.table.setColumnWidth(1, 100)
    self.table.setColumnWidth(2, 100)
    self.table.setColumnWidth(3, 100)
    self.table.setColumnWidth(4, 50)
    self.table.setColumnWidth(5, 10)
    self.table.setColumnWidth(6, 10)
    self.table.setHorizontalHeaderLabels(P_ITEM_COLUMNS)
    self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    self.table.setIconSize(QtCore.QSize(36,36))
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    
    # self.btnLoad        = cOrb(icon=P_ICON_TRIANGLE_DOWN, tooltip="Load storage data from file")
    self.btnRefresh     = cOrb("Refresh",     icon=P_ICON_REFRESH, tooltip="Fetch data from running clients and display in the viewer")
    self.btnDeconstruct = cOrb("Dissolve",    icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_deconst.png'),
                               tooltip="Dissolve all selected items (Item Deconstruction station must be selected). <br><b>Ctrl+Click</b> to skip confirmation<b>.")
    self.btnSell        = cOrb("Sell",        icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_vendor.png'),
                               tooltip="Sell all selected items to the currently open vendor. <br><b>Ctrl+Click</b> to repair equipment too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnTrade       = cOrb("Trade",       icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_trade.png'),
                               tooltip="Trade selected items with selected player. <br><b>Ctrl+Click</b> to add platinum too<b>.<br><b><i>Right-click for more options</i></b>")
    self.btnStore       = cOrb("Store",       icon=getIcon(P_DEFAULT_ICON_PATHS[0]+'/cannith_bank.png'),
                               tooltip="Store selected items in the currently open bank/chest. <br><b><i>Right-click for more options</i></b>")
    P_MUDDO_DIR+'/images/'

    self.btnRefresh.clicked.connect(self.loadStorageData)
    self.btnRefresh.ctrlClicked.connect(lambda : self.requestStorageData(True))

    self.btnDeconstruct.clicked.connect(self.requestStorageData)
    self.btnRefresh.ctrlClicked.connect(lambda : self.requestStorageData(True))

    # self.btnLoad.clicked.connect(self.loadStorageData)
    self.filterBy = QLineEdit()
    self.filterBy.textEdited.connect(self.applyFilters)
    self.filterByName = QCheckBox("Name")
    self.filterByName.setChecked(True)
    self.filterByDescription = QCheckBox("Description")
    self.filterByDescription.setChecked(True)
    self.setLayout(newVLayout([self.table, newHLayout(["Filter by...", self.filterBy, self.filterByName, self.filterByDescription]),
                               newHLayout([self.btnRefresh, self.btnStore, self.btnTrade, self.btnSell, self.btnDeconstruct])]))
  
  #----------------------------------------------------------------------------------------------------------
  def initialize(self):
    pass
  
  #----------------------------------------------------------------------------------------------------------
  def requestStorageData(self, detailed: bool = False):
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestDeconstruct(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestStore(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestTrade(self):
    pass

  #----------------------------------------------------------------------------------------------------------
  def requestSell(self, sellGems : bool = True, repair : bool = False):
    pass
   
  
  #----------------------------------------------------------------------------------------------------------
  def applyFilters(self):
    filterText = self.filterBy.text().lower().strip()

    for row in range(self.table.rowCount()):
      target = ""
      if self.filterByName.isChecked(): target += self.table.item(row, 0)._name.lower() + " "
      if self.filterByDescription.isChecked(): target += self.table.item(row, 0).toolTip().lower() + " "


      self.table.setRowHidden(row, not (filterText=="" or filterText in target))

  #----------------------------------------------------------------------------------------------------------
  def loadStorageData(self):
    # filename = '/home/soul/share/μilvian/milvian.net/InventoryData149463212643691619.bin'
    filename = '/home/steam/prefixes/DDO_Alt/pfx/drive_c/users/holysword/AppData/Roaming/Milvian/InventoryData149463212639969323.bin'

    self.table.setSortingEnabled(False)
    with open(filename, 'rb') as f:
      epoch  = int.from_bytes(f.read(8), byteorder='little', signed=True)
      nitems = int.from_bytes(f.read(4), byteorder='little', signed=False)
      print(f"Storage data from {filename} - epoch: {epoch}, nitems: {nitems}")
      allItems = []
      for _ in range(nitems):
        item = itemData()
        item._id          = int.from_bytes(f.read(8), byteorder='little', signed=False)
        item._name        = itemData.readString(f) # f.read(count).decode('utf-8')
        item._ownerID     = int.from_bytes(f.read(8), byteorder='little', signed=False)
        item._ownerName   = itemData.readString(f)
        item._container   = itemData.readString(f)
        item._weenieID    = int.from_bytes(f.read(8), byteorder='little', signed=False)
        item._type        = itemData.readString(f)
        item._quantity    = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._qualifier   = itemData.readString(f)
        item._valueCopper = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._hardness    = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._durability  = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._iconId      = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._icon        = itemData.readIcon(f)
        item._description = itemData.readString(f)
        item._minLevel    = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._material    = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._isTrash     = int.from_bytes(f.read(1), byteorder='little', signed=False)
        item._isLocked    = int.from_bytes(f.read(1), byteorder='little', signed=False)
        item._isMinorArtifact = int.from_bytes(f.read(1), byteorder='little', signed=False)
        item._setBonus1   = itemData.readString(f)
        item._setBonus2   = itemData.readString(f)
        item._currentSlot = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._binding     = int.from_bytes(f.read(4), byteorder='little', signed=False)
        item._equipsTo    = itemData.readString(f)

        item._augments = []
        item._effects  = {}
        
        count = int.from_bytes(f.read(2), byteorder='little', signed=False)
        for _ in range(count):
          item._augments.append(int.from_bytes(f.read(4), byteorder='little', signed=False))

        count = int.from_bytes(f.read(2), byteorder='little', signed=False)
        for _ in range(count):
          countKey = int.from_bytes(f.read(2), byteorder='little', signed=False)
          key = f.read(countKey).decode('utf-8')
          countVal = int.from_bytes(f.read(2), byteorder='little', signed=False)
          item._effects[key] = f.read(countVal).decode('utf-8')
        
        allItems.append(item)
        item.digest()
        
        pos = self.table.rowCount()
        self.table.insertRow(pos)
        # self.table.setRowHeight(pos, 36)
        for i, col in enumerate(P_ITEM_COLUMNS):
           self.table.setItem(pos, i, item.getColumnWidget(col))
    self.table.setSortingEnabled(True)




    


