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
from helpers.μMilvianPacket import μMilvianPacket, cPacker, μPhonyPacket, packetCommand, packetStatus, packetSignal
from helpers.tStoppableThread import tStoppableThread
from helpers.μPrint import μPrint
from helpers.χDispatcher import χSignal
from helpers.util import *
from helpers.util import P_DEFAULT_SHM_DIR
from helpers.μStrings import *
from helpers.μStrings import μString
from helpers.χHelper import χHelper
from helpers.μYAML import μYAML
from helpers.χTop import χTop
from helpers.util import P_DEFAULT_CONFIGDIR
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from μSettings import μSetup

P_MILVIAN_DEBUG=True
P_SHM_SIZE = 1024*1024
P_RESPONSE_CBUFFER_BEGIN = 64
P_RESPONSE_WRITER_POS    = 4
P_RESPONSE_READER_POS    = 0

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  P A R S E   C O M M A N D 
#
#    Module-level helpers: build packets from strings/lists without sending.
#    Used by μMilvian.execute() and internally by the list/ordered-actor builders.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def parseCommand(cmd: str, bridge) -> μMilvianPacket:
  # Parses a command string into a packet. Handles comma-separated lists and brace expansion. Does not send.
  from μMacros import μMacroRegistry
  cmd = μString(cmd.strip())

  parts = cmd.split(',')
  if len(parts) > 1: return parseList(bridge, parts)

  expanded = cmd.expand()
  if len(expanded) > 1: return parseList(bridge, expanded)
  cmd = μString(expanded[0])
  for k, a in μMacroRegistry.aliases.items():
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
  if cmd == 'setattackmode(*)':  return μMilvianPacket(packetCommand.setAttackMode, bridge, struct.pack('<I', int(cmd[14:-1])))
  if cmd == 'engagetarget(*)':   return _parseEngageTarget(cmd, bridge)
  if cmd == 'ordered(*)':  return _parseOrdered(cmd, bridge)
  if cmd == 'confirmdialog(*)':
    args     = cmd[14:-1].split(',', 1)
    dlg_name = args[0].strip()
    dlg_byte = int(args[1].strip()) if len(args) > 1 else 1
    return μMilvianPacket(packetCommand.confirmDialog, bridge, cPacker.packString(dlg_name) + struct.pack('<B', dlg_byte))
  if cmd == 'select(*)':   return μMilvianPacket(packetCommand.selectEntity, bridge, cPacker.packString(cmd[7:-1]))
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
  # Parses an ordered(...) string into an ordered() packet. Does not send.
  fields = [s.strip('"') for s in splitGroups(cmd.strip()[8:-1], ',')]
  if len(fields) < 3:
    μPrint.error(f"[μMilvian] malformed ordered() command: {cmd!r}")
    return μPhonyPacket
  filterActors  = fields[3] if len(fields) > 3 else ""
  filterTargets = fields[4] if len(fields) > 4 else ""
  return _buildOrdered(bridge, fields[0], fields[1], fields[2], filterActors, filterTargets)


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
def _parseStrategy(cmd, bridge) -> μMilvianPacket:
  from μStrategy import μStrategy
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
    directives = os.path.join(P_DEFAULT_CONFIGDIR, 'strategy', directives + '.directives')

  args = ', '.join(f'{k.strip()}={str(v).strip()}' if (v is not True and v is not None) else k.strip() for k, v in content.items())
  inData  = cPacker.packString(directives)
  inData += cPacker.packString(args)
  packet = μMilvianPacket(packetCommand.strategy, bridge, inData)
  char_name = bridge.charName
  packet.χigResponse.connect(lambda _=None, n=char_name: μStrategy.refreshFromStatus(n))
  return packet

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  P A R S E   E N G A G E   T A R G E T
#       Syntax:
#           engage(id=uint64, current, near|next|prev , closeIn, timeout=int)
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def _parseEngageTarget(cmd, bridge) -> μMilvianPacket:
  if isinstance(cmd, str):
    idx = cmd.index('(')
    content = μString.dictionary(cmd[idx+1:-1].strip())
  else:
    pass # assume it is a dict already

  targetId = 0
  timeout = 0
  if "timeout" in content.keys(): timeout = int(content['timeout'])
  if "id" in content.keys():
    targetId = int(content['id'])
  else:
    if "prev" in content.keys():    targetId = 6
    if "next" in content.keys():    targetId = 5
    if "near" in content.keys():    targetId = 4
    if "current" in content.keys(): targetId -= 3
    targetId = max(0,targetId)
  closeIn = "closein" in content.keys()

  inData  = struct.pack('<Q', targetId)
  inData += struct.pack('<I', timeout)
  inData += struct.pack('<?', closeIn)
  if "actions" in content.keys():
    content['actions'] = "sleep(0.1)," + content['actions'] # always prepend a short sleep to give engageTarget
                                                           # time to face the target
                                                           # add more sleep if needs to close in first
    actionsPacket = parseList(bridge, content['actions'])
    inData += actionsPacket.inData
  else:
    inData += struct.pack('<I', 0)  # no actions

  packet = μMilvianPacket(packetCommand.engageTarget, bridge, inData)
  return packet

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  B U I L D   O R D E R E D
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
def _buildOrdered(bridge, actors, targets, action, filterActors="", filterTargets="") -> μMilvianPacket:
  # Builds an ordered() packet from parsed arguments. Does not send.
  if isinstance(actors,  str): actors  = [a.strip() for a in actors.split(',')  if a.strip()]
  if isinstance(targets, str): targets = [t.strip() for t in targets.split(',') if t.strip()]

  if not isinstance(action, μMilvianPacket):
    action = parseList(bridge, action) if isinstance(action, (list, tuple)) else parseCommand(action, bridge)

  inData  = cPacker.pack(actors)
  inData += cPacker.pack(targets)
  inData += cPacker.pack(filterActors)
  inData += cPacker.pack(filterTargets)
  inData += cPacker.pack(action)
  return μMilvianPacket(packetCommand.ordered, bridge, inData)

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  M I L V I A N 
#
#     The star of the show.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μMilvian():
  _lastAlive = False
  charName   = None
  pid        = 0
  account    = ''
  bridgePath = ''
  inputActions = None
  responseDaemonStopSignal = None
  id = 0

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setup(cls):
    from μSettings import μSetup
    shmPath = μSetup.plugins.milvianSHMPath() or P_DEFAULT_SHM_DIR
    dhPath  = os.path.dirname(μSetup.plugins.dhExec())
    μPrint.debug(f"[μMilvian] shmPath={shmPath!r} | dhPath={dhPath!r}")
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
    from VoK.Sdk.Ddo.Enums import AltInputActions  # type: ignore
    from System import Enum as DotNetEnum        # type: ignore

    iaNames  = DotNetEnum.GetNames(InputActions)
    iaValues = DotNetEnum.GetValues(InputActions)
    ia = { n.lower(): int(v).to_bytes(4, byteorder='little', signed=False)
           for (n, v) in zip(iaNames, iaValues) }
    for b in range(10):
      for k in range(10):
        ia[f"b{b+1}k{k+1}"] = ia[f"shortcut_bar{b+1}_key{k+1}"]
    for k in range(12):
        ia[f"tpm{k+1}"] = ia[f"target_fellow_{k+1}_key"]
        ia[f"tpp{k+1}"] = ia[f"target_fellow_pet_{k+1}_key"]
    aiaNames  = DotNetEnum.GetNames(AltInputActions)
    aiaValues = DotNetEnum.GetValues(AltInputActions)
    for (n, v) in zip(aiaNames, aiaValues):
      ia[n.lower()] = int(v).to_bytes(4, byteorder='little', signed=False)
    cls.inputActions = ia
    # from helpers.χVoK import χVoK
    # cls.inputActions = χVoK.inputActions

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def findShmRootForChar(cls, charName: str) -> str | None:
    baseDir = cls.bridgePath or P_DEFAULT_SHM_DIR
    if not os.path.exists(baseDir): return None
    for d in os.listdir(baseDir):
      fullPath = os.path.join(baseDir, d)
      if not os.path.isdir(fullPath): continue
      loginPath = os.path.join(fullPath, 'login')
      if not os.path.exists(loginPath): continue
      try:
        lines = open(loginPath, 'r').read().strip().splitlines()
        charLine = lines[1].strip() if len(lines) >= 2 else ''
        firstName = charLine.split()[0] if charLine else ''
        if firstName.lower() == charName.lower():
          return fullPath.rstrip('/') + '/'
      except: continue
    return None

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
    self.charName     = None
    self.pid          = 0
    self.account      = ''
    self.knownPackets = {}

    # bridgePath is the account directory: /dev/shm/milvian/<accountName>/
    bridgePath = bridgePath.rstrip('/')
    self.shmRoot      = bridgePath.rstrip('/') + '/'
    self.pathRequest  = os.path.join(bridgePath, 'request')
    self.pathResponse = os.path.join(bridgePath, 'response')
    self.pathLogin    = os.path.join(bridgePath, 'login')

    if not os.path.exists(self.pathRequest) or not os.path.exists(self.pathResponse):
      μPrint.error(f"[μMilvian] missing request/response in {bridgePath!r}")
      return

    loginCharName = ''
    loginAccount  = ''
    if os.path.exists(self.pathLogin):
      lines = open(self.pathLogin, 'r').read().strip().splitlines()
      if len(lines) >= 1:
        try: self.pid = int(lines[0].strip())
        except ValueError: μPrint.error(f"[μMilvian] non-numeric PID in login: {bridgePath!r}"); return
      if len(lines) >= 2: loginCharName = lines[1].strip()
      if len(lines) >= 3: loginAccount  = lines[2].strip()

    self.responseDaemonStopSignal = threading.Event()
    self.χigGotData = χSignal()
    self.χigGotData.connect(self.parseData)
    self.responseDaemonThread = tStoppableThread(stopper=self.responseDaemonStopSignal, target=self.responseDaemon, daemon=True)
    self.responseDaemonThread.start()

    packet = self.query(packetCommand.validate)
    if not packet.wait(1.0):
      μPrint.error(f"[μMilvian] timeout waiting for validate in {bridgePath!r}. Bridge dead?")
      μPrint.error(f" ~~~~  {packet}")
      return

    if packet.status != packetStatus.success:
      μPrint.error(f"[μMilvian] status {packet.status} validating {bridgePath!r}")
      return

    data = packet.outData
    pos  = 0
    name_len       = struct.unpack_from('<H', data, pos)[0]; pos += 2
    parts = data[pos:pos+name_len].decode('utf-8', errors='replace').split(); pos += name_len
    self.charName = parts[0] if parts else ""
    self.charId    = struct.unpack_from('<Q', data, pos)[0] if len(data) >= pos + 8 else 0; pos += 8
    acct_len       = struct.unpack_from('<H', data, pos)[0] if len(data) >= pos + 2 else 0; pos += 2
    self.account   = data[pos:pos+acct_len].decode('utf-8', errors='replace') if acct_len > 0 else ""; pos += acct_len

    if loginCharName and self.charName.split()[0].lower() != loginCharName.split()[0].lower():
      μPrint.warning(f"[μMilvian] validate mismatch: bridge says \"{self.charName}\", login file says \"{loginCharName}\"")
      return
    if loginAccount and self.account.lower() != loginAccount.lower():
      μPrint.warning(f"[μMilvian] validate mismatch: bridge account \"{self.account}\", login file says \"{loginAccount}\"")
      return

    if self.charId:
      db = μMilvianMeta.partyPreferences
      if not db.lookup('charId', self.charId):
        db.set(f"{self.charName.lower()}/charId", self.charId)
        db.save()
    self._lastAlive = True
    μPrint.info(f"[μMilvian] bridge \"{C_SILVER}{self.charName}</font>\" (pid={self.pid}) live at {bridgePath!r}")

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
            μPrint.warning(f"[μMilvian] received message with length=0! Ignoring...")
            continue
          if not (lenMessage == 8 or lenMessage > 12):
            μPrint.error(f"[μMilvian] received message with length={lenMessage}! Expected 8 or >12.")
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
    μPrint.debug(f"[μMilvian.parseResponse]:\n{packet}")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def parseData(self, rawData: bytes):
    id = rawData[0:4]
    if id in self.knownPackets:
      status = packetStatus(rawData[4:8])
      packet = self.knownPackets[id]
      packet.χigResponse.emit(rawData)
      if status in (packetStatus.success, packetStatus.error):
        self.knownPackets.pop(id)
      return

    packet = μMilvianPacket(packetCommand.unrequested, self)
    packet.id     = id
    packet.status = packetStatus(rawData[4:8])
    packet.outData    = rawData[12:] if len(rawData) > 12 else None
    packet.outMessage = [packet.status.name, packet.outData.decode('utf-8', errors='replace') if packet.outData else None]
    μPrint.info(f"[μMilvian.parseData] Unhandled packet: {packet}")

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #   🞋  Milvian Commands
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  def debug(self, subcmd: str = "selected") -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.debug, self, cPacker.pack(subcmd)))

  def selectEntity(self, nameOrId) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.selectEntity, self, cPacker.packString(str(nameOrId))))
  
  def selectItem(self, id: int) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.selectItem, self, struct.pack('<Q', id)))

  def drawMap(self, enable: bool, intervalMs: int = 500) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.drawMap, self, struct.pack('<?I', enable, intervalMs)))

  def inputAction(self, cmd: str, timeout: int = 10000) -> μMilvianPacket:
    inData = μMilvian.inputActions[cmd.lower()]
    if timeout > 0: inData += struct.pack('<I', timeout)
    return self.send(μMilvianPacket(packetCommand.inputaction, self, inData))

  def sleep(self, nsec: float) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.sleep, self, struct.pack("<f", float(nsec))))

  def chat(self, text: str) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.chat, self, cPacker.pack(text)))

  def setAttackMode(self, mode: int) -> μMilvianPacket:
    return self.send(μMilvianPacket(packetCommand.setAttackMode, self, struct.pack('<I', mode)))
  
  def strategy(self, data: dict) -> μMilvianPacket:
    return self.send(_parseStrategy(data, self))

  def query(self, command) -> μMilvianPacket:
    cmd = command if isinstance(command, packetCommand) else packetCommand[str(command)]
    return self.send(μMilvianPacket(cmd, self))

  def ordered(self, actors, targets, action, filterActors="", filterTargets="") -> μMilvianPacket:
    return self.send(_buildOrdered(self, actors, targets, action, filterActors, filterTargets))
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def execute(self, cmd) -> μMilvianPacket:
    # Sends any command: a string, a list of strings, or a μMilvianPacket.
    cmd = μMilvianMeta.resolve(cmd)
    if isinstance(cmd, μMilvianPacket):
      return self.send(cmd)
    if isinstance(cmd, (list, tuple)):
      return self.send(parseList(self, cmd))
    return self.send(parseCommand(cmd, self))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def send(self, packet: μMilvianPacket) -> μMilvianPacket:
    if not self.isAlive(): return μPhonyPacket
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
    newStatus = os.path.exists(self.pathRequest) and (self.pid == 0 or χTop.isAlive(self.pid))
    if self._lastAlive != newStatus and self.charName is not None:
      if not newStatus:
        μPrint.warning(f"[μMilvian] bridge for \"{self.charName}\" (pid={self.pid}) is dead!")
      else:
        μPrint.warning(f"[μMilvian] bridge for \"{self.charName}\" (pid={self.pid}) is back online")
    self._lastAlive = newStatus
    return newStatus

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def validate(self) -> bool:
    if self.pid > 0 and not χTop.isAlive(self.pid):
      μPrint.warning(f"[μMilvian] validate failed: pid {self.pid} not alive")
      return False
    if not os.path.exists(self.pathRequest):
      μPrint.warning(f"[μMilvian] validate failed: request file missing")
      return False

    packet = self.query(packetCommand.validate)
    if not packet.wait(1.0) or packet.status != packetStatus.success:
      μPrint.warning(f"[μMilvian] validate failed: no response from bridge")
      return False

    data = packet.outData
    pos  = 0
    name_len = struct.unpack_from('<H', data, pos)[0]; pos += 2
    bridgeChar = data[pos:pos+name_len].decode('utf-8', errors='replace').split()[0]; pos += name_len
    pos += 8  # skip charId
    acct_len = struct.unpack_from('<H', data, pos)[0] if len(data) >= pos + 2 else 0; pos += 2
    bridgeAccount = data[pos:pos+acct_len].decode('utf-8', errors='replace') if acct_len > 0 else ""

    loginCharName = ''
    loginAccount  = ''
    if os.path.exists(self.pathLogin):
      lines = open(self.pathLogin, 'r').read().strip().splitlines()
      if len(lines) >= 1: loginCharName = lines[0].strip()
      if len(lines) >= 2: loginAccount  = lines[1].strip()

    if loginCharName and bridgeChar.lower() != loginCharName.split()[0].lower():
      μPrint.warning(f"[μMilvian] validate mismatch: bridge says \"{bridgeChar}\", login says \"{loginCharName}\"")
      return False
    if loginAccount and bridgeAccount.lower() != loginAccount.lower():
      μPrint.warning(f"[μMilvian] validate mismatch: account \"{bridgeAccount}\" vs \"{loginAccount}\"")
      return False

    return True

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def clearResponses(self):
    μPrint.info(f"[*] μMilvian: clearing {self.pathResponse}")
    with open(self.pathResponse, 'r+b') as fdSHMO:
      shmO = mmap.mmap(fdSHMO.fileno(), 0, access=mmap.ACCESS_READ | mmap.ACCESS_WRITE)
      shmO.seek(0)
      shmO.write(b'\x00' * 4)
      shmO.flush()
      os.fsync(fdSHMO.fileno())
      shmO.close()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def unpackPartyInfo(packet) -> dict | None:
    if packet is None or packet.status != packetStatus.success: return None
    data = packet.outData
    if not data: return None
    pos = 0
    member_count = struct.unpack_from('<B', data, pos)[0]; pos += 1
    names = []
    for _ in range(member_count):
      name_len = struct.unpack_from('<H', data, pos)[0]; pos += 2
      names.append(data[pos:pos+name_len].decode('utf-8')); pos += name_len
    leader_index = struct.unpack_from('<B', data, pos)[0]; pos += 1
    pet_count    = struct.unpack_from('<B', data, pos)[0]; pos += 1
    pet_indices  = set(struct.unpack_from(f'<{pet_count}B', data, pos))
    return {
      'members':      [μString(n) for n in names],
      'leaderName':    μString(names[leader_index]) if leader_index != 0xFF and leader_index < len(names) else None,
      'pets':         [μString(names[i]) for i in pet_indices if i < len(names)],
    }

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def scanBridges(cls, path=None, purgeDefunct=False) -> dict:
    if not path: path = cls.bridgePath or P_DEFAULT_SHM_DIR
    if not os.path.exists(path): return {}

    liveDirs = []
    for d in os.listdir(path):
      fullPath = os.path.join(path, d)
      if not os.path.isdir(fullPath): continue
      if not os.path.exists(os.path.join(fullPath, 'request')): continue

      loginPath = os.path.join(fullPath, 'login')
      pid = 0
      if os.path.exists(loginPath):
        try:
          firstLine = open(loginPath, 'r').readline().strip()
          pid = int(firstLine)
        except (ValueError, OSError):
          pass

      if pid == 0 or not χTop.isAlive(pid):
        if purgeDefunct:
          μPrint.info(f"[μMilvian] pid {pid} no longer alive, purging {fullPath!r}...")
          try:
            import shutil; shutil.rmtree(fullPath)
          except Exception as e:
            μPrint.warning(f"[μMilvian] purge failed: {e}")
        else:
          μPrint.debug(f"[μMilvian] pid {pid} no longer alive, skipping {fullPath!r}")
        continue
      liveDirs.append(fullPath)

    def _launchInit(bridgeDir: str, outDict):
      outDict[bridgeDir] = μMilvian(bridgeDir)

    pendingBridges = {}
    runningThreads = {}
    for d in liveDirs:
      runningThreads[d] = threading.Thread(target=_launchInit, args=(d, pendingBridges), daemon=True)
      runningThreads[d].start()

    characters = {}
    while runningThreads:
      for d, t in list(runningThreads.items()):
        if t.is_alive(): continue
        m = pendingBridges.get(d)
        if isinstance(m, μMilvian) and m.charName:
          characters[m.charName.lower()] = m
        elif purgeDefunct:
          μPrint.info(f"[μMilvian] pid dir {os.path.basename(d)!r} has no valid bridge, purging...")
          try:
            import shutil; shutil.rmtree(d)
          except Exception as e:
            μPrint.warning(f"[μMilvian] purge failed: {e}")
        del runningThreads[d]
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
class μMilvianMeta:
  realBridges      = None
  partyPreferences = μYAML(os.path.join(P_DEFAULT_CONFIGDIR, 'partyPreferences.yaml'))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def setBridges(cls, bridges):
    cls.realBridges = bridges

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getBridges(cls, purgeDefunct=False) -> dict[str, μMilvian]:
    if not cls.realBridges:
      μMilvian.scanBridges(purgeDefunct=purgeDefunct)
    if not cls.realBridges:
      μPrint.warning("[μMilvianMeta] no valid bridges found. Are Dungeon Helper and Milvian plugin running?")
      return {}
    return cls.realBridges

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def closeBridges(cls):
    if cls.realBridges:
      for bridge in cls.realBridges.values(): bridge.close()
    cls.realBridges = {}

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def normalize(cls, name: str) -> str:
    if name.isdigit():
      return μMilvianMeta.partyPreferences.lookup('charId', int(name)) or name
    return name

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getFocused(cls) -> μMilvian:
    if cls.realBridges is None: return μPhonyMilvian()
    pid = χHelper.getFocusedPID()
    if not pid: return μPhonyMilvian()
    return cls.getFromPID(pid)
  
  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getFromPID(cls, pid) -> μMilvian:
    if cls.realBridges:
      for bridge in cls.realBridges.values():
        if bridge.pid == pid: return bridge
    return μPhonyMilvian()

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getNamed(cls, target) -> μMilvian:
    return cls.realBridges.get(target, μPhonyMilvian())

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getAny(cls) -> μMilvian:
    if not cls.realBridges: return μPhonyMilvian()
    return random.choice(list(cls.realBridges.values()))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def get(cls, target) -> μMilvian:
    if target == "any":   return μMilvianMeta.getAny()
    if target == "focus": return μMilvianMeta.getFocused()
    return μMilvianMeta.getNamed(target)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def getAll(cls, exclude: set = None) -> list:
    if not cls.realBridges: return []
    return [b for k, b in cls.realBridges.items() if not exclude or k not in exclude]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def resolve(cls, cmd) -> μString:
    out = []
    it = (cmd,) if isinstance(cmd, str) else cmd
    for c in it:
      if hasKeyword(c,"focus"):
        f = cls.getFocused()
        if f and f.charName: c = c.replace('focus', f.charName)
      if hasKeyword(c,"any"):
        f = cls.getAny()
        if f and f.charName: c = c.replace('any', f.charName)
      out.append(c)
    return out[0] if isinstance(cmd,str) else out
    



  # def execute(self, cmd) -> μMilvianPacket:
  #   if bridge := self.pick() is None: return cPhonyPacket
  #   return bridge.execute(cmd)

  # def send(self, packet: μMilvianPacket) -> μMilvianPacket:
  #   if bridge := self.pick() is None: return cPhonyPacket
  #   return bridge.send(packet)

  # def close(self): pass

# def _resolveAny(cmd):
#   name = μMilvianMeta.getRandomName()
#   if not name: return cmd
#   if isinstance(cmd, str):          return re.sub(r'\bany\b', name, cmd)
#   if isinstance(cmd, (list,tuple)): return [re.sub(r'\bany\b', name, c) if isinstance(c, str) else c for c in cmd]
#   return cmd