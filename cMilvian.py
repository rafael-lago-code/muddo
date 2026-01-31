#!/usr/bin/env python3
import sys, mmap, time, os
import struct
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMilvian import cMilvian


# bridgePath = '/home/steam/prefixes/DDO_Alt/pfx/drive_c/users/holysword/AppData/Roaming/Milvian/'
P_MILVIAN_DEBUG=True

def getInputActions():
  sys.path.append('/home/steam/prefixes/DDO_Main/pfx/drive_c/users/holysword/AppData/Roaming/Dungeon Helper/')
  from pythonnet import load
  load("coreclr")
  import clr
  clr.AddReference("VoK.Sdk")
  clr.AddReference("System.Private.CoreLib") 
  from VoK.Sdk.Ddo.Enums import InputActions
  from System import Enum as DotNetEnum

  ia = {}
  iaNames  = DotNetEnum.GetNames(InputActions)
  iaValues = DotNetEnum.GetValues(InputActions)
  ia = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
                          for (n,v) in zip(iaNames,iaValues) }
    # Adds some useful shortcuts to it b4k3
  for b in range(10):
    for k in range(10):
      ia[f"b{b+1}k{k+1}"] = ia[f"shortcut_bar{b+1}_key{k+1}"]
  return ia

#---------------------------------------------------------------------------------------------------------------
class cMilvian():
  tokenPrefix = {
    'misc':          int.to_bytes(0, byteorder='little', signed=False),
    'list':          int.to_bytes(1, byteorder='little', signed=False),
    'sleep':         int.to_bytes(2, byteorder='little', signed=False),
    'inputaction':   int.to_bytes(3, byteorder='little', signed=False),
    'querycharname': int.to_bytes(4, byteorder='little', signed=False),
    'charname':      int.to_bytes(4, byteorder='little', signed=False),
  }
  bridgePath = ''
  inputActions = None
  printInfo    = lambda x : print(x)
  printDebug   = lambda x : print(x)
  printWarning = lambda x,e=None : print(x + f"\n{e}" if e else "")
  printError   = lambda x,e=None : print(x + f"\n{e}" if e else "")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(self, dhpath, console=None):
    if console:
      self.attachConsole(console)
    self.setBridgePath(os.path.dirname(dhpath)+"/Milvian/")
    self.getInputActions(dhpath)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def getInputActions(self, dhpath):
    if self.inputActions: return
    sys.path.append(dhpath)
    from pythonnet import load
    load("coreclr")
    import clr
    clr.AddReference("VoK.Sdk")
    clr.AddReference("System.Private.CoreLib") 
    from VoK.Sdk.Ddo.Enums import InputActions
    from System import Enum as DotNetEnum

    ia = {}
    iaNames  = DotNetEnum.GetNames(InputActions)
    iaValues = DotNetEnum.GetValues(InputActions)
    ia = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
                            for (n,v) in zip(iaNames,iaValues) }
      # Adds some useful shortcuts to it b4k3
    for b in range(10):
      for k in range(10):
        ia[f"b{b+1}k{k+1}"] = ia[f"shortcut_bar{b+1}_key{k+1}"]
    self.inputActions = ia

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def attachConsole(self, console):
    self.printInfo = console.info
    self.printError = console.error
    self.printDebug = console.debug
    self.printWarning = console.warning
    self.printInfo("Console attached to cMilvian")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def deattachConsole(self):
    self.printInfo    = lambda x : print(x)
    self.printError   = lambda x : print(x)
    self.printDebug   = lambda x : print(x)
    self.printWarning = lambda x : print(x)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setBridgePath(self, path):
    self.bridgePath = path

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def printInputActions(self):
    if not self.inputActions: self.getInputActions()
    self.printDebug(self.inputActions.keys())

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def isInputAction(self, cmd: str):
    if not self.inputActions: self.getInputActions()
    return cmd in self.inputActions.keys()

  #---------------------------------------------------------------------------------------------------------------
  def __init__(self, pathSHM : str):
    # pathSHM can be pathSHMI or pathSHMO, doesn't matter
    self.charName = None

    if pathSHM.endswith("I") or pathSHM.endswith("O"):
      pathSHM = pathSHM[:-1]
    self.pathSHMO = pathSHM+"O"
    self.pathSHMI = pathSHM+"I"
    
    if not os.path.exists(self.pathSHMI) or not os.path.exists(self.pathSHMO):
      self.printError(f"Error, {os.path.basename(self.pathSHMI)} or {os.path.basename(self.pathSHMO)} do not exist!")
      return
    
    self.sendRequest(self.tokenPrefix['charname'])
    time.sleep(0.05)
    response = self.waitResponse(timeout=1.0)
    if not response:
      self.printError(f"Error, could not retrieve charName. Maybe {os.path.basename(pathSHM)} is defunct?")
      return
    
    response = response.split()
    if len(response)<2:
      self.printError(f"Error, could not retrieve charName. Maybe {os.path.basename(pathSHM)} is defunct?")
      return
    
    if response[0]!="Character:":
      self.printError(f"cMilvian: strange charName for {os.path.basename(pathSHM)}: got \"{response}\"?")
      return
    self.charName = response[1].lower()


      
      
      

  #---------------------------------------------------------------------------------------------------------------
  def waitResponse(self, timeout=None) -> str:
    timer = 0.0
    while True:
      if timeout and timer>timeout:
        self.printDebug(f"[cMilvian:Debug] timeout ({timeout}) in waitResponse! charName={self.charName}, pathO={self.pathSHMO}")
        return None
      with open(self.pathSHMO, 'r+b') as fdSHMO:
        shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
        shmO.seek(0)
        msgLenBBB = shmO.read(4)
        if len(msgLenBBB)<4:
          shmO.close()
          time.sleep(0.05)
          timer += 0.05
          continue

        msgLen = int.from_bytes(msgLenBBB, byteorder='little', signed=False)
        if msgLen == 0:
          shmO.close()
          time.sleep(0.05)
          timer += 0.05
          continue

        payload = shmO.read(msgLen)
        if len(payload) < msgLen:
          shmO.close()
          time.sleep(0.05)
          timer += 0.05
          continue

        response = payload.decode("utf-8")
        # Clear (optional but recommended)
        # Cleans the first 4 bytes asap
        shmO.seek(0)
        shmO.write(b'\x00'*4)
        shmO.flush()
        shmO.close()
        return response
      
  #---------------------------------------------------------------------------------------------------------------
  def packInputAction(self, cmd: str) -> bytes:
    self.printDebug(f"[cMilvian:Debug] {self.charName} - packInputAction({cmd})")
    payload = ( self.tokenPrefix['inputaction'] +  # prefix byte = 1
                self.inputActions[cmd]             # the uint32
    )
    return payload
  
  #---------------------------------------------------------------------------------------------------------------
  def packSleep(self, nsec: float) -> bytes:
    # I know this looks silly, but I will re-use this later on
    if P_MILVIAN_DEBUG: print(f"[cMilvian:Debug] {self.charName} - packSleep({nsec})")
    payload = ( self.tokenPrefix['sleep'] +         # prefix byte = 1
                struct.pack("<f",float(nsec))       # the float
    )
    return payload
  
  #---------------------------------------------------------------------------------------------------------------
  def packSingleToken(self, token: str) -> bytes:
    self.printDebug(f"[cMilvian:Debug] {self.charName} - packSingleToken({token})")
    payload = ( self.tokenPrefix[token] )
    return payload
  
  #---------------------------------------------------------------------------------------------------------------
  def packList(self, data: list) -> bytes:
    # payload format:
    #  list_token | len(data) | item_1_len | item_1_token | item_1_data | item_2_len |...
    payload = self.tokenPrefix["list"]
    payload += len(data).to_bytes(4, byteorder='little', signed=False)
    for item in data:
      itemData = self.packString(item)
      payload += len(itemData).to_bytes(4, byteorder='little', signed=False)
      payload += itemData
    return payload

  #---------------------------------------------------------------------------------------------------------------
  def packString(self, item : str) -> bytes:
    item = item.strip().lower()
    if item in cMilvian.inputActions.keys():
      itemData = self.packInputAction(item)
    elif item.startswith('sleep_'):
      itemData = self.packSleep(float(item[6:]))
    else:
      itemData = self.packSingleToken(item)
    return itemData
  
  #---------------------------------------------------------------------------------------------------------------
  def sendList(self, data: list):
    while len(data)==1:
      data = data[0]
    if isinstance(data,list):
      self.sendRequest(self.packList(data))
    else:
      self.sendRequest(self.packString(data))
      
  #---------------------------------------------------------------------------------------------------------------
  def sendInputAction(self, cmd: str):
    self.sendRequest(self.packInputAction(cmd))

  #---------------------------------------------------------------------------------------------------------------
  def sendSleep(self, nsec: float):
    self.sendRequest(self.packSleep(nsec))

  #---------------------------------------------------------------------------------------------------------------
  def sendSingleToken(self, token: str):
    self.sendRequest(self.packSingleToken(token))

  #---------------------------------------------------------------------------------------------------------------
  def sendRequest(self, payload: bytes):
    if not isinstance(payload, bytes): payload = payload.encode('utf-8')

    msgLen = len(payload)
    msgLen = msgLen.to_bytes(4, byteorder='little', signed=False)

    with open(self.pathSHMI, 'r+b') as fdSHMI:
      shmI = mmap.mmap(fdSHMI.fileno(), 0, access=mmap.ACCESS_WRITE)
      shmI.seek(4)
      shmI.write(payload)
      shmI.seek(0)
      shmI.write(msgLen)
      shmI.flush()
      shmI.close()

  #---------------------------------------------------------------------------------------------------------------
  def clearO(self):
    self.printInfo(f"[*] cMilvian: clearing {self.pathSHMO}")
    with open(self.pathSHMO, 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(0)
      shmO.write(b'\x00' * 4)
      shmO.flush()
      os.fsync(fdSHMO.fileno()) 
      shmO.close()

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def getFromDir(path=None, getUnknown=False, purgeUnknown=False) -> list:
    if not path: path = cMilvian.bridgePath
    files = [f for f in os.listdir(path) if f.startswith("bridge")]
    filesO = [os.path.join(path, f) for f in files if f.endswith("O")]

    characters = {}
    for f in filesO:
      m = cMilvian(f)
      if m.charName:
        characters[m.charName] = m
        cMilvian.printInfo(f" [*] cMilvian: found {os.path.basename(f)}")
      elif getUnknown:
        i = 1
        while f"NA{i}" in characters: i += 1
        characters[f"NA{i}"] = m
      elif purgeUnknown:
        cMilvian.printInfo(f" [*] cMilvian: file {os.path.basename(f)} seems to be orphaned. Deleting... ")
        os.remove(f)
        os.remove(f[:-1]+"I")
    return characters 

# sleep_1.0, b5k3, interact , sleep_1.0