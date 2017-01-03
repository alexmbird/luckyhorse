#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest
from utils.monkeyseq import MonkeySequence
from itertools import islice, tee


class MonkeySequenceTest(unittest.TestCase):
  
  def _cmpseq(self, a, b):
    "Compare two sequences until one of them runs out"
    while True:
      try:
        if next(a) != next(b):
          return False
      except StopIteration:
        return True


  def test_simpleSequence(self):
    "Create sequence & add 100 items"
    seq = MonkeySequence()
    self.assertEqual(len(seq), 0)
    [seq.append(d) for d in range(0,123)]
    self.assertEqual(len(seq), 123)
  

  def test_matchOneExact(self):
    "One exact match in sequence"
    seq = MonkeySequence()
    [seq.append(d) for d in range(0,100000)]
    m1, m2 = tee( seq.match([4,5,6]), 2)
    print("%s" % (list(m1),))
    self.assertTrue(self._cmpseq(m2, iter(range(4, 99))))
  
  
  def test_matchManyExact(self):
    "Many matches exist; return left-most"
    seq = MonkeySequence()
    seq.extend( [1,1,1,2,2,2,2,1,1,1] )
    seq.extend( [9,9,9,2,2,2,2,9,9,9] )
    self.assertEqual(len(seq), 20)
    m1, m2 = tee( seq.match([2,2,2,2]), 2)
    print("Found %s" % (list(m1),))
    self.assertTrue(self._cmpseq(m2, iter([2,2,2,2,1])))
  
  
  def test_matchManyClosePos(self):
    "No exact match; two potentials.  Return the best."
    seq = MonkeySequence()
    seq.extend( [1,1,1,2,2,3,2,2,1,1,1] )
    seq.extend( [9,9,9,2,2,9,2,2,9,9,9] )
    self.assertEqual(len(seq), 22)
    m1, m2 = tee( seq.match([2,2,2,2,2]), 2)
    print("Found %s" % (list(m1),))
    self.assertTrue(self._cmpseq(m2, iter([2,2,3,2,2,1])))


  def test_matchManyCloseNeg(self):
    "No exact match; two potentials.  Return the best."
    seq = MonkeySequence()
    seq.extend( [1,1,1,2,2,-1,2,2,1,1,1] )
    seq.extend( [9,9,9,2,2,9,2,2,9,9,9] )
    self.assertEqual(len(seq), 22)
    m1, m2 = tee( seq.match([2,2,2,2,2]), 2)
    print("Found %s" % (list(m1),))
    self.assertTrue(self._cmpseq(m2, iter([2,2,-1,2,2,1])))

  
