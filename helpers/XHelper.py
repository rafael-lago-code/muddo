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
from PyQt6.QtCore import QObject, pyqtSignal
from Xlib import X, display
import Xlib.error
import Xlib.protocol.event
import time, re, threading, json, subprocess
from helpers.tStoppableThread import tStoppableThread
from helpers.cPrint import cPrint

P_DEFAULT_SLEEP = 0.05
P_DEFAULT_KEYSYM = '/usr/include/X11/keysymdef.h'

#----------------------------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------------------------
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



#---------------------------------------------------------------------------------------------------------------
#
#
#                                            X H E L P E R
#                                  
#   TODO MAKE THIS STATIC!!! Need to remove __init__ and put it somewhere else
#   TODO get rid of Qt requirement (i.e. pyqtSignal) and use cDispatcher instead
#---------------------------------------------------------------------------------------------------------------
class XHelper(QObject):
  sigGotWinID = pyqtSignal((int,list))
  KEYSYM = _parseKeysymHeader(P_DEFAULT_KEYSYM) 
  MODIFIERS, MODIFIER_MASKS = _buildModifiers()

  #----------------------------------------------------------------------------------------------------------
  def __init__(self):
    super().__init__()
    self.disp = display.Display()
    self.root : display.Window = self.disp.screen().root
    self.netWMPID = self.disp.intern_atom('_NET_WM_PID')
    self.netClientList = self.disp.intern_atom('_NET_CLIENT_LIST')
    self.netActiveWindow = self.disp.intern_atom('_NET_ACTIVE_WINDOW')
    self.netWMName = self.disp.intern_atom('_NET_WM_NAME')
    self.WMName = self.disp.intern_atom('WM_NAME')
    self.utf8String = self.disp.intern_atom('UTF8_STRING')
    self.netWMDesktop = self.disp.intern_atom('_NET_WM_DESKTOP')
    self.disp.set_error_handler(lambda d, e: None)

  #----------------------------------------------------------------------------------------------------------
  def getKeySym(self, key : str) -> int:
    return self.KEYSYM[key]
  
  #----------------------------------------------------------------------------------------------------------
  def keySym2Code(self, keysym : int) -> int:
    return self.disp.keysym_to_keycode(keysym)
  
  #----------------------------------------------------------------------------------------------------------
  def getKeyCode(self, key : str) -> int:
    return self.disp.keysym_to_keycode(self.KEYSYM[key])
    # return self.keySym2Code(self.getKeySym(key))  # why complicating things?!
  
  #----------------------------------------------------------------------------------------------------------
  def waitWinID(self, pid, timeout = 0.0) -> list:
    pid = int(pid)
    while True:
      winIDList = self.getWinID(pid)
      
      if winIDList:
        return winIDList
      elif timeout > 0.0:
        timeout -= P_DEFAULT_SLEEP
        time.sleep(P_DEFAULT_SLEEP)
        continue
      else:
        cPrint.info(f"[XHelper.getWinID] no window found {f'(timeout={timeout})' if timeout>0.0 else ''}")
        return None
      
  #----------------------------------------------------------------------------------------------------------
  def getWinID(self, pid) -> list:
    pid = int(pid)
    winIDList = []
    clientList = self.root.get_full_property(self.netClientList, X.AnyPropertyType)

    if not clientList:
      cPrint.error("[XHelper.tryWinID] no windows founds at all!")
      return None

    for winID in clientList.value:
      win = self.disp.create_resource_object('window', winID)
      try:
        pid_prop = win.get_full_property(self.netWMPID, X.AnyPropertyType)
        if pid_prop and pid_prop.value and pid_prop.value[0] == pid:
          winIDList.append(winID)
      except:
        continue
    
    if winIDList:
      self.sigGotWinID.emit(pid,winIDList)
      return winIDList
    else:
      return None
  
  #----------------------------------------------------------------------------------------------------------
  def getFocusedWindow(self):
    try:
      focus = self.disp.get_input_focus().focus
      return focus.id if focus else None
    except:
      return None
  
  #----------------------------------------------------------------------------------------------------------
  def requestWinID(self, pid, timeout = 0.0):
    t = threading.Thread(target=self.waitWinID, args=(pid,timeout), daemon=True)
    t.start()

  #----------------------------------------------------------------------------------------------------------
  def remapWindow(self, winID):
    win = self.disp.create_resource_object('window', winID)
    win.unmap()
    self.disp.flush()
    time.sleep(0.05)
    win.map()

    self.disp.flush()

  #----------------------------------------------------------------------------------------------------------
  def setBorderless(self, winID):
    self.setWindowHint(winID,flags=2,decoration=0)

  #----------------------------------------------------------------------------------------------------------
  def setBorderyes(self, winID):
    self.setWindowHint(winID,flags=2,decoration=126)

  #----------------------------------------------------------------------------------------------------------
  def setWindowHint(self, winID, flags=2, functions=0, decoration=0, input_mode=0):
    # flag values:
    #----------------------------
    # FUNCTIONS_FLAG   = 1 << 0  # 1 in decimal - Apply functions setting
    # DECORATIONS_FLAG = 1 << 1  # 2 in decimal - Apply decorations setting
    # INPUT_MODE_FLAG  = 1 << 2  # 4 in decimal - Apply input mode setting
    #
    # function values:
    #----------------------------
    # ALL_FUNCTIONS     = 0xFFFFFFFF  # Allow everything
    # NO_FUNCTIONS      = 0x00000000  # Allow nothing
    # FUNC_RESIZE       = 1 << 0  # 1 - Allow resizing
    # FUNC_MOVE         = 1 << 1  # 2 - Allow moving  
    # FUNC_MINIMIZE     = 1 << 2  # 4 - Show minimize button
    # FUNC_MAXIMIZE     = 1 << 3  # 8 - Show maximize button
    # FUNC_CLOSE        = 1 << 4  # 16 - Show close button
    #
    # decoration values:
    #----------------------------
    # ALL_DECORATIONS   = 0xFFFFFFFF  # Show everything
    # NO_DECORATIONS    = 0x00000000  # Show nothing (borderless!)
    # DECOR_BORDER      = 1 << 0  # 1 - Show window border
    # DECOR_TITLE       = 1 << 1  # 2 - Show title bar
    # DECOR_MENU        = 1 << 2  # 4 - Show window menu button
    # DECOR_MINIMIZE    = 1 << 3  # 8 - Show minimize button decoration
    # DECOR_MAXIMIZE    = 1 << 4  # 16 - Show maximize button decoration
    # DECOR_RESIZEH     = 1 << 5  # 32 - Show resize handles
    #
    # input_mode values:
    #----------------------------
    # INPUT_MODELESS      = 0  # Normal modeless window
    # INPUT_PRIMARY_APP   = 1  # Primary application modal
    # INPUT_SYSTEM_MODAL  = 2  # System modal (blocks everything)
    # INPUT_FULL_APP_MODAL = 3 # Full application modal

    window = self.disp.create_resource_object('window', winID)
    motif_wm_hints = self.disp.intern_atom('_MOTIF_WM_HINTS')

    hints_data = [ flags, functions, decoration, input_mode, 0 ]
    window.change_property(motif_wm_hints,
                           motif_wm_hints,
                           32,
                           hints_data,
                           mode=X.PropModeReplace)

    self.disp.flush()
  
  #----------------------------------------------------------------------------------------------------------
  def getWindowHint(self, winID) -> dict:
    window = self.disp.create_resource_object('window', winID)
    motif_wm_hints = self.disp.intern_atom('_MOTIF_WM_HINTS')

    prop = window.get_full_property(motif_wm_hints, X.AnyPropertyType)
    
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
      cPrint.error(f"[xHelper.getWindowHint] window {winID} has no MOTIF WM hints property")
      return None
      
  #----------------------------------------------------------------------------------------------------------
  def focusWindow(self, winID) -> None:
    win = self.disp.create_resource_object('window', winID)
    win.set_input_focus(X.RevertToParent, X.CurrentTime)
    win.map()
    self.disp.sync()
    time.sleep(P_DEFAULT_SLEEP)  # Let WM process

  #----------------------------------------------------------------------------------------------------------
  def getWindowTitle(self, winId) -> str:
    try:
        win = self.disp.create_resource_object('window', winId)
        title_prop = win.get_full_property(self.netWMName, X.AnyPropertyType)
        if title_prop:
            return title_prop.value.decode('utf-8')
        
        title_prop = win.get_full_property(self.WMName, X.AnyPropertyType)
        if title_prop:
            return title_prop.value.decode('utf-8')  # or Latin-1
        return None
    except:
        return None  # Any other error

  #----------------------------------------------------------------------------------------------------------
  def _parseKeystring(self, string) -> list:
    seq = []
    string = ' '.join(string.lower().split())
    string = string.replace(" + ","+")
    string = string.replace("+ ","+")
    string = string.replace(" +","+")
    string = string.lower().split()  # this will force XK_A = xk_a, so we loose a keycode here
    
    for t in string:
      if '+' in t:
        t = t.split('+')
        for m in t[:-1]:
          if m not in self.MODIFIERS:
            raise Exception(f" ERROR in XHelper: invalid modifier \"{m}\"")
        seq.append({'mods': t[:-1], 'key': t[-1]})
      else:
        seq.append({'mods': [], 'key': t})

    return seq

  #----------------------------------------------------------------------------------------------------------  
  def execute(self, script, winID = None) -> None:
    if winID:
      self.focusWindow(winID)
    
    # I'm confused by this parseKeyString and why I wrote it this way (the original argmuent was keystring, 
    # not script). Nevertheless, I don't think I'll need it with Milvian
    # if isinstance(keystring, list):
    #   seq = keystring
    # else:
    #   seq = self._parseKeystring(keystring)
          
    for item in script:
      # TODO: parse accepted commands properly
      if callable(item):
        item()
        time.sleep(0.1)
      elif item.startswith("sleep") or item.startswith("delay"):
        time.sleep(float(item[6:]))
        
      elif item.startswith("focus"):
        self.focusWindow(int(item[6:]))

      elif item.startswith("point"):
        self.focusWindow(int(item[6:]))
      
      elif item.startswith("click"):
        self.sendClick(int(item[6:]))
      else:
        self.sendKeystroke(self.__parseKeystring(item))
      
      self.disp.sync()

  #----------------------------------------------------------------------------------------------------------  
  def sendKeystroke(self, item) -> None:
    for mod in item['mods']:
      if mod not in self.MODIFIERS:
        raise Exception(f" ERROR in XHelper.sendKeystrokes: invalid modifier \"{item['mod']}\"")
      self.disp.xtest_fake_input(X.KeyPress, self.getKeyCode(mod))

    keycode = self.getKeyCode(item['key'])
    if keycode:
      self.disp.xtest_fake_input(X.KeyPress, keycode)
      self.disp.xtest_fake_input(X.KeyRelease, keycode)
    else:
      raise Exception(f" ERROR in XHelper.sendKeystrokes: invalid key \"{item['key']}\"")
    
    for mod in reversed(item['mods']):
      self.disp.xtest_fake_input(X.KeyRelease, self.getKeyCode(mod))
      
    self.disp.sync()
  
  #----------------------------------------------------------------------------------------------------------  
  def sendClick(self, button, winID = None, delay=None):
    if winID:
      self.focusWindow(winID)

    try:
      self.disp.xtest_fake_input(X.ButtonPress, button)
      if delay: time.sleep(delay)
      self.disp.xtest_fake_input(X.ButtonRelease, button)
      self.disp.sync()
      return True
    except:
      return False
    
  #----------------------------------------------------------------------------------------------------------  
  def sendPointTo(self, rel_x, rel_y, winID):
    try:
      geo = self.getWindowGeometry(winID)  # [x, y, width, height]
      if not geo: return
      
      # Calculate absolute screen coordinates
      abs_x = geo[0] + rel_x
      abs_y = geo[1] + rel_y
      
      self.disp.xtest_fake_input(X.MotionNotify, x=abs_x, y=abs_y)
      self.disp.sync()
    except:
      pass
  
  #----------------------------------------------------------------------------------------------------------  
  def clickInWindow(self, button, rel_x, rel_y, winID, delay=None):
    try:
      # Get window absolute position
      geo = self.getWindowGeometry(winID)  # [x, y, width, height]
      if not geo:
        return False
      
      # Calculate absolute screen coordinates
      abs_x = geo[0] + rel_x
      abs_y = geo[1] + rel_y
      
      # Move and click
      self.disp.xtest_fake_input(X.MotionNotify, x=abs_x, y=abs_y)
      self.disp.xtest_fake_input(X.ButtonPress, button)
      if delay: time.sleep(delay)
      self.disp.xtest_fake_input(X.ButtonRelease, button)
      self.disp.sync()
      return True
    except:
      return False
  
  #----------------------------------------------------------------------------------------------------------
  def getShortcutsDaemon(self, hotkeys : dict) -> tStoppableThread:
    grabbed = {}
    for keystring, callback in hotkeys.items():
      seq = self._parseKeystring(keystring)
      if not seq or len(seq) > 1:
        raise Exception(f"Error in XHelper.getShortcutsDaemon: invalid hotkey \"{keystring}\"")
      
      item = seq[0]
      modmask = 0
      for m in item['mods']:
        modmask |= self.MODIFIER_MASKS[m]
      keycode = self.getKeyCode(item['key'])
      
      # Grab key on root window
      try:
        self.root.grab_key( keycode, modmask, True, X.GrabModeAsync, X.GrabModeAsync )
        grabbed[(modmask, keycode)] = callback
        self.root.grab_key( keycode, modmask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync )
        grabbed[(modmask | X.LockMask, keycode)] = callback
        self.root.grab_key( keycode, modmask | X.Button1Mask, True, X.GrabModeAsync, X.GrabModeAsync )
        grabbed[(modmask | X.Button1Mask, keycode)] = callback
        self.root.grab_key( keycode, modmask | X.Button1Mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync )
        grabbed[(modmask | X.Button1Mask | X.LockMask, keycode)] = callback
        self.root.grab_key( keycode, modmask | X.Button3Mask, True, X.GrabModeAsync, X.GrabModeAsync )
        grabbed[(modmask | X.Button3Mask, keycode)] = callback
        self.root.grab_key( keycode, modmask | X.Button3Mask | X.LockMask, True, X.GrabModeAsync, X.GrabModeAsync )
        grabbed[(modmask | X.Button3Mask | X.LockMask, keycode)] = callback
        cPrint.debug(f"[XHelper.getShortcutsDaemon:Debug] registered \"{keystring}\"")
      except Exception as e:
        cPrint.error(f"[XHelper.getShortcutsDaemon:Error]: failed to grab \"{keystring}\"\n{e}")
    
    if not grabbed:
      cPrint.debug(f"[XHelper.getShortcutsDaemon:Debug] no hotkeys passed!")
      return
    
    daemonStopSignal = threading.Event()
    
    def daemonLoop():
      cPrint.debug(f"[XHelper.getShortcutsDaemon:Debug] daemon started running")
      self.root.change_attributes(event_mask=X.KeyPressMask)
      
      # try:
      while not daemonStopSignal.is_set():
        if self.disp.pending_events():
          event = self.disp.next_event()
          if event.type == X.KeyPress:
            modmask = event.state
            keycode = event.detail
            
            callback = grabbed.get((modmask, keycode))
            if callback: callback()  # Direct call, no extra thread
        else:
          time.sleep(0.01)
      for (modmask, keycode), _ in grabbed.items():
        self.root.ungrab_key(keycode, modmask)
      self.disp.sync()

    return tStoppableThread(stopper = daemonStopSignal, target=daemonLoop, daemon=True)

  #----------------------------------------------------------------------------------------------------------
  def forceCleanup(self):
    try:
      for keycode in range(8, 256):
        for modmask in range(0, 256):
          self.root.ungrab_key(keycode, modmask)
      self.disp.ungrab_keyboard(X.CurrentTime)
      self.disp.sync()
    except:
      pass    
  
  #----------------------------------------------------------------------------------------------------------
  def getWindowGeometry(self, winID):
    try:
      win = self.disp.create_resource_object('window', winID)
      geometry = win.get_geometry()
      coords = win.translate_coords(self.root, 0, 0)
      return [-coords.x, -coords.y, geometry.width, geometry.height]
    except Exception as e:
      raise(f"XHelper.getWindowGeometry failed\n{e}")
    
  #----------------------------------------------------------------------------------------------------------
  def getWindowsData(self, winID) -> windowData:
    winData = windowData(self.getWindowGeometry(winID))
    winData.desktop = self.getWindowsVirtualDesktop(winID)            
    winData.borderless = self.getWindowsBorder(winID)
    winData.audio = not self.audioQueryMuted(self.getPID(winID))
    return winData
  
  #----------------------------------------------------------------------------------------------------------
  def _getToplevel(self, winID):
    win = self.disp.create_resource_object('window', winID)
    while True:
      parent = win.query_tree().parent
      if parent.id == self.root.id:
        return win
      win = parent

  #----------------------------------------------------------------------------------------------------------
  def getWindowsVirtualDesktop(self, winID) -> int:
    try:
      win = self._getToplevel(winID)
      prop = win.get_full_property(self.netWMDesktop, X.AnyPropertyType)
      return int(prop.value[0]) if prop and prop.value else 0
    except Exception as e:
      raise(f"XHelper.getWindowsVirtualDesktop failed\n{e}")

  #----------------------------------------------------------------------------------------------------------
  def getWindowsBorder(self, winID) -> bool:
    try:
      hint = self.getWindowHint(winID)
      if hint is None: return True
      return bool(hint.get('decorations', 1))
    except Exception as e:
      raise(f"XHelper.getWindowsBorder failed\n{e}")

  #----------------------------------------------------------------------------------------------------------
  def getPID(self, winID) -> int:
    try:
      win = self.disp.create_resource_object('window', winID)
      prop = win.get_full_property(self.netWMPID, X.AnyPropertyType)
      return int(prop.value[0]) if prop and prop.value else 0
    except Exception as e:
      raise(f"XHelper.getPID failed\n{e}")

  #----------------------------------------------------------------------------------------------------------
  def moveVirtualDesktop(self, winID, targetDesktop: int):
    try:
      win = self.disp.create_resource_object('window', winID)
      atom = self.disp.intern_atom('_NET_WM_DESKTOP')
      evt = Xlib.protocol.event.ClientMessage(
        window=win,
        client_type=atom,
        data=(32, [targetDesktop, 2, 0, 0, 0])
      )
      self.root.send_event(evt, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
      self.disp.sync()
    except Exception as e:
      raise(f"XHelper.moveVirtualDesktop({targetDesktop}) failed\n{e}")

  #----------------------------------------------------------------------------------------------------------
  def moveWindow(self, winID, x, y):
    try:
      win = self.disp.create_resource_object('window', winID)
      win.configure(x=x, y=y)
      self.disp.sync()
      return True
    except Exception as e:
      raise(f"XHelper.moveWindow({x},{y}) failed\n{e}")

  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def audioToggle(pid):
    # if XHelper.audioQueryMuted(pid):
    #   XHelper.audioUnmute(pid)
    # else:
    #   XHelper.audioMute(pid)
    subprocess.run(["wpctl", "set-mute", "-p", str(pid), "toggle"], stderr=subprocess.DEVNULL)


  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def audioMute(pid):
    subprocess.run(["wpctl", "set-mute", "-p", str(pid), "1"], stderr=subprocess.DEVNULL)

  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def audioUnmute(pid):
    subprocess.run(["wpctl", "set-mute", "-p", str(pid), "0"], stderr=subprocess.DEVNULL)
  
  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def audioQueryMuted(pid) -> bool:
    #@TODO this is really inefficient, but wpctl doesn't have a way to query a single pid,
    # so we have to parse the entire list every time
    #@TODO each client may/will have multiple nodes, and each one of them may be toggled
    # differently (e.g. sink and sources). This will return the value of the first node it finds!
    # In DDO, there are 3 nodes, the first one is usually the sink
    output = subprocess.check_output(['pw-dump'], text=True, stderr=subprocess.DEVNULL)
    alldata = json.loads(output)

    for i in alldata:
      if i.get('type',{}).endswith("Node"):
        if str(pid) == str(i.get('info',{}).get('props',{}).get('application.process.id',{})):
          return str(i.get('info',{}).get('params',{}).get('Props',{})[0]['mute']).lower()=='true'

