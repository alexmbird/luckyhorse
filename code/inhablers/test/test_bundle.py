#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from inhablers import InhablerBundle
from inhablers import TRADE_OK, TRADE_MUST_START
from inhablers import TRADE_NO, TRADE_MUST_ABORT




class TestInhablerBundle(unittest.TestCase):
	
	def test_NoContent(self):
		"InhablerBundle behaves sensibly with no registered inhablers"
		ib = InhablerBundle()
		self.assertEqual(ib.decide(0), TRADE_OK)
		self.assertTrue(ib.is_yes(0))
		self.assertFalse(ib.is_no(0))


