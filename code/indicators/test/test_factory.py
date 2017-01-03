#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from indicators.factory import IndicatorFactory, RequiredIndicatorsMixIn

from storage import StorageEngine
from datasource.signals.dummy import DataSourceDummy
from events.broker import QueuedBrokerBundle

from indicators.inds.simple import DummyIndicator



class TestSpec_Broken(object):
	"Broken spec"
	REQD_INDICATORS	=	{}

class TestSpec_Barren(RequiredIndicatorsMixIn):
	"Simple user with no children to load"
	REQD_INDICATORS	=	{}

class TestSpec_Children(RequiredIndicatorsMixIn):
	"Simple indicator that will cause child inds to be loaded"
	REQD_INDICATORS	=	{
		'dummy':		(DummyIndicator,),
	}



class Test_IndicatorFactory(unittest.TestCase):
	
	def setUp(self):
		self.broker		= 	QueuedBrokerBundle(maxsize=20)
		self.storage 	= StorageEngine()
		self.sources		=	{'market':DataSourceDummy(self.broker)}

	
	def test_createFromReqd_Wrong(self):
		"Create indicators from broken specs"
		fakt 	= IndicatorFactory(self.storage, self.sources)
		with self.assertRaises(TypeError):
			inds 	= fakt.createFromReqd(TestSpec_Broken)
	
	
	def test_createFromReqd_Barren(self):
		"Create indicators from empty spec"
		fakt 	= IndicatorFactory(self.storage, self.sources)
		src		= self.sources['market']
		inds 	= fakt.createFromReqd(TestSpec_Barren)
		self.assertEqual(len(inds), 0)
		

	def test_createFromReqd_One(self):
		"Create indicators from spec requiring some"
		fakt 	= IndicatorFactory(self.storage, self.sources)
		src		= self.sources['market']
		with self.assertRaises(ValueError):
			inds 	= fakt.createFromReqd(TestSpec_Children, default_src=None)
		inds 	= fakt.createFromReqd(TestSpec_Children, default_src=src)
		self.assertEqual(len(inds), 1)
		self.assertIn('dummy', inds)
		self.assertIsInstance(inds['dummy'], DummyIndicator)
		
