#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from itertools import islice
import collections
from threading import Lock



def chunker(n, iterable):
  it = iter(iterable)
  return iter(lambda: tuple(islice(it, n)), ())


def next_or_none(gen):
  "Return next() of a generator or None if it's run out"
  try:
    return next(gen)
  except StopIteration:
    return None


  



#
# Merge overlapping ranges - used for merging down time periods
# See https://stackoverflow.com/questions/5679638/merging-a-list-of-time-range-tuples-that-have-overlapping-time-ranges
#

def mergeoverlapping(initialranges):
  i = sorted(set([tuple(sorted(x)) for x in initialranges]))

  # initialize final ranges to [(a,b)]
  f = [i[0]]
  for c, d in i[1:]:
      a, b = f[-1]
      if c<=b<d:
          f[-1] = a, d
      elif b<c<d:
          f.append((c,d))
      else:
          # else case included for clarity. Since 
          # we already sorted the tuples and the list
          # only remaining possibility is c<d<b
          # in which case we can silently pass
          pass
  return f




# Range but with steps < 1 - great for adding fake microseconds during testing
def hrange(start, stop, step):
  "Iterable range where step may be a float"
  for i in range(start, int(stop/step)):
    yield i * step

def infrange(start=0, step=1):
  "Range that goes on forever"
  i = start
  while True:
    yield i
    i += step







class LRUCache(object):
  
  '''
  A simple LRU cache based on collections.OrderedDict.
  '''
  def __init__(self, maxsize=16):
    super(LRUCache,self).__init__()
    self.maxsize    = maxsize
    self._cache     = collections.OrderedDict()
    self._lock      = Lock()

  def __contains__(self, k):
    with self._lock:
      return k in self._cache
  
  def __len__(self):
    with self._lock:
      return len(self._cache)
    
  def __getitem__(self, k):
    with self._lock:
      value = self._cache[k]
      self._cache.move_to_end(k)
      return value
  
  def __setitem__(self, k, v):
    with self._lock:
      self._cache[k] = v
      self._cache.move_to_end(k)
    self._trim()
  
  def _trim(self):
    "Obsolete least-used items out of the cache to bring it down to maxsize"
    with self._lock:
      while len(self._cache) > self.maxsize:
        self._cache.popitem(last=False)




