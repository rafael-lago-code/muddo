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
from helpers.cDispatcher import cDispatcher
from helpers.cPrint import cPrint
if TYPE_CHECKING:
   from helpers.cMilvianPacket import cMilvianPacket
   from cMilvian import cMilvian

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
  misc           = struct.pack('<I', 9)
  debugCircular  = struct.pack('<I', 90)
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

#---------------------------------------------------------------------------------------------------------------
#
#
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
  def __init__(self, command : packetCommand, bridge : cMilvian, inData = None):
    self.command = command
    self.id      = struct.pack('<I', secrets.randbits(32))
    self.inData  = inData
    self.status  = packetStatus.unknown
    self.bridge : cMilvian = bridge
  
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
      cPrint.info(self)
    else:
      cPrint.error(f"[cMilvianPacket.parseData] unknown packet received = {self})")
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
        cPrint.info(f"[cMilvianPacket:Debug] timeout ({timeout}) in wait! {self.command}[{int.from_bytes(self.id, byteorder='little', signed=False)}], pathO={self.bridge.pathResponse}")
        return False
      else:
        self.checkResponse()
        time.sleep(0.1)
        timer += 0.1
    return True
  
  #---------------------------------------------------------------------------------------------------------------
  def __str__(self) -> str:
    return f"     ~ milvianPacket[id:{struct.unpack('<I',self.id)[0]}, command:{self.command}, status:{self.status}]{f"\n     ~ Payload: {self.outData}" if self.outData else ""}{f"\n     ~ OutMessage: {self.outMessage}" if self.outMessage else ""}"
  
