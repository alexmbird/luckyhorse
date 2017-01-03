#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from storage import StorageEngine
from events.broker import QueuedBrokerBundle
from datasource.signals.dummy import DataSourceDummy
from indicators.factory import IndicatorFactory
from indicators.inds.simple import DummyIndicator

from utils.time.period import FloatingPeriod_5Min
from predictors.preds.toy import ToyPredictor
from predictors.preds import simple
from predictors.factory import PredictorFactory






class Test_PredictorDummy(unittest.TestCase):
	
	DUMMY_COEFFICIENTS		= {'cf1':1, 'cf2':2}
	
	def setUp(self):
		self.broker		= 	QueuedBrokerBundle(maxsize=20)
		self.storage 	= StorageEngine()
		self.src				= DataSourceDummy(self.broker)
		self.sources		=	{'market':self.src}
		self.ifakt			= IndicatorFactory(self.storage, self.sources)

	def test_create(self):
		"PredictorDummy.__init__()"
		with self.assertRaises(ValueError):
			pd = simple.PredictorDummy({}, {}, self.storage, self.src)
		pd = simple.PredictorDummy({}, self.DUMMY_COEFFICIENTS, self.storage, self.src)
		self.assertIn('cf1', pd.COEFFICIENTS)
	
	def test_predict(self):
		"PredictorDummy.predict()"
		pd = simple.PredictorDummy({}, self.DUMMY_COEFFICIENTS, self.storage, self.src)
		p = FloatingPeriod_5Min()
		self.assertEqual( pd.predict(p), 100 )	# Dummy always returns 100
	
	def test_readonly_coefficients(self):
		"Predictor coefficients are read-only"
		p = simple.PredictorDummy({}, self.DUMMY_COEFFICIENTS, self.storage, self.src)
		p.nx_can_be_set = 'yes'
		with self.assertRaises(AttributeError):
			p.cf1		= 'no'
			


class Test_PredictorFactory(unittest.TestCase):
	
	def setUp(self):
		self.broker		= 	QueuedBrokerBundle(maxsize=20)
		self.storage 	= StorageEngine()
		self.src				= DataSourceDummy(self.broker)
		self.sources		=	{'market':self.src}
		self.ifakt			= IndicatorFactory(self.storage, self.sources)
	
	
	def test_CreateWrong(self):
		"Make a PredictorFactory with wrong values"
		with self.assertRaises(TypeError):
			pf = PredictorFactory(self.src, self.ifakt)
	
	
	def test_CreateOk(self):
		"Create a Predictor*"
		pf = PredictorFactory(self.ifakt, self.src, self.storage)
		bound_coefs		= {k:c.random() for k,c in ToyPredictor.COEFFICIENTS.items()}
		pred = pf.create(ToyPredictor, bound_coefs)
		self.assertIsInstance(pred, ToyPredictor)
		for k in bound_coefs.keys():
			getattr(pred, k)
		
		
		