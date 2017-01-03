#!/usr/bin/env python3
# -*- coding: utf-8 -*-



class IndicatorBundle(dict):
  '''
  Bundle together a collection of child indicators.
  '''
  
  def dumpIndicatorTree(self, indent=0):
    '''
    Pretty-print a breakdown of the parent/child indicator relationships
    '''
    format = (' ' * indent) + '%s -> %s'
    for label, ind in self.items():
      print(format % (label, ind))
      if isinstance(ind.indicators, IndicatorBundle):
        ind.indicators.dumpIndicatorTree(indent+2)
      

