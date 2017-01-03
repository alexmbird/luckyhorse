#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from utils.time import HORSEYTIEM
from time import gmtime

from inhablers import TRADE_OK, TRADE_MUST_START
from inhablers import TRADE_NO, TRADE_MUST_ABORT
from inhablers.base import BaseInhabler

import indicators.inds.wilder as i_wilder

from utils.time.period import *

from utils.exceptions import InsufficientDataError



class Wilder(BaseInhabler):
	
	REQD_INDICATORS	= {
		'posdi_1d':     (i_wilder.PosDI_1Day,),
		'negdi_1d':     (i_wilder.NegDI_1Day,),
		'adx_1d':       (i_wilder.ADX_1Day,),
	}
	
	
	def __init__(self, *args, **kwargs):
		super(Wilder,self).__init__(*args, **kwargs)
		self._period 		= None
		
	def decide(self, ts):
		# Only regenerated once a day
		if (not self._period) or (ts not in self._period):
			self._period = FixedPeriod_1Day(around_ts=ts)
			p_yest 		= self._period - 1
			try:
				self.pdi		= self.indicators['posdi_1d'].hist(p_yest)[0]
				self.ndi		= self.indicators['negdi_1d'].hist(p_yest)[0]
				self.adx		= self.indicators['adx_1d'].hist(p_yest)[0]
			except InsufficientDataError:
				self.pdi = self.ndi = self.adx = None
		
		# Catch the case where no data could be generated
		if not all([self.pdi, self.ndi, self.adx]):
			return None
		
		# 52.5 before
		if self.adx > 32.5 and self.pdi > self.ndi:
			return TRADE_OK
		else:
			return TRADE_NO
	