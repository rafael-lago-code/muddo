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
#
import queue, threading, time, random
from helpers.μPrint import χPrint


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  D I S P A T C H E R
#
#   This is a static class. Don't instantiate it.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χDispatcher():
  _initLock = threading.Lock()
  _isInitialized = False
  eventsQueue = None
  eventHandlers : dict = {}  # key → list[callback]
  fateHandlers  : dict = {}  # key → list[callback], each fires once then removed
  isRunning = True
  daemonThread : threading.Thread = None

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __new__(cls):
        raise TypeError("cDispatcher is a static class and cannot be instantiated.")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def start(cls):
    with cls._initLock:
      if cls._isInitialized: return
      cls.eventsQueue   = queue.Queue()
      cls.eventHandlers = {}
      cls.fateHandlers  = {}
      cls.isRunning     = True
      cls.daemonThread  = threading.Thread(target=cls.daemonLoop, daemon=True)
      cls.daemonThread.start()
      cls._isInitialized = True
      χPrint.info(f"cDispatcher started")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def connect(cls, eventKey, callback):
    if not cls._isInitialized: χDispatcher.start()
    handlers = cls.eventHandlers.setdefault(eventKey, [])
    if callback not in handlers:
      handlers.append(callback)
    if callback in cls.fateHandlers.get(eventKey, []):
      χDispatcher.disfate(eventKey, callback)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def disconnect(cls, eventKey, callback=None):
    if callback is None:
      cls.eventHandlers.pop(eventKey, None)
    elif eventKey in cls.eventHandlers:
      cls.eventHandlers[eventKey] = [cb for cb in cls.eventHandlers[eventKey] if cb != callback]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Similar to connect, but each handler fires only once then is removed
  @classmethod
  def fate(cls, eventKey, callback):
    if not cls._isInitialized: χDispatcher.start()
    handlers = cls.fateHandlers.setdefault(eventKey, [])
    if callback not in handlers:
      handlers.append(callback)
    if callback in cls.eventHandlers.get(eventKey, []):
      χDispatcher.disconnect(eventKey, callback)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def disfate(cls, eventKey, callback=None):
    if callback is None:
      cls.fateHandlers.pop(eventKey, None)
    elif eventKey in cls.fateHandlers:
      cls.fateHandlers[eventKey] = [cb for cb in cls.fateHandlers[eventKey] if cb != callback]

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Synchronous emit — calls all handlers inline, does not queue
  @classmethod
  def fulfill(cls, eventKey, data):
    if not cls._isInitialized: χDispatcher.start()
    for cb in cls.eventHandlers.get(eventKey, []):
      cb(data)
    for cb in cls.fateHandlers.pop(eventKey, []):
      cb(data)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def contains(cls, item) -> bool:
    return bool(cls.eventHandlers.get(item)) or bool(cls.fateHandlers.get(item))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Asynchronous emit — queues event, daemonLoop dispatches it
  @classmethod
  def emit(cls, eventKey, data):
    if not cls._isInitialized: χDispatcher.start()
    cls.eventsQueue.put((eventKey, data))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def daemonLoop(cls):
    if not cls._isInitialized:
      χDispatcher.start()
    while cls.isRunning:
      try:
        eventKey, data = cls.eventsQueue.get(timeout=0.05)
        for cb in list(cls.eventHandlers.get(eventKey, [])):
          cb(data)
        for cb in cls.fateHandlers.pop(eventKey, []):
          cb(data)
      except queue.Empty:
        time.sleep(0.005)
        continue
      except Exception as ex:
        import traceback
        χPrint.error(f"cDispatcher.daemonLoop: unknown error while processing {ex}\n{traceback.format_exc()}", ex)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def stop(cls):
    cls.isRunning = False
    if cls.daemonThread: cls.daemonThread.join(timeout=1.0)
    cls.eventsQueue   = None
    cls.eventHandlers = {}
    cls.fateHandlers  = {}
    cls.daemonThread  = None


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S I G N A L
#
#   Instance-level signal backed by χDispatcher. Mimics PyQt signal API.
#   Use in __init__: self.mySignal = χSignal()
#   Then:           self.mySignal.connect(cb)
#                   self.mySignal.fate(cb)
#                   self.mySignal.emit(data)
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χSignal:
  _counter = 0
  _lock    = threading.Lock()

  def __init__(self):
    with χSignal._lock:
      χSignal._counter += 1
      self._key = f'χSignal.{χSignal._counter}'
    if not χDispatcher._isInitialized:
      χDispatcher.start()
    χDispatcher.eventHandlers.setdefault(self._key, [])
    χDispatcher.fateHandlers.setdefault(self._key, [])

  def connect(self, callback):         χDispatcher.connect(self._key, callback)
  def disconnect(self, callback=None): χDispatcher.disconnect(self._key, callback)
  def fate(self, callback):            χDispatcher.fate(self._key, callback)
  def disfate(self, callback=None):    χDispatcher.disfate(self._key, callback)
  def emit(self, data=None):           χDispatcher.emit(self._key, data)
  def fulfill(self, data=None):        χDispatcher.fulfill(self._key, data)

  def cleanup(self):
    χDispatcher.eventHandlers.pop(self._key, None)
    χDispatcher.fateHandlers.pop(self._key, None)

  def __del__(self):
    self.cleanup()
