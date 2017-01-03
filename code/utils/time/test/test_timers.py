#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from events.broker import ToyEventReceiver

from utils.time import HORSEYTIEM
from utils.time.htime import HorseyTiem


class Test_Timers(unittest.TestCase):

	def test_setTimer_abs(self):
		"HorseyTiem.setTimer() with absolute target"
		ht 	= HorseyTiem()
		ht.override(10000)
		ter	= ToyEventReceiver()
		ht.setTimer(ter.rcv, 10010)
		tu 	= (10010, 0, ter.rcv)
		self.assertIn(tu, ht._timers)

	
	def test_setTimer_rel(self):
		"HorseyTiem.setTimer() with relative target"
		ht 	= HorseyTiem()
		ht.override(10000)
		ter	= ToyEventReceiver()
		ht.setTimer(ter.rcv, -10)
		tu 	= (10010, 0, ter.rcv)
		self.assertIn(tu, ht._timers)
		