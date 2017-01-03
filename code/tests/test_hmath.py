#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest


from utils.hmath import *
import numpy as np    # for almost-equal comparison
from numpy import array as A



class UtilsMixIn(object):
  
  def assertAlmostEqual(self, a, b):
    assert np.allclose([a],[b])




class TestWeightedAvgStd(unittest.TestCase, UtilsMixIn):
  
  def test_WrongTypes(self):
    "weighted_avg_and_std: only accepts np.ndarray"
    with self.assertRaises(TypeError):
      weighted_avg_and_std(None, None)
      weighted_avg_and_std([1,2], None)
      weighted_avg_and_std([1,1], [1,1])
  
  def test_ZeroLength(self):
    "weighted_avg_and_std: can't make average from zero-length array"
    with self.assertRaises(ValueError):
      weighted_avg_and_std(A([]))
      weighted_avg_and_std(A([]), A([]))
  
  def test_MismatchedLength(self):
    "weighted_avg_and_std: len(values) != len(weights)"
    with self.assertRaises(ValueError):
      weighted_avg_and_std(A([1,2]), A([1,2,3]))
  
  def test_simple_unweighted(self):
    "weighted_avg_and_std: simple cases"
    
    # 1 - no variance
    self.assertEqual(weighted_avg_and_std(A([1,1]), A([1,1])), (1,0))
    
    # 2 - different numbers, still no variance
    self.assertEqual(weighted_avg_and_std(A([1,2,3]), A([1,1,1])), (2, 0.816496580927726))

    # 3 - different numbers, some variance
    self.assertEqual(weighted_avg_and_std(A([1,2,3]), A([1,1,1])), (2, 0.816496580927726))
    
    
  def test_simple_weighted(self):
    "weighted_avg_and_std: simple cases with weighting"
    
    # 1 - no variance
    average, variance = weighted_avg_and_std(
      np.array([2,5]), np.array([2,1])
    )
    self.assertEqual(average, 3)
    self.assertEqual(variance, 1.4142135623730951)
    
    # 2 - different numbers, still no variance
    average, variance = weighted_avg_and_std(A([1,2,3]), A([6,3,2]))
    self.assertAlmostEqual(average, 1.63636363)
    self.assertAlmostEqual(variance, 0.77138921)
  
    
  def test_wikipediaExample(self):
    "weighted_avg_and_std: unweighted standard deviation from Wikipedia"
    values  = np.array( [2, 4, 4, 4, 5, 5, 7, 9] )
    weights = np.array( [1] * len(values) )
    average, variance = weighted_avg_and_std(values, weights)
    self.assertEqual(variance, 2)






class TestLinearRegression(unittest.TestCase, UtilsMixIn):
  
  def testLinReg1(self):
    "linearRegressionGradient handles example from a random blog post"
    # http://glowingpython.blogspot.co.uk/2012/03/linear-regression-with-np.html
    xvals = range(0, 9)
    yvals = [19, 20, 20.5, 21.5, 22, 23, 23, 25.5, 24]
    data  = zip(xvals, yvals)
    gradient = linearRegressionGradient(data)
    self.assertAlmostEqual(gradient, 0.71666667)
    
  
  def test_LinRegPriceTime(self):
    "linearRegressionGradient handles a price/time series"
    data  = [(1417262020, 0), (1417262021, 300)]
    self.assertAlmostEqual(linearRegressionGradient(data), 300)
    data  = [(1417262020, 300), (1417262021, 300.5)]
    self.assertAlmostEqual(linearRegressionGradient(data), 0.5)
    data  = [(1417262020, 300), (1417262021, 299.5)]
    self.assertAlmostEqual(linearRegressionGradient(data), -0.5)
    data  = [(1417262020, 300), (1417262021, 0)]
    self.assertAlmostEqual(linearRegressionGradient(data), -300)
    
    
    
class TestClamp(unittest.TestCase):
  
  def testLowerBoundary(self):
    "Value lower than clamp boundary"
    self.assertEqual(clamp(-5, -5, 5), -5)

  def testOutsideUnder(self):
    "Value lower than clamp boundary"
    self.assertEqual(clamp(-5, -6, 5), -5)
  
  def testUpperBoundary(self):
    "Value on upper clamp boundary"
    self.assertEqual(clamp(-5, 5, 5), 5)

  def testOutsideOver(self):
    "Value higher than clamp boundary"
    self.assertEqual(clamp(-5, 6, 5), 5)




class TestCumulativeWeightedMean(unittest.TestCase):
  
  def testNoValues(self):
    cwm = CumulativeWeightedMean()
    self.assertEqual(cwm.mean, None)
  
  def testSingleValueZeroWeight(self):
    cwm = CumulativeWeightedMean()
    cwm.update(999, 0)
    self.assertEqual(cwm.mean, None)

  def testTwoValuepartZeroWeight(self):
    cwm = CumulativeWeightedMean()
    cwm.update(999, 0)
    cwm.update(10,1)
    self.assertEqual(cwm.mean, 10)

  def testSingleValuePos(self):
    cwm = CumulativeWeightedMean()
    cwm.update(99, 1)
    self.assertEqual(cwm.mean, 99)
  
  def testTwoValSameWeight(self):
    cwm = CumulativeWeightedMean()
    cwm.update(0, 1)
    cwm.update(100, 1)
    self.assertEqual(cwm.mean, 50)
  
  def testTwoValsDiffWeight(self):
    cwm = CumulativeWeightedMean()
    cwm.update(0, 1)
    cwm.update(100, 3)
    self.assertEqual(cwm.mean, 75)

  def testTwoValsOnePosOneNeg(self):
    cwm = CumulativeWeightedMean()
    cwm.update(100, 1)
    cwm.update(-100, 1)
    self.assertEqual(cwm.mean, 0)
  



class TestExpMovingAvg(unittest.TestCase):
  
  def test_NoData(self):
    "EMA of no data has no data"
    data = []
    ema = exponentialMovingAverage(data)
    self.assertEqual(len(ema), len(data))
  
  def test_SameValue(self):
    "EMA of a sequence of identical values"
    data  = [5] * 10
    ema   = exponentialMovingAverage(data)
    print("%s" % (ema,))
    self.assertEqual(len(ema), len(data))
    for p in ema:
      self.assertEqual(p, 5)
  
  def test_AscendingSeries(self):
    "EMA of an ascending sequence"
    data  = list( range(0, 10) )
    ema   = exponentialMovingAverage(data)
    prev  = ema[0]
    for v in ema[1:]:
      assert v > prev
  
  def test_DescendingSeries(self):
    "EMA of an descending sequence"
    data  = list( range(9, -1, -1) )
    ema   = exponentialMovingAverage(data)
    prev  = ema[0]
    for v in ema[1:]:
      assert v < prev

  
  
if __name__ == '__main__':
  unittest.main()


