#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import random

from bots.bots._base import BaseBot

from utils.exceptions import InsufficientDataError

import indicators.inds.simple as i_simple

from datasource.signals import bitstamp

import exchanges

from utils.logging import LOG_BOTS
from utils.time.period import *
from utils.time import HORSEYTIEM

from bots import strategies






class GradientPrediction(object):
  
  '''
  Predict the mean trade price based upon the linear gradient calculated for a
  given period.  Encapsulate this in an object to protect the gradient value
  from recalculation in subsequent periods.
  '''
  
  def __init__(self, grad_ind):
    super(GradientPrediction,self).__init__()
    self._period = FixedPeriod_6Hour(HORSEYTIEM.time(), anchor=ANCHOR_HOUR_LHS) - 1
    self.gradient, self.offset, self.stdev = grad_ind.hist(self._period)

  def mean_pred(self):
    "Where should the mean be at this time?"
    timediff = HORSEYTIEM.time() - self._period.lhs_ts
    return self.offset + (timediff * self.gradient)
    



class HodlBot(BaseBot):
  
  
  PRINTABLE_NAME          = "hodlbot"
  DESCRIPTION             = '''
Tries to keep money in Bitcoin but get off the bus before the worst of any
crash
  '''.strip()
  HIDDEN                  = False

  REQD_EXCHANGES    = {
    'exchange':   (exchanges.BitStampBackTest, {}),
  }
  
  REQD_DATASOURCES  = {
    'market':   (bitstamp.DataSourceBitStampFile, {})
  }

  REQD_INDICATORS   = {
    'wmean':        (i_simple.WeightedAvgPrice,     'market'),
    'lintrend':     (i_simple.LinPriceTrend,        'market'),
    # 'smgrad':       (i_simple.SmoothedLinPriceGradient_6,  'market'),
    # 'min_1d':       (i_simple.MinTradePrice,   'market'),
    'max_1d':       (i_simple.MaxTradePrice,        'market'),
    # 'open_1d':      (i_simple.OpenTradePrice_1Day,  'market'),
    # 'close_1d':     (i_simple.CloseTradePrice_1Day, 'market'),
    # 'posdm_1d':     (i_wilder.PosDM_1Day, 'market'),
    # 'negdm_1d':     (i_wilder.NegDM_1Day, 'market'),
    # 'truerange_1d': (i_wilder.TrueRange_1Day, 'market',)
  }
  
  CSV_FIELDS        = [
    'price_usd',
    'buy_usd',
    'sell_usd'
  ]
  
  DEFAULT_VARS = {
  'output_stats_csv':               'logs/hodlbot.csv',
  }
  
  def __init__(self, sources, indicators, exchanges, inhablers, *args, **kwargs):
    super(HodlBot,self).__init__(
      sources, indicators, exchanges, inhablers,
      *args, **kwargs
    )
    self.sources['market'].channel.subscribe(self.event, 1000)
    self.exch         = self.exchanges['exchange']
    self.strategy     = strategies.BalanceProportional(self.exchanges, 'exchange', 0.95)
    self._period      = None
    self._pos         = None


  def _weekGradient(self):
    p = FixedPeriod_1Week(around_ts=HORSEYTIEM.time(), anchor=ANCHOR_HOUR_LHS)-1
    gradient, offset, stdev = self.indicators['lintrend'].hist(p)
    return gradient
  
  
  def _max24h(self):
    p = FixedPeriod_1Day(around_ts=HORSEYTIEM.time(), anchor=ANCHOR_HOUR_LHS)-1
    max_1d = self.indicators['max_1d'].hist(p)[0]
    return max_1d
  
  
  def event(self, e):
    
    now   = HORSEYTIEM.time()
    if self._period is None or now not in self._period:
      self._period = FixedPeriod_1Day(around_ts=now)
      log = {'price_usd':e.price}
      self._csvlog(log)
      LOG_BOTS.info("Day is now %s", self._period)
    
    if random.randint(0, 12) == 0:
      self._csvlog({'price_usd':e.price})
      
    self.tick(e)
  
  
  def tick(self, e):
    
    fp    = float(e.price)
    now   = HORSEYTIEM.time()

    try:
      if self._pos:
        # Is it crashing?
        if e.price < self._max24h() * 0.90:
          self.strategy.sell(
            reason="Lost 10%% from 24h high of %.2f" % self._max24h()
          )
          self._csvlog({'sell_usd':e.price})
          self._pos   = None
          return
        # Is it in a long-term decline?
        if self._weekGradient() < -0.0001:
          self.strategy.sell(
            reason="In a long-term decline - week gradient %.6f" % self._weekGradient()
          )
          self._csvlog({'sell_usd':e.price})
          self._pos   = None
          return

      else:
        if self._weekGradient() > 0.00005 and e.price > self._max24h():
            LOG_BOTS.info("Gradient went positive, will buy")
            self._pos = self.strategy.buy(
              reason="In a long-term rise - week gradient %.6f" % self._weekGradient()
            )
            self._csvlog({'buy_usd':e.price})
  
    except InsufficientDataError as e:
      raise
      LOG_BOTS.error("%s", e)
      return


