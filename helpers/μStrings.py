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
from typing import TYPE_CHECKING
import re
# if TYPE_CHECKING:
#    from μString import μString

# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#   alphaRange
#   Generates a range of strings from start to stop, where start and stop are alphanumerics
def alphaRange(start, stop : str) -> list[str]:
  try:
    μstart = int(start)
    μstop = int(stop)
    return [μString(i) for i in range(μstart, μstop + 1)]
  except:
    μstart = ord(start)
    μstop = ord(stop)
    return [μString(chr(i)) for i in range(μstart, μstop + 1)]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    expandRange
#    Turns ranges like "1:4" or "a-b" or "a-b,k,f" into a list of STRINGS corresponding to all values in
#    the range.
def expandRange(text : str) -> list[str]:
  text = text.split(',')
  if len(text)>1:
    out = []
    for s in text: out += expandRange(s)
    return out
  else:
    text = text[0]
    if "-"   in text: splitIdx = text.find('-')
    elif ":" in text: splitIdx = text.find(':')
    elif "~" in text: splitIdx = text.find('~')
    else: return [μString(text)]
    return alphaRange(text[:splitIdx], text[splitIdx+1:])

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    expandRepeaters
#    Turns strings such as "prefix{1-3}suffix" into a list of "prefix1suffix, prefix2suffix, prefix3suffix".
#    Accepted ranges are the same as expandRange
def expandRepeaters(text : str) -> list:
  if "{"   in text:
    sB = text.find('{')
    eB = text.find('}')
    prefix = text[:sB]
    rng = text[sB+1:eB]
    suffix = text[eB+1:]
    # print(f" {sB} {eB} {prefix} {rng} {suffix}")
    out = []
    for s in [prefix + i + suffix for i in expandRange(rng)]: out += expandRepeaters(s)
    return out
  else:
    return [μString(text)]

P_GROUPING={"\"":"\"", "(":")", "{":"}", "[":"]", "<":">"}
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    splitGroups
#    Splits a string by a delimiter while respecting groups such as "<a,b,c>, {d,e,f}, [g,h,i]"
def splitGroups(text: str, delim : str = ",", strip: str = " ") -> list[str]:
  parts = []
  i = 0
  j = 0
  while j < len(text):
    if text[j]==delim:
      parts.append(text[i:j])
      i=j+1
    elif text[j] in P_GROUPING.keys():
      g = P_GROUPING[text[j]]
      while j+1<len(text) and text[j+1]!=g: j+=1
      j+=1
    j+=1
  parts.append(text[i:])
  if strip: return [μString(p.strip(strip)) for p in parts if p.strip(strip)]
  else:     return [μString(p) for p in parts]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    dictionary
#    Turns a string into a dictionary by splitting it by a delimiter and then automagically figuring out
#    key-value pairs. For example, "a=1,b=2,c=3" with delim "," would return {"a":"1", "b":"2", "c":"3"}
def dictionary(text: str, delim : str = ",", strip: str = " ") -> dict:
  out = {}
  for p in splitGroups(text, delim, strip):
    if "=" in p:
      k,v = p.split("=",1)
      out[k.strip(strip)] = guess(v.strip(strip))
    elif ":" in p:
      k,v = p.split(":",1)
      out[k.strip(strip)] = guess(v.strip(strip))
    else:
      out[p.strip(strip)] = None
  return out

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    guess
#    Tries to guess the type of a string by trying to convert it to int, then float, and if all fails, string
def guess(text: str):
  try:
    return int(text)
  except: pass
  try:
    return float(text)
  except: pass
  text = text.strip()
  if text.lower() == 'true':  return True
  if text.lower() == 'false': return False
  if text.startswith(tuple(P_GROUPING.keys())) and text.endswith(tuple(P_GROUPING.values())):
    if text.startswith("\"") and text.endswith("\""):
      return text[1:-1]
    else:
      return splitGroups(text[1:-1])
  return μString(text)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    replaceAlias
#    Expands one alias and replaces eventual tokens:
#
#    replaceAlias('m6a','m$1a','my_$1_alias')   = 'my_6_alias'
#    replaceAlias('m{1-3}a','m$1a','my_$1_alias')   = 'my_{1-3}_alias'
#         
def replaceAlias(text: str, key: str, translation: str) -> str:
  body  = re.sub(r'\\\$\d', lambda m: r'(\w+|\{[^}]+\})', re.escape(key))
  left  = r'(?<![\w$])' if re.match(r'[\w$]', key[:1])  else ''
  right = r'(?![\w$])'  if re.match(r'[\w$]', key[-1:]) else ''
  def repl(m: re.Match) -> str:
    s = translation
    for i, v in enumerate(m.groups(), 1): s = s.replace(f'${i}', v)
    return s
  return μString(re.sub(left + body + right, repl, text))

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    globmatch
#    Match s against a glob pattern or tuple of patterns. * matches any substring.
def globmatch(s: str, pattern, case: bool = False) -> bool:
  if isinstance(pattern, (list, tuple)): return any(globmatch(s, p, case) for p in pattern)
  regex = re.escape(str(pattern)).replace(r'\*', '.*')
  flags = re.DOTALL | (0 if case else re.IGNORECASE)
  return bool(re.fullmatch(regex, str(s), flags=flags))

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    contains
#    Check if s contains sub (or any element if sub is a tuple).
def contains(s: str, sub) -> bool:
  if isinstance(sub, (list, tuple)): return any(str(x) in str(s) for x in sub)
  return str(sub) in str(s)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    fileContents
#    returns a tuple containing each line in a file
def fileContents(path) -> tuple[str]:
  with open(path, 'r') as f:
    return tuple(μString(line.rstrip('\n')) for line in f if line.strip())
  
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    hasKeywords
#    returns a tuple containing each line in a file
def hasKeyword(text, keyword : str):
  text = ' '.join(text) if isinstance(text, (list, tuple)) else text
  return bool(re.search(rf'\b{keyword}\b', text))

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    fullExpansion    
#    expand braces in a loop until there is nothing more to expand. Returns a μString
def fullExpansion(text) -> str:
  while "{" in text:
    text = μString(text).split(",")
    parsed = []
    for word in list(text):
      parsed += μString(word).expand()
    text = ", ".join(parsed)
  return μString(text)

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
#    normalize
#    removes double spaces and newlines from string
def normalize(text) -> str:
  return μString(" ".join(str(text).split()))


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S T R I N G 
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class μString(str):
  def __new__(cls, value):
    return super().__new__(cls, value)
    
  __hash__ = str.__hash__
  def __eq__(self, other): return globmatch(self, other)
  def __ne__(self, other): return not self.__eq__(other)
  def __contains__(self, sub): return contains(self, sub) 
  def expand(self): return expandRepeaters(self)
  def fullExpansion(self): return fullExpansion(self)
  def split(self, sep : str = None, strip: str = " "): return splitGroups(self, sep, strip)
  def replace(self, key: str, translation: str): return replaceAlias(self, key, translation)
  def guess(self): return guess(self)
  def dictionary(self, delim : str = ",", strip: str = " "): return dictionary(self, delim, strip)
  def keywordIn(self, text : str): return hasKeyword(text, self)
  def hasKeyword(self, keyword : str): return hasKeyword(self, keyword)
  def normalize(self): return normalize(self)

  def __add__(self, other): return μString(super().__add__(other))
  def __radd__(self, other): return μString(str(other) + str(self))
  def join(self, iterable): return μString(super().join(iterable))
  def strip(self, chars=None):  return μString(super().strip(chars))
  def lstrip(self, chars=None): return μString(super().lstrip(chars))
  def rstrip(self, chars=None): return μString(super().rstrip(chars))
  
