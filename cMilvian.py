#!/usr/bin/env python3
import sys
import mmap
import time
import os

DEFAULT_SHMPATH = '/home/steam/prefixes/DDO_Alt/pfx/drive_c/users/holysword/AppData/Roaming/Milvian/'

#---------------------------------------------------------------------------------------------------------------
class cMilvian():
  tokenPrefix = {
    'misc':          int.to_bytes(0, byteorder='little', signed=False),
    'inputaction':   int.to_bytes(1, byteorder='little', signed=False),
    'querycharname': int.to_bytes(2, byteorder='little', signed=False),
    'charname':      int.to_bytes(2, byteorder='little', signed=False),
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
      response = self.waitResponse()
      response = response.split()
      if response[0]=="Character:":
        self.charName = response[1]
      else:
        print(f"Error, could not retrieve charName. Maybe {pathSHM} is defunct?")
    else:
      print(f"Error, {self.pathSHMI} or {self.pathSHMO} do not exist!")
      

  #---------------------------------------------------------------------------------------------------------------
  def waitResponse(self) -> str:
    while True:
      with open(self.pathSHMO, 'r+b') as fdSHMO:
        shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
        shmO.seek(0)
        msgLenBBB = shmO.read(4)
        if len(msgLenBBB)<4:
          shmO.close()
          time.sleep(0.05)
          continue

        msgLen = int.from_bytes(msgLenBBB, byteorder='little', signed=False)
        if msgLen == 0:
          shmO.close()
          time.sleep(0.05)
          continue

        payload = shmO.read(msgLen)
        if len(payload) < msgLen:
          shmO.close()
          time.sleep(0.05)
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
  def sendInputAction(self, cmd: str):
    payload = ( self.tokenPrefix['inputaction'] +  # prefix byte = 1
                self.inputActions[cmd]       # the uint32
    )
    self.sendRequest(payload)

  #---------------------------------------------------------------------------------------------------------------
  def sendRequest(self, token: str):
    if not isinstance(token, bytes): token = token.encode('utf-8')

    msgLen = len(token)
    msgLen = msgLen.to_bytes(4, byteorder='little', signed=False)

    with open(self.pathSHMI, 'r+b') as fdSHMI:
      shmI = mmap.mmap(fdSHMI.fileno(), 0, access=mmap.ACCESS_WRITE)
      shmI.seek(4)
      shmI.write(token)
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
  def getFromDir(path, getUnknown=False, purgeUnknown=False):
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
