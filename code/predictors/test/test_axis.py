#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from utils.time import HORSEYTIEM
from utils.time.period import FixedPeriod_5Min

from utils.exceptions import InsufficientDataError

from storage import StorageEngine
from indicators.factory import IndicatorFactory
from indicators.inds.simple import DummyIndicator

from events.broker import QueuedBrokerBundle
from datasource.signals.dummy import DataSourceDummy

from predictors.factory import PredictorFactory
from predictors.axis import Axis
from predictors.preds.toy import ToyPredictor2
from predictors.preds.simple import PredictorDummy
from predictors.preds._base import PredictorBase

import random
import numpy as np





class UtilsMixIn(object):
	
	def assertAlmostEqual(self, a, b):
		assert np.allclose([a],[b])
	




class Test_PredictorAxis(unittest.TestCase, UtilsMixIn):
	
	def setUp(self):
		self.broker		= 	QueuedBrokerBundle(maxsize=20)
		self.storage 	= StorageEngine()
		src						= DataSourceDummy(self.broker)
		self.sources		=	{'market':src}
		self.ifakt			= IndicatorFactory(self.storage, self.sources)
		self.pfakt			= PredictorFactory(self.ifakt, src, self.storage)
	
	
	def test_createWrong(self):
		"Axis.__init__(), bad values"
		
		# Try to set a nonexistent coefficient
		with self.assertRaises(ValueError):
			ax = Axis(
				self.pfakt, PredictorDummy,
				{'does_not_exist':1}, None
			)
		
		# Mutable coeff can't be in statics
		with self.assertRaises(ValueError):
			ax = Axis(
				self.pfakt, PredictorDummy,
				{'cf1':1}, 'cf1'
			)
		
		# Must have at least one unbound coeff
		with self.assertRaises(ValueError):
			ax = Axis(
				self.pfakt, PredictorDummy,
				{'cf1':1, 'cf2':2}
			)
		
		# Bad indicator factory
		with self.assertRaises(TypeError):
			ax = Axis(
				None, PredictorDummy,
				{'cf1':1}
			)
		
			
	
	def test_createGood(self):
		"Axis.__init__(), good values"
		ax = Axis(self.pfakt, PredictorDummy)
		assert isinstance(ax, Axis)
		str(ax)		# ensure str() isn't broken
		
		# Test coeff checks
		self.assertEqual(len(ax._bound()), 0)
		self.assertEqual(len(ax._unbound()), 2)
		
	
	def test_instantiate(self):
		"Axis._instantiate()"
		ax0 = Axis(self.pfakt, PredictorDummy)
		# Mutate for 2st value
		ax1 = ax0._instantiate(1)
		self.assertIsInstance(ax1, Axis)
		# Mutate for 2nd value; returns real Predictor obj
		ax2	= ax1._instantiate(1)
		self.assertIsInstance(ax2, PredictorDummy)
	
	
	def test_Winner(self):
		"Axis.winner()"
		ax0 = Axis(self.pfakt, PredictorDummy)
		with self.assertRaises(InsufficientDataError):
			ax0.winner()
		
		# Judge, then try again.  Should still fail because not enough hist
		n = Axis.WRONGNESS_HIST * len(PredictorDummy.COEFFICIENTS)
		for i in range(1, n):
			with self.assertRaises(InsufficientDataError):
				ax0.winner()		# Fails until enough judgements
			ax0.judge(HORSEYTIEM.time(), 100)
		
		# Check results of competition.  Since dummy always returns 100 teh wrongness
		# will be zero.
		predictor, wrongness = ax0.winner()
		self.assertIsInstance(predictor, (Axis, PredictorBase))
		self.assertIsInstance(wrongness, float)
	
	
	def test_Winner_Perfect(self):
		"Axis.winner() with true value identical to dummy's"
		ax0 = Axis(self.pfakt, PredictorDummy)
		ax0.preroll(HORSEYTIEM.time(), 100)
		predictor, wrongness = ax0.winner()
		self.assertIsInstance(predictor, (Axis,PredictorBase))
		self.assertEqual(wrongness, 0)


	def test_Winner_Imperfect(self):
		"Axis.winner() with true value slightly different to dummy's"
		ax0 = Axis(self.pfakt, PredictorDummy)
		ax0.preroll(HORSEYTIEM.time(), 103)
		predictor, wrongness = ax0.winner()
		self.assertIsInstance(predictor, (Axis,PredictorBase))
		self.assertAlmostEqual(wrongness, 0.030000000000000006)
		
	
	def test_Winner_VeryWrong(self):
		"Axis.winner() with true value very different to dummy's"
		ax0 = Axis(self.pfakt, PredictorDummy)
		ax0.preroll(HORSEYTIEM.time(), -500)
		predictor, wrongness = ax0.winner()
		self.assertIsInstance(predictor, (Axis,PredictorBase))
		self.assertAlmostEqual(wrongness, 6)

	
	def test_Mutate(self):
		"Axis.mutate()"
		ax0 = Axis(self.pfakt, ToyPredictor2)
		ax0.preroll(HORSEYTIEM.time(), -500)
		ax0.dump()
		ax0.mutate()
		value = ax0.predict(HORSEYTIEM.time()+10)

			