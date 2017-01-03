#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from storage.trades import TradeStore
from storage.orders import OrderStore
from storage.indicator import IndicatorStore

from storage._base import RecordNotExistError

from events import Trade, Order


class StorageEngine(object):

	'''
	An overall storage object containing a child class for each kind of object
	we store.
	'''

	def __init__(self, dbconf=None):
		self.trades       = TradeStore(dbconf)
		self.orders       = OrderStore(dbconf)
		self.indicators   = IndicatorStore(dbconf)


	def event(self, e):
		if isinstance(e, Trade):
			self.trades.event(e)
