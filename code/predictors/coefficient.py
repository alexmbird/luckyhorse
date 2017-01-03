#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import random




class BaseCoefficient(object):
	
	# Not all are mutable - for example small ranges where all values can be
	# represented at the same time.
	IS_MUTABLE			= True
	
	
	def random(self):
		"Return a random value from our potential range"
		raise NotImplementedError()

	def seed(self):
		'''
		Return a list of initial values to try
		'''
		raise NotImplementedError()




class RangeCoefficient(BaseCoefficient):

	'''
	Represent a range of absolute values.  All of these will exist at once.  They
	may not necessarily be numbers, any object will do.
	'''

	# Range coefficients are not mutable; every value in the range is always
	# represented.
	IS_MUTABLE		= False

	def __init__(self, values):
		super(RangeCoefficient,self).__init__()
		self.values = values

	def random(self):
		return random.choice(self.values)
	
	def seed(self):
		return list(self.values)
	




class BaseNumericCoefficient(BaseCoefficient):
	
	N_SLOTS			= 6
	
	def __init__(self, dmin, dmax):
		'''
		Declare a coefficient.  When a predictor is created all member coefficients
		will be replaced with actual variables to be tested.
		'''
		super(BaseNumericCoefficient,self).__init__()
		self.dmin 			= dmin
		self.dmax 			= dmax
	


class FloatCoefficient(BaseNumericCoefficient):

	def random(self):
		return random.uniform(self.dmin, self.dmax)

	def seed(self):
		v = (self.dmax-self.dmin) / (self.N_SLOTS-1)
		return [self.dmin+i*v for i in range(0, self.N_SLOTS)]
		

class IntCoefficient(BaseNumericCoefficient):
	
	def random(self):
		return random.randint(self.dmin, self.dmax)

	def seed(self):
		v = (self.dmax-self.dmin) / (self.N_SLOTS-1)
		return [int(self.dmin+i*v) for i in range(0, self.N_SLOTS)]

