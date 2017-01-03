#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from inhablers import TRADE_OK, TRADE_MUST_START
from inhablers import TRADE_NO, TRADE_MUST_ABORT
from inhablers.base import BaseInhabler

import indicators.inds.simple as i_simple

from utils.time.period import *
from utils.exceptions import InsufficientDataError



# class Crashing(BaseInhabler):
#   
#   '''
#   Detect when a market is crashing and refuse to trade
#   '''
#   
#   REQD_INDICATORS		=	{
#     'max_1d'		=	(MaxTradePrice, ),
#   }
#   
#   def decide(self, ts):
#     dayperiod 	= FixedPeriod_1Day(around_ts=ts, anchor=ANCHOR_HOUR_LHS) - 1
#     max24 			=	self.indicators['max_1d'].hist(dayperiod)[0]
#     latest_tr	= self.storage.trades.fetchOne(self.datasource.EXCHANGE_ID, ts)
#     return None


class MaxIn24H(BaseInhabler):
	
	'''
	Only open trades if we're at a 24-h high
	'''
	REQD_INDICATORS		=	{
		'max_1d':			(i_simple.MaxTradePrice, ),
	}
	def decide(self, ts):
		try:
			dayperiod 	= FixedPeriod_1Day(around_ts=ts, anchor=ANCHOR_HOUR_LHS) - 1
			max24 			=	self.indicators['max_1d'].hist(dayperiod)[0]
			latest_tr	= self.storage.trades.fetchOne(self.datasource.EXCHANGE_ID, ts)
		except InsufficientDataError:
			print("Nope")
			return None
		if float(latest_tr.price) >= max24:
			return TRADE_OK
		else:
			return TRADE_NO
	