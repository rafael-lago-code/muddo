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
from helpers.χPrint import χPrint


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _runSafely(fn):
  try:
    fn()
  except Exception as ex:
    import traceback
    χPrint.error(f"χDispatcher: handler raised {ex}\n{traceback.format_exc()}", ex)


# ❖  T H R E A D   B A C K E N D
#
#    Qt-free backend. Owns a daemon thread; everything posted runs there, in order.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
class _ThreadBackend:
  def __init__(self):
    self.queue     = queue.Queue()
    self.isRunning = True
    self.thread    = threading.Thread(target=self._loop, daemon=True)
    self.thread.start()

  def _loop(self):
    while self.isRunning:
      try:    fn = self.queue.get(timeout=0.05)
      except queue.Empty: continue
      _runSafely(fn)

  def post(self, fn):
    self.queue.put(fn)

  # Returns whatever is still pending, so setup() can hand it to a new backend
  def drain(self) -> list:
    pending = []
    while True:
      try:    pending.append(self.queue.get_nowait())
      except queue.Empty: break
    return pending

  def stop(self):
    self.isRunning = False
    if self.thread: self.thread.join(timeout=1.0)
    self.thread = None


# ❖  Q T   B A C K E N D
#
#    Everything posted runs on the thread that built the backend - i.e. the Qt main thread, provided
#    setup(qt=True) is called from it. Cross-thread emits are queued by Qt onto the main event loop.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _makeQtBackend():
  from PyQt6.QtCore import QObject, pyqtSignal, Qt

  class _QtBackend(QObject):
    _sig = pyqtSignal(object)

    def __init__(self):
      super().__init__()
      # Queued explicitly, not Auto. Auto would notice that an emit from the main thread already sits on
      # the receiving thread and call straight through, so post() would run inline for main-thread callers
      # - breaking both the "returns immediately" contract and any coalescing built on top of it.
      self._sig.connect(self._run, Qt.ConnectionType.QueuedConnection)

    def _run(self, fn):
      _runSafely(fn)

    def post(self, fn):
      self._sig.emit(fn)

    # Already handed to Qt's event queue; nothing left for us to hold on to
    def drain(self) -> list:
      return []

    def stop(self):
      pass

  return _QtBackend()


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   🮿  D I S P A T C H E R
#
#   This is a static class. Don't instantiate it.
#
#
#   ── R E G I S T E R I N G ──────────────────────────────────────────────────────────────────────────────
#
#   connect(key, cb)     Permanent subscription. cb runs every time that key is raised, until something
#                        calls disconnect. Duplicates are ignored: connecting the same cb twice leaves one.
#                        If cb was registered with fate() it is promoted - moved out of the one-shot list
#                        into the permanent one, so it stops being consumed.
#
#   fate(key, cb)        One-shot subscription. cb runs on the next raise of that key and is dropped
#                        immediately after, whether the raise came from emit or fulfill. Mirror image of
#                        connect: registering a cb here that was already connect'ed demotes it.
#                        For request/response - a reply that arrives once and never again.
#
#   Both lists fire on every raise, connect'ed handlers first, then the fate ones. A key may hold any mix.
#   disconnect/disfate with cb=None wipe the whole list for that key.
#
#
#   ── R A I S I N G ──────────────────────────────────────────────────────────────────────────────────────
#
#   Same handlers, three different answers to "which thread, and when":
#
#   emit(key, data)      Worker lane. Returns immediately; handlers run later, on the dispatcher's own
#                        thread. Never the UI thread - so a handler is free to block on a file, a socket or
#                        sqlite. Ordering is preserved: one thread drains one queue.
#                        A handler that needs to touch a widget wraps that part in post().
#
#   fulfill(key, data)   No lane. Handlers run inline, on the calling thread, before fulfill returns.
#                        Use when the caller must know the handlers are done, or when it is already on the
#                        right thread. An exception here propagates to the caller; with emit it is caught
#                        and logged instead.
#
#   post(fn)             UI lane, and no keys involved - a bare callable, not a subscription. Runs fn on
#                        the Qt main thread (once setup(qt=True) has run), so fn may touch widgets.
#                        Returns immediately and never waits for fn.
#
#   Keeping emit off the UI thread is deliberate. The Milvian packet stream (χigGotData → parseData →
#   χigResponse) rides on it, thousands of packets during a vault scan; routing that through the Qt event
#   loop stalls the UI.
#
#   Whatever is handed to post() must be short - it shares the thread with the UI.
#
#
#   ── S U M M A R Y ──────────────────────────────────────────────────────────────────────────────────────
#
#     call                 thread            returns          keyed     may block
#     ─────────────────────────────────────────────────────────────────────────────
#     emit(key, data)      worker            immediately      yes       yes
#     fulfill(key, data)   caller's          after handlers   yes       caller's problem
#     post(fn)             Qt main           immediately      no        no
#
#   Without setup(qt=True) there is no Qt thread and post() falls through to the worker lane, so headless
#   use needs no special casing.
# 🬲🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭🬭
class χDispatcher():
  _initLock = threading.Lock()
  _isInitialized = False
  _isRunning = True
  _isQt = False
  workBackend = None         # always threaded; carries emit()
  uiBackend   = None         # Qt once setup(qt=True) ran, else the work backend; carries post()
  eventHandlers : dict = {}  # key → list[callback]
  fateHandlers  : dict = {}  # key → list[callback], each fires once then removed

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  def __new__(cls):
        raise TypeError("cDispatcher is a static class and cannot be instantiated.")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Call with qt=True from the Qt main thread, before anything emits. Calling it later still works: the old
  # backend is stopped and whatever it had queued is handed over.
  @classmethod
  def setup(cls, qt: bool = False):
    with cls._initLock:
      cls._isRunning = True
      if cls._isInitialized and cls._isQt == qt: return
      if cls._isInitialized:
        χPrint.warning(f"χDispatcher already running (qt={cls._isQt}); switching to qt={qt}")
      if cls.workBackend is None: cls.workBackend = _ThreadBackend()
      old = cls.uiBackend
      cls.uiBackend = _makeQtBackend() if qt else cls.workBackend
      cls._isQt = qt
      cls._isInitialized = True
      # Only retire a UI backend we built ourselves; when qt=False it is the work backend, still in use
      if old is not None and old is not cls.workBackend and old is not cls.uiBackend:
        for fn in old.drain(): cls.uiBackend.post(fn)
        old.stop()
      χPrint.info(f"cDispatcher started (qt={qt})")

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Ensures a backend exists. Falls back to the Qt-free one, so importing this module never drags in PyQt.
  # Deliberately does nothing once stop() ran: a lazy restart here would silently swap the Qt backend for the
  # threaded one midway through shutdown, and handlers would go back to touching widgets off-thread.
  @classmethod
  def start(cls):
    if not cls._isRunning: return
    if not cls._isInitialized: cls.setup(qt=False)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # UI lane. Runs fn on the Qt main thread. Returns immediately - never waits for fn.
  @classmethod
  def post(cls, fn):
    if not cls._isInitialized: cls.start()
    if not cls._isRunning: return
    cls.uiBackend.post(fn)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Permanent subscription: fires on every raise of eventKey until disconnected. Connecting twice still
  # leaves one entry. A callback currently registered as fate() is promoted here, so it stops being one-shot.
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
  # One-shot subscription: fires on the next raise of eventKey (emit or fulfill, either one) and is dropped
  # straight after. Mirror of connect - a callback currently connect'ed is demoted here. For replies that
  # arrive once.
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
  # Synchronous raise: handlers run inline, on this thread, before the call returns. Nothing is queued and
  # no thread hop happens, so an exception from a handler reaches the caller instead of being logged.
  @classmethod
  def fulfill(cls, eventKey, data):
    if not cls._isInitialized: χDispatcher.start()
    if not cls._isRunning: return
    cls._dispatch(eventKey, data)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def contains(cls, item) -> bool:
    return bool(cls.eventHandlers.get(item)) or bool(cls.fateHandlers.get(item))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Asynchronous raise: returns at once, handlers run later on the worker thread. Never the UI thread, so
  # handlers may block on IO; wrap any widget call in post(). One thread drains one queue, so order holds.
  @classmethod
  def emit(cls, eventKey, data):
    if not cls._isInitialized: χDispatcher.start()
    if not cls._isRunning: return
    cls.workBackend.post(lambda k=eventKey, d=data: cls._dispatch(k, d))

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  @classmethod
  def _dispatch(cls, eventKey, data):
    for cb in list(cls.eventHandlers.get(eventKey, [])):
      cb(data)
    for cb in cls.fateHandlers.pop(eventKey, []):
      cb(data)

  # ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  # Final. post/emit/fulfill go quiet afterwards instead of resurrecting a backend; call setup() to revive.
  @classmethod
  def stop(cls):
    cls._isRunning = False
    if cls.uiBackend is not None and cls.uiBackend is not cls.workBackend:
      cls.uiBackend.stop()
    if cls.workBackend is not None: cls.workBackend.stop()
    cls.uiBackend      = None
    cls.workBackend    = None
    cls.eventHandlers  = {}
    cls.fateHandlers   = {}
    cls._isInitialized = False


# 🬕🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂🬂
#   ❖  S I G N A L
#
#   Instance-level signal backed by χDispatcher. Mimics PyQt signal API; each instance owns a private key,
#   so the χDispatcher semantics apply verbatim:
#
#     sig.connect(cb)   permanent          sig.emit(data)      async, worker thread
#     sig.fate(cb)      fires once         sig.fulfill(data)   inline, calling thread
#
#   Use in __init__: self.mySignal = χSignal()
#
#   Keep the signal alive as long as the subscription matters: __del__ calls cleanup(), which drops every
#   handler for that key. A χSignal built as a local and emitted from will lose its handlers when it falls
#   out of scope, before an async emit has been drained. Store it on the instance.
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
