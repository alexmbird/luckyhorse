#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class BaseEvent(object):
  
  '''
  Base for all event classes; implements standard data & methods that any event
  must have.
  '''
  
  def __init__(self, exchange_id, ts_update):
    '''
    `exchange_id` - Integer ID of the exchange this event came from
    `ts_update`   - Epoch timestamp when the event was received by LuckyHorse.
                    Either an int or a float.
    '''
    self.exchange_id  = exchange_id
    self.ts_update    = ts_update
