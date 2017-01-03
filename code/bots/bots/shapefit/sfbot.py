#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from bots.bots._base import BaseBot
from bots.bots.shapefit import handlers

from decimal import Decimal as D

from utils.time import HORSEYTIEM

from events import Trade

import exchanges
from datasource.signals import bitstamp



class ShapeFitBot(BaseBot):

  PRINTABLE_NAME            = 'shapefit'
  DESCRIPTION               = """
Attempt to recognize trade curve shape by fitting normalised metrics to history.
"""
  HIDDEN                    = False

  REQD_EXCHANGES    = {
    'exchange':   (exchanges.BitStampBackTest, {}),
  }
  
  REQD_DATASOURCES  = {
    'market':   (bitstamp.DataSourceBitStampFile, {})
  }
  
  # REQD_INDICATORS   = {
  # 
  #   'grad_5m':      (igrad.LinRegGradient_5m, 'market'),
  #   'grad_10m':     (igrad.LinRegGradient_10m, 'market'),
  #   
  #   'min_1d':       (ibasic.MinimumTradePrice_1d, 'market'),
  #   'max_1d':       (ibasic.MaximumTradePrice_1d, 'market'),
  #   'open_1d':      (ibasic.OpenTradePrice_1day,  'market'),
  #   'close_1d':     (ibasic.CloseTradePrice_1day, 'market'),
  #   
  # }


  DEFAULT_VARS = {
    'output_stats_csv':               'logs/shapefit.csv',
    'match_tree_file':                'data/shapefit/training.pkl.bz2',
    'mode':                           'trade',    # or can be train|analyze|test
    'match_buckets':                  12,         # match on metric from last N windows
    'buckets_to_profit':              2,
    'profit_margin':                  0.015,         # most cover 2 * 0.5% fees
    'loss_margin':                    0.010,
  }
  
  
  DEFAULT_STATS    = {
    'total_buys':       0,
    'total_sells':      0,
    'position_fail':    0,
    'position_win':     0,
    'predict_correct':  0,
    'predict_wrong':    0
  }

  # Set this to get CSV logging
  CSV_FIELDS              = None

  
  def __init__(self, *args, **kwargs):
    super(ShapeFitBot,self).__init__(*args, **kwargs)
    self._bucket_ind = self.indicators['grad_10m']
    
    # Subscribe to get events from the market, but with a priority low enough
    # that all the indicators will be updated before we get the message
    self.sources['market'].channel.subscribe(self.event, 1000)
  
  
  def event(self, e):
    "Process an event from the backplane"
    if isinstance(e, Trade):
      
      # Update the bucket chain and window if it's time
      if self._bucket_window_cycles != self._bucket_ind.window.cycles:
        self._handler.handleBucketUpdate(self._bucket_ind, e)
        self._bucket_window_cycles = self._bucket_ind.window.cycles
      
      # Always send the regular trade signal
      self._handler.handleTrade(e)

  
  
  


  #
  #`STARTUP & TEARDOWN METHODS
  #
  
  HANDLERS = {
    'trade':      handlers.SfBotHandlerTrade,
    'train':      handlers.SfBotHandlerTrain,
    'analyze':    handlers.SfBotHandlerAnalyze,
    'test':       handlers.SfBotHandlerTest,
  }
  
  def setup(self):
    "See base class's setup() for why this is here"
    
    # Track when the window has cycled
    self._bucket_window_cycles  = 0
    
    # Select the correct handler for this mode
    klass = self.HANDLERS[self.vars['mode'].lower()]
    self._handler = klass(self.vars, self.stats, self.exchanges['exchange'], self.indicators)
    print("ShapeFitBot: feeding events to %s" % self._handler.__class__.__name__)


  def shutdown(self):
    self._handler.shutdown()
      
