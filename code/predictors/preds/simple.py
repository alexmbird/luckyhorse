#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from predictors.preds._base import PredictorBase
from predictors.coefficient import FloatCoefficient, IntCoefficient, RangeCoefficient

from utils.exceptions import InsufficientDataError
import indicators.inds.simple as i_simple

from utils.time import HORSEYTIEM
from utils.time.period import *

from storage import RecordNotExistError

import numpy as np




class PredictorDummy(PredictorBase):
	'''
	Dummy predictor, used to test base class methods
	'''
	COEFFICIENTS		= {
		'cf1':		IntCoefficient(dmin=3, dmax=20),
		'cf2':		RangeCoefficient([1,2,3])
	}
	def _predict(self, ts, horizon_ts):
		return 100
	def __str__(self):
		fmt = "<%s - bound: %s>"
		return fmt % (
			self.__class__.__name__,
			{k:v for k,v in self._coefficients.items() if v is not None}
		)
		

class PredictorLinGradient(PredictorBase):
	
	COEFFICIENTS	 	= {
		'period_type': RangeCoefficient(values=[
			lambda ts: FixedPeriod_12Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_6Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_3Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_1Hour(ts, anchor=ANCHOR_10MIN_LHS),
			lambda ts: FixedPeriod_30Min(ts, anchor=ANCHOR_10MIN_LHS),
			FixedPeriod_15Min,
			# FixedPeriod_5Min,
			# FixedPeriod_1Min
		])
	}
	
	REQD_INDICATORS		= {
		'lintrend':     (i_simple.LinPriceTrend,),
	}
	
	def _predict(self, ts, horizon_ts):
		"Predict gradient at timestamp `ts`"
		p = self.period_type(horizon_ts)-1
		lintrend 	= self.indicators['lintrend']
		gradient, offset, stdev = lintrend.hist(p)
		timediff = ts - p.lhs_ts
		prediction = offset + (timediff*gradient)
		return prediction




class PredictorSmoothedLinGradient(PredictorBase):

	COEFFICIENTS	 	= {
		'period_type': RangeCoefficient(values=[
			lambda ts: FixedPeriod_12Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_6Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_3Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_1Hour(ts, anchor=ANCHOR_10MIN_LHS),
			lambda ts: FixedPeriod_30Min(ts, anchor=ANCHOR_10MIN_LHS),
			FixedPeriod_15Min,
			# FixedPeriod_5Min,
			# FixedPeriod_1Min
		])
	}

	REQD_INDICATORS		= {
		'smlingrad':     (i_simple.SmoothedLinPriceGradient_6,),
	}

	def _predict(self, ts, horizon_ts):
		"Predict at `ts` using gradient"
		p = self.period_type(horizon_ts)-1
		smlingrad 	= self.indicators['smlingrad']
		offset, gradient = smlingrad.hist(p)
		timediff = ts - p.lhs_ts
		prediction = offset + (timediff*gradient)
		return prediction




class PredictorWMeanGradient(PredictorBase):
	
	'''
	Compare the average weighted mean of the latest period to the second-latest.
	Use this to derive a value for the gradient and thence make predictions.
	'''
	COEFFICIENTS	 	= {
		'period_type': RangeCoefficient(values=[
			lambda ts: FixedPeriod_12Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_6Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_3Hour(ts, anchor=ANCHOR_HOUR_LHS),
			lambda ts: FixedPeriod_1Hour(ts, anchor=ANCHOR_10MIN_LHS),
			lambda ts: FixedPeriod_30Min(ts, anchor=ANCHOR_10MIN_LHS),
			FixedPeriod_15Min,
			# FixedPeriod_5Min,
			# FixedPeriod_1Min
		])
	}

	REQD_INDICATORS		= {
		'wmean_t':     (i_simple.WeightedAverageTrend,),
	}

	def _predict(self, ts, horizon_ts):
		"Predict gradient at timestamp `ts`"
		p 						= self.period_type(horizon_ts)-1
		wmean_t			= self.indicators['wmean_t']
		offset, gradient		= wmean_t.hist(p)
		timediff			= ts - p.lhs_ts
		prediction		= offset + (timediff*gradient)
		return prediction



class PredictorPatternTimePeriod(PredictorBase):

	'''
	Look for time-based repetition of market behaviour
	'''
	COEFFICIENTS	 	= {
		'period_sec': 	IntCoefficient(dmin=60*30+5,dmax=60*60*12),
		'delta':				FloatCoefficient(dmin=-100, dmax=+100)
	}
	
	def _predict(self, ts, horizon_ts):
		"Predict gradient at timestamp `ts`"
		check_ts = ts - self.period_sec
		if check_ts > horizon_ts:
			print("check_ts: %s   horizon_ts:%s" % (check_ts, horizon_ts) )
			raise RuntimeError("I won't look at the future")
		try:
			trade = self.storage.trades.fetchOne(self.datasource.EXCHANGE_ID, check_ts)
		except RecordNotExistError:
			raise InsufficientDataError()
		
		return float(trade.price) + self.delta

