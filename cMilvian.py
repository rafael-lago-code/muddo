#!/usr/bin/env python3
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

import sys, mmap, time, struct
import os, threading
from typing import TYPE_CHECKING
from PyQt6.QtCore import pyqtSignal, QObject
from helpers.cMilvianPacket import cMilvianPacket, packetCommand, packetStatus, packetSignal
from helpers.tStoppableThread import tStoppableThread
from helpers.cPrint import cPrint
from helpers.cDispatcher import cDispatcher
from helpers.util import *
if TYPE_CHECKING:
   from cMilvian import cMilvian

P_MILVIAN_DEBUG=True
P_SHM_SIZE = 1024*1024
P_RESPONSE_CBUFFER_BEGIN = 64 
P_RESPONSE_WRITER_POS    = 4
P_RESPONSE_READER_POS    = 0

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            M I L V I A N
#                                  
#
#---------------------------------------------------------------------------------------------------------------
class cMilvian():
  bridgePath = ''
  inputActions = None
  responseDaemonStopSignal = None
  id = 0

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(cls, dhpath):
    # cls.setBridgePath(os.path.dirname(dhpath)+"/Milvian/")
    cls.setBridgePath("/dev/shm/Milvian/")
    cls.getInputActions(dhpath)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def getInputActions(cls, dhpath):
    if cls.inputActions: return
    sys.path.append(dhpath)
    from pythonnet import load
    load("coreclr")
    import clr
    clr.AddReference("VoK.Sdk")
    clr.AddReference("System.Private.CoreLib")
    from VoK.Sdk.Ddo.Enums import InputActions # type: ignore
    from System import Enum as DotNetEnum      # type: ignore

    ia = {}
    iaNames  = DotNetEnum.GetNames(InputActions)
    iaValues = DotNetEnum.GetValues(InputActions)
    ia = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
                            for (n,v) in zip(iaNames,iaValues) }
      # Adds some useful shortcuts to it
    for b in range(10):
      for k in range(10):
        ia[f"b{b+1}k{k+1}"] = ia[f"shortcut_bar{b+1}_key{k+1}"]
    cls.inputActions = ia

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def setBridgePath(cls, path):
    cls.bridgePath = path

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def printInputActions(cls):
    if not cls.inputActions: cls.getInputActions()
    cPrint.debug(cls.inputActions.keys())

  #---------------------------------------------------------------------------------------------------------------
  @classmethod
  def isInputAction(cls, cmd: str):
    if not cls.inputActions: cls.getInputActions()
    return cmd in cls.inputActions.keys()

  #---------------------------------------------------------------------------------------------------------------
  def __init__(self, pathSHM : str):
    super().__init__()
    # pathSHM can be pathSHMI or pathSHMO, doesn't matter
    self.charName = None
    self.knownPackets = {}

    if pathSHM.endswith("I") or pathSHM.endswith("O"):
      pathSHM = pathSHM[:-1]
    self.pathResponse = pathSHM+"O"
    self.pathRequest = pathSHM+"I"
    self.id = int(os.path.basename(pathSHM)[6:])
    
    if not os.path.exists(self.pathRequest) or not os.path.exists(self.pathResponse):
      cPrint.error(f"[cMilvian] error, {os.path.basename(self.pathRequest)} or {os.path.basename(self.pathResponse)} do not exist!")
      return
    
    self.responseDaemonStopSignal = threading.Event()
    cDispatcher.connect((self.id, packetSignal.gotData), self.parseData)
    self.responseDaemonThread = tStoppableThread(stopper = self.responseDaemonStopSignal, target = self.responseDaemon, daemon=True)
    self.responseDaemonThread.start()
    
    packet = self.sendCommand(packetCommand.querycharname)
    if not packet.wait(1.0):
      cPrint.error(f"[cMilvian] timedout while waiting for charName. Is {os.path.basename(pathSHM)} is defunct?")
      cPrint.error(f" ~~~~  {packet}")
      return
      
    if packet.status != packetStatus.success:
      cPrint.error(f"[cMilvian] got status {packet.status} when querying charName on {os.path.basename(pathSHM)}.")
      return
    
    self.charName = packet.outData if isinstance(packet.outData,str) else packet.outData.decode('utf-8')
    self.charName = self.charName.split()[0]
    cPrint.info(f"[cMilvian] got charName {C_SILVER}\"{self.charName}\"</font> for {os.path.basename(pathSHM)}")

  #---------------------------------------------------------------------------------------------------------------
  def close(self):
    self.responseDaemonStopSignal.set()
    self.responseDaemonThread.join(timeout=0.1)

  #---------------------------------------------------------------------------------------------------------------
  def responseDaemon(self) -> bool:
      try:
        with open(self.pathResponse, 'r+b') as fdResponse:
          while not self.responseDaemonStopSignal.is_set():
            # shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
            mmResponse = mmap.mmap(fdResponse.fileno(), 0, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
          
            writerPos = struct.unpack('<I', mmResponse[P_RESPONSE_WRITER_POS:P_RESPONSE_WRITER_POS+4])[0]
            readerPos = struct.unpack('<I', mmResponse[P_RESPONSE_READER_POS:P_RESPONSE_READER_POS+4])[0]

            if (writerPos == readerPos):
              time.sleep(0.05)
              continue
            lenMessage = cMilvian.readCircularBuffer(mmResponse, readerPos, 4)
            lenMessage = struct.unpack('<I', lenMessage)[0]        
            if lenMessage == 0:
              cPrint.warning(f"[cMilvian] seems to have received a message with length=0! Ignoring...")
              continue
            if not(lenMessage == 8 or lenMessage > 12):
              cPrint.error(f"[cMilvian] seems to have received a message with length={lenMessage}! Valid lengths are 8 (id and status only) and 13 or more (id, status, payload lenght, + payload)...")
              return False
            
            rawData = cMilvian.readCircularBuffer(mmResponse, readerPos+4, lenMessage)
            cDispatcher.emit((self.id, packetSignal.gotData),rawData)
            cMilvian.setResponseReaderPos(mmResponse,readerPos+4+lenMessage)
      
      except Exception as e:
        print(f" EXCEPTION: {e}")
      return True
  
  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def setResponseReaderPos(mmResponse, pos : int):
      epos = P_RESPONSE_CBUFFER_BEGIN + (pos - P_RESPONSE_CBUFFER_BEGIN) % (P_SHM_SIZE - P_RESPONSE_CBUFFER_BEGIN)
      mmResponse[P_RESPONSE_READER_POS : P_RESPONSE_READER_POS + 4] = struct.pack('<I', epos)
      mmResponse.flush()
  
  #---------------------------------------------------------------------------------------------------------------
  def parseResponse(self, packet : cMilvianPacket):
    cPrint.debug(f"[cMilvian.parseResponse]:\n{packet}")

  #---------------------------------------------------------------------------------------------------------------
  def parseData(self, rawData : bytes):
    id = rawData[0:4]

    if cDispatcher.contains((self.id, id, packetSignal.gotResponse)):
      cDispatcher.emit((self.id, id, packetSignal.gotResponse), rawData)
      return
    
    packet = cMilvianPacket(packetCommand.unrequested, self)
    packet.id = id
    packet.status = packetStatus(rawData[4:8])
    if len(rawData)>12:
      packet.outData = rawData[12:]
    else:
      packet.outData = None
    packet.outMessage = [packet.status.name, packet.outData.decode('utf-8')]
    cPrint.info(f"[cMilvian.parseData] Unhandled packet: {packet}")

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def readCircularBuffer(mmResponse : mmap, pos : int, nbytes : int) -> bytes:
    pos = P_RESPONSE_CBUFFER_BEGIN + (pos - P_RESPONSE_CBUFFER_BEGIN) % (P_SHM_SIZE - P_RESPONSE_CBUFFER_BEGIN)
    firstChunk = P_SHM_SIZE - pos
    secondChunk = nbytes - firstChunk
    data = mmResponse[pos:pos+min(firstChunk, nbytes)]
    if (secondChunk > 0):
      data += mmResponse[P_RESPONSE_CBUFFER_BEGIN:secondChunk]
    return data

  #---------------------------------------------------------------------------------------------------------------
  def newInputActionRequest(self, cmd: str, timeout : int = 10000) -> cMilvianPacket:
    cPrint.debug(f"[cMilvian:Debug] {self.charName} - packInputAction({cmd})")
    inData = cMilvian.inputActions[cmd]
    if timeout > 0: inData += struct.pack('<I',timeout)
    return cMilvianPacket(packetCommand.inputaction, self, inData)
    
  
  #---------------------------------------------------------------------------------------------------------------
  def newSleepRequest(self, nsec: float) -> cMilvianPacket:
    # I know this looks silly, but I will re-use this later on
    cPrint.debug(f"[cMilvian:Debug] {self.charName} - packSleep({nsec})")
    return cMilvianPacket(packetCommand.sleep, self, struct.pack("<f",float(nsec)))
  
  #---------------------------------------------------------------------------------------------------------------
  def newCommandRequest(self, command: str) -> cMilvianPacket:
    cPrint.debug(f"[cMilvian:Debug] {self.charName} - packSimpleRequest({command})")
    if isinstance(command, packetCommand):
      return cMilvianPacket(command, self)
    else:
      return cMilvianPacket(packetCommand[str(command)], self)
  
  #---------------------------------------------------------------------------------------------------------------
  def newListRequest(self, data: list) -> cMilvianPacket:
    # list packet format:
    #  id | list_cmd | inData
    #                  len(data) | item_1_len | item_1_cmd | item_1_data | item_2_len |...
    inData = len(data).to_bytes(4, byteorder='little', signed=False)
    for item in data:
      newReq = self.newStringRequest(item)
      itemData = newReq.pack()
      inData += struct.pack('<I',len(itemData[4:])) + itemData[4:] # ditches the id for the length
    return cMilvianPacket(packetCommand.list, self, inData)

  
  #---------------------------------------------------------------------------------------------------------------
  def newDebugCircularRequest(self, nentries: int) -> cMilvianPacket:
    # I know this looks silly, but I will re-use this later on
    cPrint.debug(f"[cMilvian:DebugCircular] {self.charName} - debugCircular({nentries})")
    return cMilvianPacket(packetCommand.debugCircular, self, struct.pack("<I",nentries))

  #---------------------------------------------------------------------------------------------------------------
  def newStringRequest(self, cmd : str) -> cMilvianPacket:
    cmd = cmd.strip().lower()
    if cmd.startswith('sleep_'):
      return self.newSleepRequest(float(cmd[6:]))
    elif cmd in cMilvian.inputActions.keys():
      return self.newInputActionRequest(cmd)
    else:
      return self.newCommandRequest(cmd)
  
  #---------------------------------------------------------------------------------------------------------------
  def sendList(self, data: list) -> cMilvianPacket:
    while isinstance(data,(list,tuple)) and len(data)==1:
      data = data[0]
    if isinstance(data,list):
      return self.sendRequest(self.newListRequest(data))
    else:
      return self.sendRequest(self.newStringRequest(data))
    
  #---------------------------------------------------------------------------------------------------------------
  def sendDebugCircular(self, nentries: str) -> cMilvianPacket:
    return self.sendRequest(self.newDebugCircularRequest(int(nentries)))
      
  #---------------------------------------------------------------------------------------------------------------
  def sendInputAction(self, cmd: str) -> cMilvianPacket:
    return self.sendRequest(self.newInputActionRequest(cmd))

  #---------------------------------------------------------------------------------------------------------------
  def sendSleep(self, nsec: float) -> cMilvianPacket:
    return self.sendRequest(self.newSleepRequest(nsec))

  #---------------------------------------------------------------------------------------------------------------
  def sendCommand(self, command: str) -> cMilvianPacket:
    return self.sendRequest(self.newCommandRequest(command))

  #---------------------------------------------------------------------------------------------------------------
  def sendRequest(self, packet: cMilvianPacket) -> cMilvianPacket:
    cDispatcher.fate((self.id, packet.id, packetSignal.gotResponse), lambda data, p=packet: p.parseRawData(data))
    message = packet.pack()
    with open(self.pathRequest, 'r+b') as fdSHMI:
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
    cPrint.info(f"[*] cMilvian: clearing {self.pathResponse}")
    with open(self.pathResponse, 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(0)
      shmO.write(b'\x00' * 4)
      shmO.flush()
      os.fsync(fdSHMO.fileno()) 
      shmO.close()

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def getFromDir(path=None, getUnknown=False, purgeUnknown=False) -> dict:
    if not path: path = cMilvian.bridgePath
    files = [f for f in os.listdir(path) if f.startswith("bridge")]
    filesO = [os.path.join(path, f) for f in files if f.endswith("O")]

    characters = {}
    for f in filesO:
      m = cMilvian(f)
      if m.charName:
        characters[m.charName.lower()] = m
        # cPrint.info(f" [*] cMilvian: found {os.path.basename(f)} for character \"{m.charName}\"")
      elif getUnknown:
        i = 1
        while f"NA{i}" in characters: i += 1
        characters[f"NA{i}"] = m
      elif purgeUnknown:
        cPrint.info(f" [*] cMilvian: file {os.path.basename(f)} seems to be orphaned. Deleting... ")
        os.remove(f)
        os.remove(f[:-1]+"I")
    return characters 
