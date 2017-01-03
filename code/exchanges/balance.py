#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from decimal import Decimal as D

from utils.hmath import check_dec_is_n_places

import currencies



class ExchangeBalance(object):

  '''
  Keep track of the amount of money we should have within an exchange
  '''

  def __init__(self, currency, cash=0, btc=0):

    self.currency   = currency
    self.cash       = D(cash)
    self.btc        = D(btc)


  def __str__(self):
    return "<ExchangeBalance %s%.2f / %s%.8f>" % (
      self.currency.SYMBOL, self.cash,
      currencies.CurrencyBTC.SYMBOL, self.btc
    )


  def addCash(self, amount):
    '''
    Add an amount of cash to our balance.  -ve values mean subtract.
    '''
    if not check_dec_is_n_places(amount, 2):
      raise ValueError("Cash amounts can only have 2 decimal places.  You passed %s." % amount)

    new_balance = self.cash + amount
    if new_balance < 0:
      raise ValueError("Cash account balance can't go below zero (%s)" % new_balance)

    self.cash = new_balance


  def addBtc(self, amount):
    '''
    Add an amount of BTC to our account.  -ve values mean subtract.
    '''
    if not check_dec_is_n_places(amount, 8):
      raise ValueError("BTC amounts can only have 8 decimal places; you passed '%s'" % amount)

    new_balance = self.btc + amount
    if new_balance < 0:
      raise ValueError("BTC account balance can't go below zero (%s)" % new_balance)

    self.btc = new_balance


