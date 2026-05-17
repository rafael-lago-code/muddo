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
import os, threading, json, re, random
from helpers.μMilvianPacket import μMilvianPacket, cPacker, cPhonyPacket, packetCommand, packetStatus, packetSignal
from helpers.tStoppableThread import tStoppableThread
from helpers.μPrint import μPrint
from helpers.χDispatcher import χDispatcher, χSignal
from helpers.util import *
from helpers.μStrings import *
from helpers.μStrings import μString
from helpers.μAliases import μAliases
from helpers.χHelper import χHelper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from μSettings import μSettings

P_MILVIAN_DEBUG=True
P_SHM_SIZE = 1024*1024
P_RESPONSE_CBUFFER_BEGIN = 64
P_RESPONSE_WRITER_POS    = 4
P_RESPONSE_READER_POS    = 0

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  P A R S E   C O M M A N D 
#
#    Module-level helpers: build packets from strings/lists without sending.
#    Used by cMilvian.execute() and internally by the list/ordered-actor builders.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def parseCommand(cmd: str, bridge) -> μMilvianPacket:
  # Parses a command string into a packet. Handles comma-separated lists and brace expansion. Does not send.
  cmd = μString(cmd.strip())

  parts = cmd.split(',')
  if len(parts) > 1: return parseList(bridge, parts)

  expanded = cmd.expand()
  if len(expanded) > 1: return parseList(bridge, expanded)
  cmd = μString(expanded[0])
  for k, a in μAliases.get().items():
    cmd = μString(cmd.replace(k, a))

  parts = cmd.split(',')
  if len(parts) > 1: return parseList(bridge, parts)
  expanded = cmd.expand()
  if len(expanded) > 1: return parseList(bridge, expanded)
  cmd = μString(expanded[0].lower())

  if cmd == 'sleep_*': return μMilvianPacket(packetCommand.sleep, bridge, struct.pack("<f", float(cmd[6:])))
  if cmd == 'chat(*)': return μMilvianPacket(packetCommand.chat, bridge, cPacker.pack(cmd[5:-1]))
  if cmd == 'strategy(*)': return _parseStrategy(cmd, bridge)
  if cmd == 'debug(*)':    return μMilvianPacket(packetCommand.debug, bridge, cPacker.pack(cmd[6:-1]))
  if cmd == 'ordered(*)':  return _parseOrdered(cmd, bridge)
  if cmd == 'enterportal': return μMilvianPacket(packetCommand.enterPortal, bridge)
  if cmd == 'select(*)':   return μMilvianPacket(packetCommand.selectEntity, bridge, cPacker.packString(cmd[7:-1]))
  if cmd == 'closeexplorerjournal': return μMilvianPacket(packetCommand.closeExplorerJournal, bridge)
  if cmd in μMilvian.inputActions:
    inData = μMilvian.inputActions[cmd] + struct.pack('<I', 10000)
    return μMilvianPacket(packetCommand.inputaction, bridge, inData)

  # Fall back to namedAction — C# will resolve the name (supports * wildcards)
  return μMilvianPacket(packetCommand.namedaction, bridge, cPacker.pack(cmd))

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  P A R S E   L I S T 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def parseList(bridge, data) -> μMilvianPacket:
  # Builds a list packet from a list of command strings. Unwraps single-element lists. Does not send.
  while isinstance(data, (list, tuple)) and len(data) == 1: data = data[0]
  if not isinstance(data, (list, tuple)): return parseCommand(data, bridge)

  # true list: pack as a list packet
  # format: count(4) | [item_length(4) | command(4) | payload] ...
  inData = len(data).to_bytes(4, byteorder='little', signed=False)
  for item in data:
    packed = parseCommand(item, bridge).pack()  # id(4) + command(4) + payload
    inData += struct.pack('<I', len(packed) - 4) + packed[4:]  # drop id, prepend length
  return μMilvianPacket(packetCommand.list, bridge, inData)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  P A R S E   O R D E R E D   A C T O R S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def _parseOrdered(cmd: str, bridge) -> μMilvianPacket:
  # Parses an ordered(...) string into an orderedActors packet. Does not send.
  fields = [s.strip('"') for s in splitGroups(cmd.strip()[8:-1], ',')]
  if len(fields) < 3:
    μPrint.error(f"[cMilvian] malformed ordered() command: {cmd!r}")
    return cPhonyPacket
  filterActors  = fields[3] if len(fields) > 3 else ""
  filterTargets = fields[4] if len(fields) > 4 else ""
  return _buildOrderedActors(bridge, fields[0], fields[1], fields[2], filterActors, filterTargets)


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  P A R S E   S T R A T E G Y
#
#    Packet layout:
#      [4+N] str   filename – full path to .strategy file; empty = no file
#      [4+N] str   args     – remaining args verbatim (e.g. "flag1, flag2, flag3")
#
#    strategy(directives=blabla, flag1, flag2, flag3)
#      → filename=/home/.../strategy/blabla.strategy  args="flag1, flag2, flag3"
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def _parseStrategy(cmd, bridge, command=packetCommand.strategy) -> μMilvianPacket:
  if isinstance(cmd, str):
    idx = cmd.index('(')
    content = μString.dictionary(cmd[idx+1:-1].strip())
  else:
    pass # assume it is a dict already

  directives = ""
  if "toggle" in content.keys(): content['action'] = 'toggle'; del content['toggle']
  if "set" in content.keys():    content['action'] = 'set';    del content['set']
  if "resume" in content.keys(): content['state']  = 'resume'; del content['resume']
  if "pause" in content.keys():  content['state']  = 'pause';  del content['pause']
  if "directives" in content.keys(): directives = content['directives']; del content['directives']

  if not directives: 
    # if not tagged explicitly, then it HAS to be the first word
    idx = cmd.index('(')
    directives = μString(μString.split(cmd[idx+1:-1].strip(),",")[0])
    if directives == ("*=*","_","set","toggle","resume","pause"): directives=""
    else: del content[directives]

  if directives and not directives.startswith('/'):
    # TODO needs to do this smartly; check if file exists, and if relative paths were passed
    directives = os.path.join(P_DEFAULT_CONFIGDIR, 'strategy', directives + '.strategy')

  args = ', '.join(f'{k.strip()}={v.strip()}' if (v is not True and v is not None) else k.strip() for k, v in content.items())
  print(f" DEBUG STRATEGY: {directives}\n{args}")
  inData  = cPacker.packString(directives)
  inData += cPacker.packString(args)
  return μMilvianPacket(command, bridge, inData)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  B U I L D   O R D E R E D   A C T O R S
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def _buildOrderedActors(bridge, actors, targets, action, filterActors="", filterTargets="") -> μMilvianPacket:
  # Builds an orderedActors packet from parsed arguments. Does not send.
  if isinstance(actors,  str): actors  = [a.strip() for a in actors.split(',')  if a.strip()]
  if isinstance(targets, str): targets = [t.strip() for t in targets.split(',') if t.strip()]

  if not isinstance(action, μMilvianPacket):
    action = parseList(bridge, action) if isinstance(action, (list, tuple)) else parseCommand(action, bridge)

  inData  = cPacker.pack(actors)
  inData += cPacker.pack(targets)
  inData += cPacker.pack(filterActors)
  inData += cPacker.pack(filterTargets)
  inData += cPacker.pack(action)
  return μMilvianPacket(packetCommand.orderedActors, bridge, inData)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  M I L V I A N 
#
#     The star of the show.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMilvian():
  _lastAlive = False
  charName   = None
  bridgePath = ''
  inputActions = None
  responseDaemonStopSignal = None
  id = 0

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setup(cls):
    from μSettings import μSettings
    shmPath = μSettings.plugins.milvianSHMPath()
    dhPath  = os.path.dirname(μSettings.plugins.dhExec())
    μPrint.debug(f"[cMilvian.setup] shmPath={shmPath!r} | dhPath={dhPath!r}")
    cls.configPath = dhPath
    cls.setBridgePath(shmPath)
    cls.getInputActions(dhPath)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setBridgePath(cls, path):
    cls.bridgePath = path

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def printInputActions(cls):
    if not cls.inputActions: cls.getInputActions()
    μPrint.debug(cls.inputActions.keys())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def isInputAction(cls, cmd: str):
    if not cls.inputActions: cls.getInputActions()
    return cmd in cls.inputActions.keys()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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
      μPrint.error(f"[cMilvian] error, {os.path.basename(self.pathRequest)} or {os.path.basename(self.pathResponse)} do not exist!")
      return

    self.responseDaemonStopSignal = threading.Event()
    self.χigGotData = χSignal()
    self.χigGotData.connect(self.parseData)
    self.responseDaemonThread = tStoppableThread(stopper=self.responseDaemonStopSignal, target=self.responseDaemon, daemon=True)
    self.responseDaemonThread.start()

    packet = self.query(packetCommand.querycharname)
    if not packet.wait(1.0):
      μPrint.error(f"[cMilvian] timedout while waiting for charName. Is {os.path.basename(bridgePath)} defunct?")
      μPrint.error(f" ~~~~  {packet}")
      return

    if packet.status != packetStatus.success:
      μPrint.error(f"[cMilvian] got status {packet.status} when querying charName on {os.path.basename(bridgePath)}.")
      return

    self.charName = packet.outData if isinstance(packet.outData, str) else packet.outData.decode('utf-8')
    self.charName = self.charName.split()[0]
    self._lastAlive = True
    μPrint.info(f"[cMilvian] got charName {C_SILVER}\"{self.charName}\"</font> for {os.path.basename(bridgePath)}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def close(self):
    if self.responseDaemonStopSignal is None: return
    self.responseDaemonStopSignal.set()
    self.responseDaemonThread.join(timeout=0.1)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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

          lenMessage = struct.unpack('<I', μMilvian.readCircularBuffer(mmResponse, readerPos, 4))[0]
          if lenMessage == 0:
            μPrint.warning(f"[cMilvian] received message with length=0! Ignoring...")
            continue
          if not (lenMessage == 8 or lenMessage > 12):
            μPrint.error(f"[cMilvian] received message with length={lenMessage}! Expected 8 or >12.")
            return False

          rawData = μMilvian.readCircularBuffer(mmResponse, readerPos+4, lenMessage)
          self.χigGotData.emit(rawData)
          μMilvian.setResponseReaderPos(mmResponse, readerPos+4+lenMessage)

    except Exception as e:
      print(f" EXCEPTION: {e}")
    return True

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
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

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def setResponseReaderPos(mmResponse, pos: int):
    epos = P_RESPONSE_CBUFFER_BEGIN + (pos - P_RESPONSE_CBUFFER_BEGIN) % (P_SHM_SIZE - P_RESPONSE_CBUFFER_BEGIN)
    mmResponse[P_RESPONSE_READER_POS:P_RESPONSE_READER_POS+4] = struct.pack('<I', epos)
    mmResponse.flush()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def parseResponse(self, packet: μMilvianPacket):
    μPrint.debug(f"[cMilvian.parseResponse]:\n{packet}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def parseData(self, rawData: bytes):
    id = rawData[0:4]
    if id in self.knownPackets:
      self.knownPackets.pop(id).χigResponse.emit(rawData)
      return

    packet = μMilvianPacket(packetCommand.unrequested, self)
    packet.id     = id
    packet.status = packetStatus(rawData[4:8])
    packet.outData    = rawData[12:] if len(rawData) > 12 else None
    packet.outMessage = [packet.status.name, packet.outData.decode('utf-8') if packet.outData else None]
    μPrint.info(f"[cMilvian.parseData] Unhandled packet: {packet}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  #   ❖  Milvian Commands
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def debug(self, subcmd: str = "selected") -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.debug, self, cPacker.pack(subcmd)))

  def inputAction(self, cmd: str, timeout: int = 10000) -> μMilvianPacket:
    inData = μMilvian.inputActions[cmd.lower()]
    if timeout > 0: inData += struct.pack('<I', timeout)
    return self.send(μMilvianPacket(packetCommand.inputaction, self, inData))

  def sleep(self, nsec: float) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.sleep, self, struct.pack("<f", float(nsec))))

  def chat(self, text: str) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.chat, self, cPacker.pack(text)))
  
  def strategy(self, data: dict) -> μMilvianPacket:
    return self.send(_parseStrategy(data, self))

  def query(self, command) -> μMilvianPacket:
    cmd = command if isinstance(command, packetCommand) else packetCommand[str(command)]
    return self.send(μMilvianPacket(cmd, self))

  def orderedActors(self, actors, targets, action, filterActors="", filterTargets="") -> μMilvianPacket:
    return self.send(_buildOrderedActors(self, actors, targets, action, filterActors, filterTargets))

  def execute(self, cmd) -> μMilvianPacket:
    # Sends any command: a string, a list of strings, or a cMilvianPacket.
    cmd = μMilvianMeta.resolve(cmd)
    if isinstance(cmd, μMilvianPacket):
      return self.send(cmd)
    if isinstance(cmd, (list, tuple)):
      return self.send(parseList(self, cmd))
    return self.send(parseCommand(cmd, self))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def send(self, packet: μMilvianPacket) -> μMilvianPacket:
    if not self.isAlive(): return cPhonyPacket
    self.knownPackets[packet.id] = packet
    packet.χigResponse.fate(lambda data, p=packet: p.parseRawData(data))
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

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def isAlive(self) -> bool:
    newStatus = os.path.exists(self.pathRequest)
    if self._lastAlive != newStatus and self.charName is not None:
      if not newStatus:
        μPrint.warning(f"[cMilvian] bridge for \"{self.charName}\" ({self.pathRequest}) is dead!")
      else:
        μPrint.warning(f"[cMilvian] bridge for \"{self.charName}\" ({self.pathRequest}) is back online")
    self._lastAlive = newStatus
    return newStatus

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clearResponses(self):
    μPrint.info(f"[*] cMilvian: clearing {self.pathResponse}")
    with open(self.pathResponse, 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(0)
      shmO.write(b'\x00' * 4)
      shmO.flush()
      os.fsync(fdSHMO.fileno())
      shmO.close()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def scanBridges(cls, path=None, getUnknown=False, purgeUnknown=False) -> dict:
    if not path: path = cls.bridgePath
    if not os.path.exists(path): return
    files  = [f for f in os.listdir(path) if f.startswith("bridge")]
    filesO = [os.path.join(path, f) for f in files if f.endswith("O")]

    def _launchInit(bridgePath: str, outDict):
      outDict[bridgePath] = μMilvian(bridgePath)

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
        if isinstance(m, μMilvian) and m.charName:
          characters[m.charName.lower()] = m
        elif isinstance(m, μMilvian) and getUnknown:
          i = 1
          while f"NA{i}" in characters: i += 1
          characters[f"NA{i}"] = m
        elif purgeUnknown:
          μPrint.info(f" [*] cMilvian: file {os.path.basename(f)} seems to be orphaned. Deleting... ")
          os.remove(f)
          os.remove(f[:-1]+"I")
        del runningThreads[f]
      if runningThreads: time.sleep(0.05)
    μMilvianMeta.setBridges(characters)
    return characters

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  P H O N Y   M I L V I A N
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μPhonyMilvian:
  charName = ""
  def __getattr__(self, name):
    return lambda *args, **kwargs: None


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  M I L V I A N   M E T A
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMilvianMeta():
  realBridges = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setBridges(cls, bridges):
    cls.realBridges = bridges

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getFocused(cls) -> μMilvian:
    if cls.realBridges is None: return μPhonyMilvian()
    title = χHelper.getWindowTitle(χHelper.getFocusedWindow())
    if not title: return μPhonyMilvian()
    target = title.split()[0].lower()
    return cls.realBridges.get(target, μPhonyMilvian())
    
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getAny(cls) -> μMilvian:
    if not cls.realBridges or len(cls.realBridges.keys())==0: return μPhonyMilvian()
    return cls.realBridges[random.choice(list(cls.realBridges.keys()))]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def get(cls, meta) -> μMilvian:
    if meta == "any": return μMilvianMeta.getAny()
    if meta == "self": return μMilvianMeta.getFocused()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def resolve(cls, cmd) -> μString:
    out = []
    it = (cmd,) if isinstance(cmd, str) else cmd
    for c in it:
      if hasKeyword(c,"self"): c = c.replace('self', f.charName) if (f := cls.getFocused()) else c
      if hasKeyword(c,"any"):  c = c.replace('any',  f.charName) if (f := cls.getAny())     else c
      out.append(c)
    return out[0] if isinstance(cmd,str) else out
    



  # def execute(self, cmd) -> cMilvianPacket:
  #   if bridge := self.pick() is None: return cPhonyPacket
  #   return bridge.execute(cmd)

  # def send(self, packet: cMilvianPacket) -> cMilvianPacket:
  #   if bridge := self.pick() is None: return cPhonyPacket
  #   return bridge.send(packet)

  # def close(self): pass

# def _resolveAny(cmd):
#   name = μMilvianMeta.getRandomName()
#   if not name: return cmd
#   if isinstance(cmd, str):          return re.sub(r'\bany\b', name, cmd)
#   if isinstance(cmd, (list,tuple)): return [re.sub(r'\bany\b', name, c) if isinstance(c, str) else c for c in cmd]
#   return cmd