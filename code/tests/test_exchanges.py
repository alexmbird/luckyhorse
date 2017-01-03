#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import random


import decimal
from decimal import Decimal as D

import exchanges
import currencies

from events.broker import QueuedBrokerBundle
from exchanges.balance import ExchangeBalance




class TestExchange(unittest.TestCase):
  
  
  def testFeeCalculation(self):
    broker = QueuedBrokerBundle(maxsize=10)
    bs = exchanges.BitStampBackTest(broker)

    fee = bs.calculateFee( D(0) )
    self.assertEqual( fee, 0)
    
    # An easy one
    fee = bs.calculateFee( D('100.00'))
    self.assertEqual(fee, D('0.5'))
    
    # Now with some rounding - fees are rounded up to 2 decimal places
    fee = bs.calculateFee( D('5.00'))
    self.assertEqual(fee, D('0.03'))
    
    fee = bs.calculateFee( D('0.01'))
    self.assertEqual(fee, D('0.01') )
    
    # Fees on negative amounts raise an exception
    self.assertRaises( ValueError, bs.calculateFee, D('-1') )


  





class TestExchangeBalance(unittest.TestCase):
  
  def testAddCash(self):
    b = ExchangeBalance(currencies.CurrencyUSD)
    self.assertEqual(b.cash, D(0) )
    
    b.addCash( D(0) )
    self.assertEqual(b.cash, D(0) )
    
    b.addCash( D(5) )
    self.assertEqual(b.cash, D(5))
    
    b.addCash( D('-0.1') )
    self.assertEqual(b.cash, D('4.9'))
    
    # Balance can't fall below zero
    self.assertRaises( ValueError, b.addCash, D('-10') )
    
    # Too many decimal places
    self.assertRaises( ValueError, b.addCash, D('0.123') )
  
  
  
  def testAddBtc(self):
    b = ExchangeBalance(currencies.CurrencyUSD)
    self.assertEqual( b.btc, D(0) )
    
    b.addBtc( D(0) )
    self.assertEqual( b.btc, D(0) )

    b.addBtc( D(5) )
    self.assertEqual( b.btc, D(5) )
    
    b.addBtc( D('-1') )
    self.assertEqual( b.btc, D(4) )
    
    # Can't fall below zero
    self.assertRaises( ValueError, b.addBtc, D(-5) )
    
    # Too many decimal places
    self.assertRaises( ValueError, b.addBtc, D('0.000000001'))




