#!/usr/bin/env python3
# -*- coding: utf-8 -*-




class BasePosition(object):
  
  def __init__(self, exchange):
    self.exchange       = exchange



class SimplePosition(BasePosition):

  def __init__(self, exchange, volume, p_entry, p_target, p_stop, notes=None):
    super(SimplePosition,self).__init__(exchange)
    
    self.volume         = volume
    self.cost_entry     = p_entry
    self.cost_target    = p_target
    self.cost_stop      = p_stop
    self.notes          = notes if notes else {}


  def __str__(self):
    return "<%s vol:%.3f entry:%.2f target:%.2f stop:%.2f>" % (
      self.__class__.__name__, self.volume,
      self.cost_entry, self.cost_target, self.cost_stop
    )


  def bidLimit(self):
    '''
    Assuming we'll realize our target, what is the highest we can bid without
    exchange costs consuming all the profits?
    '''
    return self.cost_target - self.costSuccess()


  def costSuccess(self):
    "What will the exchange charge us if it works out?"
    return sum( [
      self.exchange.calculateFee(self.cost_entry),
      self.exchange.calculateFee(self.cost_target)
    ])


  def costFail(self):
    "What will the exchange charge us if we exit early?"
    return sum( [
      self.exchange.calculateFee(self.cost_entry),
      self.exchange.calculateFee(self.cost_stop)
    ])

  
  def grossProfitAtPrice(self, p):
    '''
    Assuming a sale at price `p`, how much would this position have been worth
    before any fees?
    '''
    return (p * self.volume) - (self.cost_entry * self.volume)
  
  
