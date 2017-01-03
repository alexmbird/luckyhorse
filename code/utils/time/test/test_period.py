#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest
from events.broker import ToyEventReceiver

import time

from utils.time import HORSEYTIEM






from utils.time.period import FixedPeriod_1Day, ANCHOR_HOUR_LHS
class TestFixedPeriod_1Day(unittest.TestCase):

	'''
	The operator override methods are common to all FixedPeriod* classes so we only
	test them in here.
	'''

	def test_PeriodCreate(self):
		"Create a simple 1-day period"
		p = FixedPeriod_1Day(1417518687)
		self.assertEqual(p.lhs_ts, 1417478400)
		self.assertEqual(p.rhs_ts, 1417564800)
		str(p)

	def test_PeriodCreate_Anchor(self):
		"Create a simple 1-day period anchored"
		p = FixedPeriod_1Day(1417518687, anchor=ANCHOR_HOUR_LHS)
		self.assertEqual(p.lhs_ts, 1417518000)
		self.assertEqual(p.rhs_ts, 1417604400)
		str(p)

	def test_Offset(self):
		"Offsets from a 1-day period"
		p1 = FixedPeriod_1Day(100000009)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"1-day period contains a timestamp"
		p1 = FixedPeriod_1Day(100000009)
		assert 100000008 in p1

	def test_contains_fixedperiod(self):
		"1-day period contains another period"
		p1 = FixedPeriod_1Day(100000009)
		p2 = FixedPeriod_5Min(100000009)
		assert p2 in p1

	def test_contains_wrong(self):
		"1-day period contains incomparable object"
		p1 = FixedPeriod_1Day(34554523)
		with self.assertRaises(TypeError):
			assert 'spam' not in p1
			assert None not in p1
			assert True not in p1
			assert False not in p1
			assert {} not in p1

	def test_period_equals(self):
		"1-day periods comparable with == operator"
		p1 = FixedPeriod_1Day(100000009)
		p2 = FixedPeriod_1Day(100000008)
		assert p1 == p2



from utils.time.period import FixedPeriod_12Hour, ANCHOR_HOUR_LHS
class TestFixedPeriod_12Hour(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 12-hour period"
		p = FixedPeriod_12Hour(1417531103)
		self.assertEqual(p.lhs_ts, 1417521600)
		self.assertEqual(p.rhs_ts, 1417564800)

	def test_PeriodCreateAnchor(self):
		"Create a 12-hour period anchored at one end"
		p = FixedPeriod_12Hour(1417541944, anchor=ANCHOR_HOUR_LHS)
		self.assertEqual(p.lhs_ts, 1417539600)
		self.assertEqual(p.rhs_ts, 1417582800)

	def test_Offset(self):
		"Offsets from a 12-hour period"
		p1 = FixedPeriod_12Hour(1417541944)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"12-hour period contains a timestamp"
		p1 = FixedPeriod_12Hour(1417531103)
		assert 1417521666 in p1

	def test_period_equals(self):
		"12-hour periods comparable with == operator"
		p1 = FixedPeriod_12Hour(1417531103)
		p2 = FixedPeriod_12Hour(1417521666)
		assert p1 == p2




from utils.time.period import FixedPeriod_6Hour, ANCHOR_HOUR_LHS
class TestFixedPeriod_6Hour(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 6-hour period"
		p = FixedPeriod_6Hour(1417519956)
		self.assertEqual(p.lhs_ts, 1417500000)
		self.assertEqual(p.rhs_ts, 1417521600)

	def test_PeriodCreateAnchor(self):
		"Create a 6-hour period anchored at one end"
		p = FixedPeriod_6Hour(1417520014, anchor=ANCHOR_HOUR_LHS)
		self.assertEqual(p.lhs_ts, 1417518000)
		self.assertEqual(p.rhs_ts, 1417539600)

	def test_Offset(self):
		"Offsets from a 6-hour period"
		p1 = FixedPeriod_6Hour(1417520014)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"6-hour period contains a timestamp"
		p1 = FixedPeriod_6Hour(1417520158)
		assert 1417515477 in p1

	def test_period_equals(self):
		"6-hour periods comparable with == operator"
		p1 = FixedPeriod_6Hour(1417520158)
		p2 = FixedPeriod_6Hour(1417515477)
		assert p1 == p2


from utils.time.period import FixedPeriod_3Hour, ANCHOR_HOUR_LHS
class TestFixedPeriod_3Hour(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 3-hour period"
		p = FixedPeriod_3Hour(1417874397)
		self.assertEqual(p.lhs_ts, 1417867200)
		self.assertEqual(p.rhs_ts, 1417878000)

	def test_PeriodCreateAnchor(self):
		"Create a 3-hour period anchored at one end"
		p = FixedPeriod_3Hour(1417874438, anchor=ANCHOR_HOUR_LHS)
		self.assertEqual(p.lhs_ts, 1417874400)
		self.assertEqual(p.rhs_ts, 1417885200)

	def test_Offset(self):
		"Offsets from a 3-hour period"
		p1 = FixedPeriod_3Hour(1417520014)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"3-hour period contains a timestamp"
		p1 = FixedPeriod_3Hour(1417874438)
		assert 1417874499 in p1

	def test_period_equals(self):
		"3-hour periods comparable with == operator"
		p1 = FixedPeriod_6Hour(1417520158)
		p2 = FixedPeriod_6Hour(1417515477)
		assert p1 == p2


from utils.time.period import FixedPeriod_1Hour, ANCHOR_HOUR_LHS
class TestFixedPeriod_1Hour(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 1-hour period"
		p = FixedPeriod_1Hour(1417519446)
		self.assertEqual(p.lhs_ts, 1417518000)
		self.assertEqual(p.rhs_ts, 1417521600)

	def test_PeriodCreateAnchor(self):
		"Create a 1-hour period anchored at one end"
		p = FixedPeriod_1Hour(1417519446, anchor=ANCHOR_HOUR_LHS)
		self.assertEqual(p.lhs_ts, 1417518000)
		self.assertEqual(p.rhs_ts, 1417521600)

	def test_Offset(self):
		"Offsets from a 1-hour period"
		p1 = FixedPeriod_1Hour(1417519446)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"1-hour period contains a timestamp"
		p1 = FixedPeriod_1Hour(1417519106)
		assert 1417518742 in p1

	def test_period_equals(self):
		"1-hour periods comparable with == operator"
		p1 = FixedPeriod_1Hour(1417519106)
		p2 = FixedPeriod_1Hour(1417519010)
		assert p1 == p2




from utils.time.period import FixedPeriod_30Min, ANCHOR_HOUR_LHS
@unittest.skip("Adjust values for 30m")
class TestFixedPeriod_30Min(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 30-min period"
		p = FixedPeriod_30Min(1417521626)
		self.assertEqual(p.lhs_ts, 1417521600)
		self.assertEqual(p.rhs_ts, 1417522500)

	def test_PeriodCreateAnchor(self):
		with self.assertRaises(ValueError):
			p2 = FixedPeriod_30Min(100000009, anchor=ANCHOR_HOUR_LHS)

	def test_Offset(self):
		"Offsets from a 30-min period"
		p1 = FixedPeriod_30Min(1417521626)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"30-min period contains a timestamp"
		p1 = FixedPeriod_30Min(1417521626)
		assert 1417521629 in p1

	def test_period_equals(self):
		"30-min periods comparable with == operator"
		p1 = FixedPeriod_30Min(1417521626)
		p2 = FixedPeriod_30Min(1417521629)
		assert p1 == p2




from utils.time.period import FixedPeriod_15Min, ANCHOR_HOUR_LHS
class TestFixedPeriod_15Min(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 15-min period"
		p = FixedPeriod_15Min(1417521626)
		self.assertEqual(p.lhs_ts, 1417521600)
		self.assertEqual(p.rhs_ts, 1417522500)

	def test_PeriodCreateAnchor(self):
		with self.assertRaises(ValueError):
			p2 = FixedPeriod_15Min(100000009, anchor=ANCHOR_HOUR_LHS)

	def test_Offset(self):
		"Offsets from a 15-min period"
		p1 = FixedPeriod_15Min(1417521626)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"15-min period contains a timestamp"
		p1 = FixedPeriod_15Min(1417521626)
		assert 1417521629 in p1

	def test_period_equals(self):
		"15-min periods comparable with == operator"
		p1 = FixedPeriod_15Min(1417521626)
		p2 = FixedPeriod_15Min(1417521629)
		assert p1 == p2



from utils.time.period import FixedPeriod_5Min, ANCHOR_HOUR_LHS
class TestFixedPeriod_5Min(unittest.TestCase):

	def test_PeriodCreate(self):
		"Create a simple 5-min period"
		p = FixedPeriod_5Min(1417518687)
		self.assertEqual(p.lhs_ts, 1417518600)
		self.assertEqual(p.rhs_ts, 1417518900)

	def test_PeriodCreateAnchor(self):
		with self.assertRaises(ValueError):
			p2 = FixedPeriod_5Min(100000009, anchor=ANCHOR_HOUR_LHS)

	def test_Offset(self):
		"Offsets from a 5-min period"
		p1 = FixedPeriod_5Min(100000009)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"5-min period contains a timestamp"
		p1 = FixedPeriod_5Min(100000009)
		assert 100000008 in p1

	def test_period_equals(self):
		"5-min periods comparable with == operator"
		p1 = FixedPeriod_5Min(100000009)
		p2 = FixedPeriod_5Min(100000008)
		assert p1 == p2



from utils.time.period import FixedPeriod_1Min, ANCHOR_HOUR_LHS
class TestFixedPeriod_1Min(unittest.TestCase):

	def test_Offset(self):
		"Offsets from a 1-min period"
		p1 = FixedPeriod_1Min(100000009)
		p2 = p1.offset(-5)
		self.assertEqual(p1.lhs_ts, p2.lhs_ts + (5*p2.PERIOD_SEC))
		p3 = p1.offset(+5)
		self.assertEqual(p1.lhs_ts, p3.lhs_ts - (5*p3.PERIOD_SEC))

	def test_contains_ts(self):
		"1-min period contains a timestamp"
		p1 = FixedPeriod_5Min(100000009)
		assert 100000008 in p1




from utils.time.period import FloatingPeriod_1Day, FloatingPeriod_5Min, ANCHOR_HOUR_LHS
class TestFloatingPeriod_1Day(unittest.TestCase):

	def test_create(self):
		"1-day floating period creates ok"
		p1 = FloatingPeriod_1Day()
		p1.lhs_ts
		p1.rhs_ts
		str(p1)

	def test_contains_ts(self):
		"1-day floating period contains timestamp"
		now = HORSEYTIEM.time()
		p1 = FloatingPeriod_1Day()
		assert now in p1
		assert now-5 in p1
		assert now + 1 not in p1
		assert now - (60*60*24) + 1 in p1
		assert now - (60*60*24) - 1 not in p1

	def test_contains_fixperiod(self):
		"1-day floating period contains fixed period"
		now = HORSEYTIEM.time()
		p1 = FloatingPeriod_1Day()
		p2 = FixedPeriod_5Min(now - (60*5))   # so in the past, not around now
		assert p2 in p1
		p3 = FixedPeriod_5Min(now + (60*30))  # so half an hour in the future
		assert p3 not in p1
		p4 = FixedPeriod_5Min(now - (60*60*25)) # over 1 day ago
		assert p4 not in p1

	def test_contains_floatperiod(self):
		"1-day floating period contains other floating period"
		p1 = FloatingPeriod_1Day()
		p2 = FloatingPeriod_5Min()
		assert p2 in p1
		assert p1 not in p2   # too big

	def test_eq_floatperiod(self):
		"1-day floating period equality"
		p1 = FloatingPeriod_1Day()
		assert p1 == FloatingPeriod_1Day()
		assert p1 != FloatingPeriod_5Min()
		assert p1 != FloatingPeriod_1Day(offset=30)
		assert p1 != FloatingPeriod_5Min(offset=60*60*24)

	def test_eq_fixperiod(self):
		"1-day floating period never equal to fixed period"
		# ...or rather it is, but only for an infinitely-small point time
		p1 = FloatingPeriod_1Day()
		assert p1 != FixedPeriod_1Day(HORSEYTIEM.time())


	def test_eq_wrong(self):
		"1-day floating period equals wrong things"
		p1 = FloatingPeriod_1Day(offset=12)
		assert p1 != None
		assert p1 != 'abcde'
		assert p1 != 589679356
		assert p1 != {}





from utils.time.period import FloatingPeriod_5Min, FixedPeriod_1Min, ANCHOR_HOUR_LHS
class TestFloatingPeriod_5Min(unittest.TestCase):

	def test_contains_ts(self):
		"5-min floating period contains timestamp"
		now = HORSEYTIEM.time()
		p1 = FloatingPeriod_5Min()
		assert now in p1
		assert now-5 in p1
		assert now + 1 not in p1
		assert now - (60*5) + 1 in p1
		assert now - (60*5) - 1 not in p1

	def test_contains_fixperiod(self):
		"5-min floating period contains tiny fixed period"
		now = HORSEYTIEM.time()
		p1 = FloatingPeriod_5Min()
		p2 = FixedPeriod_1Min(now - (60*2))   # so in the past, not around now
		assert p2 in p1
		p3 = FixedPeriod_1Min(now + (60*30))  # so half an hour in the future
		assert p3 not in p1
		p4 = FixedPeriod_1Min(now - (60*60*25)) # over 1 day ago
		assert p4 not in p1




