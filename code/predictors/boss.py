#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from operator import itemgetter

from predictors.container import PredictionContainer
from predictors.axis import Axis

from datasource.signals.base import DataSourceBase

from indicators.factory import IndicatorFactory
from predictors.factory import PredictorFactory

from events import Trade

from utils.time import HORSEYTIEM

import random



class PredictionBoss(PredictionContainer):
	
	'''
	Manage a tree of Axes and Predictor* objects.
	'''
	
	def __init__(self, pred_targ_ds, predictors, ifakt, storage):
		'''
		`pred_targ_ds`		-	The datasource we are prediting for
		`predictors`			- List of the predictor classes we are testing
		`ifakt`					-	Factory for Indicators
		`storage`				- StorageEngine
		'''
		super(PredictionBoss,self).__init__()
		
		if not isinstance(pred_targ_ds, DataSourceBase):
			raise TypeError("pred_targ_ds needs to be a DataSourceBase, not %s" % type(DataSourceBase))
		
		if not isinstance(ifakt, IndicatorFactory):
			raise TypeError("ifakt needs to be an IndicatorFactory")
		
		if not isinstance(predictors,list):
			raise TypeError("predictors needs to be a list, not %s" % type(predictors))
		
		
		# Create the PredictorFactory we'll use to make all the predictors
		pfakt						= PredictorFactory(ifakt, pred_targ_ds, storage)
		
		# Create the massive Axis trees
		self.children 		= [Axis(pfakt, p) for p in predictors]
		
		# We are definitely not the last node in the tree.
		self.last_node		= False
		
		# Every new event will trigger a groom()
		def groom(e):
			if isinstance(e, Trade):
				if False or random.randint(0,10) == 5:
					self.judge(e.ts_exec, float(e.price))
					# for c in self.children:
					# 	c.judge(e.ts_exec, float(e.price))
		pred_targ_ds.channel.subscribe(groom, 500)
	
		# Every 60s, attempt to mutate our prediction tree
		def mutate_task():
			if self.hist_full_all():
				for c in self.children:
					c.mutate()
			HORSEYTIEM.setTimer(mutate_task, -60, priority=0)
		
		mutate_task()
	
	
	def forceMutate(self):
		'''
		Force a mutation right now
		'''
		for c in self.children:
			#print("Mutating child %s" % c)
			c.mutate()
	
	
	def dump(self):
		for c in self.children:
			print("%s (avg norm wrong %s)" % (
				c,
				"%.4f"%self.wrongness_avg[c] if c in self.wrongness_avg else '-'
			))
			c.dump(indent=2)
	
	
	def leastWrong(self):
		'''
		Return the best normalized-wrongness score we presently have.  This is a
		metric for the best accuracy attained recently.
		
		Returns a pair of (Predictor* class, normwrong)
		'''
		pairs  = list(self.wrongness_avg.items())
		pairs.sort(key=itemgetter(1))
		axis, nwrong = pairs[0]
		return (axis.klass, nwrong)

	
