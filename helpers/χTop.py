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
import os, pwd, signal, pwd, grp
import time
P_DEFAULT_USERNAME=os.getlogin()

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  T O P
#                                  
#   This is a static class. Don't instantiate it.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χTop():
  
  @staticmethod
  def userOwns(username, target) -> list:
    if not username: return True
    uid = pwd.getpwnam(username).pw_uid
    statInfo = os.stat(target)
    return statInfo.st_uid == uid

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getAll(username=P_DEFAULT_USERNAME) -> list:
    pids = []
    try:
      for entry in os.listdir('/proc'):
        if entry.isdigit() and χTop.userOwns(username,f'/proc/{entry}'):
          pids.append(int(entry))
    except:
      pass
    return pids
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getByExec(execName, username=P_DEFAULT_USERNAME) -> list:
    pids = []
    for pid in χTop.getAll(username):
      try:
        exePath = f'/proc/{pid}/exe'
        if os.path.exists(exePath):
          actualPath = os.path.realpath(exePath)
          if os.path.basename(actualPath) == execName:
            pids.append(pid)
      except:
        continue
    return pids
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getExec(pid) -> str:
    if os.path.exists(f'/proc/{pid}/exe'):
      return os.path.realpath(f'/proc/{pid}/exe')
    else:
      return ""
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getCommand(pid) -> str:
    if os.path.exists(f'/proc/{pid}/cmdline'):
      with open(f'/proc/{pid}/cmdline', 'rb') as f:
        return f.read().decode('utf-8', errors='ignore')
    else:
      return ""
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getByCommand(searchTerm, username=P_DEFAULT_USERNAME) -> list:
    pids = []
    for pid in χTop.getAll(username):
      try:
        cmdlinePath = f'/proc/{pid}/cmdline'
        if os.path.exists(cmdlinePath):
          with open(cmdlinePath, 'rb') as f:
            cmdline = f.read().decode('utf-8', errors='ignore')
          if searchTerm in cmdline:
            pids.append(pid)
      except:
        continue
    
    return pids
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getInfo(pid):
    if not χTop.isRunning(pid): return None
    
    info = {'pid': pid} 
    try:
      # Get executable path
      exePath = f'/proc/{pid}/exe'
      if os.path.exists(exePath):
        info['exe'] = os.path.realpath(exePath)
      else:
        info['exe'] = None
      
      # Get command line
      cmdlinePath = f'/proc/{pid}/cmdline'
      if os.path.exists(cmdlinePath):
        with open(cmdlinePath, 'rb') as f:
          cmdline = f.read().decode('utf-8', errors='ignore')
        info['cmdline'] = cmdline.replace('\x00', ' ').strip()
      else:
        info['cmdline'] = None
      
      # Get status information
      statusPath = f'/proc/{pid}/status'
      if os.path.exists(statusPath):
        with open(statusPath, 'r') as f:
          for line in f:
            if ':' in line:
              key, value = line.split(':', 1)
              info[key.strip()] = value.strip()
      
      # Get stat information (for process state)
      statPath = f'/proc/{pid}/stat'
      if os.path.exists(statPath):
        with open(statPath, 'r') as f:
          statData = f.read().split()
          if len(statData) > 2:
            info['state'] = statData[2]  # R=Running, S=Sleeping, etc.
      
      # Get open file descriptors count
      fdDir = f'/proc/{pid}/fd'
      if os.path.exists(fdDir):
        info['fdCount'] = len(os.listdir(fdDir))
      else:
        info['fdCount'] = 0
      
      return info
      
    except:
      return None
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getOwner(pid) -> str:
    try:
      statInfo = os.stat(f'/proc/{pid}')
      return pwd.getpwuid(statInfo.st_uid).pw_name
    except:
      return None
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getGroup(pid) -> str:
    try:
      statInfo = os.stat(f'/proc/{pid}')
      return grp.getgrgid(statInfo.st_gid).gr_name
    except:
      return None
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def isRunning(pid) -> bool:
    return os.path.exists(f'/proc/{pid}')
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def sendSignal(pid, sig):
    if not χTop.isRunning(pid): return
   
    if isinstance(sig, str):
      sig = sig.upper()
      if sig.startswith('SIG'):
        sig = sig[3:]
      sig = getattr(signal, f'SIG{sig}')
    
    os.kill(pid, sig)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def sinalAll(cmd, sig):
    allPIDs = χTop.getByCommand(cmd)
    for p in allPIDs:
      χTop.sendSignal(p, sig)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def terminateAll(cmd):
    χTop.sinalAll(cmd, signal.SIGTERM)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def killAll(cmd):
    χTop.sinalAll(cmd, signal.SIGKILL)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def kill(pid):
    χTop.sendSignal(pid, signal.SIGKILL)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def terminate(pid):
    χTop.sendSignal(pid, signal.SIGTERM)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def stop(pid):
    χTop.sendSignal(pid, signal.SIGSTOP)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def cont(pid):
    χTop.sendSignal(pid, signal.SIGCONT)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getTree(pid, username=P_DEFAULT_USERNAME):
    # Get process tree starting from given PID and returns it as a dictionary
    # Dictionary with parent->children relationships
    if username and χTop.getOwner(pid) != username: return {}
    if not χTop.isRunning(pid): return {}
    
    tree = {}
    toCheck = [pid]
    
    while toCheck:
      currentPid = toCheck.pop()
      children = []
      
      # Check all processes to find children of current pid
      for candidate in χTop.getAll():
        try:
          statusPath = f'/proc/{candidate}/status'
          if os.path.exists(statusPath):
            with open(statusPath, 'r') as f:
              for line in f:
                if line.startswith('PPid:'):
                  ppid = int(line.split()[1])
                  if ppid == currentPid:
                    children.append(candidate)
                    toCheck.append(candidate)
                  break
        except:
          continue
      
      tree[currentPid] = children
    
    return tree
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def killTree(pid):
    tree = χTop.getTree(pid, username=None)
    
    # Kill all processes in reverse order (children first)
    allPids = []
    def collectPids(root):
      allPids.append(root)
      for child in tree.get(root, []):
        collectPids(child)
    
    collectPids(pid)
  
    # Kill children first, then parent
    success = True
    for processPid in reversed(allPids):
      if not χTop.kill(processPid):
        success = False
    
    return success
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getMemoryUsage(pid):
    # Get memory usage in KB
    try:
      statusPath = f'/proc/{pid}/status'
      if os.path.exists(statusPath):
        with open(statusPath, 'r') as f:
          for line in f:
            if line.startswith('VmRSS:'):
              return int(line.split()[1])
    except:
      pass
    return -1
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def getCPUTime(pid):
    # Get CPU time in clock ticks
    try:
      statPath = f'/proc/{pid}/stat'
      if os.path.exists(statPath):
        with open(statPath, 'r') as f:
          statData = f.read().split()
          if len(statData) > 16:
            userTime = int(statData[13])
            sysTime = int(statData[14])
            return (userTime, sysTime)
    except:
      pass
    return (-1, -1)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def detailAll(username=P_DEFAULT_USERNAME):
    processes = []
    for pid in χTop.getAll(username):
      info = χTop.getInfo(pid)
      if info:
        processes.append(info)
    return processes
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def wait(pid, timeout=None):
    startTime = time.time()
    while χTop.isRunning(pid):
      if timeout is not None and (time.time() - startTime) > timeout:
        return False
      time.sleep(0.1)
    
    return True
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def waitPID(exec=None, cmd=None, timeout=None):
    # Matches are exec OR cmd, not AND!
    startTime = time.time()
    while True:
      candidates = []
      if exec: candidates += χTop.getByExec(exec)
      if cmd:  candidates += χTop.getByCommand(cmd)
      if candidates:
        return candidates
      if timeout is not None and (time.time() - startTime) > timeout:
        return False      
      time.sleep(0.1)
