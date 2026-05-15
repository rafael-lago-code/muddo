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
import mmap, time
import struct, secrets
from enum import Enum
from typing import TYPE_CHECKING
from PyQt6.QtCore import pyqtSignal
from helpers.μDispatcher import cDispatcher
from helpers.μPrint import μPrint
if TYPE_CHECKING:
   from helpers.μMilvianPacket import cMilvianPacket
   from μMilvian import μMilvian

P_MILVIAN_DEBUG=True
P_SHM_SIZE = 1024*1024
P_SHMO_CBUFFER_BEGIN = 64 
P_SHMO_WRITER_POS    = 0  
P_SHMO_READER_POS    = P_SHMO_WRITER_POS + 4

class packetCommand(Enum):
  list           = struct.pack('<I', 1)
  sleep          = struct.pack('<I', 2)
  inputaction    = struct.pack('<I', 3)
  querycharname  = struct.pack('<I', 4)
  queryparty     = struct.pack('<I', 5)
  queryselected  = struct.pack('<I', 6)
  queryinventory = struct.pack('<I', 8)
  debug          = struct.pack('<I', 7)
  dissolveItems  = struct.pack('<I', 20)
  sellItems      = struct.pack('<I', 21)
  storeItems     = struct.pack('<I', 22)
  orderedActors  = struct.pack('<I', 30)
  chat           = struct.pack('<I', 31)
  namedaction    = struct.pack('<I', 32)
  strategy       = struct.pack('<I', 40)
  pauseStrategy  = struct.pack('<I', 41)
  resumeStrategy = struct.pack('<I', 42)
  toggleStrategy = struct.pack('<I', 43)
  enterPortal          = struct.pack('<I', 44)
  closeExplorerJournal = struct.pack('<I', 45)
  toggleFlag           = struct.pack('<I', 46)
  selectEntity         = struct.pack('<I', 47)
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

class packetSignal(Enum):
  gotData      = struct.pack('<I', 0)
  gotResponse  = struct.pack('<I', 1)
  running      = struct.pack('<I', 2)
  statusUpdate = struct.pack('<I', 3)


#---------------------------------------------------------------------------------------------------------------
#
#                                                    P A C K E R 
#
#---------------------------------------------------------------------------------------------------------------
class cPacker():

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def packString(a0 : str) -> bytes:
    e = a0.encode('utf-8')
    out  = struct.pack('<I',len(e))
    out += struct.pack(f'<{len(e)}s',e)
    return out

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def packList(a0 : list) -> bytes:
    out  = struct.pack('<I',len(a0))
    for i in a0:
      out += cPacker.pack(i)
    return out

  #---------------------------------------------------------------------------------------------------------------
  @staticmethod
  def pack(a0) -> bytes:
    if isinstance(a0,str):
      return cPacker.packString(a0)
    elif isinstance(a0,(list,tuple)):
      return cPacker.packList(a0)
    elif isinstance(a0,int):
      return struct.pack("<i",a0)  # problematic if I'm trying to send unsigned ints...
    elif isinstance(a0,float):
      return struct.pack("<d",a0)
    elif isinstance(a0,float):
      return struct.pack("<d",a0)
    elif isinstance(a0,bytes):
      return a0
    elif isinstance(a0,(packetSignal,packetStatus,packetCommand)):
      return a0.value
    elif isinstance(a0,cMilvianPacket):
      return a0.pack()
    else:
      print(f"[cPacker] no idea what you passed me, what is this?\n  ->{a0} | {type(a0)}")
      μPrint.error(f"[cPacker] no idea what you passed me, what is this?\n  ->{a0} | {type(a0)}")


#---------------------------------------------------------------------------------------------------------------
#
#                                       M I L V I A N   P A C K E T
#
#---------------------------------------------------------------------------------------------------------------
class cMilvianPacket():
  command : packetCommand = packetCommand.none
  status  : packetStatus  = packetStatus.unknown
  id      = b''
  inData = None
  outMessage = None
  outData = None
  bridge = None

  #---------------------------------------------------------------------------------------------------------------
  def __init__(self, command : packetCommand, bridge : μMilvian, inData = None):
    self.command = command
    self.id      = struct.pack('<I', secrets.randbits(32))
    self.inData  = inData
    self.status  = packetStatus.unknown
    self.bridge : μMilvian = bridge
  
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
  def parseRawData(self, rawData: bytes):
    self.status = packetStatus(rawData[4:8])
    if len(rawData) > 12:
      self.outData = rawData[12:]
    else:
      self.outData = None
    if isinstance(self.command, packetCommand):
      if self.command == packetCommand.querycharname:
        self.outData = self.outData.decode('utf-8')
    else:
      μPrint.error(f"[cMilvianPacket.parseData] unknown packet received = {self})")
      return

  #---------------------------------------------------------------------------------------------------------------
  def checkResponse(self) -> bool:
    if self.outData: return True
    else: return False

  #---------------------------------------------------------------------------------------------------------------
  def wait(self, timeout=None) -> bool:
    timer = 0.0
    self.status = packetStatus.waiting
    while self.status == packetStatus.waiting:
      if timeout and timer>timeout:
        # cMilvian.printDebug(f"[cMilvian:Debug] timeout ({timeout}) in wait! {self.command}[{int.from_bytes(self.id, byteorder='little', signed=False)}], pathO={self.pathSHM}")
        μPrint.info(f"[cMilvianPacket:Debug] timeout ({timeout}) in wait! {self.command}[{int.from_bytes(self.id, byteorder='little', signed=False)}], pathO={self.bridge.pathResponse}")
        return False
      else:
        self.checkResponse()
        time.sleep(0.1)
        timer += 0.1
    return True
  
  #---------------------------------------------------------------------------------------------------------------
  def __str__(self) -> str:
    return f"     ~ milvianPacket[id:{struct.unpack('<I',self.id)[0]}, command:{self.command}, status:{self.status}]{f"\n     ~ Payload: {self.outData}" if self.outData else ""}{f"\n     ~ OutMessage: {self.outMessage}" if self.outMessage else ""}"
  

#---------------------------------------------------------------------------------------------------------------
#
#                                       P H O N Y P A C K E T
#
#---------------------------------------------------------------------------------------------------------------
class cPhonyPacket:
  command : packetCommand = packetCommand.none
  status  : packetStatus  = packetStatus.unknown
  id      = b''
  inData = None
  outMessage = None
  outData = None
  bridge = None

  def __init__(self, command : packetCommand, bridge : μMilvian, inData = None): pass
  def pack(self) -> bytes: return b''
  def parseRawData(self, rawData: bytes): pass
  def checkResponse(self) -> bool: return False
  def wait(self, timeout=None) -> bool: return False  
  def __str__(self) -> str: return '[cPhonyPacket]'
  
  
