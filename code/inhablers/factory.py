#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from datasource.signals.base import DataSourceBase
from indicators.factory import IndicatorFactory
from storage import StorageEngine

from inhablers import InhablerBundle


class InhablerFactory(object):

	'''
	Generate Inhablers.
	'''

	def __init__(self, ifakt, storage, sources):
		'''
		`ifakt`						-	Indicator factory.
		`storage`					- StorageEngine which an inhabler can query for further history
		`sources`					- DataSource-s
		'''
		if not isinstance(ifakt, IndicatorFactory):
			raise TypeError("ifakt needs to be an IndicatorFactory")
		self.ifakt							= ifakt

		if not isinstance(storage, StorageEngine):
			raise TypeError("storage needs to be a StorageEngine")
		self.storage						= storage
		
		if not isinstance(sources, dict):
			raise TypeError("sources must be a dict of label->datasource")
		self.sources						= sources
		


	def createFromReqd(self, reqd):
		'''
		Create the inhablers described by the `reqd` list.
		'''
		bundle 			= InhablerBundle()
		for klass, ds_label in reqd:
			src					= self.sources[ds_label]
			indicators = self.ifakt.createFromReqd(
				klass, default_src=src
			)
			new_inh = klass(indicators, self.storage, src)
			bundle.add(new_inh)
		return bundle

