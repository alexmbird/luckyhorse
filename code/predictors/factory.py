#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from datasource.signals.base import DataSourceBase
from indicators.factory import IndicatorFactory
from storage import StorageEngine



class PredictorFactory(object):
	
	'''
	Generate Predictors.
	'''
	
	def __init__(self, ifakt, pred_targ_ds, storage):
		'''
		`ifakt`						-	Indicator factory.
		`pred_target_ds`		-	Datasource for which we are predicting the future.  This
												will be supplied as a default datasource to any indicators.
		'''
		if not isinstance(pred_targ_ds, DataSourceBase):
			raise TypeError("pred_targ_ds must derive from DataSourceBase")
		self.pred_targ_ds			= pred_targ_ds
		
		if not isinstance(ifakt, IndicatorFactory):
			raise TypeError("ifakt needs to be an IndicatorFactory")
		self.ifakt							= ifakt
		
		if not isinstance(storage, StorageEngine):
			raise TypeError("storage needs to be a StorageEngine")
		self.storage						= storage
		
	
	def create(self, klass, coefficients):
		'''
		Create a predictor based on the given coefficients
		'''
		indicators = self.ifakt.createFromReqd(
			klass, default_src=self.pred_targ_ds
		)
		return klass(indicators, coefficients, self.storage, self.pred_targ_ds)

	