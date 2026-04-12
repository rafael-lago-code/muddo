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
#
import threading

class tStoppableThread(threading.Thread):
  def __init__(self, stopper : threading.Event, group = None, target = None, name = None, daemon = None):
    super().__init__(group, target, name, daemon=daemon)
    self.stopper = stopper
  
  def stop(self):
    self.stopper.set()