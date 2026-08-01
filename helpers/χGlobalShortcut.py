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
from helpers.μPrint import χPrint

# This is used so that key grabs are insensitive to the following modifiers and their combinations:
#  - capslock
#  - left and right mouse button
P_EXTRA_MOD_MASKS = [0, X.LockMask, X.Button1Mask, X.Button1Mask | X.LockMask, X.Button3Mask, X.Button3Mask | X.LockMask]


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  G L O B A L   S H O R T C U T
#
#   Manages shortcuts directly from XLib instead of going through Qt. This allows really global shortcuts to be
#   used. Uses χHelper's Xlib display connection.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χGlobalShortcut():
  _managedWindows: set = set()
  _hotkeys: dict = {}
  daemonStopFlag: threading.Event = None
  daemonThread: tStoppableThread = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def registerWindow(cls, winID: int):
    cls._managedWindows.add(winID)
    χPrint.debug(f"[χGlobalShortcut] registered managed window {winID}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def unregisterWindow(cls, winID: int):
    cls._managedWindows.discard(winID)
    χPrint.debug(f"[χGlobalShortcut] unregistered managed window {winID}")

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   ⌖  S H O R T C U T S   D A E M O N
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @classmethod
  def startDaemon(cls):
    if cls.daemonThread and cls.daemonThread.is_alive():
      return
    cls.daemonStopFlag = threading.Event()

    def daemonLoop():
      χPrint.debug(f"[χGlobalShortcut] shortcuts daemon started")
      with χHelper._lock:
        χHelper.root.change_attributes(event_mask=X.KeyPressMask)
      while not cls.daemonStopFlag.is_set():
        with χHelper._lock:
          has_events = χHelper.disp.pending_events()
        if has_events:
          with χHelper._lock:
            event = χHelper.disp.next_event()
          if event.type == X.KeyPress:
            try:
              focus = χHelper.disp.get_input_focus().focus
              if focus.id not in cls._managedWindows:
                χHelper.disp.allow_events(X.ReplayKeyboard, X.CurrentTime)
                χHelper.disp.sync()
                continue
            except Exception:
              pass
            with χHelper._lock:
              callback = cls._hotkeys.get((event.state, event.detail))
            if callback: callback()
        else:
          time.sleep(0.01)
      χPrint.debug(f"[χGlobalShortcut] shortcuts daemon stopped")

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
      for extra in P_EXTRA_MOD_MASKS:
        χHelper.root.grab_key(keycode, modmask | extra, True, X.GrabModeAsync, X.GrabModeAsync)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def ungrabKey(cls, modmask, keycode):
    with χHelper._lock:
      for extra in P_EXTRA_MOD_MASKS:
        χHelper.root.ungrab_key(keycode, modmask | extra)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _parseHotkeyMap(cls, hotkeys: dict) -> dict:
    parsed = {}
    for keystring, callback in hotkeys.items():
      seq = χHelper._parseKeystring(keystring)
      if not seq or len(seq) > 1:
        χPrint.error(f"[χGlobalShortcut] invalid hotkey \"{keystring}\"")
        continue
      item = seq[0]
      modmask = 0
      for m in item['mods']: modmask |= χHelper.MODIFIER_MASKS[m]
      keycode = χHelper.getKeyCode(item['key'])
      for extra in P_EXTRA_MOD_MASKS:
        parsed[(modmask | extra, keycode)] = callback
    return parsed

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def updateHotkeys(cls, hotkeys: dict):
    newMap = cls._parseHotkeyMap(hotkeys)
    oldKeys = set(cls._hotkeys.keys())
    newKeys = set(newMap.keys())

    oldBase = {(m & ~0x502, k) for m, k in oldKeys}
    newBase = {(m & ~0x502, k) for m, k in newKeys}

    for modmask, keycode in (oldBase - newBase):
      try:    cls.ungrabKey(modmask, keycode)
      except: pass
    for modmask, keycode in (newBase - oldBase):
      try:    cls.grabKey(modmask, keycode)
      except Exception as e:
        χPrint.error(f"[χGlobalShortcut] failed to grab key ({modmask}, {keycode})", e)

    with χHelper._lock:
      cls._hotkeys = newMap
      χHelper.disp.sync()
    χPrint.debug(f"[χGlobalShortcut] hotkeys updated: {len(hotkeys)} active ({len(newBase - oldBase)} added, {len(oldBase - newBase)} removed)")
