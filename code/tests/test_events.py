#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from events import Trade, Order, OrderAsk, OrderBid
from events.broker import QueuedBrokerBundle, Broker, ToyEventReceiver

from decimal import Decimal as D


DUMMY_EXCH_ID   = 0



class TestTrade(unittest.TestCase):
  
  def test_CreateOk(self):
    "Create trade with sensible values"
    t = Trade(
      DUMMY_EXCH_ID, D('0.01'), D('0.00000001'), 1000001, 1000001.123, 987654321
    )
    self.assertEqual(t.exchange_id, DUMMY_EXCH_ID)
    self.assertEqual(t.ts_exec, 1000001)
  
  
  def test_CreateBadValues(self):
    "Create with -ve price or volume"
    with self.assertRaises(ValueError):
      Trade(DUMMY_EXCH_ID, D('-0.01'), D('0.00000001'), 1000001, 1000001.123, 987654321)
    with self.assertRaises(ValueError):
      Trade(DUMMY_EXCH_ID, D('0.01'), D('-0.00000001'), 1000001, 1000001.123, 987654321)


class TestOrder(unittest.TestCase):
  
  def test_CreateOk(self):
    "Create order with sensible values"
    o = Order(
      DUMMY_EXCH_ID, D('1.99'), D('0.0000001'), Order.STATE_CREATED, 1000001.123
    )
    self.assertEqual(o.exchange_id, DUMMY_EXCH_ID)
    self.assertEqual(o.ts_update, 1000001.123)





class TestBroker(unittest.TestCase):
  
  def test_CallbackPriority(self):
    b = Broker()
    tec1 = ToyEventReceiver(delay=0.1)
    tec2 = ToyEventReceiver(delay=0.1)
    b.subscribe(tec1.rcv, 0)
    b.subscribe(tec2.rcv, 1)
    b.publish('a string')
    assert tec2.events[0][0] > tec1.events[0][0]



@unittest.skip("Write me")
class TestQueuedBrokerBundle(unittest.TestCase):
  pass
