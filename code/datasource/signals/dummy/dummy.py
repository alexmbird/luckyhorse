#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datasource.signals.base import DataSourceBitcoinExchange

from events import Trade, Order, OrderAsk, OrderBid

from utils.time import HORSEYTIEM
import time

import threading
from itertools import cycle
from copy import deepcopy
import random

from decimal import Decimal as D





class DataSourceDummy(DataSourceBitcoinExchange):

  BROKER_CHANNEL   = 'exchange:dummy'
  EXCHANGE_ID      = 0
  
  # Internal settings
  FAKE_LATENCY    = 0.250
  
  
  def __init__(self, broker, frequency=0,
      t_price=66, t_price_sigma=None, t_vol=1, t_vol_sigma=None ):
    '''
    `frequency`   - Limit events to one every n seconds.  Otherwise piss them
                    out as fast as possible.
    `t_price`     - Dummy trades will have this price
    `t_fuzz`      - Dummy trade price varies by +- this much
    '''
    self._frequency       = float(frequency)
    self._prev_time       = HORSEYTIEM.time()
    self._t_price         = t_price
    self._t_price_sigma   = t_price_sigma
    self._t_vol           = t_vol
    self._t_vol_sigma     = t_vol_sigma
    
    super(DataSourceDummy,self).__init__(broker)

    # Signal when it's time to exit
    self._time_to_die   = threading.Event()

    # All trades must have a unique ID
    self._fake_trade_id = 0
  

  def _makeFakeTrade(self):
    "Generate a realistic-looking trade"
    tp    = self._t_price
    tpf   = self._t_price_sigma
    tv    = self._t_vol
    tvf   = self._t_vol_sigma
    t_exec      = self._prev_time + self._frequency
    t_update    = t_exec + random.uniform(0, self.FAKE_LATENCY)
    self._fake_trade_id += 1
    self._prev_time     = t_update
    
    return Trade(
      exchange_id = self.EXCHANGE_ID,
      price       = tp if tpf is None else random.gauss(tp, tpf),
      volume      = tv if tvf is None else random.gauss(tv, tvf),
      ts_exec     = t_exec,
      ts_update   = t_update,
      trade_id    = self._fake_trade_id
    )
  
  
  def run(self, limit=None):
    '''
    Spit out dummy trades.
    '''
    n_published = 0
    while True:
      t = self._makeFakeTrade()
      self.broker.publish(self.channel, t)
      n_published += 1
      if limit is not None and n_published >= limit:
        break


