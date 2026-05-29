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
import mmap, struct, os
from helpers.util import P_DEFAULT_SHM_DIR

# ── Layout mirrors μStatusLayout in μStatus.cs ────────────────────────────────
FILE_SIZE           = 8192

OFF_SELECTED_ENTITY     = 0    # ulong  8
OFF_LAST_DIALOGUE       = 8    # byte   1
OFF_DIALOGUE_POS_X      = 9    # int16  2
OFF_DIALOGUE_POS_Y      = 11   # int16  2
OFF_DIALOGUE_TIMESTAMP  = 13   # uint32 4
OFF_IS_JUMPING          = 17   # byte
OFF_IS_RECALLING        = 18   # byte
OFF_IS_AUTOATTACKING    = 19   # byte
OFF_LAST_PORTAL         = 20   # ulong  8
OFF_PORTAL_TIMESTAMP    = 28   # uint32 4
OFF_CURRENT_MAP         = 32   # uint32 4
OFF_CAMERA_PITCH        = 36   # float  4
OFF_EFFECT_COUNT        = 40   # uint32 4
OFF_EFFECTS_START       = 44
EFFECT_ENTRY_SIZE       = 8
MAX_EFFECTS             = 64

OFF_STRAT_FOLLOW_MOUNT      = 4096
OFF_STRAT_FOLLOW_RECALL     = 4097
OFF_STRAT_ACCEPT_PARTY      = 4098
OFF_STRAT_ACCEPT_RESS       = 4099
OFF_STRAT_ACCEPT_QUEST      = 4100
OFF_STRAT_CLOSE_EXJOURNAL   = 4101
OFF_STRAT_FOLLOW_JUMP       = 4102
OFF_STRAT_FOLLOW_SELECT     = 4103
OFF_STRAT_FOLLOW_ATTACK     = 4104
OFF_STRAT_FOLLOW_PORTAL     = 4105
OFF_STRAT_FOLLOW_DIRECTION  = 4106
OFF_STRAT_FOLLOW_DIALOGUE   = 4107
OFF_STRAT_STOP_DISTANCE     = 4112  # float
OFF_STRAT_AUTONOMY_TIME     = 4116  # float
OFF_STRAT_REFRESH_INTERVAL  = 4120  # int32
OFF_STRAT_CAPTAIN           = 4124  # 32 bytes UTF-8
OFF_STRAT_COMMANDER         = 4156  # 32 bytes UTF-8
NAME_SIZE                   = 32


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  μ S T A T U S R E A D E R
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μStatusReader:
  def __init__(self, char_name: str):
    self._path = μStatusReader.filePath(char_name)
    self._f    = None
    self._mm   = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def filePath(char_name: str) -> str:
    return os.path.join(P_DEFAULT_SHM_DIR, char_name.lower(), 'status')

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def open(self) -> bool:
    if not os.path.exists(self._path): return False
    try:
      self._f  = open(self._path, 'rb')
      self._mm = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_READ)
      return True
    except OSError:
      return False

  @property
  def hasStrategyData(self) -> bool:
    return self._mm is not None and len(self._mm) >= FILE_SIZE

  def close(self):
    if self._mm: self._mm.close(); self._mm = None
    if self._f:  self._f.close();  self._f  = None

  def __enter__(self): self.open(); return self
  def __exit__(self, *_): self.close()

  @property
  def isOpen(self) -> bool: return self._mm is not None

  # ── helpers ────────────────────────────────────────────────────────────────────────────────────────────────
  def _u8 (self, off: int) -> int:   return self._mm[off]
  def _b  (self, off: int) -> bool:  return self._mm[off] != 0
  def _u64(self, off: int) -> int:   return struct.unpack_from('<Q', self._mm, off)[0]
  def _u32(self, off: int) -> int:   return struct.unpack_from('<I', self._mm, off)[0]
  def _i32(self, off: int) -> int:   return struct.unpack_from('<i', self._mm, off)[0]
  def _i16(self, off: int) -> int:   return struct.unpack_from('<h', self._mm, off)[0]
  def _f32(self, off: int) -> float: return struct.unpack_from('<f', self._mm, off)[0]
  def _str(self, off: int, size: int = NAME_SIZE) -> str:
    raw = bytes(self._mm[off:off + size])
    return raw.split(b'\x00', 1)[0].decode('utf-8', errors='replace')

  # ── runtime fields ─────────────────────────────────────────────────────────────────────────────────────────
  @property
  def selectedEntity(self)    -> int:   return self._u64(OFF_SELECTED_ENTITY)
  @property
  def lastDialogue(self)      -> int:   return self._u8(OFF_LAST_DIALOGUE)
  @property
  def dialoguePosX(self)      -> int:   return self._i16(OFF_DIALOGUE_POS_X)
  @property
  def dialoguePosY(self)      -> int:   return self._i16(OFF_DIALOGUE_POS_Y)
  @property
  def dialogueTimestamp(self) -> int:   return self._u32(OFF_DIALOGUE_TIMESTAMP)
  @property
  def isJumping(self)         -> bool:  return self._b(OFF_IS_JUMPING)
  @property
  def isRecalling(self)       -> bool:  return self._b(OFF_IS_RECALLING)
  @property
  def isAutoAttacking(self)   -> bool:  return self._b(OFF_IS_AUTOATTACKING)
  @property
  def lastPortal(self)        -> int:   return self._u64(OFF_LAST_PORTAL)
  @property
  def portalTimestamp(self)   -> int:   return self._u32(OFF_PORTAL_TIMESTAMP)
  @property
  def currentMap(self)        -> int:   return self._u32(OFF_CURRENT_MAP)
  @property
  def cameraPitch(self)       -> float: return self._f32(OFF_CAMERA_PITCH)

  def effects(self) -> list[tuple[int, int]]:
    count = min(self._u32(OFF_EFFECT_COUNT), MAX_EFFECTS)
    return [(self._u32(OFF_EFFECTS_START + i * EFFECT_ENTRY_SIZE),
             self._u32(OFF_EFFECTS_START + i * EFFECT_ENTRY_SIZE + 4))
            for i in range(count)]

  # ── strategy directives ────────────────────────────────────────────────────────────────────────────────────
  @property
  def followMount(self)           -> bool:  return self._b(OFF_STRAT_FOLLOW_MOUNT)
  @property
  def followRecall(self)          -> bool:  return self._b(OFF_STRAT_FOLLOW_RECALL)
  @property
  def acceptParty(self)           -> bool:  return self._b(OFF_STRAT_ACCEPT_PARTY)
  @property
  def acceptRess(self)            -> bool:  return self._b(OFF_STRAT_ACCEPT_RESS)
  @property
  def acceptQuest(self)           -> bool:  return self._b(OFF_STRAT_ACCEPT_QUEST)
  @property
  def closeExplorerJournal(self)  -> bool:  return self._b(OFF_STRAT_CLOSE_EXJOURNAL)
  @property
  def followJump(self)            -> bool:  return self._b(OFF_STRAT_FOLLOW_JUMP)
  @property
  def followSelect(self)          -> bool:  return self._b(OFF_STRAT_FOLLOW_SELECT)
  @property
  def followAttack(self)          -> bool:  return self._b(OFF_STRAT_FOLLOW_ATTACK)
  @property
  def followPortal(self)          -> bool:  return self._b(OFF_STRAT_FOLLOW_PORTAL)
  @property
  def followDirection(self)       -> bool:  return self._b(OFF_STRAT_FOLLOW_DIRECTION)
  @property
  def followDialogue(self)        -> bool:  return self._b(OFF_STRAT_FOLLOW_DIALOGUE)
  @property
  def stopDistance(self)          -> float: return self._f32(OFF_STRAT_STOP_DISTANCE)
  @property
  def autonomyTime(self)          -> float: return self._f32(OFF_STRAT_AUTONOMY_TIME)
  @property
  def refreshInterval(self)       -> int:   return self._i32(OFF_STRAT_REFRESH_INTERVAL)
  @property
  def captain(self)               -> str:   return self._str(OFF_STRAT_CAPTAIN)
  @property
  def commander(self)             -> str:   return self._str(OFF_STRAT_COMMANDER)
