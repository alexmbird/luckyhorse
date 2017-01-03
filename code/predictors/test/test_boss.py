#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from storage import StorageEngine
from events.broker import QueuedBrokerBundle
from datasource.signals.dummy import DataSourceDummy
from indicators.factory import IndicatorFactory

from predictors.boss import PredictionBoss
from predictors.axis import Axis

from predictors.preds.toy import ToyPredictor

from utils.time import HORSEYTIEM
from utils.exceptions import InsufficientDataError

from events import Trade
from decimal import Decimal as D 


class Test_PredictionBoss(unittest.TestCase):

	def setUp(self):
		self.broker		= 	QueuedBrokerBundle(maxsize=20)
		self.storage 	= StorageEngine()
		self.src				= DataSourceDummy(self.broker)
		self.sources		=	{'market':self.src}
		self.ifakt			= IndicatorFactory(self.storage, self.sources)
	
	
	def test_createWrong(self):
		"PredictionBoss: create with stupid values"
		with self.assertRaises(TypeError):
			pb = PredictionBoss(None, None, None)
	
	
	def test_MakeTree(self):
		"PredictionBoss: make prediction tree for ToyPredictor"
		preds	= [ToyPredictor,]
		pb 		= PredictionBoss(self.src, preds, self.ifakt, self.storage)
		self.assertEqual(len(pb.children), 1)
		for c in pb.children:
			self.assertIsInstance(c, Axis)
	
	
	def test_preroll(self):
		"PredictionBoss.preroll() gets predictions flowing"
		preds	= [ToyPredictor,]
		pb 		= PredictionBoss(self.src, preds, self.ifakt, self.storage)
		with self.assertRaises(InsufficientDataError):
			pb.predict(HORSEYTIEM.time()+3600)
		pb.preroll(HORSEYTIEM.time(), 100)
		for c in pb.children:
			self.assertTrue(pb.hist_full(c))
	
	
	def test_prediction(self):
		"PredictionBoss.predict() can see the future"
		preds	= [ToyPredictor,]
		pb 		= PredictionBoss(self.src, preds, self.ifakt, self.storage)
		pb.preroll(HORSEYTIEM.time(), 100)
		prediction	 	= pb.predict(HORSEYTIEM.time()+3600)
		self.assertIsInstance(prediction, float)
		assert 90 <= prediction <= 110
	
	
	def test_mutate(self):
		"PredictionBoss.groom()"
		now = HORSEYTIEM.time()
		t = Trade(0, D(100), D(1), now, now, 0)
		preds	= [ToyPredictor,]
		pb 		= PredictionBoss(self.src, preds, self.ifakt, self.storage)
		pb.children[0].dump()
		pb.forceMutate()			# Won't do anything, no training data
		pb.preroll(HORSEYTIEM.time(), 100)
		pb.children[0].dump()
		pred1	 	= pb.predict(HORSEYTIEM.time()+3600)
		pb.preroll(HORSEYTIEM.time(), 100)
		pb.forceMutate()			# Now we have training data, results will improve
		pb.children[0].dump()
		pb.preroll(HORSEYTIEM.time(), 100)
		pb.children[0].dump()
		pred2	 	= pb.predict(HORSEYTIEM.time()+3600)
		self.assertNotEqual(pred1, pred2)
		self.assertEqual(pred2, 100)

