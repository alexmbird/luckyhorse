#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pickle import Pickler, Unpickler
import gzip, bz2
from itertools import islice
from operator import sub
import numpy as np


class MonkeySequenceMatch(object):
  
  '''
  Represent a sequence match.  Functions as an iterable beginning at the start
  of the match.
  '''
  
  def __init__(self, needle, haystack, start_idx):
    self.needle     = needle
    self.haystack   = haystack
    self.m_start    = start_idx
    self.m_end      = start_idx + len(needle)
  
  
  def __iter__(self):
    return islice(self.haystack, self.m_start, None)
  
  
  def __str__(self):
    match_seq = self.haystack[self.m_start:self.m_end]
    match_seq = ["%.3f" % met for met in match_seq]
    return "<%s %s>" % (
      self.__class__.__name__, match_seq
    )
  
  
  def following(self, n):
    "Return list of `n` metrics following the match"
    return self.haystack[ self.m_end : self.m_end + n ]
  
  
  def followingAll(self, funk, n):
    '''
    Return True if the `n` metrics following the match all evaluate to True
    under funk(m).
    '''
    for m in islice(self.haystack, self.m_end, self.m_end+n):
      if not funk(m):
        return False
    
    return True

    
  def dump(self):
    "Dump a tab-separated table of the match"
    for i in range(0, len(self.needle)):
      print("%s\t%s\t%s" % (i, self.needle[i], self.haystack[self.m_start+i]))





class MonkeySequence(object):
  
  '''
  A searchable, fittable sequence of values
  '''
  
  def __init__(self, data=None):
    super(MonkeySequence,self).__init__()
    self._data = data if data is not None else list()
  
  
  @staticmethod
  def load(filename):
    "Load in an existing sequence from disk"
    if filename.endswith('.gz'):
      fp = gzip.GzipFile(filename, 'r')
    elif filename.endswith('.bz2'):
      fp = bz2.BZ2File(filename, 'r')
    else:
      fp = open(filename, 'rb')
    u = Unpickler(fp)
    return MonkeySequence(data=u.load())


  def save(self, filename):
    "Save sequence to disk"
    if filename.endswith('.gz'):
      fp = gzip.GzipFile(filename, 'w')
    elif filename.endswith('.bz2'):
      fp = bz2.BZ2File(filename, 'w')
    else:
      fp = open(filename, 'wb')
    p = Pickler(fp)
    p.dump(self._data)
    fp.close()

  
  def __len__(self):
    return len(self._data)
  
  
  def __str__(self):
    return "<%s of %d items>" % (
      self.__class__.__name__, len(self._data)
    )
  
  
  def append(self, d):
    "Append a new point to the dataset"
    try:
      int(d)
    except ValueError:
      raise ValueError("Won't append non-numeric value '%s'" % (d,))
    self._data.append(d)
  
  def extend(self, d):
    "Extend the dataset on the RHS with list `d`"
    try:
      [int(m) for m in d]
    except ValueError:
      raise ValueError("Won't append non-numeric value from %s" % (d,))
    self._data.extend(d)
  
  
  def match(self, s):
    '''
    Look for the best correlation between the stored dataset and sequence `s`.
    Returns tuple of (start index in _data, iterator to our dataset beginning
    at start of match).
    
    Fudge is out of stock.
    
    Matching starts at the RHS of the dataset and travels left.  The closest
    match will be returned; in the event that >1 identical matches are found the
    left-most one will be returned so that you'll have the most trailing data
    available to work with.
    '''
    def normalize(seq):
      factor  = max( [abs(min(seq)), abs(max(seq))] )
      if factor == 0:
        return seq        # All zeroes, can't normalize
      else:
        return [ v / factor for v in seq]
    
    best_dist       = None
    best_start_idx  = None
    norm_s          = normalize(s)
    size            = len(norm_s)
    
    # Scan the dataset from the RHS looking for the closest match to `s`
    for block_start in range(len(self._data)-size, 0, -1):
      norm_candidate  = normalize(self._data[block_start : block_start+size])
      distances       = map(sub, norm_candidate, norm_s)
      abs_distances   = map(abs, distances)
      total_distance  = sum(abs_distances)
      if best_dist is None or total_distance <= best_dist:
        best_dist       = total_distance
        best_start_idx  = block_start
    
    #print("MATCH: %s" % (norm_candidate,))
    return MonkeySequenceMatch(s, self._data, best_start_idx)





