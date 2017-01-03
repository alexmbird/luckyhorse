#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time, datetime
import threading

from blist import sortedlist
from operator import itemgetter

from utils.time.tools import DT_FORMAT_ISO_WITHOUT_MS_LITTLE_T






class HorseyTiem(object):
  
  '''
  Time manager for the Lucky Horse.  All enquiries about current time should be
  directed this class which will return correct timestamps if running live or
  an appropriate fake time if backtesting.
  
  Also handles timed callbacks with setTimer() and ensures they get called
  appropriately after an override().  DEAR GOD IS THIS THING NOT THREADSAFE.
  '''
  
  def __init__(self):
    super(HorseyTiem,self).__init__()
    self._lock_override       = threading.Lock()
    self._override_timestamp  = None
    
    # Can only order by numeric fields, not function refs
    self._lock_timers   = threading.Lock()
    self._timers        = sortedlist(key=lambda t: t[0:1])  # (ts, prio, callback)
  
  
  def printable(self):
    "Return a printable version of our assumed current time"
    tstruct = time.gmtime(self.time())
    return time.strftime(DT_FORMAT_ISO_WITHOUT_MS_LITTLE_T, tstruct)
  

  def override(self, ts):
    '''
    Override the answer we will give to questions about the current time.
    
    `ts`  - a timestamp we will always respond with, or 'None' meaning go back
            to returning the real time.
    '''
    with self._lock_override:
      self._override_timestamp = ts
    #print("Overrode; time is now %s" % self.time())
    self.runTimers()
  
  
  def is_overridden(self):
    "Threadsafe way to check if time is presently overridden"
    with self._lock_override:
      return self._override_timestamp is not None
    
    
  def time(self):
    '''
    Return one of:
      - the real time, if no override is in place
      - the most recently set override timestamp
    '''
    with self._lock_override:
      if self._override_timestamp is None:
        return time.time()
      else:
        return self._override_timestamp
  
  
  def sleep(self, sec):
    "Sleep for `sec` seconds, correctly firing any timers we encounter"
    while sec > 0:
      with self._lock_timers:
        t = self.time()
        if len(self._timers) and self._timers[0][0] < t + sec:
          wait = self._timers[0][0] - t
        else:
          wait = sec
      self._sleep( wait )
      self.runTimers()
      sec -= wait
  
  
  def _sleep(self, sec):
    "Sleep, without paying any attention to timers"
    if self.is_overridden():
      self._override_timestamp += sec
    else:
      time.sleep(sec)

    
  def setTimer(self, callback, ts, priority=0):
    '''
    Set a callback to be called at a particular time.  If multiple callbacks
    are scheduled for the same time, call in ascending order of priority.
    
    If `ts` is +ve, treat it as an absolute time to fire the timer.
    If `ts` is -ve, treat it as a number of seconds to wait.
    
    '''
    if ts == 0:
      raise ValueError("Refusing to set a timer that fires immediately")
    if ts < 0:
      ts = self.time() - ts
    if ts < self.time():
      raise ValueError("You can't set a timer for the past")
    if not callable(callback):
      raise ValueError("Callback %s isn't callable!" % (callback,))
      
    with self._lock_timers:
      if callback in map(itemgetter(2), self._timers):
        raise ValueError("Callback %s is already scheduled; you can't have it more than once" % callback)
      # This tuple is special; sortedlist will sort in order of timestamp/priority
      t = (ts, priority, callback)
      self._timers.add(t)
  
  
  def runTimers(self):
    '''
    Run any timers that have become overdue & remove them from the list.  There
    is one problem with this: if you take a large jump forward in time
    (unlikely) timers which would have been /created/ in the intervening period
    will never exist.  This means that during a long data-drought you might not
    calculate indicators.
    
    It isn't really a problem unless you use very short term timers.
    '''
    # NB: while we run through this list the callbacks may set new timers!
    #     Fortunately the list is automatically sorted so it is always sane to
    #     examine the first item.
    #
    # Why the "while True" chicanery?  So we hold the lock for as short a time
    # as possible.  Otherwise we would deadlock if anything in a callback tried
    # to set a new timer.
    while True:
      with self._lock_timers:
        if len(self._timers) == 0 or self._timers[0][0] > self.time():
          break   # Nothing due
        ts, prio, callback = self._timers.pop(0)
      #print("Running timer %s @ %s" % (callback, self.time()))
      callback()
  
  
  def resetTimers(self):
    "Destroy all timers.  Only for testing."
    with self._lock_timers:
      self._timers = sortedlist()
  
  
  
  
  
