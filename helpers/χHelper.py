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
from Xlib import X, display
import Xlib.error
import Xlib.protocol.event
import Xlib.Xutil
import time, re, threading, json, subprocess
from helpers.χPrint import χPrint
from helpers.χDispatcher import χDispatcher
from helpers.μStrings import μString
import os

P_DEFAULT_SLEEP = 0.05
P_DEFAULT_KEYSYM = '/usr/include/X11/keysymdef.h'


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _parseKeysymHeader(filename):
  keysyms = {}
  with open(filename, 'r') as f:
    content = f.read()
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    for line in content.split('\n'):
      line = line.strip()
      if not line: continue
      if line.startswith('//'): continue
      line = line.split()
      if line[0]=="#define":
        if len(line[1])>4: line[1] = line[1].lower() # different keysyms for XK_A and XK_a
        keysyms[line[1][3:]] = int(line[2],16)

  for s in ["_l", "_r"]:
    keysyms[f"ctrl{s}"] = keysyms[f"control{s}"]
    keysyms[f"win{s}"] = keysyms[f"super{s}"]
    keysyms[f"windows{s}"] = keysyms[f"super{s}"]

  for m in ['alt','shift','control','meta','super','win','windows','ctrl']:
    keysyms[f"{m}"]  = keysyms[f"{m}_l"]
    keysyms[f"l{m}"] = keysyms[f"{m}_l"]
    keysyms[f"{m}l"] = keysyms[f"{m}_l"]
    keysyms[f"r{m}"] = keysyms[f"{m}_r"]
    keysyms[f"{m}r"] = keysyms[f"{m}_r"]

  keysyms["altgr"] = keysyms["alt_r"]
  keysyms["enter"]  = keysyms["return"]
  return keysyms

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _buildModifiers():
  mkeys = []
  mmask = {
    'shift':   X.ShiftMask,
    'ctrl':    X.ControlMask,
    'alt':     X.Mod1Mask,
    'super':   X.Mod5Mask,
    'win':     X.Mod4Mask,
    'meta':    X.Mod3Mask,
  }
  mmask['control'] = mmask['ctrl']
  mmask['windows'] = mmask['super']
  mods = [k for k in mmask.keys()]
  for m in mods:
    mkeys.append(f"{m}")
    mkeys.append(f"l{m}")
    mkeys.append(f"{m}l")
    mkeys.append(f"{m}_l")
    mkeys.append(f"r{m}")
    mkeys.append(f"{m}r")
    mkeys.append(f"{m}_r")

    mmask[f"l{m}"]  = mmask[m]
    mmask[f"{m}l"]  = mmask[m]
    mmask[f"{m}_l"] = mmask[m]
    mmask[f"r{m}"]  = mmask[m]
    mmask[f"{m}r"]  = mmask[m]
    mmask[f"{m}_r"] = mmask[m]
  mkeys.append('altgr')
  mkeys.append('mod1')
  mkeys.append('mod2')
  mkeys.append('mod3')
  mkeys.append('mod4')
  mkeys.append('mod5')
  mmask['altgr'] = mmask['alt']
  mmask['mod1']  = X.Mod1Mask
  mmask['mod2']  = X.Mod2Mask
  mmask['mod3']  = X.Mod3Mask
  mmask['mod4']  = X.Mod4Mask
  mmask['mod5']  = X.Mod5Mask
  return mkeys, mmask

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
class windowData():
  posx = 0
  posy = 0
  width = 0
  height = 0
  desktop = 0
  borderless = True
  audio = True
  log = False

  def __init__(self, info : list):
    if len(info)>0: self.posx    = info[0]
    if len(info)>1: self.posy    = info[1]
    if len(info)>2: self.width   = info[2]
    if len(info)>3: self.height  = info[3]
    if len(info)>4: self.desktop = info[4]
    if len(info)>5: self.borderless = info[5]
    if len(info)>6: self.audio   = info[6]
    if len(info)>7: self.log     = info[7]


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  X H E L P E R 
#                                  
#   This is a static class. Don't instantiate it.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χHelper():
  KEYSYM = _parseKeysymHeader(P_DEFAULT_KEYSYM)
  MODIFIERS, MODIFIER_MASKS = _buildModifiers()
  disp : display.Display = None
  root = None
  netWMPID = None
  netClientList = None
  netActiveWindow = None
  netWMName = None
  WMName = None
  utf8String = None
  netWMDesktop = None
  _lock = threading.RLock()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setup(cls):
    cls.disp = display.Display()
    cls.root = cls.disp.screen().root
    cls.netWMPID = cls.disp.intern_atom('_NET_WM_PID')
    cls.netClientList = cls.disp.intern_atom('_NET_CLIENT_LIST')
    cls.netActiveWindow = cls.disp.intern_atom('_NET_ACTIVE_WINDOW')
    cls.netWMName = cls.disp.intern_atom('_NET_WM_NAME')
    cls.WMName = cls.disp.intern_atom('WM_NAME')
    cls.utf8String = cls.disp.intern_atom('UTF8_STRING')
    cls.netWMDesktop = cls.disp.intern_atom('_NET_WM_DESKTOP')
    cls.disp.set_error_handler(lambda d, e: None)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getKeySym(cls, key : str) -> int:
    return cls.KEYSYM[key]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def keySym2Code(cls, keysym : int) -> int:
    with cls._lock: return cls.disp.keysym_to_keycode(keysym)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getKeyCode(cls, key : str) -> int:
    with cls._lock: return cls.disp.keysym_to_keycode(cls.KEYSYM[key])

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def waitWinID(cls, pid, timeout = 0.0) -> list:
    pid = int(pid)
    disp  = display.Display()
    root  = disp.screen().root
    netClientList = disp.intern_atom('_NET_CLIENT_LIST')
    netWMPID      = disp.intern_atom('_NET_WM_PID')
    try:
      while True:
        winIDList = []
        clientList = root.get_full_property(netClientList, X.AnyPropertyType)
        if clientList:
          for winID in clientList.value:
            win = disp.create_resource_object('window', winID)
            try:
              pid_prop = win.get_full_property(netWMPID, X.AnyPropertyType)
              if pid_prop and pid_prop.value and pid_prop.value[0] == pid:
                winIDList.append(winID)
            except:
              continue
        if winIDList:
          return winIDList
        elif timeout > 0.0:
          timeout -= P_DEFAULT_SLEEP
          time.sleep(P_DEFAULT_SLEEP)
        else:
          χPrint.info(f"[XHelper] no window ID found for pid={pid}")
          return None
    finally:
      disp.close()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWinID(cls, pid) -> list:
    if isinstance(pid,str) and not pid.isdigit(): return None
    with cls._lock:
      pid = int(pid)
      winIDList = []
      clientList = cls.root.get_full_property(cls.netClientList, X.AnyPropertyType)
      if not clientList:
        χPrint.error("[XHelper.tryWinID] no windows founds at all!")
        return None
      for winID in clientList.value:
        win = cls.disp.create_resource_object('window', winID)
        try:
          pid_prop = win.get_full_property(cls.netWMPID, X.AnyPropertyType)
          if pid_prop and pid_prop.value and pid_prop.value[0] == pid:
            winIDList.append(winID)
        except:
          continue
      return winIDList if winIDList else None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getFocusedWindow(cls):
    disp = display.Display()
    try:
      focus = disp.get_input_focus().focus
      return focus.id if focus else None
    except:
      return None
    finally:
      disp.close()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getFocusedPID(cls) -> int:
    disp = display.Display()
    try:
      focus = disp.get_input_focus().focus
      if not focus: return None
      netWMPID = disp.intern_atom('_NET_WM_PID')
      prop = focus.get_full_property(netWMPID, X.AnyPropertyType)
      return int(prop.value[0]) if prop and prop.value else None
    except:
      return None
    finally:
      disp.close()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def remapWindow(cls, winID):
    with cls._lock:
      win = cls.disp.create_resource_object('window', winID)
      win.unmap()
      cls.disp.flush()
    time.sleep(0.05)
    with cls._lock:
      win.map()
      cls.disp.flush()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setBorderless(cls, winID):
    cls.setWindowHint(winID, flags=2, decoration=0)
    for _ in range(5):
      time.sleep(P_DEFAULT_SLEEP)
      hint = cls.getWindowHint(winID)
      if hint and hint.get('decorations', 1) == 0:
        return True
    χPrint.warning(f"[χHelper] setBorderless: window {winID} not confirmed borderless")
    return False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setBorderyes(cls, winID):
    cls.setWindowHint(winID, flags=2, decoration=126)
    for _ in range(5):
      time.sleep(P_DEFAULT_SLEEP)
      hint = cls.getWindowHint(winID)
      if hint and hint.get('decorations', 1) != 0:
        return True
    χPrint.warning(f"[χHelper] setBorderyes: window {winID} not confirmed bordered")
    return False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setWindowHint(cls, winID, flags=2, functions=0, decoration=0, input_mode=0):
    with cls._lock:
      window = cls.disp.create_resource_object('window', winID)
      motif_wm_hints = cls.disp.intern_atom('_MOTIF_WM_HINTS')
      hints_data = [ flags, functions, decoration, input_mode, 0 ]
      window.change_property(motif_wm_hints, motif_wm_hints, 32, hints_data, mode=X.PropModeReplace)
      cls.disp.flush()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWindowHint(cls, winID) -> dict:
    with cls._lock:
      window = cls.disp.create_resource_object('window', winID)
      motif_wm_hints = cls.disp.intern_atom('_MOTIF_WM_HINTS')
      try:
        prop = window.get_full_property(motif_wm_hints, X.AnyPropertyType)
      except Exception as e:
        χPrint.warning(f"[χHelper] getWindowHint({winID}) failed", e)
        return None
      if prop and prop.value:
        values = prop.value
        if len(values) >= 5:
            return {
                'flags': values[0],
                'functions': values[1],
                'decorations': values[2],
                'input_mode': values[3],
                'status': values[4]
            }
        else:
          print(f"Warning: MOTIF hints has {len(values)} values (expected 5)")
          return {'raw': values}
      else:
        χPrint.error(f"[xHelper.getWindowHint] window {winID} has no MOTIF WM hints property")
        return None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def focusWindow(cls, winID) -> None:
    with cls._lock:
      win = cls.disp.create_resource_object('window', winID)
      win.set_input_focus(X.RevertToParent, X.CurrentTime)
      win.map()
      cls.disp.sync()
    time.sleep(P_DEFAULT_SLEEP)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWindowTitle(cls, winId) -> str:
    disp = display.Display()
    try:
      win = disp.create_resource_object('window', winId)
      netWMName = disp.intern_atom('_NET_WM_NAME')
      WMName    = disp.intern_atom('WM_NAME')
      prop = win.get_full_property(netWMName, X.AnyPropertyType)
      if prop: return prop.value.decode('utf-8')
      prop = win.get_full_property(WMName, X.AnyPropertyType)
      if prop: return prop.value.decode('utf-8')
      return None
    except:
      return None
    finally:
      disp.close()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWinIDByName(cls, name: str) -> list:
    with cls._lock:
      clientList = cls.root.get_full_property(cls.netClientList, X.AnyPropertyType)
      if not clientList: return []
      results = []
      for winID in clientList.value:
        win = cls.disp.create_resource_object('window', winID)
        try:
          prop = win.get_full_property(cls.netWMName, X.AnyPropertyType)
          title = μString(prop.value.decode('utf-8')) if prop else None
          if title is None:
            prop = win.get_full_property(cls.WMName, X.AnyPropertyType)
            title = μString(prop.value.decode('utf-8')) if prop else None
          if title and title == name:
            results.append(winID)
        except:
          continue
      return results

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def iconify(cls, winID, val: bool = None) -> None:
    with cls._lock:
      win = cls.disp.create_resource_object('window', winID)
      if val is None:
        val = win.get_attributes().map_state == X.IsViewable
      if val:
        netChangeState = cls.disp.intern_atom('WM_CHANGE_STATE')
        event = Xlib.protocol.event.ClientMessage(
          window      = win,
          client_type = netChangeState,
          data        = (32, [Xlib.Xutil.IconicState, 0, 0, 0, 0])
        )
        cls.root.send_event(event, event_mask=X.SubstructureNotifyMask | X.SubstructureRedirectMask)
      else:
        event = Xlib.protocol.event.ClientMessage(
          window      = win,
          client_type = cls.netActiveWindow,
          data        = (32, [1, X.CurrentTime, 0, 0, 0])
        )
        cls.root.send_event(event, event_mask=X.SubstructureNotifyMask | X.SubstructureRedirectMask)
      cls.disp.sync()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def parseKeystring(cls, string) -> list:
    seq = []
    string = ' '.join(string.lower().split())
    string = string.replace(" + ","+")
    string = string.replace("+ ","+")
    string = string.replace(" +","+")
    string = string.lower().split()

    for t in string:
      if '+' in t:
        t = t.split('+')
        for m in t[:-1]:
          if m not in cls.MODIFIERS:
            raise Exception(f" ERROR in XHelper: invalid modifier \"{m}\"")
        seq.append({'mods': t[:-1], 'key': t[-1]})
      else:
        seq.append({'mods': [], 'key': t})

    return seq

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def execute(cls, script, winID = None) -> None:
    if winID: cls.focusWindow(winID)

    for item in script:
      if callable(item):
        item()
        time.sleep(0.1)
      elif item.startswith("sleep") or item.startswith("delay"):
        time.sleep(float(item[6:]))
      elif item.startswith("focus"):
        cls.focusWindow(int(item[6:]))
      elif item.startswith("point"):
        cls.focusWindow(int(item[6:]))
      elif item.startswith("click"):
        cls.sendClick(int(item[6:]))
      else:
        cls.sendKeystroke(cls.parseKeystring(item))

      with cls._lock: cls.disp.sync()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def sendKeystroke(cls, item) -> None:
    with cls._lock:
      for mod in item['mods']:
        if mod not in cls.MODIFIERS:
          raise Exception(f" ERROR in XHelper.sendKeystrokes: invalid modifier \"{item['mod']}\"")
        cls.disp.xtest_fake_input(X.KeyPress, cls.getKeyCode(mod))

      keycode = cls.getKeyCode(item['key'])
      if keycode:
        cls.disp.xtest_fake_input(X.KeyPress, keycode)
        cls.disp.xtest_fake_input(X.KeyRelease, keycode)
      else:
        raise Exception(f" ERROR in XHelper.sendKeystrokes: invalid key \"{item['key']}\"")

      for mod in reversed(item['mods']):
        cls.disp.xtest_fake_input(X.KeyRelease, cls.getKeyCode(mod))

      cls.disp.sync()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def sendClick(cls, button, winID = None, delay=None):
    if winID:
      cls.focusWindow(winID)
    try:
      with cls._lock:
        cls.disp.xtest_fake_input(X.ButtonPress, button)
      if delay: time.sleep(delay)
      with cls._lock:
        cls.disp.xtest_fake_input(X.ButtonRelease, button)
        cls.disp.sync()
      return True
    except:
      return False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def sendPointTo(cls, rel_x, rel_y, winID):
    try:
      geo = cls.getWindowGeometry(winID)
      if not geo: return
      abs_x = geo[0] + rel_x
      abs_y = geo[1] + rel_y
      with cls._lock:
        cls.disp.xtest_fake_input(X.MotionNotify, x=abs_x, y=abs_y)
        cls.disp.sync()
    except:
      pass

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def clickInWindow(cls, button, rel_x, rel_y, winID, delay=None):
    try:
      geo = cls.getWindowGeometry(winID)
      if not geo: return False
      abs_x = geo[0] + rel_x
      abs_y = geo[1] + rel_y
      with cls._lock:
        cls.disp.xtest_fake_input(X.MotionNotify, x=abs_x, y=abs_y)
        cls.disp.xtest_fake_input(X.ButtonPress, button)
      if delay: time.sleep(delay)
      with cls._lock:
        cls.disp.xtest_fake_input(X.ButtonRelease, button)
        cls.disp.sync()
      return True
    except:
      return False


  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWindowGeometry(cls, winID):
    with cls._lock:
      try:
        win = cls.disp.create_resource_object('window', winID)
        geometry = win.get_geometry()
        coords = win.translate_coords(cls.root, 0, 0)
        return [-coords.x, -coords.y, geometry.width, geometry.height]
      except Exception as e:
        # Window may be gone already (BadWindow/BadDrawable); normal after a game dies
        χPrint.warning(f"[χHelper] getWindowGeometry({winID}) failed", e)
        return None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWindowsData(cls, winID) -> windowData:
    geo = cls.getWindowGeometry(winID)
    if geo is None: return None
    winData = windowData(geo)
    winData.desktop = cls.getWindowsVirtualDesktop(winID) or 0
    winData.borderless = cls.getWindowsBorder(winID)
    winData.audio = not cls.audioQueryMuted(cls.getPID(winID))
    return winData

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _getToplevel(cls, winID):
    with cls._lock:
      win = cls.disp.create_resource_object('window', winID)
      while True:
        parent = win.query_tree().parent
        if parent.id == cls.root.id:
          return win
        win = parent

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWindowsVirtualDesktop(cls, winID) -> int:
    with cls._lock:
      try:
        win = cls._getToplevel(winID)
        prop = win.get_full_property(cls.netWMDesktop, X.AnyPropertyType)
        return int(prop.value[0]) if prop and prop.value else 0
      except Exception as e:
        χPrint.warning(f"[χHelper] getWindowsVirtualDesktop({winID}) failed", e)
        return None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getWindowsBorder(cls, winID) -> bool:
    try:
      hint = cls.getWindowHint(winID)
      if hint is None: return True
      return bool(hint.get('decorations', 1))
    except Exception as e:
      χPrint.warning(f"[χHelper] getWindowsBorder({winID}) failed", e)
      return True

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getPID(cls, winID) -> int:
    with cls._lock:
      try:
        win = cls.disp.create_resource_object('window', winID)
        prop = win.get_full_property(cls.netWMPID, X.AnyPropertyType)
        return int(prop.value[0]) if prop and prop.value else 0
      except Exception as e:
        χPrint.warning(f"[χHelper] getPID({winID}) failed", e)
        return 0

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def moveVirtualDesktop(cls, winID, targetDesktop: int):
    try:
      with cls._lock:
        win = cls.disp.create_resource_object('window', winID)
        atom = cls.disp.intern_atom('_NET_WM_DESKTOP')
        evt = Xlib.protocol.event.ClientMessage(
          window=win,
          client_type=atom,
          data=(32, [targetDesktop, 2, 0, 0, 0])
        )
        cls.root.send_event(evt, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        cls.disp.sync()
      for _ in range(5):
        time.sleep(P_DEFAULT_SLEEP)
        if cls.getWindowsVirtualDesktop(winID) == targetDesktop:
          return True
      χPrint.warning(f"[χHelper] moveVirtualDesktop: window {winID} not confirmed on desktop {targetDesktop}")
      return False
    except Exception as e:
      χPrint.warning(f"[χHelper] moveVirtualDesktop({winID},{targetDesktop}) failed", e)
      return False

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def moveWindow(cls, winID, x, y):
    try:
      with cls._lock:
        win = cls.disp.create_resource_object('window', winID)
        win.configure(x=x, y=y)
        cls.disp.sync()
      for _ in range(5):
        time.sleep(P_DEFAULT_SLEEP)
        geo = cls.getWindowGeometry(winID)
        if geo and geo[0] == x and geo[1] == y:
          return True
      χPrint.warning(f"[χHelper] moveWindow: window {winID} not confirmed at ({x},{y})")
      return False
    except Exception as e:
      χPrint.warning(f"[χHelper] moveWindow({winID},{x},{y}) failed", e)
      return False

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   ⌖  A U D I O 
  #      
  #      Actually uses pipewirectl (wpctl) to control audio for a given process ID. Maybe move to a different
  #      module in the future
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @staticmethod
  def audioToggle(pid):
    subprocess.run(["wpctl", "set-mute", "-p", str(pid), "toggle"], stderr=subprocess.DEVNULL)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def audioMute(pid):
    subprocess.run(["wpctl", "set-mute", "-p", str(pid), "1"], stderr=subprocess.DEVNULL)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def audioUnmute(pid):
    subprocess.run(["wpctl", "set-mute", "-p", str(pid), "0"], stderr=subprocess.DEVNULL)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def audioQueryMuted(pid) -> bool:
    try:
      output = subprocess.check_output(['pw-dump'], text=True, stderr=subprocess.DEVNULL)
      alldata = json.loads(output)
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as e:
      χPrint.warning(f"[χHelper.audioQueryMuted] pw-dump failed", e)
      return False
    for i in alldata:
      if not str(i.get('type','')).endswith("Node"): continue
      info  = i.get('info')  or {}
      props = info.get('props') or {}
      if str(pid) != str(props.get('application.process.id','')): continue
      params = info.get('params') or {}
      for p in params.get('Props') or []:
        if isinstance(p, dict) and 'mute' in p:
          return str(p['mute']).lower()=='true'
    return False
