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
import queue, threading, time
from helpers.cPrint import cPrint

#---------------------------------------------------------------------------------------------------------------
#
#
#                                            D I S P A T C H E R
#                                  
#   This is a static class. Don't instantiate it.
#---------------------------------------------------------------------------------------------------------------
class cDispatcher():
  _initLock = threading.Lock()
  _isInitialized = False
  eventsQueue = None
  eventsData : dict = {}
  eventHandlers : dict = {}
  fateHandlers : dict = {}
  isRunning = True
  daemonThread : threading.Thread = None

  #----------------------------------------------------------------------------------------------------------
  def __new__(cls):
        raise TypeError("cDispatcher is a static class and cannot be instantiated.")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def start(cls):
    with cls._initLock:
      if cls._isInitialized: return
      cls.eventsQueue = queue.Queue()
      cls.eventsData = {}
      cls.eventHandlers = {}
      cls.fateHandlers = {}
      cls.isRunning = True
      cls.daemonThread = threading.Thread(target=cls.daemonLoop, daemon=True)
      cls.daemonThread.start()
      cls._isInitialized = True
      cPrint.info(f"cDispatcher started")

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def connect(cls, eventKey, callback):
    if not cls._isInitialized: cDispatcher.start()
    cls.eventHandlers[eventKey] = callback
  
  #----------------------------------------------------------------------------------------------------------
  # Similar to connect, but function will only be called once and then deleted
  @classmethod
  def fate(cls, eventKey, callback):
    if not cls._isInitialized: cDispatcher.start()
    cls.eventHandlers[eventKey] = callback

  #----------------------------------------------------------------------------------------------------------
  # Similar to emit + daemonLoop, doesn't need the daemon
  @classmethod
  def fulfill(cls, eventKey, data):
    if not cls._isInitialized: cDispatcher.start()
    if eventKey in cls.eventHandlers.keys(): 
      callback = cls.eventHandlers[eventKey]
      del cls.eventHandlers[eventKey]
      callback(data)
    elif eventKey in cls.fateHandlers.keys(): 
      callback = cls.fateHandlers[eventKey]
      del cls.fateHandlers[eventKey]
      callback(data)
  
  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def contains(cls, item) -> bool:
    return item in cls.eventHandlers.keys() or item in cls.fateHandlers.keys()

  #----------------------------------------------------------------------------------------------------------
  # can/will be triggered multiple times
  @classmethod
  def emit(cls, eventKey, data):
    if not cls._isInitialized: cDispatcher.start()
    cls.eventsQueue.put(eventKey)
    cls.eventsData[eventKey] = data

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def daemonLoop(cls):
    if not cls._isInitialized:
      cDispatcher.start()
    while cls.isRunning:
      try:
        e    = cls.eventsQueue.get(timeout=0.05)
        data = cls.eventsData[e]
        if e in cls.eventHandlers:
          cls.eventHandlers[e](data)
        elif e in cls.fateHandlers:
          handler = cls.fateHandlers[e]
          del cls.fateHandlers[e]
          handler(data)
      except queue.Empty:
        time.sleep(0.005)
        continue
      except Exception as e:
        import traceback
        cPrint.error(f"cDispatcher.daemonLoop: unknown error while processing {e}\n{traceback.format_exc()}", e)

  #----------------------------------------------------------------------------------------------------------
  @classmethod
  def stop(cls):
    cls.isRunning = False
    if cls.daemonThread: cls.daemonThread.join(timeout=1.0)
    cls.eventsQueue = None
    cls.eventHandlers = {}
    cls.fateHandlers = {}
    cls.eventsData = {}
    cls.daemonThread = None
