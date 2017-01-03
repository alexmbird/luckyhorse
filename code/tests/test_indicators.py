#!/usr/bin/env python3
# -*- coding: utf-8 -*-


if __name__ == '__main__':
	import sys
	sys.path.append('./')
	sys.path.append('code/')


import unittest
from importlib import import_module
import inspect

from datasource.signals.dummy import DataSourceDummy
from indicators.inds._base import IndicatorBase
from utils.time.period import FixedPeriod_5Min


class TestAllIndicators(unittest.TestCase):
	
	'''
	Dynamically identify all indicators.  Create a test fixture for each that
	loads & creates it.
	'''
	
	INDICATOR_MODULES	= (
		'simple',
		'wilder'
	)
	
	# this doesn't work.
	@classmethod
	def discover(cls, *args, **kwargs):
		
		# Dynamically create fixture methods for every Indicator we discover
		testperiod = FixedPeriod_5Min(1416484800)
		
		for modname in cls.INDICATOR_MODULES:
			module = import_module('.'+modname, 'indicators.inds')
			for thing_name in dir(module):
				thing = getattr(module, thing_name)
				print("%s type %s" % (thing, type(thing)))
				if inspect.isclass(thing) and issubclass(thing, IndicatorBase):
					fix_name 	= 'test_' + thing_name
					def fix_meth(s):
						print("%s" % type(thing))
						ind = thing()
						v = ind.calculate(testperiod)
						assert isinstance(v, float)
					setattr(cls, fix_name, fix_meth)
		
		

if __name__ == '__main__':
	TestAllIndicators.discover()
	unittest.main()


