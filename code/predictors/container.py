#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A MixIn that supplies prediction tracking, success measurement and tree
management for the Predictor system.
'''



from collections import deque, defaultdict
from operator import itemgetter
import numpy as np

from utils.exceptions import InsufficientDataError


# We need division by zero errors to be raised
np.seterr(divide='raise')



class PredictionContainer(object):

	'''
	An object which contains predictions
	'''

	# N previous wrongness values will be kept for each child
	WRONGNESS_HIST						= 50
	
	# What prediction delay are we testing for?
	PREDICTION_WINDOW_SEC		= 60*30
	
	


	def __init__(self, level=0):
		super(PredictionContainer,self).__init__()
		
		# Children stored in a straightforward list
		self.children					= []
		
		# Initialize performance structures
		self.initWrongness()
		
		# Most containers do not have threading.  Axes do.
		self.threadpool_ex			= None
	
	
	def initWrongness(self):
		'''
		(re)initialize the datastructures holding performance data for our children
		'''
		# Dict of child -> deque() of wrongness hist.  This is a record of how the
		# predictor has performed over the last WRONGNESS_HIST prediction periods.
		self.wrongness_hist		= defaultdict(lambda: deque(maxlen=self.WRONGNESS_HIST))
		
		# Dict of child -> float wrongness rating.  None for each child until enough
		# hist exists to judge.
		self.wrongness_avg			= defaultdict(None)
		


	def predict(self, ts, horizon_ts=None):
		'''
		Return a prediction for timestamp `ts` using information from all our
		predictors, weighted by their success rate.
		'''
		
		valid_children	 	= [c for c in self.children if self.hist_full(c)]
		if not len(valid_children):
			raise InsufficientDataError("No children with complete history; can't predict")
		
		# Gather results, but only from good children
		def get_pred(c):
			try:
				return (c, c.predict(ts, horizon_ts) )
			except InsufficientDataError:
				return (c, None)
		
		# Multithread, but only on second level - i.e. first of an axis
		if self.threadpool_ex:
			preds	= list(self.threadpool_ex.map(get_pred, valid_children))
			# from concurrent.futures import ProcessPoolExecutor
			# with ProcessPoolExecutor(max_workers=4) as executor:
			# 	futures 	= [(c, executor.submit(c.predict, ts, horizon_ts)) for c in valid_children]
			# 	preds		= [(c, f.result()) if not f.exception() else (c,None) for f in futures]
		else:
			preds = list(map(get_pred, valid_children))
		
		try:
			pairs 			= [(pred, 1/self.wrongness_avg[c]) for c,pred in preds if pred is not None]
		except FloatingPointError:
			# One predictor has an average wrongness of 0.  It must be correct.  Find and
			# return its answer.
			for c, pred in preds:
				if self.wrongness_avg[c] == 0:
					return pred
		
		if not len(pairs):
			raise InsufficientDataError("No child returned a prediction")
		values, inv_nw		= zip(*pairs)
		
		# Average of all prediction values weighted by trustworthiness
		return np.average(values, weights=inv_nw)
	
	
	def judge(self, ts, true_value):
		'''
		Rate our predictors based on a prediction from PREDICTION_WINDOW_SEC in past.
		Update our internal wrongness history for each child.
		
		`ts`						- Time we are predicting for
		`true_value`		-	The real price at that time
		'''
		
		horizon_ts		= ts - self.PREDICTION_WINDOW_SEC

		def p2nw(pred):
			dist 	= abs(true_value - pred)
			norm		= dist / pred
			return norm
		
		def score(c):
			try:
				if self.last_node:
					normw = p2nw(c.predict(ts,horizon_ts))
				else:
					c.judge(ts, true_value)
					normw = c.winner()[1]
				return (c, normw)
			except InsufficientDataError:
				return (c,None)
		
		# Use mutleythreading at top level of an axis
		if self.threadpool_ex:
			scores = self.threadpool_ex.map(score, self.children)
		else:
			scores = map(score, self.children)

		for c, normw in scores:
			if normw is not None:
				self.wrongness_hist[c].append(normw)
		
		for c, hist in self.wrongness_hist.items():
			if len(hist) == self.WRONGNESS_HIST:
				self.wrongness_avg[c] = np.average(hist)
		
	
	def hist_full(self, c):
		'''
		Boolean: whether we have enough history to judge a child
		'''
		return len(self.wrongness_hist[c]) == self.WRONGNESS_HIST

	
	def hist_full_all(self):
		'''
		Boolean: whether every one of our children has a full historyset
		'''
		return all( map(self.hist_full, self.children) )
	
		
	def winner(self):
		'''
		Return the currently winning predictor as a pair of (predictor, score)
		'''
		candidates = self.wrongness_avg.items()		# pairs of (predictor, score)
		candidates = filter(lambda c: c[1] is not None, candidates)
		try:
			return min(candidates, key=itemgetter(1))
		except ValueError:
			raise InsufficientDataError("Not enough candidates to have a winner")


	def preroll(self, ts, true_value):
		'''
		Call judge() until all of our children have had enough iterations to measure
		their performance.  Even then they may not succeed, for example if they are
		broken.  Recurse into children so they do the same.
		'''
		if not self.last_node:
			for c in self.children:
				c.preroll(ts, true_value)
		
		for i in range(0, self.WRONGNESS_HIST):
			self.judge(ts, true_value)
	
	
