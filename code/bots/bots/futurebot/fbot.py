#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import random

from bots.bots._base import BaseBot

from utils.exceptions import InsufficientDataError

import indicators.inds.simple as i_simple

import inhablers.inhibitors.time as inh_time
import inhablers.inhibitors.wilder as inh_wilder
import inhablers.inhibitors.shape as inh_shape

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
    



class FutureBot(BaseBot):
  
  
  PRINTABLE_NAME          = "futurebot"
  DESCRIPTION             = "Next-generation bot"
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
    # 'max_1d':       (i_simple.MaxTradePrice,   'market'),
    # 'open_1d':      (i_simple.OpenTradePrice_1Day,  'market'),
    # 'close_1d':     (i_simple.CloseTradePrice_1Day, 'market'),
    # 'posdm_1d':     (i_wilder.PosDM_1Day, 'market'),
    # 'negdm_1d':     (i_wilder.NegDM_1Day, 'market'),
    # 'truerange_1d': (i_wilder.TrueRange_1Day, 'market',)
  }
  
  REQD_INHABLERS    = [
    (inh_shape.MaxIn24H,        'market'),
    # (inh_time.GoodHours,        'market'),
    # (inh_wilder.Wilder,         'market'),
  ]
  
  CSV_FIELDS        = [
    'price_usd',
    'buy_usd',
    'sell_usd'
  ]
  
  DEFAULT_VARS = {
  'output_stats_csv':               'logs/fbot.csv',
  }
  
  def __init__(self, sources, indicators, exchanges, inhablers, *args, **kwargs):
    super(FutureBot,self).__init__(
      sources, indicators, exchanges, inhablers,
      *args, **kwargs
    )
    self.sources['market'].channel.subscribe(self.event, 1000)
    self.exch         = self.exchanges['exchange']
    self.strategy     = strategies.BalanceProportional(self.exchanges, 'exchange', 0.95)
    self._period      = None


  def _shortGradient(self):
    # p = Fixed(HORSEYTIEM.time()) - 1
    p = FloatingPeriod_10Min()
    gradient, offset, stdev = self.indicators['lintrend'].hist(p)
    return gradient
  
  
  def _medGradient(self):
    # p = Fixed(HORSEYTIEM.time()) - 1
    p = FloatingPeriod_30Min()
    gradient, offset, stdev = self.indicators['lintrend'].hist(p)
    return gradient

  
  def event(self, e):
    
    now   = HORSEYTIEM.time()
    if self._period is None or now not in self._period:
      self._period = FixedPeriod_1Day(around_ts=now)
      log = {'price_usd':e.price}
      self._csvlog(log)
      LOG_BOTS.info("Day is now %s", self._period)
    
    if True or random.randint(0, 10) == 5:
      self._csvlog({'price_usd':e.price})
    self.tick(e)
  
  
  def tick(self, e):
    
    fp    = float(e.price)
    pos   = self.strategy.position
    now   = HORSEYTIEM.time()

    try:
      if not pos:
        if self.inhablers.is_no(now):
          return
        gp = GradientPrediction(self.indicators['lintrend'])
        if fp < gp.mean_pred() * 0.990:   # gp.stdev > 0.005*fp and 
          if self._medGradient() > 0:
            LOG_BOTS.info(
              "Prediction was %.2f; std %.2f; price actually %.2f; will trade",
              gp.mean_pred(), gp.stdev, e.price
            )
            target = max( [fp*1.013, fp+gp.stdev] )
            pos = self.strategy.buy(target=target, stop=fp*0.985)
            pos.notes['init_pred_offset'] = gp.mean_pred() - fp
            pos.notes['gradient_pred']    = gp
            self._csvlog({'buy_usd':e.price})
  
      # We are in a trade.  Reconsider it on every tick.
      if pos:
        if e.price > pos.cost_target:
          if self._shortGradient() < 0:
            self.strategy.sell(reason="success: stopped rising")
            self._csvlog({'sell_usd':e.price})
            return
        elif e.price < pos.cost_stop:
          self.strategy.sell(reason="fail: passed loss threshold")
          self._csvlog({'sell_usd':e.price})
          return
        
        # Groom an existing position: quit if underperforming
        # gp = pos.notes['gradient_pred']
        # mean_pred_now = gp.mean_pred() - self.strategy.position.notes['init_pred_offset']
        # if fp < mean_pred_now - (float(pos.cost_entry)*0.01):
        #   self.strategy.sell(reason="fail: exceeded risk margin")
        #   self._csvlog({'sell_usd':e.price})
        #   return

    except InsufficientDataError as e:
      raise
      LOG_BOTS.error("%s", e)
      return


