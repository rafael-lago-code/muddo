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


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  M A C R O   P A R S E R
#
#   Pipeline:
#     1. Validate aliases (discard broken $N refs)
#     2. Apply alias substitution to full script body (catches simple + parametrised
#        aliases before any splitting can disrupt word boundaries)
#     3. Split body by ';' → individual scripts
#     4. For each script, partition on the FIRST ':' → actor_part / action_part
#     5. Per token (actors and actions separately):
#           a. brace-expand  (e.g. b4k{1-3} → b4k1, b4k2, b4k3)
#           b. alias sub again (catches parametrised aliases whose $N token is
#              now a concrete value after expansion)
#     6. Resolve meta actors at consolidation time:
#           all / self / etal → expand to all known bridge names
#           none             → skip entire script
#           focus / any      → kept as literal keys, resolved at fire time
#     7. Resolve self / all in action tokens per destination bridge:
#           self → that bridge's name
#           all  → comma-joined list of all bridge names
#           focus / any / etal / none → left verbatim (runtime concern)
#
#   Output: consolidated[hotkey] = {actor: [action_str, ...]}
#           meta[hotkey]         = {'icon': str|None, 'names': set()}
#
#   One flat ordered action list per actor → one execute() call per bridge.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭

import re
from helpers.μStrings import splitGroups, expandRepeaters, replaceAlias
from helpers.μPrint import μPrint


class MacroParser:

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def _validateAliases(aliases: dict) -> dict:
    valid = {}
    for k, a in aliases.items():
      keyIds   = set(re.findall(r'\$(\d)', k))
      transIds = set(re.findall(r'\$(\d)', a))
      if not transIds.issubset(keyIds):
        μPrint.error(f'[MacroParser] discarding alias "{k}" → "{a}" ($N mismatch)')
        continue
      valid[k] = a
    return valid

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def _applyAliases(text: str, aliases: dict) -> str:
    for k, a in aliases.items():
      text = replaceAlias(text, k, a)
    return text

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _expandAndAlias(cls, token: str, aliases: dict) -> list[str]:
    """Brace-expand one token, then run alias sub on each result."""
    result = []
    for t in expandRepeaters(token.strip()):
      t = t.strip()
      t = cls._applyAliases(t, aliases)
      if t:
        result.append(t)
    return result

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _parseActors(cls, actor_part: str, aliases: dict, bridge_names: list[str]) -> list[str] | None:
    """
    Parse the actor portion of a script.
    Returns list of resolved actor names, or None if the script should be skipped (none actor).
    'focus' and 'any' are returned as literal strings for late resolution.
    """
    resolved = []
    for raw in [a.strip().lower() for a in actor_part.split(',') if a.strip()]:
      for token in cls._expandAndAlias(raw, aliases):
        token = token.strip().lower()
        if token == 'none':
          return None
        elif token in ('all', 'self', 'etal'):
          for b in bridge_names:
            if b not in resolved:
              resolved.append(b)
        elif token in ('focus', 'any'):
          if token not in resolved:
            resolved.append(token)
        else:
          if token not in resolved:
            resolved.append(token)
    return resolved

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _parseActions(cls, action_part: str, aliases: dict) -> list[str]:
    """Split the action portion by comma (group-aware), then expand and alias each token."""
    result = []
    for token in splitGroups(action_part.strip(), ','):
      result.extend(cls._expandAndAlias(token, aliases))
    return result

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @staticmethod
  def _resolveActionsForBridge(actions: list[str], bridge_name: str, all_bridges_str: str) -> list[str]:
    """
    Substitute 'self' and 'all' in action strings for a specific destination bridge.
    focus/any bridges skip substitution — they resolve at fire time.
    """
    if bridge_name in ('focus', 'any'):
      return list(actions)
    resolved = []
    for action in actions:
      action = re.sub(r'\bself\b', bridge_name,    action)
      action = re.sub(r'\ball\b',  all_bridges_str, action)
      resolved.append(action)
    return resolved

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def consolidate(cls, active_sets, aliases: dict, bridge_names: list[str]) -> tuple[dict, dict]:
    """
    active_sets : list of cMacroSet objects (must have a .data attribute)
    aliases     : raw alias dict (will be validated internally)
    bridge_names: lowercase names of all currently known bridges

    Returns:
      consolidated[hotkey] = {actor: [action_str, ...]}
      meta[hotkey]         = {'icon': str|None, 'names': set()}
    """
    aliases         = cls._validateAliases(aliases)
    all_bridges_str = ', '.join(bridge_names)
    consolidated    = {}
    meta            = {}

    for cset in active_sets:
      for row in cset.data:
        icon, name  = row[0], row[1]
        raw_hotkey  = (row[2] or '').strip()
        raw_scripts = (row[3] or '').strip()

        if not raw_hotkey or not raw_scripts:
          continue

        hotkey = cls._applyAliases(raw_hotkey, aliases).replace(' ', '').lower()
        if not hotkey or hotkey == 'none':
          continue

        m = meta.setdefault(hotkey, {'icon': None, 'names': set()})
        if icon: m['icon'] = icon
        if name: m['names'].add(name)

        # alias substitution on full body before any splitting
        body    = cls._applyAliases(raw_scripts, aliases)
        scripts = [s.strip() for s in body.split(';') if s.strip()]
        cs      = consolidated.setdefault(hotkey, {})

        for script in scripts:
          if ':' in script:
            actor_part, _, action_part = script.partition(':')
          else:
            actor_part, action_part = 'self', script

          actors = cls._parseActors(actor_part, aliases, bridge_names)
          if not actors:  # None (skipped) or empty
            continue

          actions = cls._parseActions(action_part, aliases)
          if not actions:
            continue

          for actor in actors:
            resolved = cls._resolveActionsForBridge(actions, actor, all_bridges_str)
            cs[actor] = cs.get(actor, []) + resolved

    return consolidated, meta
