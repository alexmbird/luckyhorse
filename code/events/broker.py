#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import threading, queue
from operator import itemgetter
from blist import sortedlist

from utils.time import HORSEYTIEM
import time   # Just for the ToyEventReceiver

from events import BaseEvent
from warnings import warn




class Broker(object):
  "Event broker that dispatches immediately in the same thread"
  
  def __init__(self):
    super(Broker,self).__init__()
    # Can only order by the prio column; method refs are not orderable
    self._callbacks       = sortedlist(key=lambda t: t[0])  # (prio, callback)
  
  def subscribe(self, callback, priority):
    "Subscribe a callback to events from this source"
    # NB: special tuple, will naturally sort correctly
    if not callable(callback):
      raise ValueError("Callback %s isn't callable!" % (callback,))
    t = (priority, callback)
    self._callbacks.add(t)

  def publish(self, e):
    "Publish event object to all our subscribers, in the same thread"
    for prio, callback in self._callbacks:
      callback(e)




  
  
class QueuedBrokerBundle(object):
  
  '''
  Bundle up a number of labeled brokers behind a single, shared, threadsafe
  publishing queue.
  '''
  
  def __init__(self, maxsize=0):
    super(QueuedBrokerBundle,self).__init__()
    self._brokers   = {}
    self._queue     = queue.Queue(maxsize=maxsize)
  
  def __getitem__(self, i):
    if i not in self._brokers:
      self._brokers[i] = Broker()
    return self._brokers[i]

  def subscribe(self, *args, **kwargs):
    raise RuntimeError("You subscribe to channels, not the whole bundle")
  
  def publish(self, b, e):
    "Publish event `e` to broker `b`"
    self._queue.put( (b, e) )


  def run(self, src_thread_group=[], fake_time=False, once=False, timeout=0.5):
    '''
    Fetch events off the queue and dispatch to their consumers.
    
    `src_thread_group`  - when all of these have exited, we quit
    `fake_time`         - use ts_update attr from events to set the clock time
    `once`              - consume all items in queue then quit
    '''
    while True:
      try:
        b, e = self._queue.get(True, timeout)
      except queue.Empty:
        if once:    # Failed to read.  Should we be quitting?
          break
        if not any(map(lambda t: t.is_alive(), src_thread_group)):
          break
      else:
        if fake_time and isinstance(e, BaseEvent):
          HORSEYTIEM.override(e.ts_update)
        b.publish(e)
        self._queue.task_done()
        HORSEYTIEM.runTimers()






class ToyEventReceiver(object):
  
  '''
  Simple tool to receive and record events.  Useful for testing, not much else.
  '''
  
  def __init__(self, delay=None, timefunk=time.time):
    '''
    `timefunk`   - Where to record time from.  You may wish to use HorseyTiem.
    '''
    self.events     = []
    self.delay      = delay
    self.timefunk   = timefunk
  
  def rcv(self, e=None):
    self.events.append( (self.timefunk(), e ) )
    if self.delay is not None:
      time.sleep(self.delay)
  
