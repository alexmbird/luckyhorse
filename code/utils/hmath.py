#!/usr/bin/env python3
# -*- coding: utf-8 -*-




import decimal
from decimal import Decimal as D

import numpy as np
import math
from random import randint

from operator import itemgetter



UTIL_CTX_ROUND_UP    = decimal.Context(rounding=decimal.ROUND_UP)
UTIL_CTX_ROUND_DOWN  = decimal.Context(rounding=decimal.ROUND_DOWN)
UTIL_CTX_FLOAT_OK    = decimal.Context(traps=[])


def round_dec_up_to_n_places(num, places):

  if not isinstance(num, decimal.Decimal):
    raise TypeError("We only deal in decimals")

  q = D(10) ** -places
  return num.quantize(q, context=UTIL_CTX_ROUND_UP)


def round_dec_down_to_n_places(num, places):

  if not isinstance(num, decimal.Decimal):
    raise TypeError("We only deal in decimals")

  q = D(10) ** -places
  return num.quantize(q, context=UTIL_CTX_ROUND_DOWN)


def check_dec_is_n_places(num, places):
  return num == round_dec_up_to_n_places(num, places)




# From https://stackoverflow.com/questions/2413522/weighted-standard-deviation-in-numpy

def weighted_avg_and_std(values, weights=None):
  '''
  Return the weighted average and standard deviation.

  `values`  - np.ndarray of values to average.
  `weights` - Optional np.ndarray of weights.  Otherwise all values are assumed
              equally weighted.
  
  Note the helpful np.fromiter() function, helpful building arrays.
  '''
  if not isinstance(values, np.ndarray):
    raise TypeError("Values must be an np.array")
  if len(values) == 0:
    raise ValueError("Can't calculate with no values")
  if weights is not None:
    if not isinstance(weights, np.ndarray):
      raise TypeError("Weights must be None or an np.array")
    if len(values) != len(weights):
      raise ValueError("Length of values and weights differ")

  average = np.average(values, weights=weights)
  variance = np.average((values-average)**2, weights=weights)  # Fast and numerically precise
  return (average, math.sqrt(variance))



def weightedMeanGradient(vals_a, weights_a, vals_b, weights_b):
  '''
  Return the ratio of mean(a) to mean(b), taking into account the weightings of
  their values.
  '''
  wm_a = np.average(vals_a, weights=weights_a)
  wm_b = np.average(vals_b, weights=weights_b)

  return (wm_b / wm_a) - 1



def makeRandomSeq(length, init=[]):
  to_gen = length - len(init)
  return init + [randint(1,10) for n in range(0, length)]
  


# Adapted from http://glowingpython.blogspot.co.uk/2012/03/linear-regression-with-np.html
def linearRegressionGradient(data):
  '''
  Given a collection of (x,y) data points, use numpy's linear regression
  function to determine a line-of-best-fit and thence its gradient.
  '''
  if not len(data):
    raise ValueError("Can't have a line with no datapoints")
  xvals, yvals = zip(*data)
  min_xval = min(xvals)
  norm_xvals = [v - min_xval for v in xvals]
  A = np.array([ norm_xvals, np.ones(len(norm_xvals))])
  w = np.linalg.lstsq(A.T,yvals)[0] # obtaining the parameters
  return w[0]


def linearRegression(data):
  '''
  Given a collection of (x,y) data points, use numpy's linear regression
  function to determine a line-of-best-fit.  Return a sequence of (gradient,
  offset).
  '''
  if not len(data):
    raise ValueError("Can't have a line with no datapoints")
  xvals, yvals = zip(*data)
  min_xval = min(xvals)
  norm_xvals = [v - min_xval for v in xvals]
  A = np.array([ norm_xvals, np.ones(len(norm_xvals))])
  w = np.linalg.lstsq(A.T,yvals)[0] # obtaining the parameters
  return w


def clamp(a, b, c):
  "Clamo a value such that a <= b <= c"
  return sorted((a, b, c))[1]




class CumulativeWeightedMean(object):
  
  def __init__(self):
    self.mean   = None
    self.cw     = None
    
  def update(self, a, w=1):
    if w == 0:
      return
    elif w < 0:
      raise ValueError("Antigravity is not supported; '%s' is a silly weight" % (w,))
    
    if self.cw is None:
      self.mean = a
      self.cw   = w
    else:
      self.cw   += w
      proportion = w / self.cw
      self.mean = (self.mean * (1-proportion)) + (proportion * a)



#
# Exponential Moving Average - http://stackoverflow.com/a/488825
#
def exponentialMovingAverage(values, alpha=0.5, epsilon=0):

  if not 0 < alpha < 1:
     raise ValueError("out of range, alpha='%s'" % alpha)

  if not 0 <= epsilon < alpha:
     raise ValueError("out of range, epsilon='%s'" % epsilon)

  result = [None] * len(values)

  for i in range(len(result)):
    currentWeight = 1.0

    numerator     = 0
    denominator   = 0
    for value in values[i::-1]:
      numerator     += value * currentWeight
      denominator   += currentWeight

      currentWeight *= alpha
      if currentWeight < epsilon: 
         break

    result[i] = numerator / denominator

  return result


def exponentialSmooth(data, alpha=0.5, epsilon=0):
  "Return the most recent value of data, smoothed using an EMA"
  rev = list(reversed(data))
  ema = exponentialMovingAverage(rev, alpha, epsilon)
  return ema[-1]

