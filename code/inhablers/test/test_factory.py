#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from storage import StorageEngine
from indicators.factory import IndicatorFactory
from indicators.inds.simple import DummyIndicator

from events.broker import QueuedBrokerBundle
from datasource.signals.dummy import DataSourceDummy

from inhablers import InhablerBundle
from inhablers.factory import InhablerFactory



class TestInhablerFactory(unittest.TestCase):
	
	def setUp(self):
		self.broker		= 	QueuedBrokerBundle(maxsize=20)
		self.storage 	= StorageEngine()
		self.src				= DataSourceDummy(self.broker)
		self.sources		=	{'market':self.src}
		self.ifakt			= IndicatorFactory(self.storage, self.sources)

	
	def test_Empty(self):
		"InhablerFactory.__init__() wprks"
		infakt			= InhablerFactory(self.ifakt, self.storage, self.sources)
		