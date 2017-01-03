#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Talk to me, computer
import os
import random
import csv

from bots.bots._base import BaseBot

from events import Trade

from utils.exceptions import InsufficientDataError

from datasource.signals import bitstamp
import exchanges

from utils.logging import LOG_BOTS
from utils.time.period import *
from utils.time import HORSEYTIEM

import indicators.inds.simple as i_simple
import indicators.inds.wilder as i_wilder

from bots import strategies

from predictors.boss import PredictionBoss
from predictors.preds.simple import *





class FuzzBot(BaseBot):
  
  
  PRINTABLE_NAME          = "fuzzbot"
  DESCRIPTION             = "Extensible Probablistic Nostradamus"
  HIDDEN                  = False

  REQD_EXCHANGES    = {
    'exchange':   (exchanges.BitStampBackTest, {}),
  }
  
  REQD_DATASOURCES  = {
    'market':   (bitstamp.DataSourceBitStampFile, {})
  }
  
  REQD_INDICATORS   = {
    'smgrad':       (i_simple.SmoothedLinPriceGradient_6,   'market'),
    'posdi_1d':     (i_wilder.PosDI_1Day,                   'market',),
    'negdi_1d':     (i_wilder.NegDI_1Day,                   'market',),
    'adx_1d':       (i_wilder.ADX_1Day,                     'market',),
  }
  
  CSV_FIELDS        = [
    'price_usd',
    'buy_usd',
    'sell_usd'
  ]
  
  DEFAULT_VARS = {
    'output_stats_csv':               'logs/fbot.csv',
  }
  
  def __init__(self, sources, indicators, exchanges, *args, **kwargs):
    super(FuzzBot,self).__init__(sources, indicators, exchanges, *args, **kwargs)
    self.sources['market'].channel.subscribe(self.event, 1000)
    self.exch         = self.exchanges['exchange']
    self.strategy     = strategies.BalanceProportional(self.exchanges, 'exchange', 0.95)
    
    # HERE IS THE MAGIC
    preds = [
      PredictorLinGradient,
      # PredictorSmoothedLinGradient,
      PredictorWMeanGradient,
      PredictorPatternTimePeriod
    ]
    self.predictron   = PredictionBoss(
      self.sources['market'], preds, 
      kwargs['ifakt'], kwargs['storage']
    )
    self.predictron_init  = False
    # self.predictron.dump()
    
    self.period       = FixedPeriod_1Day(HORSEYTIEM.time())
    self.period_inds  = self._periodInds()
    
    # Setup CSV loggers
    self._csv_price_pred  = csv.DictWriter(
      open('logs/prediction.csv', 'w'),
      [ 'timestamp', 'price', 'predicted', 'error' ]
    )

  
  def _periodInds(self):
    
    try:
      p_yest = self.period-1
      #LOG_BOTS.info("My yesterday is now %s" % p_yest)
      return {
        'adx':    self.indicators['adx_1d'].hist(p_yest)[0],
        'pdi':    self.indicators['posdi_1d'].hist(p_yest)[0],
        'ndi':    self.indicators['negdi_1d'].hist(p_yest)[0]
      }
    except InsufficientDataError:
      LOG_BOTS.warn("No data from indicators for this day")
      return {}


  def preroll(self, e):
    LOG_BOTS.info("Prerolling predictron")
    self.predictron.preroll(e.ts_exec, float(e.price))
    self.predictron_init = True
    LOG_BOTS.info("Preroll complete")

  
  def dayChanged(self, e):
    self.period = FixedPeriod_1Day(HORSEYTIEM.time())
    # self.period_inds = self._periodInds()
    log = {'price_usd':e.price}
    self._csvlog(log)
    LOG_BOTS.info("Day is now %s", self.period)
    LOG_BOTS.info("Predictron best: %s gives %.4f" % self.predictron.leastWrong())
    LOG_BOTS.info("Prediction for 30m time: %.2f; presently %.2f", 
      self.predictron.predict(HORSEYTIEM.time() + 60*30), e.price)
    # self.predictron.dump()


  def event(self, e):
    
    if not isinstance(e, Trade):
      return
    
    if not self.predictron_init:
      self.preroll(e)
    
    now = HORSEYTIEM.time()
    if now not in self.period:
      self.dayChanged(e)
    
    if random.randint(0, 10) == 5:
      predicted_price = self.predictron.predict(now, horizon_ts=now-(60*30))
      self._csv_price_pred.writerow({
        'timestamp':      e.ts_exec,
        'price':          e.price,
        'predicted':      predicted_price,
        'error':          abs(float(e.price) - predicted_price)
      })
      LOG_BOTS.debug("%.2f", predicted_price)
      return
      
    # pdi = self.period_inds['pdi']
    # ndi = self.period_inds['ndi']
    # adx = self.period_inds['adx']

    
    pos = self.strategy.position
    
    # Shall we open a trade?
    if not pos:
    # if True or pdi > ndi and adx > 52.5 and not pos:
      if self.predictron.leastWrong()[1] < 0.01:
        price_now   = float(e.price)
        price_30m    = self.predictron.predict(HORSEYTIEM.time() + 60*30)
        if price_30m > price_now * 1.015:
          pos = self.strategy.buy(
            target=price_now*1.011,
            stop=price_now*0.995,
            reason="price predicted to rise"
          )
          self._csvlog({'buy_usd':e.price})
          #LOG_BOTS.info("Predictron best: %s gives %.4f" % self.predictron.leastWrong())
    
    # We are in a trade.  Reconsider it on every tick.
    if pos:
      # if price_30m < price_now * 0.99:
      #   self.strategy.sell(reason="price predicted to fall; exiting early")
      #   self._csvlog({'sell_usd':e.price})
      #   return
      if e.price > pos.cost_target:
        try:
          # p = FloatingPeriod_5Min()
          p = FixedPeriod_5Min(HORSEYTIEM.time())-1
          smg = self.indicators['smgrad'].hist(p)[0]
        except InsufficientDataError:
          return
        if smg < 0:
          self.strategy.sell(reason="success: stopped rising")
          self._csvlog({'sell_usd':e.price})
        return
      elif e.price < pos.cost_stop:
        self.strategy.sell(reason="fail: passed loss threshold")
        self._csvlog({'sell_usd':e.price})
        return
      
