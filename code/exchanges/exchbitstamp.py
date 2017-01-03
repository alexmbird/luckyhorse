#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Why is this called exchbitstamp?  So as not to clash with the 'bitstamp'
# module supplying our API.




# Ugly test hack
if __name__ == '__main__':
  import sys
  sys.path.append('./')
  sys.path.append('code/')



import time
import decimal
from decimal import Decimal as D
import collections
import numpy
import threading

import bitstamp.client

from utils.hmath import round_dec_down_to_n_places, round_dec_up_to_n_places

from exchanges.orderbook import OrderBookDistinct
from events import Trade, Order, OrderAsk, OrderBid

import currencies

from exchanges._base import ExchangeBase, BackTestExchangeMixIn
from exchanges._connection import PusherSocketThread




class BitStampBase(ExchangeBase):
  
  '''
  Implement all standard BitStamp features.  This is abstract; you want to use
  either the BitStampLive or BitStampBackTest exchange.
  '''
  
  NAME            = "BitStampAbstractBaseDoNotUse"
  EXCHANGE_ID     = 1
  CURRENCY        = currencies.CurrencyUSD

  BROKER_CHANNEL  = 'exchange:bitstamp'

  TRADE_MINIMUM_BTC         = 0
  TRADE_MINIMUM_CURRENCY    = D(5)
  
  # Map of the fees in ascending order.  Tuples of (threshold, percentage)
  FEES        = [
    (500,     '0.50'),
    (1000,    '0.480'),
    (2000,    '0.460'),
    (4000,    '0.440'),
    (6500,    '0.420'),
    (10000,   '0.400'),
    (15000,   '0.380'),
    (20000,   '0.360'),
    (25000,   '0.340'),
    (37500,   '0.320'),
    (50000,   '0.300'),
    (62500,   '0.280'),
    (75000,   '0.260'),
    (100000,  '0.240'),
    (None,    '0.200')
  ]
  
  
  def __init__(self, broker):
    super(BitStampBase,self).__init__(broker)
    self.orderbook = OrderBookDistinct()
    
    # Subscribe our orderbook to the backplane channel for live trades/orders
    # Can't pass self.orderbook.event directly as it's not considered hashable.
    funk = lambda e: self.orderbook.event(e)
    self.channel.subscribe(funk, priority=5)

  
  def calculateFee(self, cost):
    '''
    Implementation of the fee schedule from https://www.bitstamp.net/fee_schedule/
    '''
  
    if cost < 0:
      raise ValueError("No such thing as a negative cost")
  
    # Fee depends on how much we've traded on that market in the previous 30
    # days.  Cheat for now and always apply the highest.
    fee_pct = self.FEES[0][1]
    fraction = D(fee_pct) / 100
    fee = round_dec_up_to_n_places(fraction * cost, 2)
    return fee






class BitStampBackTest(BackTestExchangeMixIn, BitStampBase):
  '''
  An exchange designed for backtesting.  No communication with upstream API's.
  Just trades and records changes to balance.  Fee structure a copy of BitStmp.
  '''

  NAME        = 'BitStampBackTest'
  





  
  
class BitStampLive(BitStampBase):
  
  '''
  A connection to the live BitStamp exchange.
  
  This can transmit orders & will maintain a model of the orderbook fed from the
  live exchange's backplane channel.
  '''
  
  NAME              = 'BitStampLive'
  
  def __init__(self, broker, username, api_key, secret):
    super(BitStampLive, self).__init__(broker)
    self._api_p       = bitstamp.client.Public()
    

  def execute(self, o):
    raise NotImplementedError()


  def __str__(self):
    return "<%s - %d orders>" % (
      self.__class__.__name__,
      len(self.orderbook)
    )

  
  def ticker(self):
    return self._api_p.ticker()
    
  



