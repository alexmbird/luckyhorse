#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from collections import deque
from random import randint
import numpy as np

from utils.monkeytree import MonkeyNode, NoSuchNode
from utils.hmath import makeRandomSeq


class TestMonkeyTree(unittest.TestCase):
  
  def assertAlmostEqual(self, a, b):
    if not np.allclose([a], [b]):
      raise AssertionError("%s not close to %s" % (a,b))


  def test_createOne(self):
    "Create a single MonkeyNode"
    root = MonkeyNode()
    self.assertEqual(len(root), 0)
    s = deque( makeRandomSeq(8, [1,1]) )
    root.update(s)
    self.assertEqual(len(root), 1)
    root.checkCounts()
  
  
  def test_createMany(self):
    "A monkey tree 8 levels deep containing 1000 random sequences"
    root = MonkeyNode()
    for i in range(0, 1000):
      s = deque( makeRandomSeq(8, [1,1]) )
      root.update(s)

    root.checkCounts()
    root.checkProbabilityMass()
  

  def test_sortOrder(self):
    "An exact match is not available, return the least wrong candidate"
    root = MonkeyNode()
    root.update( deque( [1]*8 ) )
    root.update( deque( [1]*8 ) )
    root.update( deque( [4]*8 ) )
    pred = root.sortPredictions()
    triplet = pred[0]
    self.assertEqual(triplet[0], 1)
    self.assertEqual(triplet[1], 0.6666666666666666)
    triplet = pred[1]
    self.assertEqual(triplet[0], 4)
    self.assertEqual(triplet[1], 0.3333333333333333)
    

  def test_simplePredict(self):
    "Predictions from a sequence of 1's"
    root = MonkeyNode()
    root.update( deque( [1]*8 ) )
    self.assertEqual( root.predict( deque( [1]*4 )), 1 )
    root.update( deque( [2]*8 ) )
    self.assertEqual( root.predict( deque( [1]   )), 1 )
    self.assertEqual( root.predict( deque( [1]*4 )), 1 )
    self.assertEqual( root.predict( deque( [1]*7 )), 1 )
  
  
  def test_predictNoMatch(self):
    "Ask for a prediction where no exact data is present"
    root = MonkeyNode()
    root.update( deque( [1]*8 ) )
    self.assertRaises(NoSuchNode, root.predict, deque( [5]*4 ) )
  
  
  def test_predictClosestMatch(self):
    "An exact match is not available, return the least wrong candidate"
    root = MonkeyNode()
    root.update( deque( [1]*8 ) )
    root.update( deque( [1]*8 ) )
    root.update( deque( [1,1,1,9,9,9,9,9] ) )
    self.assertEqual(root.predict( deque([1,1,1,2,2]), closest=True ), 1)
  
  
  def test_checkCoverage(self):
    "Coverage metric generated correctly"
    root = MonkeyNode()
    root.update( deque( [1]*8 ) )
    self.assertEqual(root.checkCoverage([1]), 1.0)
    self.assertEqual(root.checkCoverage([1,2]), 0.5)
    

  def test_cumulativeProbSimple(self):
    "Node can add up the cumulative probabilities of a range of outcomes"
    root = MonkeyNode()
    root.update( deque( [1]*8 ) )
    self.assertEqual(root.cumulativeProbability(lambda n: n == 1), 1)
    self.assertEqual(root.cumulativeProbability(lambda n: n == 99), 0)


  def test_cumulativeProbComplex(self):
    "Node can add up the cumulative probabilities of a range of outcomes"
    root = MonkeyNode()
    [ root.update( deque( [i] ) ) for i in range(-5, 6) ]
    self.assertAlmostEqual(root.cumulativeProbability(lambda n: n == 0), 1/11)
    self.assertAlmostEqual(root.cumulativeProbability(lambda n: n > 0), 5/11)
    self.assertAlmostEqual(root.cumulativeProbability(lambda n: n < 0), 5/11)
    self.assertEqual(root.cumulativeProbability(lambda n: n < -99), 0)
    self.assertEqual(root.cumulativeProbability(lambda n: n > 99), 0)


    
