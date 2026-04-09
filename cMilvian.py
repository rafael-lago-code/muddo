#!/usr/bin/env python3
import sys, mmap, time, os
import struct, secrets
from enum import Enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
   from cMilvian import cMilvian


# bridgePath = '/home/steam/prefixes/DDO_Alt/pfx/drive_c/users/holysword/AppData/Roaming/Milvian/'
P_MILVIAN_DEBUG=True

# def getInputActions():
#   sys.path.append('/home/steam/prefixes/DDO_Main/pfx/drive_c/users/holysword/AppData/Roaming/Dungeon Helper/')
#   from pythonnet import load
#   load("coreclr")
#   import clr
#   clr.AddReference("VoK.Sdk")
#   clr.AddReference("System.Private.CoreLib") 
#   from VoK.Sdk.Ddo.Enums import InputActions
#   from System import Enum as DotNetEnum

#   ia = {}
#   iaNames  = DotNetEnum.GetNames(InputActions)
#   iaValues = DotNetEnum.GetValues(InputActions)
#   ia = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
#                           for (n,v) in zip(iaNames,iaValues) }
#     # Adds some useful shortcuts to it b4k3
#   for b in range(10):
#     for k in range(10):
#       ia[f"b{b+1}k{k+1}"] = ia[f"shortcut_bar{b+1}_key{k+1}"]
#   return ia



class packetCommand(Enum):
  list           = struct.pack('<I', 1)
  sleep          = struct.pack('<I', 2)
  inputaction    = struct.pack('<I', 3)
  querycharname  = struct.pack('<I', 4)
  queryparty     = struct.pack('<I', 5)
  queryselected  = struct.pack('<I', 6)
  queryinventory = struct.pack('<I', 8)
  debug          = struct.pack('<I', 7)
  misc           = struct.pack('<I', 9)
  unrequested    = struct.pack('<I', 100)
  none           = struct.pack('<I', 200)

class packetStatus(Enum):
  unknown = struct.pack('<I', 0)
  running = struct.pack('<I', 1)
  parsing = struct.pack('<I', 2)
  queued  = struct.pack('<I', 3)
  success = struct.pack('<I', 42)
  waiting = struct.pack('<I', 40)
  error   = struct.pack('<I', 255)


class milvianPacket():
  command = packetCommand.none
  status  = packetStatus.unknown
  id      = b''
  inData = None
  outMessage = None
  outData = None
  pathSHM = ""

  #---------------------------------------------------------------------------------------------------------------
  def __init__(self, command : packetCommand, pathSHM, inData = None):
    self.command = command
    self.id      = struct.pack('<I', secrets.randbits(32))
    self.inData = inData
    self.status  = packetStatus.unknown
    self.pathSHM = pathSHM
  
  # #---------------------------------------------------------------------------------------------------------------
  # def getLength(self) -> int:
  #   if isinstance(self.inData, bytes):
  #     return len(self.inData)+8
  #   else:
  #     return len(self.inData.encode('utf-8'))+8
    
  #---------------------------------------------------------------------------------------------------------------
  def pack(self) -> bytes:
    message  = self.id+self.command.value
    if self.inData:
      if isinstance(self.inData, bytes):
        message += self.inData
      else:
        message += self.inData.encode('utf-8')
    return message

  #---------------------------------------------------------------------------------------------------------------
  def checkResponse(self, pos=0) -> bool:
    with open(self.pathSHM+"O", 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(pos)
      responseLength = int.from_bytes(shmO.read(4), byteorder='little', signed=False)
      if responseLength > 0:
        if responseLength == 8 or responseLength > 12:
          if (self.id == shmO.read(4)):
            self.status = packetStatus(shmO.read(4))
            cMilvian.printInfo(f"milvianRequest.checkResponse: found response matching id {int.from_bytes(self.id, byteorder='little', signed=False)}, status={self.status}. ResponseLength={responseLength}, DataLength = {responseLength - 12 if responseLength > 12 else 0}")

            if responseLength > 12: # there is an outData
              outDataLength = int.from_bytes(shmO.read(4), byteorder='little', signed=False)
              self.outData = shmO.read(outDataLength)

            # Clear (optional but recommended)
            # Cleans the first 4 bytes asap to mark message as read
            shmO.seek(pos)
            shmO.write(b'\x00'*4)
            shmO.flush()
            shmO.close()
            return True
        else:
          cMilvian.printError(f"milvianRequest.checkResponse: got a message with length {responseLength}. Minimum length is 8b (no data) or 13b (with 1b data)\nData corrupted?")

      shmO.close()
      return False

  #---------------------------------------------------------------------------------------------------------------
  def wait(self, timeout=None) -> bool:
    timer = 0.0
    self.status = packetStatus.waiting
    while self.status == packetStatus.waiting:
      if timeout and timer>timeout:
        cMilvian.printDebug(f"[cMilvian:Debug] timeout ({timeout}) in wait! {self.command}[{int.from_bytes(self.id, byteorder='little', signed=False)}], pathO={self.pathSHM}")
        return False
      else:
        self.checkResponse(pos=0)
        time.sleep(0.05)
        timer += 0.05
    return True

#---------------------------------------------------------------------------------------------------------------
class cMilvian():
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
      # Adds some useful shortcuts to it
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
    self.printWarning = lambda x,e=None : print(x + f"\n{e}" if e else "")
    self.printError   = lambda x,e=None : print(x + f"\n{e}" if e else "")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setBridgePath(self, path):
    self.bridgePath = path

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def printInputActions(self):
    if not self.inputActions: self.getInputActions()
    cMilvian.printDebug(self.inputActions.keys())

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
      cMilvian.printError(f"Error, {os.path.basename(self.pathSHMI)} or {os.path.basename(self.pathSHMO)} do not exist!")
      return
    
    packet = self.sendSimpleRequest(packetCommand.querycharname)
    time.sleep(0.05)
    if not packet.wait(1.0):
      cMilvian.printError(f"cMilvian.init: timedout while waiting for charName. Is {os.path.basename(pathSHM)} is defunct?")
      return
  
    if packet.status != packetStatus.success:
      cMilvian.printError(f"cMilvian.init: got status {packet.status} when querying charName on {{os.path.basename(pathSHM)}}.")
      return
    
    self.charName = packet.outData.decode('utf-8')
    cMilvian.printInfo(f"cMilvian.init: got charName \"{self.charName}\" for bridge{os.path.basename(pathSHM)[:-1]}")
    self.charName = self.charName.lower()

  #---------------------------------------------------------------------------------------------------------------
  def newInputActionRequest(self, cmd: str) -> milvianPacket:
    cMilvian.printDebug(f"[cMilvian:Debug] {self.charName} - packInputAction({cmd})")
    return milvianPacket(packetCommand.inputaction, self.pathSHMO[:-1], cMilvian.inputActions[cmd])
  
  #---------------------------------------------------------------------------------------------------------------
  def newSleepRequest(self, nsec: float) -> milvianPacket:
    # I know this looks silly, but I will re-use this later on
    cMilvian.printDebug(f"[cMilvian:Debug] {self.charName} - packSleep({nsec})")
    return milvianPacket(packetCommand.sleep, self.pathSHMO[:-1], struct.pack("<f",float(nsec)))
  
  #---------------------------------------------------------------------------------------------------------------
  def newSimpleRequest(self, command: str) -> milvianPacket:
    cMilvian.printDebug(f"[cMilvian:Debug] {self.charName} - packSimpleRequest({command})")
    if isinstance(command, packetCommand):
      return milvianPacket(command, self.pathSHMO[:-1])
    else:
      return milvianPacket(packetCommand[str(command)], self.pathSHMO[:-1])
  
  #---------------------------------------------------------------------------------------------------------------
  def newListRequest(self, data: list) -> milvianPacket:
    # list packet format:
    #  id | list_cmd | inData
    #                  len(data) | item_1_len | item_1_cmd | item_1_data | item_2_len |...
    inData = len(data).to_bytes(4, byteorder='little', signed=False)
    for item in data:
      newReq = self.newStringRequest(item)
      itemData = newReq.pack()
      inData += struct.pack('<I',len(itemData[4:])) + itemData[4:] # ditches the id for the length
    return milvianPacket(packetCommand.list, self.pathSHMO[:-1], inData)

  #---------------------------------------------------------------------------------------------------------------
  def newStringRequest(self, cmd : str) -> milvianPacket:
    cmd = cmd.strip().lower()
    if cmd.startswith('sleep_'):
      return self.newSleepRequest(float(cmd[6:]))
    elif cmd in cMilvian.inputActions.keys():
      return self.newInputActionRequest(cmd)
    else:
      return self.newSimpleRequest(cmd)
  
  #---------------------------------------------------------------------------------------------------------------
  def sendList(self, data: list) -> milvianPacket:
    while isinstance(data,(list,tuple)) and len(data)==1:
      data = data[0]
    if isinstance(data,list):
      return self.sendRequest(self.newListRequest(data))
    else:
      return self.sendRequest(self.newStringRequest(data))
      
  #---------------------------------------------------------------------------------------------------------------
  def sendInputAction(self, cmd: str) -> milvianPacket:
    return self.sendRequest(self.newInputActionRequest(cmd))

  #---------------------------------------------------------------------------------------------------------------
  def sendSleep(self, nsec: float) -> milvianPacket:
    return self.sendRequest(self.newSleepRequest(nsec))

  #---------------------------------------------------------------------------------------------------------------
  def sendSimpleRequest(self, command: str) -> milvianPacket:
    return self.sendRequest(self.newSimpleRequest(command))

  #---------------------------------------------------------------------------------------------------------------
  def sendRequest(self, packet: milvianPacket) -> milvianPacket:
    message = packet.pack()
    with open(self.pathSHMI, 'r+b') as fdSHMI:
      shmI = mmap.mmap(fdSHMI.fileno(), 0, access=mmap.ACCESS_WRITE)
      shmI.seek(4)
      shmI.write(message)
      shmI.seek(0)
      shmI.write(len(message).to_bytes(4, byteorder='little', signed=False))
      shmI.flush()
      shmI.close()
    return packet

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
