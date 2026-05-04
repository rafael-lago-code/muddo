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

import re

#----------------------------------------------------------------------------------------------------------
#   alphaRange
#   Generates a range of strings from start to stop, where start and stop are alphanumerics
def alphaRange(start, stop : str) -> list[str]:
  try:
    μstart = int(start)
    μstop = int(stop)
    return [str(i) for i in range(μstart, μstop + 1)]
  except:
    μstart = ord(start)
    μstop = ord(stop)
    return [chr(i) for i in range(μstart, μstop + 1)]

#----------------------------------------------------------------------------------------------------------
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
    else: return [text]
    return alphaRange(text[:splitIdx], text[splitIdx+1:])

#----------------------------------------------------------------------------------------------------------
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
    return [text]

P_GROUPING={"\"":"\"", "(":")", "{":"}", "[":"]", "<":">"}
#----------------------------------------------------------------------------------------------------------
#    splitGroups
#    Splits a string by a delimiter while respecting groups such as "<a,b,c>, {d,e,f}, [g,h,i]"
def splitGroups(text: str, delim: str) -> list[str]:
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
  return parts
