#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from utils.time.period import PeriodBase, FixedPeriod_1Day
from operator import itemgetter, attrgetter
import numpy as np

from utils.hmath import weighted_avg_and_std, linearRegression, exponentialSmooth
from utils.exceptions import InsufficientDataError

from indicators.inds._base import IndicatorBase

from storage import RecordNotExistError



class DummyIndicator(IndicatorBase):
	INDICATOR_ID		= 0
	def _calculate(self, period):
		return (float(66.66),)



class MinTradePrice(IndicatorBase):
	INDICATOR_ID		= 10
	def _calculate(self, period):
		data = self.loadTradesForPeriod(period)
		try:
			return (min(map(attrgetter('price'), data)),)
		except ValueError:
			raise InsufficientDataError("Empty period")


class MaxTradePrice(IndicatorBase):
	INDICATOR_ID		= 11
	def _calculate(self, period):
		data = self.loadTradesForPeriod(period)
		try:
			return (max(map(attrgetter('price'), data)),)
		except ValueError:
			raise InsufficientDataError("Empty period")


class OpenTradePrice_1Day(IndicatorBase):
	INDICATOR_ID		= 20
	PERIOD_TYPE		= FixedPeriod_1Day
	def _calculate(self, period):
		data = list(self.loadTradesForPeriod(period))
		if len(data) == 0:
			raise InsufficientDataError()
		else:
			return (data[0].price,)
			

class CloseTradePrice_1Day(IndicatorBase):
	INDICATOR_ID		= 21
	PERIOD_TYPE		= FixedPeriod_1Day
	def _calculate(self, period):
		data = list(self.loadTradesForPeriod(period))
		if len(data) == 0:
			raise InsufficientDataError()
		else:
			return (data[-1].price,)


class WeightedAvgPrice(IndicatorBase):
	INDICATOR_ID				= 31
	INDICATOR_FIELDS		= 1
	PERIOD_TYPE				= PeriodBase
	def _calculate(self, period):
		data = list(self.loadTradesForPeriod(period))
		if len(data) == 0:
			raise InsufficientDataError()
		values 		= np.fromiter(map(attrgetter('price'), data), np.float, len(data))
		weights		= np.fromiter(map(attrgetter('volume'), data), np.float, len(data))
		mean, std = weighted_avg_and_std(values, weights)
		return (mean,)


class WeightedAverageTrend(IndicatorBase):
	INDICATOR_ID				= 32
	INDICATOR_FIELDS		= 2
	PERIOD_TYPE				= PeriodBase
	REQD_INDICATORS		= {
		'wmean':			(WeightedAvgPrice,),
	}
	def _calculate(self, period):
		ind_wmean		= self.indicators['wmean']
		mean0 				= ind_wmean.hist(period)[0]
		mean1				= ind_wmean.hist(period-1)[0]
		gradient			= (mean0 / mean1) / period.PERIOD_SEC
		try:
			lhs_trade		= next( self.loadTradesForPeriod(period) )
		except StopIteration:
			raise InsufficientDataError()
		offset				= lhs_trade.price
		return (offset, gradient)

	
class LinPriceTrend(IndicatorBase):
	'''
	Return a tuple of (gradient, offset, stdev) of price points in the period.
	'''
	INDICATOR_ID				= 41
	INDICATOR_FIELDS		= 3
	PERIOD_TYPE				= PeriodBase
	def _calculate(self, period):
		it_data = map(lambda d: (d.ts_exec, d.price), self.loadTradesForPeriod(period))
		data = list(it_data)
		if not len(data):
			raise InsufficientDataError()

		gradient, offset = linearRegression(data)
		
		# Subtract from each datapoint the predicted y-value.  Use these to make std
		# deviation.
		init_time	= data[0][0]
		deltas			= [float(p) - ((ts-init_time)*gradient) - offset for ts, p in data]
		stdev = np.std(deltas)
		return (gradient, offset, stdev)


class SmoothedLinPriceGradient_Base(IndicatorBase):
	'''
	Exponential smoothing of N blocks of linear price gradient with period.
	'''
	INDICATOR_ID			= None
	PERIOD_TYPE			= PeriodBase
	REQD_INDICATORS	= {
		'lpg':			(LinPriceTrend,),
	}
	N_BLOCKS					= None
	def _calculate(self, period):
		try:
			pairs 		= [self.indicators['lpg'].hist(period-n) for n in range(0,self.N_BLOCKS)]
			blocks  	= list(map(itemgetter(0), pairs))
			trades		= self.loadTradesForPeriod(period)
		except RecordNotExistError:
			raise InsufficientDataError()
		try:
			offset = next(trades).price
		except StopIteration:
			raise InsufficientDataError()
		return (offset, exponentialSmooth(blocks),)


class SmoothedLinPriceGradient_14(SmoothedLinPriceGradient_Base):
	"Exponential smoothing of 14 blocks of linear price gradient with period"
	INDICATOR_ID			= 81
	N_BLOCKS					= 14

class SmoothedLinPriceGradient_6(SmoothedLinPriceGradient_Base):
	"Exponential smoothing of 6 blocks of linear price gradient with period"
	INDICATOR_ID			= 86
	N_BLOCKS					= 6
