#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from predictors.coefficient import *


class Test_RangeCoefficient(unittest.TestCase):
	
	TEST_VALUES = [1,2,3,4,5,6,7,8,9,10]
	
	def test_random(self):
		"RangeCoefficient.random()"
		rc = RangeCoefficient(values=self.TEST_VALUES)
		for i in range(0,100):
			self.assertIn(rc.random(), self.TEST_VALUES)
	
	
	def test_seed(self):
		"RangeCoefficient.seed()"
		rc = RangeCoefficient(values=self.TEST_VALUES)
		seed = rc.seed()
		assert isinstance(seed, list)
		self.assertEqual(seed, self.TEST_VALUES)
		self.assertEqual(seed[0], self.TEST_VALUES[0])
		self.assertEqual(seed[-1], self.TEST_VALUES[-1])
	
		
		
class Test_FloatCoefficient(unittest.TestCase):
	
	def test_random(self):
		"FloatCoefficient.random()"
		fc = FloatCoefficient(dmin=10, dmax=20)
		for i in range(0, 100):
			assert 10 <= fc.random() <= 20
	
	def test_seed(self):
		"FloatCoefficient.seed()"
		fc = FloatCoefficient(dmin=10, dmax=20)
		seed = fc.seed()
		self.assertEqual(len(seed), FloatCoefficient.N_SLOTS)
		self.assertEqual(seed[0], 10)
		self.assertEqual(seed[-1], 20)
		

class Test_IntCoefficient(unittest.TestCase):
	
	def test_random(self):
		"IntCoefficient.random()"
		ic = IntCoefficient(dmin=10, dmax=20)
		for i in range(0, 100):
			self.assertIn(ic.random(), range(10,21))
	
	def test_seed(self):
		"IntCoefficient.seed()"
		ic = IntCoefficient(dmin=10, dmax=20)
		seed = ic.seed()
		self.assertEqual(seed[0], 10)
		self.assertEqual(seed[-1], 20)
		for v in seed:
			self.assertIn(v, range(10,21))
		
