#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import currencies

import datetime

from events.base import BaseEvent



class Trade(BaseEvent):
  '''
  Represent a single trade on the exchange.
  '''

  def __init__(self, exchange_id, price, volume, ts_exec, ts_update, trade_id):
    '''
    `exchange_id` - Integer ID of the exchange this happened on
    `trade_id`    - unique id given by the exchange, if there was one
    `price`       - price, up to 2 decimal places, in exchange currency
    `volume`      - btc volume, decimal up to 8 decimal places
    `ts_exec`     - int timestamp when the exchange says this trade was executed
    `ts_update`   - float timestamp this trade arrived at our end of the line
    '''
    
    super(Trade,self).__init__(exchange_id, ts_update)
    # Yes, sometimes bonkers values creep in
    if price <= 0:
      raise ValueError("Can't have price <= 0 - %s" % price)
    if volume <= 0:
      raise ValueError("Can't have volume <= 0 - %s" % volume)

    self.trade_id   = trade_id
    self.price      = price
    self.volume     = volume
    self.ts_exec    = ts_exec


  def __str__(self):
    ts_exec_dt = datetime.datetime.fromtimestamp(self.ts_exec)
    return "<%s %s%.8f @ %.2f @ %s>" % (
      self.__class__.__name__, currencies.CurrencyBTC.SYMBOL,
      self.volume, self.price, ts_exec_dt.isoformat()
    )





