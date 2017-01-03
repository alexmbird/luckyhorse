#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from utils.time.period import PeriodBase, FixedPeriodBase, FloatingPeriodBase
from storage import RecordNotExistError
from utils.data import LRUCache

from indicators.factory import RequiredIndicatorsMixIn




class IndicatorBase(RequiredIndicatorsMixIn):
	
	'''
	Standard base for all indicators.
	
	calculate(p) 	- Returns value for period p (but does not save it).  Valid for
	                fixed or floating periods.
	hist(p)				- Returns value for a period, caching in the DB for future use.
	
	Indicators value(s) for a given time period.  Values are returned from the
	indicator's _calculate(p) function as a tuple.  If the period was some kind of
	FixedPeriod (so deterministic and replicable) the values are cached by our
	storage engine.
	'''
	
	INDICATOR_ID				= None
	PERIOD_TYPE				= PeriodBase
	INDICATOR_FIELDS		= None			# If set, used to sanity-check data loaded from db
	REQD_INDICATORS		= {}
	
	def __init__(self, storage, dsrc, indicators):
		self.storage				= storage
		self.datasource		= dsrc
		self.indicators		= indicators
		self.cache					= LRUCache(256)
	
	
	def hist(self, period):
		'''
		Get the values of this indicator for `period`.  Returns a tuple of floats.
		'''
		if not isinstance(period, PeriodBase):
			raise TypeError("Period must be specified as a %s" % self.PERIOD_TYPE)
		
		exch_id = self.datasource.EXCHANGE_ID
		
		# Attempt to return from our own LRU cache
		try:
			return self.cache[period]
		except KeyError:
			pass
		
		if isinstance(period, FixedPeriodBase):
			try:
				values = self.storage.indicators.load(exch_id, self.INDICATOR_ID, period)
				if self.INDICATOR_FIELDS is not None:
					if len(values) != self.INDICATOR_FIELDS:
						raise RuntimeError("Corrupt DB data?  %s (%d) has value %s" % (
							self.__class__.__name__, self.INDICATOR_ID, values
						))
				self.cache[period] = values
				return values
			except RecordNotExistError:
				pass
		
		# Do the calculation we've been trying to avoid
		values = self.calculate(period)
		
		# Only FixedPeriods are storable; floating ones can never match a request
		if isinstance(period, FixedPeriodBase):
			self.cache[period] = values
			self.storage.indicators.store(exch_id, self.INDICATOR_ID, period, values)
		
		return values
	
	
	def calculate(self, period):
		'''
		Determine the value of this indicator for timespan `period`.
		'''
		if not isinstance(period, self.PERIOD_TYPE):
			raise TypeError("Period must be specified as a %s" % self.PERIOD_TYPE)
		values = self._calculate(period)
		if not isinstance(values, tuple):
			raise ValueError("_calculate returned something other than a tuple")
		if self.INDICATOR_FIELDS is not None and len(values) != self.INDICATOR_FIELDS:
			raise RuntimeError("Malformed indicator result:  %s (%d) has value %s" % (
				self.__class__.__name__, self.INDICATOR_ID, values
			))
		
		# Ensure we are certainly dealing in floats
		return tuple(map(float,values))
	
	
	def _calculate(self, period):
		'''
		Actual calculation takes place here.  Override when implementing.  Must return
		a tuple of floats.
		'''
		raise NotImplementedError()
	
	
	def loadTradesForPeriod(self, period):
		'''
		Return an iterator to all the trades within window `period`.
		'''
		if isinstance(period, FixedPeriodBase):
			return self.storage.trades.fetch(self.datasource.EXCHANGE_ID, period)
		elif isinstance(period, FloatingPeriodBase):
			# Return from local cache?
			return self.storage.trades.fetch(self.datasource.EXCHANGE_ID, period)
			raise NotImplementedError("Build the trade cache")
		else:
			raise TypeError("Period must be specified as a %s" % self.PERIOD_TYPE)
	
	
	def loadOrdersForPeriod(self, period):
		if not isinstance(period, self.PERIOD_TYPE):
			raise TypeError("Period must be specified as a %s" % self.PERIOD_TYPE)
		raise NotImplementedError()
	
