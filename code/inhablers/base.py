#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from indicators.factory import RequiredIndicatorsMixIn



class BaseInhabler(RequiredIndicatorsMixIn):
	
	'''
	Inhablers exist to answer a simple question: "should we trade right now?"
	
	They expose one method, decide(), which will return one of:
	
	None													- no opinion
	inhablers.TRADE_OK						- ok to trade if bot wants
	inhablers.TRADE_MUST_START		- unused; trading always at bot's discretion
	inhablers.TRADE_NO						- do not enter any new trades
	inhablers.TRADE_MUST_ABORT		- do not enter any trades; abort pos if in it
	'''
	
	def __init__(self, indicators, storage, datasource):
		self.indicators				= indicators
		self.storage						= storage
		self.datasource				= datasource
		super(BaseInhabler,self).__init__()
	
	def decide(self, ts):
		return None

