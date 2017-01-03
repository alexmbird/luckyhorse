#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from collections import defaultdict


from storage.engine import StorageEngine

from indicators import IndicatorBundle




class RequiredIndicatorsMixIn(object):

	'''
	All indicator-bearing classes inherit from this to get the REQD_INDICATORS
	requirement processing. 
	
	Recurse through a class's parents to discover all required indicators.  Used
	for bots and for composite indicators.
	
	May also be used alone to specify a set of indicators you want created.
	'''

	# Dict of indicators this bot needs.  Symbolic name / tuple of:
	#   1) The class of the indicator to use
	#   2) If a composite indicator - the name of a datasource (from 
	#      REQD_DATASOURCES) the indicator is fed its data from.
	REQD_INDICATORS = {}

	@classmethod
	def requiredIndicators(cls):
		'''
		Recurse down through our subclasses to generate a complete list of all the
		indicators which will be required.
		'''
		inds = {}
		for label, ituple in cls.REQD_INDICATORS.items():
			inds[label] = ituple
			for parent in cls.__bases__:
				if hasattr(parent, 'REQD_INDICATORS'):
					#print("Adding inds from parent %s" % parent)
					inds.update(parent.requiredIndicators())
		return inds






class IndicatorFactory(object):
	
	'''
	Create and cache indicator objects.  The intention here is ensure only one copy
	of each indicator exists per datasource.
	'''
	
	def __init__(self, storage, dsources):
		'''
		`storage`			-	A StorageEngine instance
		`dsources`			- A dict of datasources (label->source) used to satisfy
										explicitly labelled source requirements.
		'''
		super(IndicatorFactory,self).__init__()
		
		if not isinstance(storage, StorageEngine):
			raise TypeError("storage must be a StorageEngine")
		self.storage				= storage
		
		if not isinstance(dsources, dict):
			raise TypeError("dsources must be a dict of existing datasources")
		self.datasources		= dsources
		
		self.cache					= defaultdict(dict)
		
	
	
	def createFromReqd(self, klass, default_src=None):
		'''
		Make the indicators required by a bot, including recursion to give all sub-
		indicators their dependencies.
		
		`sources`     	- A label/dsrc dict of all the datasources loaded.  Bots which
										use multiple sources can specify what is required then find
										them via this label.
		`klass`       	- Class containing a REQD_INDICATORS dict - so bot/indicator
		`default_src` 	- 	Child indicators may be used in many places so they can't
										specify a source by label.  Instead when recursing for child
										inds we leave sources empty and specify a single default.
		'''
		if not issubclass(klass, RequiredIndicatorsMixIn):
			raise TypeError("Spec klass must inherit from RequiredIndicatorsMixIn")
		
		indicators = IndicatorBundle()
		
		for label, ind_tuple in klass.requiredIndicators().items():
			ind_list 	= list(ind_tuple)
			itype 			= ind_list.pop(0)
			dsrc 			= self.datasources[ind_list.pop(0)] if len(ind_list) else default_src
			if dsrc is None:
				raise ValueError("Indicator has no src_label and no default passed")
			
			try:
				indicators[label] = self.cache[dsrc][itype]
			except KeyError:
				child_inds = self.createFromReqd(itype, dsrc)		# recurse for children
				self.cache[dsrc][itype] = itype(self.storage, dsrc, child_inds)
			
			indicators[label] = self.cache[dsrc][itype]
		
		return indicators

