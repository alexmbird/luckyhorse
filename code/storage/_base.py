#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from storage._connection import DbConnectionFactory
from collections import OrderedDict, deque
from blist import sortedlist
from operator import attrgetter
from itertools import islice
from threading import Lock

from utils.config import CONFIG
from utils.time import HORSEYTIEM


#
# Common database exceptions
#
class RecordError(Exception):
  "Some logical error with your data"

class RecordNotExistError(RecordError):
  "Record did not exist in DB"

class RecordAlreadyExistError(RecordError):
  "Record already existed"





class BaseStore(object):
  
  # A string of SQL to execute to make the tables for this store
  CREATE_SQL    = None
  
  
  def __init__(self, dbconf=None):
    
    fakt = DbConnectionFactory()

    # Allow alternate dbconf for testing
    if dbconf is None:
      self.db = fakt.connect(CONFIG['database'])
    else:
      self.db = fakt.connect(dbconf)
      

  def event(self, e):
    '''
    We will receive a stream of exchange events.  It's down to each Store class
    to decide what to accept and what to discard.
    '''
    pass
  



class EventCacheBase(object):
  
  '''
  Maintain a cache of events for a particular exchange.  This is a base:
  subclass it and set TS_ATTRIB for the event you want to cache.  Threadsafe.
  '''
  
  # This is a placeholder; set correctly for the type of event you're caching
  TS_ATTRIB           = None
  
  # Enough for even 14-day ADX
  CACHE_LATEST_DAYS   = 15.1
  
  def __init__(self):
    super(EventCacheBase,self).__init__()
    
    self._lock              = Lock()
    
    # This will return the thing we index on
    self._ts_attr_getter    = attrgetter(self.TS_ATTRIB)
    
    # Always cache the most recent day of trades.  Prepopulate it.
    self._cache_latest_sec  = 60*60*24*self.CACHE_LATEST_DAYS
    self._cache_latest_ev   = sortedlist(key=attrgetter('ts_exec'))
    self._cache_latest_ts   = sortedlist()   # Store timestamps separately for easy searching
  
  
  def get(self, p):
    '''
    Look for events fulfilling period `p` in cache and if possible, return them.
    Otherwise raise a RecordNotExist error.
    '''
    try:
      with self._lock:
        # This assumes that new events get straight into the cache
        if p.lhs_ts >= self._cache_latest_ts[0] and p.rhs_ts <= HORSEYTIEM.time():
          lhs_index  = self._cache_latest_ts.bisect_left(p.lhs_ts)
          rhs_index  = self._cache_latest_ts.bisect_left(p.rhs_ts)
          return tuple(islice(self._cache_latest_ev, lhs_index, rhs_index))
    except IndexError:
      pass
    
    raise RecordNotExistError()
  
  
  def getBeforeTs(self, ts):
    '''
    Return the last event that happened before `ts`
    '''
    try:
      with self._lock:
        if self._cache_latest_ts[0] < ts <= self._cache_latest_ts[-1]:
          index = self._cache_latest_ts.bisect_left(ts)
          return self._cache_latest_ev[index]
    except IndexError:
      pass
    
    raise RecordNotExistError("Not in cache")
  
    
  def addLatest(self, e):
    '''
    Add an event to the permanent cache bucket which stores the latest N events.
    '''
    with self._lock:
      self._cache_latest_ts.add(self._ts_attr_getter(e))
      self._cache_latest_ev.add(e)
      try:
        cutoff = HORSEYTIEM.time() - self._cache_latest_sec
        while self._cache_latest_ts[0] < cutoff:
          self._cache_latest_ts.pop(0)
          self._cache_latest_ev.pop(0)
      except IndexError:
        pass


