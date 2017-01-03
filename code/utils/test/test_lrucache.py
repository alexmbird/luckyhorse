#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from utils.data import LRUCache
from utils.time.period import FixedPeriod_1Day, FixedPeriod_5Min
from utils.time import HORSEYTIEM



class TestLRUCache(unittest.TestCase):

	def test_LRUCacheNoAccess(self):
		"When nothing has been accessed, LRUCache discards earliest items"
		c = LRUCache(3)
		self.assertEqual(len(c), 0)
		for i in range(0, 5):
			c[i] = 'foo'
		self.assertEqual(len(c), 3)
		assert 4 in c
		assert 3 in c
		assert 2 in c
		assert 1 not in c
		assert 0 not in c


	def test_LRUCacheAccessed(self):
		"Least recently read items get discarded first"
		c = LRUCache(3)
		for i in range(0, 3):
			c[i] = 'hello'
		v = c[0]
		c[3] = 'hello2'
		assert 3 in c
		assert 2 in c
		assert 1 not in c
		assert 0 in c

	
	def test_StoreTupleKey(self):
		"LRUCache() tuple key"
		t0 = (1, 2, 3)
		t1	 = (3, 2, 1)
		c = LRUCache()
		c[t0]		= 'a string'
		with self.assertRaises(KeyError):
			c[t1]
		self.assertEqual(c[t0], 'a string')
	
	
	def test_StorePeriodKey(self):
		"LRUCache() utils.time.period key"
		c 		= LRUCache()
		p0 	= FixedPeriod_1Day(HORSEYTIEM.time())
		p1		= p0 - 1
		c[p0]		= 'a string'
		with self.assertRaises(KeyError):
			c[p1]
		self.assertEqual(c[p0], 'a string')
	
	
	def test_StorePeriodTupleKey(self):
		"LRUCache() tuple-utils.time.period key"
		c 		= LRUCache()
		p0 	= FixedPeriod_5Min(HORSEYTIEM.time())
		p1		= p0 - 1
		tp0	= (1, p0)
		tp1	= (1, p1)
		c[tp0]		= 'a string'
		with self.assertRaises(KeyError):
			c[tp1]
		self.assertEqual(c[tp0], 'a string')
	