#!/usr/bin/env python3
# -*- coding: utf-8 -*-



# Positive opinions
TRADE_MUST_START			= 725
TRADE_OK							= 724


# Negative opinions
TRADE_NO							= -724
TRADE_MUST_ABORT			= -725



from inhablers.base import BaseInhabler



class InhablerBundle(object):
	"A specialized dict for holding all a bot's inhablers"
	
	def __init__(self, default=TRADE_OK):
		super(InhablerBundle,self).__init__()
		self._default			= default
		self._inhablers		= []
	
	def add(self, inh):
		if not isinstance(inh, BaseInhabler):
			raise TypeError("Should be a BaseInhabler")
		self._inhablers.append(inh)
	
	def decide(self, ts):
		decisions 	= filter(None, map(lambda i: i.decide(ts), self._inhablers))
		try:
			return min(decisions)
		except ValueError:
			return self._default
	
	def is_no(self, ts):
		"Must not trade (& maybe should close pos)"
		return self.decide(ts) < 0
	
	def is_yes(self, ts):
		"Is ok (or mandatory) to trade"
		return self.decide(ts) > 0

	