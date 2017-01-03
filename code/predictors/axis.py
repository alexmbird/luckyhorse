#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque, defaultdict, namedtuple
import random
from operator import itemgetter
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from predictors.container import PredictionContainer

from predictors.coefficient import BaseCoefficient
from predictors.preds._base import PredictorBase

from utils.time import HORSEYTIEM
from utils.exceptions import InsufficientDataError

from predictors.factory import PredictorFactory






class Axis(PredictionContainer):
	
	'''
	Manage a coefficient by maintaining multiple versions of a predictor using
	different values.  Mutate those values to converge on the a good value. 
	Coefficients can never truly converge: the market's behaviour changes over time
	so we must mutate constantly in case a new, more appropriate value emerges.
	'''
	
	# Use N parallel threads from top-level of an axis to do prediction & judging
	NUM_THREADS			= 4
	
	
	def __init__(self, pfakt, klass, coefficients=None, target_coef=None, level=0):
		'''
		Setup a new axis.
		
		`klass`				- The Predictor class to work with.
		`pfakt`				- PredictorFactory to create Predictors with appropriate sources
		`coefficients`	- dict of coefs bound so far.  We will add `mutate` to this for
										our children.  
		`target_coef`	- Name of the coefficient we will mutate.  If not supplied a
										random one will be selected.
		'''
		super(Axis,self).__init__()
		
		if not isinstance(pfakt, PredictorFactory):
			raise TypeError("pfakt needs to be an PredictorFactory, not %s" % type(pfakt))
		self.pfakt					= pfakt
		
		if not issubclass(klass, PredictorBase):
			raise TypeError("klass must descend from PredictorBase, not %s" % type(klass))
		if coefficients is not None:
			if set(coefficients.keys()) != set(klass.COEFFICIENTS.keys()):
				raise ValueError("Supplied coefficients don't match Predictor")
			self.coefficients = coefficients
			if len(self._unbound()) == 0:
				raise ValueError("All coefficients bound; nothing left to mutate")
		else:
			self.coefficients	= dict.fromkeys(klass.COEFFICIENTS.keys(), None)
			
		# Starting? pick a random coefficient to mutate.  If none are left to mutate
		# use 'None' to signal we'll create real Predictors as our children.
		if target_coef is None:
			self.target_coef = random.choice(self._unbound())
		else:
			self.target_coef = target_coef
		
		if self.coefficients[self.target_coef] is not None:
			raise ValueError("%s already bound, cannot mutate" % mutate)
		
		# Top-level Axes may use threading to parallelize
		# predictions & judgement.
		self.level 					= level
		if self.level == 0:
			self.threadpool_ex		= ThreadPoolExecutor(self.NUM_THREADS)

		self.klass					= klass
		self.target_desc		= klass.COEFFICIENTS[self.target_coef]
		
		# Will our children be real Prediction* objects?
		self.last_node			= len(self._unbound()) == 1
		
		# Store the present value of our mutable coefficient assigned to each child
		self.coef_values 	= {}
		
		# Populate ourself with children based on sensible values
		for value in self.target_desc.seed():
			ch = self._instantiate(value)
			self.children.append(ch)
			self.coef_values[ch] = value

	
	def __str__(self):
		fmt = "<%s mutating '%s', statics: %s>"
		statics = filter(itemgetter(1), self.coefficients.items())
		return fmt % (
			self.__class__.__name__,
			self.target_coef,
			', '.join(["%s:%s" % (k,v) for k,v in statics]) if statics else 'none'
		)
	
	
	def dump(self, indent=0, last=True):
		'''
		Pretty-print a tree of containers and predictors
		'''
		for c in self.children:
			fmt 		= "%s avnw:%s value:%s"
			wavg 	= ('%.3f'%self.wrongness_avg[c]) if c in self.wrongness_avg else '-'
			print(		(' '*indent) + fmt % (c, wavg, self.coef_values[c]) )
			if isinstance(c, PredictionContainer):
				c.dump(indent+2, last=False)
		if last:
			print()
		

	def _instantiate(self, value):
		'''
		Instantiate a child node.  This will be either:
		1) If no more coefficients are left to bind, a real Predictor obj OR
		2) An Axis() object 
		'''
		my_coefficients 								= self.coefficients.copy()
		my_coefficients[self.target_coef] 	= value
		if self.last_node:
			return self.pfakt.create(self.klass, my_coefficients)
		else:
			next_mutate = sorted(self._unbound(my_coefficients))[0]
			return Axis(
				self.pfakt, self.klass,
				my_coefficients, next_mutate,
				level=self.level+1
			)
	
		
	def _unbound(self, c=None):
		'''
		Return a list of coefficients yet to be bound
		'''
		if c is None:
			c = self.coefficients
		return [k for k, v in c.items() if v is None]


	def _bound(self, c=None):
		'''
		Return a dict of coefficients that are already bound
		'''
		if c is None:
			c = self.coefficients
		return {k:v for k,v in c.items() if v is not None}
	
	
	def _mutantval(self, child):
		'''
		Get a child's 
		'''
	
	
	def mutate(self, coefficients=None):
		'''
		Mutate our mutable value by:
		1) Replacing the weakest performer with a new value halfway between the best
		2) Replacing the next two weakest performer's mutable values with XXX
		
		New coefficients are passed into children as a dict with the `coefficients`
		parameter.
		'''
		# Dict to convey changes to our children
		if coefficients is None:
			coefficients = {}
		
		def mutatechild(ch, coefs, new_val=None):
			coefs = coefs.copy()
			if new_val is not None:
				coefs[self.target_coef] = new_val
				del self.coef_values[ch]
				self.coef_values[ch] = new_val
			self.wrongness_avg.pop(ch,None)
			self.wrongness_hist.pop(ch,None)
			ch.mutate(coefs)
		
		# Only mutate our children if:
		#   1) We are mutating on a mutable coef type - not all are
		#   2) all have history to be judged by
		if self.target_desc.IS_MUTABLE:
			if len(self.wrongness_avg) == len(self.children):
				# triplets of (child, value, avg normalized wrongness)
				cands = [(c,self.wrongness_avg[c]) for c in self.children]
				cands.sort(key=itemgetter(1))
				
				# Create a child between the two best scorers
				v0		= self.coef_values[cands[0][0]]
				v1		= self.coef_values[cands[1][0]]
				new_val = v1 + ((v0-v1)/2) if v0 > v1 else v0 + ((v1-v0)/2)
				mutatechild(cands.pop()[0], coefficients, new_val)
				# print("mutate() - finding point between v0:%s and v1:%s" % (v0,v1))
				
				# Replace two worst performing with random values
				for i in range(0,2):
					mutatechild(cands.pop()[0], coefficients, self.target_desc.random())
		
		# Finally - if other values have changed, relay them to the children
		if len(coefficients):
			for c in self.children:
				mutatechild(c, coefficients)

	
	
