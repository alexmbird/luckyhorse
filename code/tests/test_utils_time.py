#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from events.broker import ToyEventReceiver

import time

from utils.time import HORSEYTIEM



from utils.time.htime import HorseyTiem
class TestHTime(unittest.TestCase):

	def test_TimeNormal(self):
		"HorseyTiem.time() returns correct time when not overridden"
		ht = HorseyTiem()
		t = time.time()
		assert t-1 < ht.time() < t+1
		ht.override(None)
		assert t-1 < ht.time() < t+1


	def test_TimeOverride(self):
		"HorseyTiem.time() returns override value"
		ht = HorseyTiem()
		t = time.time()
		assert t-1 < ht.time() < t+1    # Not yet overridden
		ht.override(t+1000)
		assert ht.time() == t+1000      # Visit to the future
		ht.override(None)
		t = time.time()
		assert t-1 < ht.time() < t+1    # Back to normal


	def test_TimeSleepNormal(self):
		"HorseyTiem.sleep() in normal time"
		ht = HorseyTiem()
		naptime = 0.5
		t0 = ht.time()
		ht.sleep(naptime)
		t1 = ht.time()
		assert t1 >= t0 + naptime


	def test_TimeSleepOverride(self):
		"HorseyTiem.sleep() in ketatime"
		ht = HorseyTiem()
		naptime = 0.5
		ht.override(1000000)
		t0 = ht.time()
		ht.sleep(naptime)
		t1 = ht.time()
		assert t1 >= t0 + naptime


	def test_TimeSleepNormalFiresTimers(self):
		"Timers fire correctly in normal sleep()"
		ht = HorseyTiem()
		er = ToyEventReceiver(timefunk=ht.time)
		t0 = ht.time()
		ht.setTimer(er.rcv, t0+0.25)
		ht.sleep(1)
		self.assertEqual(len(er.events), 1)   # timer fired
		t1 = ht.time()
		assert t0 + 0.25 <= er.events[0][0] < t1


	def test_TimeSleepOverrideFiresTimers(self):
		"Timers fire correctly in overridden sleep()"
		ht = HorseyTiem()
		ht.override(1000000)
		er = ToyEventReceiver(timefunk=ht.time)
		t0 = ht.time()
		self.assertEqual(t0, 1000000)
		ht.setTimer(er.rcv, t0+0.25)
		ht.sleep(1)
		self.assertEqual(len(er.events), 1)   # timer fired
		t1 = ht.time()
		assert t0 + 0.25 <= er.events[0][0] < t1





if __name__ == '__main__':
	unittest.main()


