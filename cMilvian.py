#!/usr/bin/env python3
import sys, mmap, time, os
import struct
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMilvian import cMilvian


P_DEFAULT_SHMPATH = '/home/steam/prefixes/DDO_Alt/pfx/drive_c/users/holysword/AppData/Roaming/Milvian/'
P_MILVIAN_DEBUG=True

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
  inputActions = None

  @classmethod
  def getInputActions(self):
    sys.path.append('/home/steam/prefixes/DDO_Main/pfx/drive_c/users/holysword/AppData/Roaming/Dungeon Helper/')
    from pythonnet import load
    load("coreclr")
    import clr
    clr.AddReference("VoK.Sdk")
    clr.AddReference("System.Private.CoreLib") 
    from VoK.Sdk.Ddo.Enums import InputActions
    from System import Enum as DotNetEnum

    if not self.inputActions:
      iaNames  = DotNetEnum.GetNames(InputActions)
      iaValues = DotNetEnum.GetValues(InputActions)
      self.inputActions = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
                           for (n,v) in zip(iaNames,iaValues) }
      # Adds some useful shortcuts to it b4k3
      for b in range(10):
        for k in range(10):
          self.inputActions[f"b{b+1}k{k+1}"] = self.inputActions[f"shortcut_bar{b+1}_key{k+1}"]

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def printInputActions(self):
    if not self.inputActions: self.getInputActions()
    print(self.inputActions.keys())

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def isInputAction(self, cmd: str):
    if not self.inputActions: self.getInputActions()
    return cmd in self.inputActions.keys()

  #---------------------------------------------------------------------------------------------------------------
  def __init__(self, pathSHM : str):
    # pathSHM can be pathSHMI or pathSHMO, doesn't matter
    self.charName = None

    self.__class__.getInputActions()

    if pathSHM.endswith("I") or pathSHM.endswith("O"):
      pathSHM = pathSHM[:-1]
    self.pathSHMO = pathSHM+"O"
    self.pathSHMI = pathSHM+"I"
    if os.path.exists(self.pathSHMI) and os.path.exists(self.pathSHMO):
      self.sendRequest(self.tokenPrefix['charname'])
      time.sleep(0.05)
      response = self.waitResponse(timeout=1.0)
      if response:
        response = response.split()
        if response[0]=="Character:":
          self.charName = response[1].lower()
        else:
          print(f"Error, could not retrieve charName. Maybe {pathSHM} is defunct?")
      else:
        print(f"Error, could not retrieve charName. Maybe {pathSHM} is defunct?")
    else:
      print(f"Error, {self.pathSHMI} or {self.pathSHMO} do not exist!")
      

  #---------------------------------------------------------------------------------------------------------------
  def waitResponse(self, timeout=None) -> str:
    timer = 0.0
    while True:
      if timeout and timer>timeout:
        if P_MILVIAN_DEBUG: print(f"[cMilvian:Debug] timeout ({timeout}) in waitResponse! charName={self.charName}, pathO={self.pathSHMO}")
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
    if P_MILVIAN_DEBUG: print(f"[cMilvian:Debug] {self.charName} - packInputAction({cmd})")
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
    if P_MILVIAN_DEBUG: print(f"[cMilvian:Debug] {self.charName} - packSingleToken({token})")
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
    if len(data)==1:
      self.sendRequest(self.packString(data[0]))
    self.sendRequest(self.packList(data))
      
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
    print(f"[*] Clearing {self.pathSHMO}")
    with open(self.pathSHMO, 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(0)
      shmO.write(b'\x00' * 4)
      shmO.flush()
      os.fsync(fdSHMO.fileno()) 
      shmO.close()

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def getFromDir(path=P_DEFAULT_SHMPATH, getUnknown=False, purgeUnknown=False) -> list:
    files = [f for f in os.listdir(path) if f.startswith("tmpAccount")]
    filesO = [os.path.join(path, f) for f in files if f.endswith("O")]

    characters = {}
    for f in filesO:
      m = cMilvian(f)
      if m.charName:
        characters[m.charName] = m
      elif getUnknown:
        i = 1
        while f"NA{i}" in characters: i += 1
        characters[f"NA{i}"] = m
      elif purgeUnknown:
        print(f" [*] cMilvian: file {f} seems to be orphaned. Deleting... ")
        os.remove(f)
        os.remove(f[:-1]+"I")
    return characters

# sleep_1.0, b5k3, interact , sleep_1.0