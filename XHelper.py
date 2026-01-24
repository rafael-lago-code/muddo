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
from Xlib import X, display, Xutil, XK
import time, re, threading, json, subprocess

P_DEFAULT_SLEEP = 0.05
P_DEFAULT_KEYSYM = '/usr/include/X11/keysymdef.h'

#----------------------------------------------------------------------------------------------------------
def parseKeysymHeader(filename):
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
def buildModifiers():
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
class StoppableThread(threading.Thread):
  def __init__(self, stopper : threading.Event, group = None, target = None, name = None, daemon = None):
    super().__init__(group, target, name, daemon=daemon)
    self.stopper = stopper
  
  def stop(self):
    self.stopper.set()

#----------------------------------------------------------------------------------------------------------
class XHelper(QObject):
  sigInfoPrinted = pyqtSignal(str)
  sigErrorPrinted = pyqtSignal(str,Exception)
  sigDebugPrinted = pyqtSignal(str)
  sigGotWinID = pyqtSignal((int,list))
  KEYSYM = parseKeysymHeader(P_DEFAULT_KEYSYM) 
  MODIFIERS, MODIFIER_MASKS = buildModifiers()

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
        self.sigInfoPrinted.emit(f" Error in XHelper.getWinID: no window found {f'(timeout={timeout})' if timeout>0.0 else ''}")
        return None
      
  #----------------------------------------------------------------------------------------------------------
  def getWinID(self, pid) -> list:
    pid = int(pid)
    winIDList = []
    clientList = self.root.get_full_property(self.netClientList, X.AnyPropertyType)

    if not clientList:
      self.sigInfoPrinted.emit(" Error in XHelper.tryWinID: no windows founds at all!")
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
      print(f"executing {item}")
      # TODO: parse accepted commands properly
      if callable(item):
        print(f"calling callable {item}")
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
  def getShortcutsDaemon(self, hotkeys : dict) -> StoppableThread:
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
        self.sigDebugPrinted.emit(f"XHelper.getShortcutsDaemon: registered \"{keystring}\"")
      except Exception as e:
        raise(f"XHelper.getShortcutsDaemon: failed to grab \"{keystring}\"\n{e}")
    
    if not grabbed:
      self.sigDebugPrinted.emit(f"XHelper.getShortcutsDaemon: not hotkeys passed!")
      return
    
    daemonStopSignal = threading.Event()
    
    def daemonLoop():
      self.sigDebugPrinted.emit(f"XHelper.getShortcutsDaemon: daemon started running")
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
      # except Exception as e:
      #   print(f" ERROR in XHelper: \n{e}\n")
      # finally:
      for (modmask, keycode), _ in grabbed.items():
        self.root.ungrab_key(keycode, modmask)
      self.disp.sync()

    return StoppableThread(stopper = daemonStopSignal, target=daemonLoop, daemon=True)

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
  def mutePID(pid):
    try:
      cmd = ["pw-cli", "list-objects", "Node", "-f", "json"]
      output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
      
      # Parse JSON output
      nodes = json.loads(output)
      
      for node in nodes:
        # Check if this node belongs to our PID
        props = node.get('info', {}).get('props', {})
        app_pid = props.get('application.process.id')
        
        if app_pid and str(pid) == str(app_pid):
          # Found it! Get node ID and mute
          node_id = node['id']
          
          # Mute command
          subprocess.run([
              "pw-cli", "set-param", str(node_id), 
              "Props", "Mute", "true"
          ], stderr=subprocess.DEVNULL)
          return True
    except Exception as e:
        print(e)
    return False

  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def unmutePID(pid):
    try:
      cmd = ["pw-cli", "list-objects", "Node", "-f", "json"]
      output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
      nodes = json.loads(output)
      
      for node in nodes:
        props = node.get('info', {}).get('props', {})
        app_pid = props.get('application.process.id')
        
        if app_pid and str(pid) == str(app_pid):
          node_id = node['id']
          subprocess.run([
              "pw-cli", "set-param", str(node_id),
              "Props", "Mute", "false"
          ], stderr=subprocess.DEVNULL)
          return True
    except Exception as e:
        print(e)
    return False
  
  #----------------------------------------------------------------------------------------------------------
  @staticmethod
  def isPIDMuted(pid):
    try:
      cmd = ["pw-cli", "list-objects", "Node", "-f", "json"]
      output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
      nodes = json.loads(output)
      
      for node in nodes:
        props = node.get('info', {}).get('props', {})
        app_pid = props.get('application.process.id')
        
        if app_pid and str(pid) == str(app_pid):
          # Check mute state
          mute_state = props.get('Mute', 'false')
          return mute_state.lower() == 'true'
    except Exception as e:
        print(e)
    return None  # Couldn't determine

# hotkeys = {
#   "super+q": lambda: print("Super+Space pressed!"),
#   "alt+a": lambda: print("alt+A pressed!"),
#   "mod1+a": lambda: print("1 pressed!"),
#   "mod2+a": lambda: print("2 pressed!"),
#   "mod3+a": lambda: print("3 pressed!"),
#   "mod4+a": lambda: print("4 pressed!"),
#   "mod5+a": lambda: print("5 pressed!"),
#   "alt+f3": lambda: print("Alt+F3 pressed!")
# }

# xhelper = XHelper()
# daemon = xhelper.getShortcutsDaemon(hotkeys)

# daemon.start()
# time.sleep(5)
# daemon.stop()

# pid = 11589
# xhelp = XHelper()
# winid = xhelp.getWinID(pid)  # Your PID
# print(f"{pid} = {winid}")
# for w in winid:
#   print(xhelp.getWindowTitle(w))
# xhelp.focusWindow(winid[0])
# print(xhelp.getWindowGeometry(winid[0]))
# xhelp.moveWindow(winid[0], 0, 23)

# print(xhelp._parseKeystring("shift + q v  shift+a"))
# xhelp.sendKeystrokes("kp_1 sleep:1.3 shift+a sleep:1.3 shift+w ", winid[0])


# # if window_id:
# #     focuser.send_shift_q(window_id)