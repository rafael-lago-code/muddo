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
#
from Xlib import X
import threading, time
from helpers.tStoppableThread import tStoppableThread
from helpers.χHelper import χHelper
from helpers.χPrint import χPrint

# This is used so that key grabs are insensitive to the following modifiers and their combinations:
#  - capslock
#  - left and right mouse button
P_IGNORED_MODS  = [X.LockMask, X.Button1Mask, X.Button3Mask]
P_TOCLEAN_MODS  = X.LockMask | X.Button1Mask | X.Button3Mask
P_IGNORED_COMBO = [0, X.LockMask, X.Button1Mask, X.Button1Mask | X.LockMask, X.Button3Mask, X.Button3Mask | X.LockMask]



# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  S H O R T C U T
#
#   Manages shortcuts directly from XLib instead of going through Qt. This allows really global shortcuts to be
#   used. Uses χHelper's Xlib display connection.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χShortcut():
  _managedWindows: set = set()
  _hotkeys: dict = {}
  daemonStopFlag: threading.Event = None
  daemonThread: tStoppableThread = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def registerWindow(cls, winID: int):
    cls._managedWindows.add(winID)
    χPrint.debug(f"[χShortcut] registered managed window {winID}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def unregisterWindow(cls, winID: int):
    cls._managedWindows.discard(winID)
    χPrint.debug(f"[χShortcut] unregistered managed window {winID}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def clearExtraModifiers(modmask: int) -> int:
    return modmask & ~P_TOCLEAN_MODS

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   ⌖  S H O R T C U T S   D A E M O N
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @classmethod
  def startDaemon(cls):

    if cls.daemonThread and cls.daemonThread.is_alive():
      return
    cls.daemonStopFlag = threading.Event()

    def daemonLoop():
      χPrint.debug(f"[χShortcut] shortcuts daemon started")
      with χHelper._lock:
        χHelper.root.change_attributes(event_mask=X.KeyPressMask)
      while not cls.daemonStopFlag.is_set():
        with χHelper._lock:
          has_events = χHelper.disp.pending_events()
        if has_events:
          with χHelper._lock:
            event = χHelper.disp.next_event()
          if event.type == X.KeyPress:
            modmask = χShortcut.clearExtraModifiers(event.state)
            keycode = event.detail
            try:
              focus = χHelper.disp.get_input_focus().focus
              if focus.id not in cls._managedWindows:
                χHelper.disp.allow_events(X.ReplayKeyboard, X.CurrentTime)
                χHelper.disp.sync()
                continue
            except Exception:
              pass
            with χHelper._lock:
              callback = cls._hotkeys.get((modmask, keycode))
            if callback: callback()
        else:
          time.sleep(0.01)
      χPrint.debug(f"[χShortcut] shortcuts daemon stopped")

    cls.daemonThread = tStoppableThread(stopper=cls.daemonStopFlag, target=daemonLoop, daemon=True)
    cls.daemonThread.start()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def stopDaemon(cls):
    if cls.daemonStopFlag:
      cls.daemonStopFlag.set()
    if cls.daemonThread:
      cls.daemonThread.join(timeout=2.0)
      cls.daemonThread = None
    with χHelper._lock:
      for (modmask, keycode) in list(cls._hotkeys.keys()):
        try:    cls.ungrabKey(modmask, keycode)
        except: pass
      cls._hotkeys.clear()
      χHelper.disp.sync()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def forceCleanup(cls):
    if cls.daemonStopFlag:
      cls.daemonStopFlag.set()
    with χHelper._lock:
      try:
        for keycode in range(8, 256):
          for modmask in range(0, 256):
            χHelper.root.ungrab_key(keycode, modmask)
        χHelper.disp.ungrab_keyboard(X.CurrentTime)
        χHelper.disp.sync()
        cls._hotkeys.clear()
        cls._managedWindows.clear()
      except:
        pass
    if cls.daemonThread:
      cls.daemonThread.join(timeout=2.0)
      cls.daemonThread = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def grabKey(cls, modmask, keycode):
    with χHelper._lock:
      for extra in P_IGNORED_COMBO:
        χHelper.root.grab_key(keycode, modmask | extra, True, X.GrabModeAsync, X.GrabModeAsync)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def ungrabKey(cls, modmask, keycode):
    with χHelper._lock:
      for extra in P_IGNORED_COMBO:
        χHelper.root.ungrab_key(keycode, modmask | extra)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  #  Converts a dictionary of hotkeys in the form { "Ctrl+Shift+X": callback } into a dictionary of
  #  {(modmask, keycode) : callback }
  @classmethod
  def _parseHotkeyMap(cls, hotkeys: dict) -> dict:
    parsed = {}
    for keystring, callback in hotkeys.items():
      seq = χHelper.parseKeystring(keystring)
      if not seq or len(seq) > 1:
        χPrint.error(f"[χShortcut] invalid hotkey \"{keystring}\"")
        continue
      item = seq[0]
      modmask = 0
      for m in item['mods']: modmask |= χHelper.MODIFIER_MASKS[m]
      keycode = χHelper.getKeyCode(item['key'])
      parsed[(modmask, keycode)] = callback
    return parsed

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  #  Because of the way Milvian does consolidation, we rarely have a single hotkey. 
  #  This function basically registers a bunch of hotkeys at once, passed by dictionary
  @classmethod
  def updateHotkeys(cls, hotkeys: dict):
    newMap = cls._parseHotkeyMap(hotkeys)
    oldKeys = set(cls._hotkeys.keys())
    newKeys = set(newMap.keys())

    for modmask, keycode in (oldKeys - newKeys):
      try:    cls.ungrabKey(modmask, keycode)
      except: pass
    for modmask, keycode in (newKeys - oldKeys):
      try:    cls.grabKey(modmask, keycode)
      except Exception as e:
        χPrint.error(f"[χShortcut] failed to grab key ({modmask}, {keycode})", e)

    with χHelper._lock:
      cls._hotkeys = newMap
      χHelper.disp.sync()
    χPrint.debug(f"[χShortcut] hotkeys updated: {len(hotkeys)} active ({len(newKeys - oldKeys)} added, {len(oldKeys - newKeys)} removed)")
