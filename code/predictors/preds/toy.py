#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from predictors.preds._base import PredictorBase
from predictors.coefficient import IntCoefficient, FloatCoefficient
from indicators.inds.simple import DummyIndicator

import random



class ToyPredictor(PredictorBase):
	'''
	Simple toy predictor requiring an indicator; used in testing
	'''
	REQD_INDICATORS		= {
		'dummy':		(DummyIndicator,),
	}
	COEFFICIENTS				=	{
		'n_to_return':		IntCoefficient(dmin=50, dmax=150)
	}
	def _predict(self, ts, horizon_ts):
		return self.n_to_return




class ToyPredictor2(PredictorBase):
	'''
	Simple toy predictor with two coefficients; used in testing
	'''
	COEFFICIENTS				=	{
		'cf1':		IntCoefficient(dmin=50, dmax=150),
		'cf2':		FloatCoefficient(dmin=0.1, dmax=100)
	}
	def _predict(self, ts, horizon_ts):
		return self.cf1 * self.cf2

