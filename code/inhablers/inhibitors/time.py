#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from utils.time import HORSEYTIEM
from time import gmtime

from inhablers import TRADE_OK, TRADE_MUST_START
from inhablers import TRADE_NO, TRADE_MUST_ABORT
from inhablers.base import BaseInhabler


class GoodHours(BaseInhabler):
	
	'''
	Volatility is at its highest on BitStamp between 7am and 6pm
	'''
	
	def decide(self, ts):
		hour = gmtime(ts)[3]
		
		if 6 <= hour <= 18:
			return TRADE_OK
		elif 5 <= hour <= 19:
			return TRADE_NO
		else:
			return TRADE_NO


		