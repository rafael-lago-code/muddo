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
from enum import IntFlag
from typing import TYPE_CHECKING
from helpers.cMilvianPacket import cMilvianPacket, cPacker, cPhonyPacket, packetCommand, packetStatus, packetSignal
from helpers.tStoppableThread import tStoppableThread
from helpers.cPrint import cPrint
from helpers.cDispatcher import cDispatcher
from helpers.util import *
from helpers.strings import *
from helpers.strings import cString
from helpers.cAliases import cAliases
if TYPE_CHECKING:
  from cSettings import cSettings

P_MILVIAN_DEBUG=True
P_SHM_SIZE = 1024*1024
P_RESPONSE_CBUFFER_BEGIN = 64
P_RESPONSE_WRITER_POS    = 4
P_RESPONSE_READER_POS    = 0

# ---------------------------------------------------------------------------------------------------------------
#
#                                   C O M M A N D   P A R S I N G
#
# Module-level helpers: build packets from strings/lists without sending.
# Used by cMilvian.execute() and internally by the list/multi-actor builders.
#
# ---------------------------------------------------------------------------------------------------------------
def parseCommand(cmd: str, bridge) -> cMilvianPacket:
  # Parses a command string into a packet. Handles comma-separated lists and brace expansion. Does not send.
  cmd = cString(cmd.strip())

  parts = cmd.split(',')
  if len(parts) > 1: return parseList(bridge, parts)

  expanded = cmd.expand()
  if len(expanded) > 1: return parseList(bridge, expanded)
  cmd = cString(expanded[0])
  for k, a in cAliases.get().items():
    cmd = cString(cmd.replace(k, a))

  parts = cmd.split(',')
  if len(parts) > 1: return parseList(bridge, parts)
  expanded = cmd.expand()
  if len(expanded) > 1: return parseList(bridge, expanded)
  cmd = cString(expanded[0].lower())

  if cmd == 'sleep_*': return cMilvianPacket(packetCommand.sleep, bridge, struct.pack("<f", float(cmd[6:])))
  if cmd == 'chat(*)': return cMilvianPacket(packetCommand.chat, bridge, cPacker.pack(cmd[5:-1]))
  if cmd == 'strategy(*)': return _parseStrategy(cmd, bridge)
  if cmd == 'debug(*)': return cMilvianPacket(packetCommand.debug, bridge, cPacker.pack(cmd[6:-1]))
  if cmd == 'multi(*)': return _parseMultiActor(cmd, bridge)

  if cmd in cMilvian.inputActions:
    inData = cMilvian.inputActions[cmd] + struct.pack('<I', 10000)
    return cMilvianPacket(packetCommand.inputaction, bridge, inData)

  # Fall back to namedAction — C# will resolve the name (supports * wildcards)
  return cMilvianPacket(packetCommand.namedaction, bridge, cPacker.pack(cmd))

# ----------------------------------------------------------------------------------------------------------
def parseList(bridge, data) -> cMilvianPacket:
  # Builds a list packet from a list of command strings. Unwraps single-element lists. Does not send.
  while isinstance(data, (list, tuple)) and len(data) == 1: data = data[0]
  if not isinstance(data, (list, tuple)): return parseCommand(data, bridge)

  # true list: pack as a list packet
  # format: count(4) | [item_length(4) | command(4) | payload] ...
  inData = len(data).to_bytes(4, byteorder='little', signed=False)
  for item in data:
    packed = parseCommand(item, bridge).pack()  # id(4) + command(4) + payload
    inData += struct.pack('<I', len(packed) - 4) + packed[4:]  # drop id, prepend length
  return cMilvianPacket(packetCommand.list, bridge, inData)

# ----------------------------------------------------------------------------------------------------------
def _parseMultiActor(cmd: str, bridge) -> cMilvianPacket:
  # Parses a multi(...) string into a multiActor packet. Does not send.
  fields = [s.strip('"') for s in splitGroups(cmd.strip()[6:-1], ',')]
  if len(fields) < 3:
    cPrint.error(f"[cMilvian] malformed multi() command: {cmd!r}")
    return cPhonyPacket
  filterActors  = fields[3] if len(fields) > 3 else ""
  filterTargets = fields[4] if len(fields) > 4 else ""
  return _buildMultiActor(bridge, fields[0], fields[1], fields[2], filterActors, filterTargets)

# Flags packed into a single uint — must match StrategyFlags enum in Strategy.cs
class StrategyFlags(IntFlag):
  followMount         = 1 << 0
  followRecall        = 1 << 1
  acceptParty         = 1 << 2
  acceptRess          = 1 << 3
  acceptQuest         = 1 << 4
  autoExplorerJournal = 1 << 5
  followJump          = 1 << 6

_STRATEGY_FLAG_DEFAULTS = (
  StrategyFlags.followMount |
  StrategyFlags.followRecall |
  StrategyFlags.acceptParty |
  StrategyFlags.acceptRess |
  StrategyFlags.acceptQuest |
  StrategyFlags.autoExplorerJournal |
  StrategyFlags.followJump
)

# ----------------------------------------------------------------------------------------------------------
# Packet layout (little-endian):
#   [4]   uint  follow       – 0=stop, 1=start, 2=toggle
#   [4]   float distance     – stop distance
#   [4]   uint  strategy     – 0=entity, 1=party-location
#   [4]   uint  flags        – StrategyFlags bitmask
#   [4]   float formation_x  – offset from target (X)
#   [4]   float formation_y  – offset from target (Y)
#   [4+n] str   target       – "selected", "leader", or party member first name
def _parseStrategy(cmd, bridge) -> cMilvianPacket:
  if isinstance(cmd, str): cmd = cString(cmd[9:-1]).dictionary()

  flags = int(_STRATEGY_FLAG_DEFAULTS)
  for flag in StrategyFlags:
    key = flag.name
    if key in cmd:
      if cmd[key]: flags |=  int(flag)
      else:        flags &= ~int(flag)

  formation = cmd.get('formation', None)
  if isinstance(formation, (list, tuple)) and len(formation) >= 2:
    fx, fy = float(formation[0]), float(formation[1])
  else:
    fx = float(cmd.get('formation_x', 0.0))
    fy = float(cmd.get('formation_y', 0.0))

  inData  = struct.pack('<I', cmd.get('follow',   2))
  inData += struct.pack('<f', cmd.get('distance', 1.0))
  inData += struct.pack('<I', cmd.get('strategy', 0))
  inData += struct.pack('<I', flags)
  inData += struct.pack('<f', fx)
  inData += struct.pack('<f', fy)
  inData += cPacker.packString(str(cmd.get('target', 'leader')))
  return cMilvianPacket(packetCommand.strategy, bridge, inData)

# ----------------------------------------------------------------------------------------------------------
def _buildMultiActor(bridge, actors, targets, action, filterActors="", filterTargets="") -> cMilvianPacket:
  # Builds a multiActor packet from parsed arguments. Does not send.
  if isinstance(actors,  str): actors  = [a.strip() for a in actors.split(',')  if a.strip()]
  if isinstance(targets, str): targets = [t.strip() for t in targets.split(',') if t.strip()]

  if not isinstance(action, cMilvianPacket):
    action = parseList(bridge, action) if isinstance(action, (list, tuple)) else parseCommand(action, bridge)

  inData  = cPacker.pack(actors)
  inData += cPacker.pack(targets)
  inData += cPacker.pack(filterActors)
  inData += cPacker.pack(filterTargets)
  inData += cPacker.pack(action)
  return cMilvianPacket(packetCommand.multiActor, bridge, inData)

# ---------------------------------------------------------------------------------------------------------------
#
#
#                                            M I L V I A N
#
#
# ---------------------------------------------------------------------------------------------------------------
class cMilvian():
  _lastAlive = False
  charName   = None
  bridgePath = ''
  inputActions = None
  responseDaemonStopSignal = None
  id = 0

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(cls):
    from cSettings import cSettings
    shmPath = cSettings.plugins.milvianSHMPath()
    dhPath  = os.path.dirname(cSettings.plugins.dhExec())
    cPrint.debug(f"[cMilvian.setup] shmPath={shmPath!r} | dhPath={dhPath!r}")
    cls.setBridgePath(shmPath)
    cls.getInputActions(dhPath)

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def getInputActions(cls, dhpath):
    if cls.inputActions: return
    sys.path.append(dhpath)
    from pythonnet import load
    load("coreclr")
    import clr
    clr.AddReference("VoK.Sdk")
    clr.AddReference("System.Private.CoreLib")
    from VoK.Sdk.Ddo.Enums import InputActions  # type: ignore
    from System import Enum as DotNetEnum        # type: ignore

    iaNames  = DotNetEnum.GetNames(InputActions)
    iaValues = DotNetEnum.GetValues(InputActions)
    ia = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
           for (n, v) in zip(iaNames, iaValues) }
    for b in range(10):
      for k in range(10):
        ia[f"b{b+1}k{k+1}"] = ia[f"shortcut_bar{b+1}_key{k+1}"]
    cls.inputActions = ia

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def setBridgePath(cls, path):
    cls.bridgePath = path

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def printInputActions(cls):
    if not cls.inputActions: cls.getInputActions()
    cPrint.debug(cls.inputActions.keys())

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def isInputAction(cls, cmd: str):
    if not cls.inputActions: cls.getInputActions()
    return cmd in cls.inputActions.keys()

  # ----------------------------------------------------------------------------------------------------------
  def __init__(self, bridgePath: str):
    super().__init__()
    self.charName    = None
    self.knownPackets = {}

    if bridgePath.endswith("I") or bridgePath.endswith("O"):
      bridgePath = bridgePath[:-1]
    self.pathResponse = bridgePath + "O"
    self.pathRequest  = bridgePath + "I"
    self.id = int(os.path.basename(bridgePath)[6:])

    if not os.path.exists(self.pathRequest) or not os.path.exists(self.pathResponse):
      cPrint.error(f"[cMilvian] error, {os.path.basename(self.pathRequest)} or {os.path.basename(self.pathResponse)} do not exist!")
      return

    self.responseDaemonStopSignal = threading.Event()
    cDispatcher.connect((self.id, packetSignal.gotData), self.parseData)
    self.responseDaemonThread = tStoppableThread(stopper=self.responseDaemonStopSignal, target=self.responseDaemon, daemon=True)
    self.responseDaemonThread.start()

    packet = self.query(packetCommand.querycharname)
    if not packet.wait(1.0):
      cPrint.error(f"[cMilvian] timedout while waiting for charName. Is {os.path.basename(bridgePath)} defunct?")
      cPrint.error(f" ~~~~  {packet}")
      return

    if packet.status != packetStatus.success:
      cPrint.error(f"[cMilvian] got status {packet.status} when querying charName on {os.path.basename(bridgePath)}.")
      return

    self.charName = packet.outData if isinstance(packet.outData, str) else packet.outData.decode('utf-8')
    self.charName = self.charName.split()[0]
    self._lastAlive = True
    cPrint.info(f"[cMilvian] got charName {C_SILVER}\"{self.charName}\"</font> for {os.path.basename(bridgePath)}")

  # ----------------------------------------------------------------------------------------------------------
  def close(self):
    self.responseDaemonStopSignal.set()
    self.responseDaemonThread.join(timeout=0.1)

  # ----------------------------------------------------------------------------------------------------------
  def responseDaemon(self) -> bool:
    try:
      with open(self.pathResponse, 'r+b') as fdResponse:
        while not self.responseDaemonStopSignal.is_set():
          mmResponse = mmap.mmap(fdResponse.fileno(), 0, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)

          writerPos = struct.unpack('<I', mmResponse[P_RESPONSE_WRITER_POS:P_RESPONSE_WRITER_POS+4])[0]
          readerPos = struct.unpack('<I', mmResponse[P_RESPONSE_READER_POS:P_RESPONSE_READER_POS+4])[0]

          if writerPos == readerPos:
            time.sleep(0.05)
            continue

          lenMessage = struct.unpack('<I', cMilvian.readCircularBuffer(mmResponse, readerPos, 4))[0]
          if lenMessage == 0:
            cPrint.warning(f"[cMilvian] received message with length=0! Ignoring...")
            continue
          if not (lenMessage == 8 or lenMessage > 12):
            cPrint.error(f"[cMilvian] received message with length={lenMessage}! Expected 8 or >12.")
            return False

          rawData = cMilvian.readCircularBuffer(mmResponse, readerPos+4, lenMessage)
          cDispatcher.emit((self.id, packetSignal.gotData), rawData)
          cMilvian.setResponseReaderPos(mmResponse, readerPos+4+lenMessage)

    except Exception as e:
      print(f" EXCEPTION: {e}")
    return True

  # ----------------------------------------------------------------------------------------------------------
  @staticmethod
  def readCircularBuffer(mmResponse: mmap, pos: int, nbytes: int) -> bytes:
    pos = P_RESPONSE_CBUFFER_BEGIN + (pos - P_RESPONSE_CBUFFER_BEGIN) % (P_SHM_SIZE - P_RESPONSE_CBUFFER_BEGIN)
    firstChunk  = P_SHM_SIZE - pos
    secondChunk = nbytes - firstChunk
    data = mmResponse[pos:pos+min(firstChunk, nbytes)]
    if secondChunk > 0:
      data += mmResponse[P_RESPONSE_CBUFFER_BEGIN:P_RESPONSE_CBUFFER_BEGIN+secondChunk]
      # NOTE: This was originally as bellow, but at some point some AI insisted this was a bug.
      # This was, however, tested before, so no idea who is right. Keeping this comment in case
      # something goes wrong with readCircularBuffer again
      # data += mmResponse[P_RESPONSE_CBUFFER_BEGIN:secondChunk]
    return data

  # ----------------------------------------------------------------------------------------------------------
  @staticmethod
  def setResponseReaderPos(mmResponse, pos: int):
    epos = P_RESPONSE_CBUFFER_BEGIN + (pos - P_RESPONSE_CBUFFER_BEGIN) % (P_SHM_SIZE - P_RESPONSE_CBUFFER_BEGIN)
    mmResponse[P_RESPONSE_READER_POS:P_RESPONSE_READER_POS+4] = struct.pack('<I', epos)
    mmResponse.flush()

  # ----------------------------------------------------------------------------------------------------------
  def parseResponse(self, packet: cMilvianPacket):
    cPrint.debug(f"[cMilvian.parseResponse]:\n{packet}")

  # ----------------------------------------------------------------------------------------------------------
  def parseData(self, rawData: bytes):
    id = rawData[0:4]
    if cDispatcher.contains((self.id, id, packetSignal.gotResponse)):
      cDispatcher.emit((self.id, id, packetSignal.gotResponse), rawData)
      return

    packet = cMilvianPacket(packetCommand.unrequested, self)
    packet.id     = id
    packet.status = packetStatus(rawData[4:8])
    packet.outData    = rawData[12:] if len(rawData) > 12 else None
    packet.outMessage = [packet.status.name, packet.outData.decode('utf-8') if packet.outData else None]
    cPrint.info(f"[cMilvian.parseData] Unhandled packet: {packet}")

  # ----------------------------------------------------------------------------------------------------------
  #
  #                               C O M M A N D   M E T H O D S
  #
  # ----------------------------------------------------------------------------------------------------------

  def debug(self, subcmd: str = "selected") -> cMilvianPacket:
    return self.send(cMilvianPacket(packetCommand.debug, self, cPacker.pack(subcmd)))

  def inputAction(self, cmd: str, timeout: int = 10000) -> cMilvianPacket:
    inData = cMilvian.inputActions[cmd.lower()]
    if timeout > 0: inData += struct.pack('<I', timeout)
    return self.send(cMilvianPacket(packetCommand.inputaction, self, inData))

  def sleep(self, nsec: float) -> cMilvianPacket:
    return self.send(cMilvianPacket(packetCommand.sleep, self, struct.pack("<f", float(nsec))))

  def chat(self, text: str) -> cMilvianPacket:
    return self.send(cMilvianPacket(packetCommand.chat, self, cPacker.pack(text)))
  
  def strategy(self, data: dict) -> cMilvianPacket:
    return self.send(_parseStrategy(data, self))

  def query(self, command) -> cMilvianPacket:
    cmd = command if isinstance(command, packetCommand) else packetCommand[str(command)]
    return self.send(cMilvianPacket(cmd, self))

  def multiActor(self, actors, targets, action, filterActors="", filterTargets="") -> cMilvianPacket:
    return self.send(_buildMultiActor(self, actors, targets, action, filterActors, filterTargets))

  def execute(self, cmd) -> cMilvianPacket:
    # Sends any command: a string, a list of strings, or a cMilvianPacket.
    if isinstance(cmd, cMilvianPacket):
      return self.send(cmd)
    if isinstance(cmd, (list, tuple)):
      return self.send(parseList(self, cmd))
    return self.send(parseCommand(cmd, self))

  # ----------------------------------------------------------------------------------------------------------
  def send(self, packet: cMilvianPacket) -> cMilvianPacket:
    if not self.isAlive(): return cPhonyPacket
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

  # ----------------------------------------------------------------------------------------------------------
  def isAlive(self) -> bool:
    newStatus = os.path.exists(self.pathRequest)
    if self._lastAlive != newStatus and self.charName is not None:
      if not newStatus:
        cPrint.warning(f"[cMilvian] bridge for \"{self.charName}\" ({self.pathRequest}) is dead!")
      else:
        cPrint.warning(f"[cMilvian] bridge for \"{self.charName}\" ({self.pathRequest}) is back online")
    self._lastAlive = newStatus
    return newStatus

  # ----------------------------------------------------------------------------------------------------------
  def clearResponses(self):
    cPrint.info(f"[*] cMilvian: clearing {self.pathResponse}")
    with open(self.pathResponse, 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(0)
      shmO.write(b'\x00' * 4)
      shmO.flush()
      os.fsync(fdSHMO.fileno())
      shmO.close()

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def scanBridges(cls, path=None, getUnknown=False, purgeUnknown=False) -> dict:
    if not path: path = cls.bridgePath
    if not os.path.exists(path): return
    files  = [f for f in os.listdir(path) if f.startswith("bridge")]
    filesO = [os.path.join(path, f) for f in files if f.endswith("O")]

    def _launchInit(bridgePath: str, outDict):
      outDict[bridgePath] = cMilvian(bridgePath)

    pendingBridges = {}
    runningThreads = {}
    for f in filesO:
      runningThreads[f] = threading.Thread(target=_launchInit, args=(f, pendingBridges), daemon=True)
      runningThreads[f].start()

    characters = {}
    while runningThreads:
      for f, t in list(runningThreads.items()):
        if t.is_alive(): continue
        m = pendingBridges.get(f)
        if isinstance(m, cMilvian) and m.charName:
          characters[m.charName.lower()] = m
        elif isinstance(m, cMilvian) and getUnknown:
          i = 1
          while f"NA{i}" in characters: i += 1
          characters[f"NA{i}"] = m
        elif purgeUnknown:
          cPrint.info(f" [*] cMilvian: file {os.path.basename(f)} seems to be orphaned. Deleting... ")
          os.remove(f)
          os.remove(f[:-1]+"I")
        del runningThreads[f]
      if runningThreads: time.sleep(0.05)

    return characters
