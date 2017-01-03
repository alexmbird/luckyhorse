#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from indicators.factory import RequiredIndicatorsMixIn

from predictors.coefficient import BaseCoefficient

from utils.time import HORSEYTIEM



class PredictorBase(RequiredIndicatorsMixIn):
	
	REQD_INDICATORS 	= 	{
	}
	COEFFICIENTS			=	{
	}
	
	def __init__(self, indicators, coefficients, storage, datasource):
		'''
		Setup a new predictor.  `coefficients` is a dict of items which will replace
		the class variables which defined them.
		'''
		super(PredictorBase,self).__init__()
		if set(coefficients.keys()) != set(self.COEFFICIENTS.keys()):
			raise ValueError("Supplied coefficient names don't match this class's requirements")
		self.__dict__['_coefficients'] 	= coefficients
		self.__dict__['indicators']			= indicators
		self.__dict__['storage']					= storage
		self.__dict__['datasource']			= datasource

	
	def mutate(self, coefficients):
		'''
		Assign new coefficients to this predictor
		'''
		self.__dict__['_coefficients'].update(coefficients)

	
	def __getattr__(self, name):
		'''
		Make coefficients appear as object variables
		'''
		try:
			return self._coefficients[name]
		except KeyError:
			coefs = ', '.join(self._coefficients.keys())
			raise AttributeError("Missing coefficient '%s'.  Options are: %s" % (name, coefs))
	
	
	def __setattr__(self, name, value):
		'''
		Prevent overwriting coefficients
		'''
		print("In setattr")
		if name in self._coefficients:
			raise AttributeError("Coefficients are read-only")
		else:
			self.__dict__[name] = value
	
	
	def predict(self, ts, horizon_ts=None, level=0):
		'''
		Set an appropriate horizon_ts and call the individual predictor's _predict()
		method.
		
		`ts`						- Timestamp prediction is for
		`horizon_ts` 	-	Base prediction on data before this point.  Used for measuring
										past performance against current data.
		`level`				- 	Number of mutations deep we are.  Not used, only present to make
										recursion easy.
		
		Return a tuple of (ts, predicted_price).
		'''
		if horizon_ts is None:
			horizon_ts = HORSEYTIEM.time()
		return self._predict(ts, horizon_ts)

	
	def _predict(self, ts, horizon_ts):
		'''
		Make the actual prediction for this predictor.  Override.
		'''
		raise NotImplementedError()
	