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
import os
import sqlite3
from helpers.util import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from widgets.μItemsTable import μItemData

# StorageType values must match C# enum
P_STORAGE_INVALID        = 0
P_STORAGE_INVENTORY      = 1
P_STORAGE_CHARACTER_BANK = 2
P_STORAGE_SHARED_BANK    = 3
P_STORAGE_REINCARNATION  = 4
P_STORAGE_GUILD_GENERAL1 = 5
P_STORAGE_GUILD_GENERAL2 = 6
P_STORAGE_GUILD_OFFICER1 = 7
P_STORAGE_GUILD_OFFICER2 = 8
P_STORAGE_GUILD_CHEST_SM = 9
P_STORAGE_GUILD_CHEST_LG = 10

DB_ITEM_COLS = ["id","storage_type","name","owner_id","owner_name","weenie_id","type",
                "quantity","qualifier","value_copper","hardness","durability","icon_id",
                "description","min_level","material","is_junk","is_locked","is_minor_artifact",
                "is_sellable","set_bonus_1","set_bonus_2","current_slot","binding","equips_to",
                "augments","effects"]

# ─────────────────────────────────────────────────────────────────────────────────────────────────
def resolveOwnerName(ownerName: str) -> str:
  if not ownerName.startswith("0x"):
    return ownerName
  from μWorlds import μWorldList
  try:
    server = μWorldList.getServerName()
  except Exception:
    return ownerName
  settings = loadExtendedSettings()
  server_data = settings.get(server, {})
  if not isinstance(server_data, dict):
    return ownerName
  normalized = {
    (f"0x{k:X}" if isinstance(k, int) else k): v
    for k, v in server_data.items()
  }
  entry = normalized.get(ownerName.upper(), normalized.get(ownerName, {}))
  if isinstance(entry, dict) and "guildName" in entry:
    return entry["guildName"]
  return ownerName

# ─────────────────────────────────────────────────────────────────────────────────────────────────
def getVaultDBPath() -> str:
  from μWorlds import μWorldList
  try:
    server = μWorldList.getServerName()
  except Exception:
    server = "default"
  return os.path.join(P_DEFAULT_CONFIGDIR, f"storage{server}.db")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
def openVaultDB() -> sqlite3.Connection:
  os.makedirs(P_DEFAULT_CONFIGDIR, exist_ok=True)
  conn = sqlite3.connect(getVaultDBPath(), timeout=10)
  conn.execute("PRAGMA journal_mode=WAL")
  conn.execute("PRAGMA busy_timeout=5000")
  conn.execute("""
    CREATE TABLE IF NOT EXISTS items (
      id            INTEGER PRIMARY KEY,
      storage_type  INTEGER NOT NULL DEFAULT 0,
      name          TEXT    NOT NULL DEFAULT '',
      owner_id      INTEGER NOT NULL DEFAULT 0,
      owner_name    TEXT    NOT NULL DEFAULT '',
      weenie_id     INTEGER NOT NULL DEFAULT 0,
      type          TEXT    NOT NULL DEFAULT '',
      quantity      INTEGER NOT NULL DEFAULT 0,
      qualifier     TEXT    NOT NULL DEFAULT '',
      value_copper  INTEGER NOT NULL DEFAULT 0,
      hardness      INTEGER NOT NULL DEFAULT 0,
      durability    INTEGER NOT NULL DEFAULT 0,
      icon_id       INTEGER NOT NULL DEFAULT 0,
      description   TEXT    NOT NULL DEFAULT '',
      min_level     INTEGER NOT NULL DEFAULT 0,
      material      INTEGER NOT NULL DEFAULT 0,
      is_junk       INTEGER NOT NULL DEFAULT 0,
      is_locked     INTEGER NOT NULL DEFAULT 0,
      is_minor_artifact INTEGER NOT NULL DEFAULT 0,
      is_sellable   INTEGER NOT NULL DEFAULT 0,
      set_bonus_1   TEXT    NOT NULL DEFAULT '',
      set_bonus_2   TEXT    NOT NULL DEFAULT '',
      current_slot  INTEGER NOT NULL DEFAULT 0,
      binding       INTEGER NOT NULL DEFAULT 0,
      equips_to     TEXT    NOT NULL DEFAULT '',
      augments      TEXT    NOT NULL DEFAULT '',
      effects       TEXT    NOT NULL DEFAULT ''
    )
  """)
  conn.commit()
  return conn

# ─────────────────────────────────────────────────────────────────────────────────────────────────
def upsertVaultItem(conn: sqlite3.Connection, item: μItemData, storageType: int):
  is_bank      = storageType != P_STORAGE_INVENTORY
  augments_str = ",".join(str(a) for a in item._augments)
  effects_str  = "|".join(f"{k}={v}" for k, v in item._effects.items())

  if is_bank:
    conn.execute("""
      INSERT INTO items
        (id, storage_type, name, owner_id, owner_name, weenie_id, type,
         quantity, qualifier, value_copper, hardness, icon_id,
         description, min_level, material, is_minor_artifact,
         set_bonus_1, set_bonus_2, binding, augments,
         durability, is_junk, is_locked, is_sellable, equips_to,
         current_slot, effects)
      VALUES (?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?, 0,0,0,0,'', 4294967295,'')
      ON CONFLICT(id) DO UPDATE SET
        storage_type  = excluded.storage_type,
        name          = excluded.name,
        owner_id      = excluded.owner_id,
        owner_name    = excluded.owner_name,
        weenie_id     = excluded.weenie_id,
        type          = excluded.type,
        quantity      = excluded.quantity,
        qualifier     = excluded.qualifier,
        value_copper  = excluded.value_copper,
        hardness      = excluded.hardness,
        icon_id       = excluded.icon_id,
        description   = excluded.description,
        min_level     = excluded.min_level,
        material      = excluded.material,
        is_minor_artifact = excluded.is_minor_artifact,
        set_bonus_1   = excluded.set_bonus_1,
        set_bonus_2   = excluded.set_bonus_2,
        binding       = excluded.binding,
        augments      = excluded.augments
    """, (item._id, storageType, item._name, item._ownerID, item._ownerName,
          item._weenieID, item._type, item._quantity, item._qualifier,
          item._valueCopper, item._hardness, item._iconId,
          item._description, item._minLevel, item._material, item._isMinorArtifact,
          item._setBonus1, item._setBonus2, item._binding, augments_str))
  else:
    conn.execute("""
      INSERT INTO items
        (id, storage_type, name, owner_id, owner_name, weenie_id, type,
         quantity, qualifier, value_copper, hardness, durability, icon_id,
         description, min_level, material, is_junk, is_locked, is_sellable,
         is_minor_artifact, set_bonus_1, set_bonus_2, current_slot,
         binding, equips_to, augments, effects)
      VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?,?, ?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET
        storage_type  = excluded.storage_type,
        name          = excluded.name,
        owner_id      = excluded.owner_id,
        owner_name    = excluded.owner_name,
        weenie_id     = excluded.weenie_id,
        type          = excluded.type,
        quantity      = excluded.quantity,
        qualifier     = excluded.qualifier,
        value_copper  = excluded.value_copper,
        hardness      = excluded.hardness,
        durability    = excluded.durability,
        icon_id       = excluded.icon_id,
        description   = excluded.description,
        min_level     = excluded.min_level,
        material      = excluded.material,
        is_junk       = excluded.is_junk,
        is_locked     = excluded.is_locked,
        is_sellable   = excluded.is_sellable,
        is_minor_artifact = excluded.is_minor_artifact,
        set_bonus_1   = excluded.set_bonus_1,
        set_bonus_2   = excluded.set_bonus_2,
        current_slot  = excluded.current_slot,
        binding       = excluded.binding,
        equips_to     = excluded.equips_to,
        augments      = excluded.augments,
        effects       = excluded.effects
    """, (item._id, storageType, item._name, item._ownerID, item._ownerName,
          item._weenieID, item._type, item._quantity, item._qualifier,
          item._valueCopper, item._hardness, item._durability, item._iconId,
          item._description, item._minLevel, item._material,
          item._isJunk, item._isLocked, item._isSellable, item._isMinorArtifact,
          item._setBonus1, item._setBonus2, item._currentSlot,
          item._binding, item._equipsTo, augments_str, effects_str))

# ─────────────────────────────────────────────────────────────────────────────────────────────────
def purgeStaleVault(conn: sqlite3.Connection, storageType: int, ownerName: str, freshIds: set):
  if not freshIds:
    return
  placeholders = ",".join("?" * len(freshIds))
  conn.execute(
    f"DELETE FROM items WHERE storage_type=? AND owner_name=? AND id NOT IN ({placeholders})",
    [storageType, ownerName] + list(freshIds)
  )
