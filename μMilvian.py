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
from enum import IntFlag
from typing import TYPE_CHECKING
from helpers.μMilvianPacket import cMilvianPacket, cPacker, cPhonyPacket, packetCommand, packetStatus, packetSignal
from helpers.tStoppableThread import tStoppableThread
from helpers.μPrint import μPrint
from helpers.μDispatcher import cDispatcher
from helpers.util import *
from helpers.μStrings import *
from helpers.μStrings import cString
from helpers.μAliases import cAliases
from helpers.χHelper import χHelper
if TYPE_CHECKING:
  from μSettings import μSettings

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
# Used by cMilvian.execute() and internally by the list/ordered-actor builders.
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
  if cmd == 'strategy(*)':       return _parseStrategy(cmd, bridge)
  if cmd == 'pausestrategy(*)':  return _parseStrategy(cmd, bridge, packetCommand.pauseStrategy)
  if cmd == 'resumestrategy(*)': return _parseStrategy(cmd, bridge, packetCommand.resumeStrategy)
  if cmd == 'togglestrategy(*,*)':
    content  = cmd[cmd.index('(')+1:-1]
    parts    = splitGroups(content)
    flagName = ''
    overrides = {}
    for p in parts[1:]:
      if '=' in p:
        k, v = p.split('=', 1)
        overrides[k.strip()] = v.strip()
      else:
        flagName = p.strip()
    if not flagName:
      return _parseStrategy({'filename': parts[0], **overrides}, bridge, packetCommand.toggleStrategy)
    patchJson = json.dumps(overrides) if overrides else ''
    inData  = cPacker.packString(flagName)
    inData += cPacker.packString(patchJson)
    return cMilvianPacket(packetCommand.toggleFlag, bridge, inData)
  if cmd == 'togglestrategy(*)': return _parseStrategy(cmd, bridge, packetCommand.toggleStrategy)
  if cmd == 'debug(*)': return cMilvianPacket(packetCommand.debug, bridge, cPacker.pack(cmd[6:-1]))
  if cmd == 'ordered(*)': return _parseOrderedActors(cmd, bridge)

  if cmd == 'enterportal': return cMilvianPacket(packetCommand.enterPortal, bridge)
  if cmd == 'closeexplorerjournal': return cMilvianPacket(packetCommand.closeExplorerJournal, bridge)
  if cmd == 'select(*)': return cMilvianPacket(packetCommand.selectEntity, bridge, cPacker.packString(cmd[7:-1]))
  if cmd in μMilvian.inputActions:
    inData = μMilvian.inputActions[cmd] + struct.pack('<I', 10000)
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
def _parseOrderedActors(cmd: str, bridge) -> cMilvianPacket:
  # Parses an ordered(...) string into an orderedActors packet. Does not send.
  fields = [s.strip('"') for s in splitGroups(cmd.strip()[8:-1], ',')]
  if len(fields) < 3:
    μPrint.error(f"[cMilvian] malformed ordered() command: {cmd!r}")
    return cPhonyPacket
  filterActors  = fields[3] if len(fields) > 3 else ""
  filterTargets = fields[4] if len(fields) > 4 else ""
  return _buildOrderedActors(bridge, fields[0], fields[1], fields[2], filterActors, filterTargets)

# Known strategy setting keys that map to JSON fields in the .strategy file
_STRATEGY_SETTING_KEYS = {
  'class', 'captain', 'commander', 'leader', 'stopDistance', 'refreshIntervalMs',
  'followMount', 'followRecall', 'acceptParty', 'acceptRess', 'acceptQuest',
  'closeExplorerJournal', 'followJump', 'followSelect', 'followAttack', 'followPortal', 'followDirection',
  'autonomyTime',
}

# ----------------------------------------------------------------------------------------------------------
# Packet layout:
#   [4+N] str   filename   – full path to .strategy file; empty string = no file
#   [4+N] str   patchJson  – partial JSON overrides; empty string = no overrides
#
# strategy(filename='default')                    → load file, launch
# strategy(filename='default', followPortal=false) → load file, override flags, launch
# strategy(followPortal=false)                    → override flags on running strategy
def _parseStrategy(cmd, bridge, command=packetCommand.strategy) -> cMilvianPacket:
  if isinstance(cmd, str):
    idx = cmd.index('(')
    content = cmd[idx+1:-1].strip()
    cmd = {'filename': content} if content and '=' not in content else cString(content).dictionary()

  filename = cmd.get('filename', '')
  if filename and not filename.startswith('/'):
    filename = os.path.join(P_DEFAULT_CONFIGDIR, 'strategy', filename + '.strategy')

  overrides = {k: v for k, v in cmd.items() if k in _STRATEGY_SETTING_KEYS and k != 'filename'}
  patchJson = json.dumps(overrides) if overrides else ''

  inData  = cPacker.packString(filename)
  inData += cPacker.packString(patchJson)
  return cMilvianPacket(command, bridge, inData)

# ----------------------------------------------------------------------------------------------------------
def _buildOrderedActors(bridge, actors, targets, action, filterActors="", filterTargets="") -> cMilvianPacket:
  # Builds an orderedActors packet from parsed arguments. Does not send.
  if isinstance(actors,  str): actors  = [a.strip() for a in actors.split(',')  if a.strip()]
  if isinstance(targets, str): targets = [t.strip() for t in targets.split(',') if t.strip()]

  if not isinstance(action, cMilvianPacket):
    action = parseList(bridge, action) if isinstance(action, (list, tuple)) else parseCommand(action, bridge)

  inData  = cPacker.pack(actors)
  inData += cPacker.pack(targets)
  inData += cPacker.pack(filterActors)
  inData += cPacker.pack(filterTargets)
  inData += cPacker.pack(action)
  return cMilvianPacket(packetCommand.orderedActors, bridge, inData)

# ---------------------------------------------------------------------------------------------------------------
#
#
#                                            M I L V I A N
#
#
# ---------------------------------------------------------------------------------------------------------------
def _resolveSelf(cmd):
  name = μMilvianSelf.getFocusedName()
  if not name: return cmd
  if isinstance(cmd, str):          return re.sub(r'\bself\b', name, cmd)
  if isinstance(cmd, (list,tuple)): return [re.sub(r'\bself\b', name, c) if isinstance(c, str) else c for c in cmd]
  return cmd

def _resolveAny(cmd):
  name = μMilvianSelf.getRandomName()
  if not name: return cmd
  if isinstance(cmd, str):          return re.sub(r'\bany\b', name, cmd)
  if isinstance(cmd, (list,tuple)): return [re.sub(r'\bany\b', name, c) if isinstance(c, str) else c for c in cmd]
  return cmd

class μMilvian():
  _lastAlive = False
  charName   = None
  bridgePath = ''
  inputActions = None
  responseDaemonStopSignal = None
  id = 0

  # ----------------------------------------------------------------------------------------------------------
  @classmethod
  def setup(cls):
    from μSettings import μSettings
    shmPath = μSettings.plugins.milvianSHMPath()
    dhPath  = os.path.dirname(μSettings.plugins.dhExec())
    μPrint.debug(f"[cMilvian.setup] shmPath={shmPath!r} | dhPath={dhPath!r}")
    cls.configPath = dhPath
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
    μPrint.debug(cls.inputActions.keys())

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
      μPrint.error(f"[cMilvian] error, {os.path.basename(self.pathRequest)} or {os.path.basename(self.pathResponse)} do not exist!")
      return

    self.responseDaemonStopSignal = threading.Event()
    cDispatcher.connect((self.id, packetSignal.gotData), self.parseData)
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

  # ----------------------------------------------------------------------------------------------------------
  def close(self):
    if self.responseDaemonStopSignal is None: return
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

          lenMessage = struct.unpack('<I', μMilvian.readCircularBuffer(mmResponse, readerPos, 4))[0]
          if lenMessage == 0:
            μPrint.warning(f"[cMilvian] received message with length=0! Ignoring...")
            continue
          if not (lenMessage == 8 or lenMessage > 12):
            μPrint.error(f"[cMilvian] received message with length={lenMessage}! Expected 8 or >12.")
            return False

          rawData = μMilvian.readCircularBuffer(mmResponse, readerPos+4, lenMessage)
          cDispatcher.emit((self.id, packetSignal.gotData), rawData)
          μMilvian.setResponseReaderPos(mmResponse, readerPos+4+lenMessage)

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
    μPrint.debug(f"[cMilvian.parseResponse]:\n{packet}")

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
    μPrint.info(f"[cMilvian.parseData] Unhandled packet: {packet}")

  # ----------------------------------------------------------------------------------------------------------
  #
  #                               C O M M A N D   M E T H O D S
  #
  # ----------------------------------------------------------------------------------------------------------

  def debug(self, subcmd: str = "selected") -> cMilvianPacket:
    return self.send(cMilvianPacket(packetCommand.debug, self, cPacker.pack(subcmd)))

  def inputAction(self, cmd: str, timeout: int = 10000) -> cMilvianPacket:
    inData = μMilvian.inputActions[cmd.lower()]
    if timeout > 0: inData += struct.pack('<I', timeout)
    return self.send(cMilvianPacket(packetCommand.inputaction, self, inData))

  def sleep(self, nsec: float) -> cMilvianPacket:
    return self.send(cMilvianPacket(packetCommand.sleep, self, struct.pack("<f", float(nsec))))

  def chat(self, text: str) -> cMilvianPacket:
    return self.send(cMilvianPacket(packetCommand.chat, self, cPacker.pack(text)))
  
  def strategy(self, data: dict) -> cMilvianPacket:
    return self.send(_parseStrategy(data, self))

  def pauseStrategy(self, data: dict = {}) -> cMilvianPacket:
    return self.send(_parseStrategy(data, self, packetCommand.pauseStrategy))

  def resumeStrategy(self, data: dict = {}) -> cMilvianPacket:
    return self.send(_parseStrategy(data, self, packetCommand.resumeStrategy))

  def toggleStrategy(self, data: dict = {}) -> cMilvianPacket:
    return self.send(_parseStrategy(data, self, packetCommand.toggleStrategy))

  def query(self, command) -> cMilvianPacket:
    cmd = command if isinstance(command, packetCommand) else packetCommand[str(command)]
    return self.send(cMilvianPacket(cmd, self))

  def orderedActors(self, actors, targets, action, filterActors="", filterTargets="") -> cMilvianPacket:
    return self.send(_buildOrderedActors(self, actors, targets, action, filterActors, filterTargets))

  def execute(self, cmd) -> cMilvianPacket:
    # Sends any command: a string, a list of strings, or a cMilvianPacket.
    cmd = _resolveSelf(cmd)
    cmd = _resolveAny(cmd)
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
        μPrint.warning(f"[cMilvian] bridge for \"{self.charName}\" ({self.pathRequest}) is dead!")
      else:
        μPrint.warning(f"[cMilvian] bridge for \"{self.charName}\" ({self.pathRequest}) is back online")
    self._lastAlive = newStatus
    return newStatus

  # ----------------------------------------------------------------------------------------------------------
  def clearResponses(self):
    μPrint.info(f"[*] cMilvian: clearing {self.pathResponse}")
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
    if len(characters.keys())>0: characters['self'] = μMilvianSelf(characters)
    return characters

# ---------------------------------------------------------------------------------------------------------------
#
#
#                                            M I L V I A N
#
#
# ---------------------------------------------------------------------------------------------------------------
class μMilvianSelf(μMilvian):
  _instance: 'μMilvianSelf' = None

  def __init__(self, otherBridges : dict):
    self.otherBridges = otherBridges
    self._xh = χHelper()
    μMilvianSelf._instance = self

  @classmethod
  def getFocusedName(cls) -> str:
    if cls._instance is None: return None
    bridge = cls._instance._resolve()
    return bridge.charName if bridge else None

  @classmethod
  def getRandomName(cls) -> str:
    if cls._instance is None: return None
    keys = [k for k in cls._instance.otherBridges if k != 'self']
    if not keys: return None
    return random.choice(keys)

  def _resolve(self) -> 'μMilvian':
    title = self._xh.getWindowTitle(self._xh.getFocusedWindow())
    if not title:
      μPrint.warning(f"[μMilvianSelf] could not get focused window title")
      return None
    target = title.split()[0].lower()
    bridge = self.otherBridges.get(target)
    if bridge is None:
      μPrint.warning(f"[μMilvianSelf] no bridge for \"{target}\" (title=\"{title}\")")
    return bridge

  def execute(self, cmd) -> cMilvianPacket:
    bridge = self._resolve()
    if bridge is None: return cPhonyPacket
    return bridge.execute(cmd)

  def send(self, packet: cMilvianPacket) -> cMilvianPacket:
    bridge = self._resolve()
    if bridge is None: return cPhonyPacket
    return bridge.send(packet)

  def close(self): pass