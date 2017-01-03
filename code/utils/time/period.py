#!/usr/bin/env python3
# -*- coding: utf-8 -*-





#
# Time Period classes.  These represent a fixed window of time.  They may not be
# super-efficient but they have eliminated the chaos in indicator storage.
#

import time, calendar
from utils.time.tools import timestamp_to_printable as ts2p
from utils.time import HORSEYTIEM

from numbers import Number



class TemporalError(Exception):
	"Some kind of problem with time"


# Constants for specifying the anchorage of new periods
ANCHOR_HOUR_LHS			= 98
ANCHOR_10MIN_LHS			= 97
#ANCHOR_HOUR_RHS			= 99



class PeriodBase(object):
	pass


class FixedPeriodBase(PeriodBase):

	'''
	Represent a fixed time period.  Epoch timestamps of its bounds are stored in
	member variables `lhs_ts` and `rhs_ts`.
	'''

	PERIOD_SEC = None

	def __init__(self, around_ts, anchor=None):
		'''
		Create a fixed time period around `around_ts`.  The left and right boundaries
		default to values that divide easily into 24h. 
		
		`anchor`	- change the boundary behaviour.  ANCHOR_LHS places the LHS as close
							to `around_ts` as possible.  ANCHOR_RHS does the same for the RHS.
		'''
		super(FixedPeriodBase,self).__init__()
		self.anchor	= anchor
		self.lhs_ts, self.rhs_ts = self.boundTimestamps(around_ts, anchor)

	def __str__(self):
		format = "<%s from %s>"
		return format % (
			self.__class__.__name__,
			ts2p(self.lhs_ts)
		)

	def __contains__(self, other):
		"Does timestamp `ts` fall within this period?"
		if isinstance(other, FixedPeriodBase):
			if self.lhs_ts <= other.lhs_ts < self.rhs_ts \
					and self.lhs_ts <= other.rhs_ts < self.rhs_ts:
				return True
		elif isinstance(other, Number):
			return self.lhs_ts <= other < self.rhs_ts
		else:
			raise TypeError("Can only compare other *Period types")

	def __add__(self, n):
		"Return a period `n` later than this one.  Preserves original anchor setting."
		return self.offset(n)

	def __sub__(self, n):
		"Return a period `n` before than this one.  Preserves original anchor setting."
		return self.offset(-n)

	def __eq__(self, other):
		return (
			(self.__class__ == other.__class__) and
			(self.PERIOD_SEC == other.PERIOD_SEC) and
			(self.lhs_ts == other.lhs_ts)
		)

	def __hash__(self):
		"Make periods hashable"
		# Make tuple of enough data to be unique and hash that
		t = (self.__class__, self.lhs_ts)
		return hash(t)

	@classmethod
	def boundTimestamps(cls):
		raise NotImplementedError()

	def offset(self, n):
		'''
		Return a new Period of the same type but offset by `n` periods.

		`n` - a positive or negative integer

		p.offset(0) == p
		'''
		if n != int(n):
			raise ValueError("Only integer offsets are supported")
		return self.__class__(self.lhs_ts + (n*self.PERIOD_SEC), anchor=self.anchor)


class FixedPeriod_1Week(FixedPeriodBase):
	'''
	Period precisely 1 UTC week long.  Default boundaries anchored to midnight.
	'''
	PERIOD_SEC      = 60*60*24*7
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  = time.gmtime(ref_ts)
		if anchor is ANCHOR_HOUR_LHS:
			ts_min 	= calendar.timegm(struct[0:4] + (0,0))
		elif anchor is None:
			ts_min  = calendar.timegm(struct[0:3] + (0,0,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_1Day(FixedPeriodBase):
	'''
	Period precisely 1 UTC day long.  Default boundaries anchored to midnight.
	'''
	PERIOD_SEC      = 60*60*24
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  = time.gmtime(ref_ts)
		if anchor is ANCHOR_HOUR_LHS:
			ts_min 	= calendar.timegm(struct[0:4] + (0,0))
		elif anchor is None:
			ts_min  = calendar.timegm(struct[0:3] + (0,0,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_12Hour(FixedPeriodBase):
	'''
	Period precisely 1/2 UTC day long with bounds at 0h or 12h.  Default boundaries
	anchored to 00:00 or 12:00.
	'''
	PERIOD_SEC      = 60*60*12
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  = time.gmtime(ref_ts)
		if anchor is ANCHOR_HOUR_LHS:
			ts_min		= calendar.timegm(struct[0:4] + (0,0))
		elif anchor is None:
			hour			= (struct[3] // 12) * 12
			ts_min  = calendar.timegm(struct[0:3] + (hour,0,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_6Hour(FixedPeriodBase):
	'''
	Period precisely 6 UTC hours long.  Default boundaries anchored at 0, 6, 12
	or 18h.
	'''
	PERIOD_SEC      = 60*60*6
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  = time.gmtime(ref_ts)
		if anchor is ANCHOR_HOUR_LHS:
			ts_min		= calendar.timegm(struct[0:4] + (0,0))
		elif anchor is None:
			hour			= (struct[3] // 6) * 6
			ts_min  = calendar.timegm(struct[0:3] + (hour,0,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_3Hour(FixedPeriodBase):
	'''
	Period precisely 3 UTC hours long.  Default boundaries anchored at 0, 3, 6, 9,
	12, 15, 18 or 21h.
	'''
	PERIOD_SEC      = 60*60*3
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  = time.gmtime(ref_ts)
		if anchor is ANCHOR_HOUR_LHS:
			ts_min		= calendar.timegm(struct[0:4] + (0,0))
		elif anchor is None:
			hour			= (struct[3] // 3) * 3
			ts_min  = calendar.timegm(struct[0:3] + (hour,0,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_1Hour(FixedPeriodBase):
	'''
	Period precisely 1 hour long.  Default boundaries anchored at 0 minutes past
	the hour.
	'''
	PERIOD_SEC      = 60*60
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  = time.gmtime(ref_ts)
		if anchor in (None, ANCHOR_HOUR_LHS):
			ts_min  = calendar.timegm(struct[0:4] + (0,0) )
		elif anchor is ANCHOR_10MIN_LHS:
			minutes 		= 10 * (struct[4] // 10)
			ts_min			= calendar.timegm(struct[0:4] + (minutes,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_30Min(FixedPeriodBase):
	'''
	Period precisely 30 minutes long.  Default boundaries anchored at 0, 15, 30, 45
	minutes past the hour.
	'''
	PERIOD_SEC      = 60*30
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  			= time.gmtime(ref_ts)
		if anchor is None:
			minutes 		= 30 * (struct[4] // 30)
			ts_min  		= calendar.timegm(struct[0:4] + (minutes,0) )
		elif anchor is ANCHOR_10MIN_LHS:
			minutes 		= 10 * (struct[4] // 10)
			ts_min  		= calendar.timegm(struct[0:4] + (minutes,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_15Min(FixedPeriodBase):
	'''
	Period precisely 15 minutes long.  Default boundaries anchored at 0, 15, 30, 45
	minutes past the hour.
	'''
	PERIOD_SEC      = 60*15
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  			= time.gmtime(ref_ts)
		if anchor is None:
			minutes 		= 15 * (struct[4] // 15)
			ts_min  		= calendar.timegm(struct[0:4] + (minutes,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_5Min(FixedPeriodBase):
	'''
	Period precisely 5 minutes long.  Default boundaries anchored at multiples of 5
	minutes past the hours.  05m, 10m, 15m etc.
	'''
	PERIOD_SEC      = 60*5
	@classmethod
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  			= time.gmtime(ref_ts)
		if anchor is None:
			minutes 		= 5 * (struct[4] // 5)
			ts_min  		= calendar.timegm(struct[0:4] + (minutes,0) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)


class FixedPeriod_1Min(FixedPeriodBase):
	'''
	Period precisely 1 minute long with default boundaries on 0 seconds past the
	minute.
	'''
	PERIOD_SEC				= 60
	def boundTimestamps(cls, ref_ts, anchor=None):
		struct  	= time.gmtime(ref_ts)
		if anchor is None:
			ts_min  = calendar.timegm(struct[0:5] + (0,) )
		else:
			raise ValueError("Unsupported anchor")
		ts_max  = ts_min + cls.PERIOD_SEC
		assert ts_min <= ref_ts < ts_max
		return (ts_min, ts_max)






class FloatingPeriodBase(PeriodBase):
	
	'''
	Base of all floating periods.  In this kind of period the RHS is fixed relative
	to now (which generally comes from the shared HORSEYTIEM object) and the LHS
	trails 	it by precisely PERIOD_SEC.
	'''
	
	PERIOD_SEC			= None
	
	def __init__(self, offset=0):
		'''
		Make a new floating period.
		
		`offset`		- RHS of the period will always be `offset` sec behind now
		'''
		super(FloatingPeriodBase,self).__init__()
		self.offset			= offset
	
	def __str__(self):
		format = "<%s offset=%d sec currently %s - %s>"
		return format % (
			self.__class__.__name__,
			self.PERIOD_SEC,
			ts2p(self.lhs_ts), ts2p(self.rhs_ts)
		)

	def __contains__(self, p):
		my_lhs 	= 0 - self.offset - self.PERIOD_SEC
		my_rhs		= 0 - self.offset
		if isinstance(p, FixedPeriodBase):
			return self.lhs_ts <= p.lhs_ts <= self.rhs_ts and \
						 self.lhs_ts <= p.rhs_ts <= self.rhs_ts
		elif isinstance(p, FloatingPeriodBase):
			ot_lhs 	= 0 - p.offset - p.PERIOD_SEC
			ot_rhs 	= 0 - p.offset
			return my_lhs <= ot_lhs <= my_rhs and \
						 my_lhs <= ot_rhs <= my_rhs
		elif isinstance(p, Number):
			return self.lhs_ts <= p < self.rhs_ts
		else:
			raise TypeError("Can only compare other *Period types")

	def __add__(self, n):
		"New floating window shifted `n` periods right"
		offset = self.offset - (n*self.PERIOD_SEC)
		if offset < 0:
			raise ValueError("Can't have a floating window in the future")
		return self.__class__(offset)
	
	def __sub__(self, n):
		"New floating window shifted `n` periods left"
		offset = self.offset + (n*self.PERIOD_SEC)
		if offset < 0:
			raise ValueError("Can't have a floating window in the future")
		return self.__class__(offset)
	
	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.offset == other.offset
		return False
	
	def __hash__(self):
		t = (self.__class__, self.offset)
		return hash(t)
	
	def getLhsTs(self):
		return self.rhs_ts - self.PERIOD_SEC
	
	lhs_ts = property(lambda s: s.getLhsTs(), None, None, None)
	rhs_ts = property(lambda s: HORSEYTIEM.time() - s.offset, None, None, None)
	

class FloatingPeriod_1Day(FloatingPeriodBase):
	PERIOD_SEC			= 60*60*24

class FloatingPeriod_6Hour(FloatingPeriodBase):
	PERIOD_SEC			= 60*60*6

class FloatingPeriod_3Hour(FloatingPeriodBase):
	PERIOD_SEC			= 60*60*3

class FloatingPeriod_1Hour(FloatingPeriodBase):
	PERIOD_SEC			= 60*60

class FloatingPeriod_30Min(FloatingPeriodBase):
	PERIOD_SEC			= 60*30

class FloatingPeriod_15Min(FloatingPeriodBase):
	PERIOD_SEC			= 60*15

class FloatingPeriod_10Min(FloatingPeriodBase):
	PERIOD_SEC			= 60*10

class FloatingPeriod_5Min(FloatingPeriodBase):
	PERIOD_SEC			= 60*5






class ArbitraryPeriod(PeriodBase):
	
	PERIOD_SEC			= None
	
	def __init__(self, lhs_ts, rhs_ts):
		self.lhs_ts		= lhs_ts
		self.rhs_ts		= rhs_ts
	
	