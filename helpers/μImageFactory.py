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
import os
from helpers.util import *
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon, QPixmap

P_DEFAULT_ICON_SIZE=QtCore.QSize(28,28)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  D E F A U L T   T H E M E 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
P_ICON_NONE      = "none"
P_ICON_UNDO      = "edit-undo"
P_ICON_SORT      = "view-sort"
P_ICON_OPEN      = "document-open"
P_ICON_OPENFOLDER= "document-open-folder"
P_ICON_SAVE      = "document-save"
P_ICON_SAVEALL   = "document-save-all"
P_ICON_SAVEAS    = "document-save-as"
P_ICON_DUPDOC    = "document-duplicate"
P_ICON_ADD       = "list-add"
P_ICON_REMOVE    = "list-remove"
P_ICON_REFRESH   = "view-refresh"
P_ICON_CHECKMARK = "checkmark"
P_ICON_SMPLCHECK = "simple-checkmark"
P_ICON_SMPLX     = "simple-x"
P_ICON_QUESTION  = "question"
P_ICON_MUTE      = "audio-volume-muted"
P_ICON_UNMUTE    = "audio-on"
P_ICON_PLAY      = "media-playback-start"
P_ICON_PAUSE     = "media-playback-pause"
P_ICON_STOP      = "media-playback-stop"
P_ICON_FILTER    = "view-filter"
P_ICON_EXIT      = "dungeon-exit"
P_ICON_CONFIRM   = "dialog-ok-apply"
P_ICON_CONFIGURE = "configure"
P_ICON_PROPERTIES= "document-properties"
P_ICON_CLEAR     = "edit-clear"
P_ICON_CANCEL    = "dialog-cancel"
P_ICON_CLOSE     = "window-close"
P_ICON_AUTO      = "autocorrection"
P_ICON_COMPASS   = "compass"
P_ICON_LOCKOPEN  = "document-decrypt"
P_ICON_LOCKCLOSE = "document-encrypted"
P_ICON_EDIT      = "document-edit"
P_ICON_IMAGE     = "viewimage"
P_ICON_SCROLL    = "curled-scroll"
P_ICON_NEWDOC    = "document-new"
P_ICON_STAR      = "draw-star"
P_ICON_BROOM     = "edit-clear-all"
P_ICON_CLEARALL  = "edit-clear-red"
P_ICON_SHRED     = "edit-delete-shred"
P_ICON_TRASH     = "edit-delete"
P_ICON_REDX      = "paint-none"
P_ICON_PROCSTOP  = "process-stop"
P_ICON_NOTES     = "view-pim-notes"
P_ICON_DOWNLOAD  = "edit-download"
P_ICON_UPDATE    = "update"
P_ICON_CONSOLE   = "console"
P_ICON_LOGIN     = "login"
P_ICON_GEARLOOP  = "gear-loop"
P_ICON_LIGHTNING = "lightning"
P_ICON_DRAGON    = "dragon"
P_ICON_GEARHIER  = "gears-hierarchy"
P_ICON_GEARSTACK = "gears-stack"
P_ICON_BACKPACK  = "backpack"
P_ICON_CHEST     = "chest"
P_ICON_BLACKSCREEN = "blackscreen"

P_ICON_PLACEHOLDER = "placeholder"

P_ICON_HARDDISK  = "drive-harddisk"
P_ICON_PASTE     = "edit-paste"

P_ICON_TRIANGLE_UP    = "draw-triangle3"
P_ICON_TRIANGLE_DOWN  = "draw-triangle4"
P_ICON_TRIANGLE_LEFT  = "draw-triangle1"
P_ICON_TRIANGLE_RIGHT = "draw-triangle2"

P_ICON_D20   = "dice-d20-white"
P_ICON_GEAR  = "gear-white"
P_ICON_SKULL = "human-skull-white"
P_ICON_SKULL_RED = "human-skull-red"
P_ICON_LOCKOPEN_GREEN = "document-decrypt-green"
P_ICON_LOCKCLOSE_RED  = "document-encrypted-red"
P_ICON_CONNECTED_GREEN = "network-connect-green"
P_ICON_DISCONNECTED_RED  = "network-disconnect-red"

P_FG_REDORB = "orb_fg"
P_BG_REDORB = "redorb_bg"
P_BG_PRESSED_REDORB = "redorb_pressed"
P_FG_REDBOX = "box_fg"
P_BG_REDBOX = "redbox_bg"
P_BG_PRESSED_REDBOX = "redbox_pressed"
P_FG_REDFRAME = "frame_fg"
P_BG_REDFRAME = "redframe_bg"

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  I M A G E   F A C T O R Y
#                                  
#   This is a static class. Don't instantiate it.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μImageFactory():
  
  # Order matters here!
  paths = [P_MUDDO_DIR+'/images/custom-icons/',
           P_MUDDO_DIR+'/images/ui_elements/',
           P_MUDDO_DIR+'/images/breeze-dark-icons/',
           '/usr/share/icons/breeze-dark',
           '/usr/share/icons/breeze',
           '/usr/share/icons/Adwaita',
           '/usr/share/icons/gnome',
           '/usr/share/icons/Humanity-Dark',
           '/usr/share/icons/Humanity']
  extensions = ['.svg', '.png']  
  _theme = None
  _maskColour = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def appendPath(cls, text):
    if text in cls.paths: return
    cls.paths.append(text)
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setPath(cls, paths):
    cls.paths = paths
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def prependPath(cls, text):
    if text in cls.paths: return
    cls.paths = [text] + cls.paths
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setExtensions(cls, ext):
    cls.extensions = ext
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def appendExtensions(cls, ext):
    cls.extensions.append(ext)
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def prependExtensions(cls, ext):
    cls.extensions = [ext] + cls.extensions
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setMask(cls, mask):
    if isinstance(mask, QColor): cls._maskColour = mask
    else: cls._maskColour = QColor(mask[0], mask[1], mask[2])

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def find(cls, name : str) -> QPixmap:
    def _findFile() -> QPixmap:
      if os.path.exists(name): return QPixmap(name)
      for e in [""] + cls.extensions:
        for d in cls.paths:
          if os.path.exists(d+name+e): return QPixmap(d+name+e)
          elif os.path.exists(d+"/actions/"+name+e): return QPixmap(d+"/actions/"+name+e)
          else:
            for s in ["64", "32", "16"]:
              if os.path.exists(d+"/actions/"+s+"/"+name+e): return QPixmap(d+"/actions/"+s+"/"+name+e)
      return None
    
    pmap : QPixmap = _findFile()
    if pmap is not None and cls._maskColour is not None:
      pmap.setMask(pmap.createMaskFromColor(cls._maskColour, Qt.MaskMode.MaskInColor))
    return pmap
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def theme(cls, a0) -> dict:
    if cls._theme is None: cls._theme = {}
    return cls._theme.get(a0, None)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def addImage(cls, name : str, pmap : QPixmap):
    if cls._theme is None: cls._theme = {}
    cls._theme[name] = pmap

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getPixmap(cls, a0 : str) -> QPixmap:
    if isinstance(a0, str):
      if qp := cls.theme(a0): return qp
      elif qp := cls.find(a0):
        cls.addImage(a0, qp)
        return qp
      else: return QPixmap()
    elif isinstance(a0, QIcon): return a0.pixmap(a0.availableSizes()[0])
    elif isinstance(a0, QPixmap): return a0
    else: return QPixmap()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getIcon(cls, a0) -> QIcon:
    if isinstance(a0, QIcon): return a0
    elif isinstance(a0, QPixmap): return QIcon(a0)
    elif isinstance(a0, str): return QIcon(cls.getPixmap(a0))
    else: return QIcon()
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __init__(self):
    pass

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  L A Z Y   R E F E R E N C E S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def getPixmap(a0 : str) -> QPixmap: return μImageFactory.getPixmap(a0)
def getIcon(a0) -> QIcon: return μImageFactory.getIcon(a0)