#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from decimal import Decimal as D

from bots.strategies._base import BaseStrategy
from bots.positions import SimplePosition

from utils.hmath import round_dec_down_to_n_places as r_dec_dn

from utils.logging import LOG_BOTS



class BalanceProportional(BaseStrategy):
	
	def __init__(self, exchanges, trade_on, proportion=0.5):
		super(BalanceProportional,self).__init__(exchanges)
		self.exch 				= exchanges[trade_on]
		self.proportion	= proportion
		self.position 		= None
		
	
	def buy(self, confidence=100, target=None, stop=None, reason=''):
		if self.position:
			return
		
		spend = self.exch.balance.cash * D(self.proportion) * D(confidence/100)
		spend 	= r_dec_dn(spend, 2)
		fee, spend, vol = self.exch.executeBid(spend=spend)
		LOG_BOTS.info("BUY:\t%s - %s", self.exch.balance, reason)
		buy_price_avg = r_dec_dn(spend/vol, 2)
		p_target 	= (buy_price_avg * D(1.015)) if target is None else D(target)
		p_stop			= (buy_price_avg * D(0.99) ) if stop is None else D(stop)
		self.position = SimplePosition(
			self.exch, vol, buy_price_avg, p_target, p_stop
		)
		LOG_BOTS.info("%s", self.position)
		return self.position
	
	
	def sell(self, confidence=100, reason=''):
		if not self.position:
			return
		vol = self.exch.balance.btc
		fee, cash_earned, btc_sold = self.exch.executeAsk(volume=vol)
		LOG_BOTS.info("SELL:\t%s - %s", self.exch.balance, reason)
		self.position = None
	

