#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import datetime
import time

from decimal import Decimal

import collections

from utils.time.tools import to_epoch_timestamp
from utils.time.htime import HorseyTiem
from utils.time import HORSEYTIEM

from utils.data import chunker, infrange, hrange
from utils.hmath import round_dec_up_to_n_places, round_dec_down_to_n_places, check_dec_is_n_places

from events.broker import ToyEventReceiver



class TestHelpers(unittest.TestCase):
  
  def test_to_epochtime(self):
    dt1 = datetime.datetime.now()
    dt2 = datetime.datetime.now() + datetime.timedelta(hours=1)
    self.assertNotEqual( to_epoch_timestamp(dt1), to_epoch_timestamp(dt2) )
  
  
  def test_chunker(self):
    chunks = list( chunker(4, 'abcdef') )
    self.assertEqual(len(chunks), 2)
    self.assertEqual(''.join(chunks[0]), 'abcd')
    self.assertEqual(''.join(chunks[1]), 'ef')




class TestDecimalHelpers(unittest.TestCase):
  
  def test_check_dp(self):
    self.assertTrue(  check_dec_is_n_places( Decimal('0.1'), 1) )
    self.assertFalse( check_dec_is_n_places( Decimal('0.1111'), 2) )
  
  
  def test_round_up(self):
    self.assertEqual( round_dec_up_to_n_places( Decimal('0.10'), 2), Decimal('0.10'))
    self.assertEqual( round_dec_up_to_n_places( Decimal('0.111'), 2), Decimal('0.12'))
  
  
  def test_round_down(self):
    self.assertEqual( round_dec_down_to_n_places(Decimal(999), 2), Decimal('999'))
    self.assertEqual( round_dec_down_to_n_places(Decimal('0.18'), 2), Decimal('0.18'))
    self.assertEqual( round_dec_down_to_n_places(Decimal('0.119'), 2), Decimal('0.11'))
  
  
  def test_check_dp(self):
    "Numbers correctly pass & fail decimal place count"
    self.assertTrue( check_dec_is_n_places(Decimal('0.01315961'), 8))
    self.assertTrue( check_dec_is_n_places(Decimal('0.01315961'), 9))
    self.assertFalse( check_dec_is_n_places(Decimal('0.01315961'), 7))


    

class TestHRange(unittest.TestCase):
  "Ranges that can step by floating point numbers"
  
  def test_IntegerPosStep(self):
    "Range of positive integers from 0-9"
    ir = hrange(0, 10, 1)
    for i in range(0, 10):
      self.assertEqual(i, next(ir))
    with self.assertRaises(StopIteration):
      next(ir)
  
  
  def test_IntegerNegStep(self):
    "Range of positive integers from 0-9"
    ir = hrange(0, -10, -1)
    for i in range(0, -10, -1):
      self.assertEqual(i, next(ir))
    with self.assertRaises(StopIteration):
      next(ir)
  
  
  def test_FloatPosStep(self):
    "Range of positive integers from 0-9"
    ir = hrange(0, 1, 0.5)
    for i in [0, 0.5]:
      self.assertEqual(i, next(ir))
    with self.assertRaises(StopIteration):
      next(ir)
  
  
  def test_FloatNegStep(self):
    "Range of positive integers from 0-9"
    ir = hrange(0, -1, -0.5)
    for i in [0, -0.5]:
      self.assertEqual(i, next(ir))
    with self.assertRaises(StopIteration):
      next(ir)





class TestInfRange(unittest.TestCase):
  "Ranges that go on forever"
  
  def test_IntegerPosStep(self):
    "Range of positive integers from 0-9"
    ir = infrange()
    for i in range(0, 10):
      self.assertEqual(i, next(ir))
  
  
  def test_IntegerNegStep(self):
    "Range from 0 to -9"
    ir = infrange(0, -1)
    for i in range(0, 10, -1):
      self.assertEqual(i, next(ir))
  
  
  def test_FloatPosStep(self):
    "Float steps +ve"
    ir = infrange(0, 0.01)
    for i in [0, 0.01, 0.02, 0.03]:
      self.assertEqual(i, next(ir))
  
  
  def test_FloatNegStep(self):
    "Float steps -ve"
    ir = infrange(0, -0.01)
    for i in [0, -0.01, -0.02, -0.03]:
      self.assertEqual(i, next(ir))

    


  
  
if __name__ == '__main__':
  unittest.main()
  
