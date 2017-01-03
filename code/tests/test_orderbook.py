#!/usr/bin/env python3
# -*- coding: utf-8 -*-



# # Ugly hack
# if __name__ == '__main__':
#   import sys
#   sys.path.append('./')
#   sys.path.append('code/')


import unittest

import decimal
from decimal import Decimal as D
from decimal import Decimal

from exchanges.orderbook import *
from events import Order, OrderAsk, OrderBid



  
DUMMY_EX_ID = 0


class UtilsMixIn(object):
  
  def populateRangeOfAsks(self, low, high, vol=1):
    "Populate our orderbook with descending fake bids"
    for price in range(low, high+1):
      o = OrderAsk(DUMMY_EX_ID, D(price), D(vol), Order.STATE_CREATED, 0)
      #print("  adding %s" % o)
      self.ob.event(o)
  
  def populateRangeOfBids(self, low, high, vol=1):
    "Populate our orderbook with descending fake bids"
    for price in range(low, high+1):
      o = OrderBid(DUMMY_EX_ID, D(price), D(vol), Order.STATE_CREATED, 0)
      #print("  adding %s" % o)
      self.ob.event(o)





class TestOrderBookDistinct(unittest.TestCase, UtilsMixIn):
  
  '''
  Unit tests for an orderbook containing distinct orders, i.e. where many orders
  at the same price are not compressed into a single one.
  '''
  
  OB_TYPE   = OrderBookDistinct
  
  
  def setUp(self):
    self.ob = self.OB_TYPE()
  
  
  def testEmptyAsks(self):
    "Nothing can match against OB with no Asks"
    self.assertEqual(len(self.ob.getAsks()), 0)
    self.assertEqual(self.ob.estimateBid(volume=5, limit=None), (0,0))
    self.assertEqual(self.ob.estimateBid(spend=66.66, limit=None), (0,0))
    spent, volume = self.ob.estimateBid(spend=66.66, limit=None)
    assert isinstance(spent, Decimal)
    assert isinstance(volume, Decimal)

  
  def testEmptyBids(self):
    "Nothing can match against OB with no Bids"
    self.assertEqual(len(self.ob.getBids()), 0)
    self.assertEqual(self.ob.estimateAsk(volume=5, limit=None), (0,0))
    self.assertEqual(self.ob.estimateAsk(earn=66.66, limit=None), (0,0))
    earned, volume = self.ob.estimateAsk(earn=66.66, limit=None)
    assert isinstance(earned, Decimal)
    assert isinstance(volume, Decimal)


  def testAddAsks(self):
    "Add asks to distinct orderbook"
    self.populateRangeOfAsks(1, 10, vol=1)
    self.assertEqual(len(self.ob), 10)
  
  
  def testAddBids(self):
    "Add bids to distinct orderbook"
    self.populateRangeOfBids(1, 10, vol=1)
    self.assertEqual(len(self.ob), 10)
  
  
  def test_ChangeAsk(self):
    "Update an OrderAsk"
    o1a = OrderAsk(DUMMY_EX_ID, D('150.01'), D('3.3330'), Order.STATE_CREATED, 0, order_id=12345)
    o2  = OrderAsk(DUMMY_EX_ID, D('151.53'), D('4.6466'), Order.STATE_CREATED, 1, order_id=12346)
    self.ob.event(o1a)
    self.ob.event(o2)
    self.assertEqual(len(self.ob), 2)
    o1b = OrderAsk(DUMMY_EX_ID, D('150.01'), D('2.9964'), Order.STATE_CHANGED, 2, order_id=12345)
    self.ob.event(o1b)
    self.assertEqual(len(self.ob), 2)
    # Cheat by looking inside the object
    assert o1a not in self.ob._asks
    assert o1b in self.ob._asks
    
  
  def test_ChangeBid(self):
    "Update an OrderBid"
    o1a = OrderBid(DUMMY_EX_ID, D('150.01'), D('3.3330'), Order.STATE_CREATED, 0, order_id=12345)
    o2  = OrderBid(DUMMY_EX_ID, D('151.53'), D('4.6466'), Order.STATE_CREATED, 1, order_id=12346)
    self.ob.event(o1a)
    self.ob.event(o2)
    self.assertEqual(len(self.ob), 2)
    o1b = OrderBid(DUMMY_EX_ID, D('150.01'), D('2.9964'), Order.STATE_CHANGED, 2, order_id=12345)
    self.ob.event(o1b)
    self.assertEqual(len(self.ob), 2)
    # Cheat by looking inside the object
    assert o1a not in self.ob._bids
    assert o1b in self.ob._bids


  def test_DeleteAsk(self):
    "Delete an OrderAsk"
    o1a = OrderAsk(DUMMY_EX_ID, D('150.01'), D('3.3330'), Order.STATE_CREATED, 0, order_id=12345)
    o2  = OrderAsk(DUMMY_EX_ID, D('151.53'), D('4.6466'), Order.STATE_CREATED, 1, order_id=12346)
    self.ob.event(o1a)
    self.ob.event(o2)
    self.assertEqual(len(self.ob), 2)
    o1b = OrderAsk(DUMMY_EX_ID, D('150.01'), D('3.3330'), Order.STATE_DELETED, 2, order_id=12345)
    self.ob.event(o1b)
    self.assertEqual(len(self.ob), 1)
  
  def test_DeleteBid(self):
    "Delete an OrderBid"
    o1a = OrderBid(DUMMY_EX_ID, D('150.01'), D('3.3330'), Order.STATE_CREATED, 0, order_id=12345)
    o2  = OrderBid(DUMMY_EX_ID, D('151.53'), D('4.6466'), Order.STATE_CREATED, 1, order_id=12346)
    self.ob.event(o1a)
    self.ob.event(o2)
    self.assertEqual(len(self.ob), 2)
    o1b = OrderBid(DUMMY_EX_ID, D('150.01'), D('3.3330'), Order.STATE_DELETED, 2, order_id=12345)
    self.ob.event(o1b)
    self.assertEqual(len(self.ob), 1)

  def testEstimate_BidSanity(self):
    "estimateBid() catches stupid values"
    self.populateRangeOfAsks(1, 5, vol=1)
    with self.assertRaises(ValueError):
      self.ob.estimateBid(spend=1, volume=1)
    with self.assertRaises(ValueError):
      self.ob.estimateBid(volume=D(-1))
    with self.assertRaises(ValueError):
      self.ob.estimateBid(spend=D(-1.00))
    with self.assertRaises(ValueError):
      self.ob.estimateBid(spend=D(1.00), limit=-1)

  
  def testEstimate_AskSanity(self):
    "estimateAsk() catches stupid values"
    self.populateRangeOfBids(1, 5, vol=1)
    with self.assertRaises(ValueError):
      self.ob.estimateAsk(earn=1, volume=1)
    with self.assertRaises(ValueError):
      self.ob.estimateAsk(volume=D(-1))
    with self.assertRaises(ValueError):
      self.ob.estimateAsk(earn=D(-1.00))
    with self.assertRaises(ValueError):
      self.ob.estimateAsk(earn=D(1.00), limit=-1)


  def testEstimate_FixedVolumeBid(self):
    "Estimate fixed-volume bid"
    self.populateRangeOfAsks(1, 5, vol=1)
    self.assertEqual(self.ob.estimateBid(volume=D(1)), (1,1))
    self.assertEqual(self.ob.estimateBid(volume=D(2)), (3,2))
    self.assertEqual(self.ob.estimateBid(volume=D(2), limit=1.5), (1,1))
    spent, volume = self.ob.estimateBid(volume=D(2), limit=1.5)
    assert isinstance(spent, Decimal)
    assert isinstance(volume, Decimal)
    
  
  def testEstimate_FixedPriceBid(self):
    "Estimate fixed-price bid"
    self.populateRangeOfAsks(1, 5, vol=1)
    self.assertEqual(self.ob.estimateBid(spend=D(1.00)), (1.00, 1))
    self.assertEqual(self.ob.estimateBid(spend=D(2.00)), (2.00, 1.5))
    self.assertEqual(self.ob.estimateBid(spend=D(9.00), limit=1), (1,1))
    spent, volume = self.ob.estimateBid(spend=D(9.00), limit=1)
    assert isinstance(spent, Decimal)
    assert isinstance(volume, Decimal)

    
  def testEstimate_FixedVolumeAsk(self):
    "Estimate fixed-volume ask"
    self.populateRangeOfBids(1, 5, vol=1)
    self.assertEqual(self.ob.estimateAsk(volume=D(1)), (5,1))
    self.assertEqual(self.ob.estimateAsk(volume=D(2)), (9,2))
    self.assertEqual(self.ob.estimateAsk(volume=D(2), limit=4.5), (5,1))
    self.assertEqual(self.ob.estimateAsk(volume=D(2), limit=4), (9,2))
    earned, volume = self.ob.estimateAsk(volume=D(2), limit=4)
    assert isinstance(earned, Decimal)
    assert isinstance(volume, Decimal)

  
  def testEstimate_FixedPriceAsk(self):
    "Estimate fixed-price ask"
    self.populateRangeOfBids(1, 5, vol=1)
    self.assertEqual(self.ob.estimateAsk(earn=D(5)), (5, 1))
    self.assertEqual(self.ob.estimateAsk(earn=D(8.5)), (8.5, 1.875))
    self.assertEqual(self.ob.estimateAsk(earn=D(9), limit=4.5), (5,1))
    self.assertEqual(self.ob.estimateAsk(earn=D(9), limit=4), (9,2))
    earned, volume = self.ob.estimateAsk(earn=D(9), limit=4)
    assert isinstance(earned, Decimal)
    assert isinstance(volume, Decimal)


if __name__ == '__main__':
  unittest.main()


