#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from decimal import Decimal as D

from exchanges.balance import ExchangeBalance

import currencies




class ExchangeBase(object):
  
  # A string name for your exchange
  NAME       = 'UNDEF'
  
  # Integer ID used for database storage
  ID         = None
  
  # Class representing the currency this exchange is using
  CURRENCY    = currencies.CurrencyBase
  
  # Other exchange limitations
  TRADE_MINIMUM_BTC         = D(0)
  TRADE_MINIMUM_CURRENCY    = D(0)
  

  def __init__(self, broker):
    if self.__class__ == ExchangeBase:
      raise NotImplementedError("ExchangeBase is an abstract base")
      
    # It is up to the implementation to choose their own order book
    self.orderbook    = None
    
    # Where we may find our datasource's channel
    self.broker       = broker
    self.channel      = broker[self.BROKER_CHANNEL]
  

  def calculateFee(self, cost):
    raise NotImplementedError()


  def execute(self, o):
    "Execute a given order on this exchange"
    raise NotImplementedError()


  def cancel(self, o):
    "Cancel an order on this exchange"
    raise NotImplementedError()





class BackTestExchangeMixIn(object):
  '''
  Add things a backtest will want, such as dummy trading methods and balance
  tracking.
  '''
  
  def __init__(self, broker ,*args, **kwargs):
    self.balance = ExchangeBalance(self.CURRENCY, cash=1000)
    super(BackTestExchangeMixIn,self).__init__(broker)
  
  
  def executeBid(self, volume=None, spend=None, limit=None):
    '''
    Execute this ask against the current orderbook and book the results.
    Return a tuple of (fee, cash_spent, btc_bought).
    If the orderbook is completely empty (happens if backtesting history has
    no order data) use trade_price to give a shit estimate of the return.
    
    `volume`    - Buy fixed number of BTC       -OR-
    `spend`     - Spend fixed amount of cash
    `limit`     - Do not pay more than `limit` per BTC
    `fallback`  - If the orderbook has no orders, fake price from the last trade
    
    `volume` and `spend` are mutually exclusive.
    
    '''
    if volume == 0 or spend == 0:
      raise ValueError("Volume or spend must be non-zero")
    if bool(volume) == bool(spend):
      raise ValueError("volume and spend are mutually exclusive")
    cash_spent, btc_bought = self.orderbook.estimateBid(
      volume, spend, limit, fallback=True
    )
    fee = self.calculateFee(cash_spent)
    self.balance.addCash(-cash_spent-fee)
    self.balance.addBtc(btc_bought)
    return (fee, cash_spent, btc_bought)
  
  
  def executeAsk(self, volume=None, earn=None, limit=None):
    '''
    Execute this ask precisely in the current orderbook and book the results.
    Return a tuple of (fee, cash_earned, btc_sold)
    '''
    if bool(volume) == bool(earn):
      raise ValueError("volume and earn are mutually exclusive")
    cash_earned, btc_sold = self.orderbook.estimateAsk(
      volume, earn, limit, fallback=True
    )
    fee = self.calculateFee(cash_earned)
    self.balance.addCash(cash_earned-fee)
    self.balance.addBtc(-btc_sold)
    return (fee, cash_earned, btc_sold)
  
  
  def estimateCloseOut(self, alt_vol=None):
    '''
    What would our balances be worth if liquidated now?
    
    If `alt_vol` is specified use it instead of the real one.
    '''
    if alt_vol is not None:
      btc_income, volume = self.orderbook.estimateAsk(alt_vol, limit=None, fallback=True)
      fee = self.calculateFee(btc_income)
      return btc_income - fee
    else:
      btc_income, volume = self.orderbook.estimateAsk(self.balance.btc, limit=None, fallback=True)
      fee = self.calculateFee(btc_income)
      return self.balance.cash + btc_income - fee
    
    
  

  
