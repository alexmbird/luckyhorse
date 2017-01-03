#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class BaseStrategy(object):
	
	'''
	Base trading strategy
	'''
	
	def __init__(self, exchanges):
		super(BaseStrategy,self).__init__()
		self.exchanges = exchanges
	
	
	def buy(self):
		pass
	
	def sell(self):
		pass
		