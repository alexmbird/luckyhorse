#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import csv

import exchanges
from events import Trade, Order
from indicators.factory import RequiredIndicatorsMixIn

from utils.time import HORSEYTIEM

from utils.logging import LOG_EXCH


class BaseBot(RequiredIndicatorsMixIn):
  
  PRINTABLE_NAME          = "basebot"
  DESCRIPTION             = """
  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis varius quam a sem porta dapibus. Phasellus lobortis convallis risus vitae viverra. Maecenas lacinia lacus non ante auctor ornare. Etiam venenatis, metus nec finibus efficitur, arcu odio ultricies sapien, nec ornare ex risus non lacus. Nulla in purus lorem. Suspendisse ornare non odio id efficitur. Nulla facilisi. Praesent nisl mauris, lacinia ac pharetra id, egestas sit amet ipsum. 
  """.strip()
  HIDDEN                  = True
  
  # All tunable settings for the bot.  Can be overridden at init.
  DEFAULT_VARS            = {
    'output_stats_csv':   'logs/basebot.csv',      # OVERRIDE THIS
  }
  
  # A standard way to publish stats gathered while the bot ran
  DEFAULT_STATS           = {}
  
  # Set this to get CSV logging.  `timestamp` is prepended to this.
  CSV_FIELDS              = None
  
  # Dict of exchanges a bot needs.  These are just defaults and can be
  # overridden at runtime.  Use exchanges.ExchangeBase to force a choice.
  # Format is label -> (klass, kwargs)
  REQD_EXCHANGES    = {}
  
  # Dict of datasources a bot needs in the form of label -> tuple(klass, kwargs)
  # If the default is None a source must be supplied on the command line.
  REQD_DATASOURCES  = {}
  
  # List of the inhabler classes required.  These will be assembled by a factory
  # and passed to your bot within an InhablerBundle as the `inhablers` arg.
  REQD_INHABLERS    = []
  
  # Supplied by the RequiredIndicatorsMixIn - see that for explanation
  # REQD_INDICATORS   = {
  # }
  

  def __init__(self, 
    sources, indicators, exchanges, inhablers,
    override_vars={}, quiet=False, *args, **kwargs):
    
    super(BaseBot,self).__init__()

    self._quiet     = quiet
    
    self.exchanges  = exchanges
    self.sources    = sources
    self.indicators = indicators
    self.inhablers  = inhablers
    
    self.vars       = self.DEFAULT_VARS.copy()
    self.stats      = self.DEFAULT_STATS.copy()
    print("Overriding: %s" % (override_vars,))
    self.vars.update(override_vars)
    
    if self.CSV_FIELDS:
      # Get a data log open; all bots should use one
      csv_fp = open(self.vars['output_stats_csv'], 'w')
      self._csv = csv.DictWriter(csv_fp, ['timestamp']+self.CSV_FIELDS)
    

    
  def event(self, e):
    '''
    Comply with the NetAdapter interface.  This method gets a firehose of events
    from the exchange.  It's down to the consumer to pick out what they want and
    discard the rest.
    '''
    pass
  
  
  def setup(self):
    "Soon to be deprecated"
    pass
  
  
  def shutdown(self):
    '''
    Called when there are no more events to come and the app is about to exit.
    '''
    pass
  
  
  def _print(self, s):
    "Print a string, formatted with the current time"
    if not self._quiet:
      print("%s %s" % (HORSEYTIEM.printable(), s))
  
  
  def _csvlog(self, d):
    "Log a dict of values to the csv file with timestamp added"
    if not self.CSV_FIELDS:
      raise RuntimeError("You can't use _csvlog in a bot without CSV logging")
    d['timestamp'] = HORSEYTIEM.time()
    self._csv.writerow(d)
  
  

  
  



class EchoBot(BaseBot):
  
  PRINTABLE_NAME          = "echobot"
  DESCRIPTION             = "Echobot echoes events"
  HIDDEN                  = False
  
  ORDER_LABELS = {
    Order.STATE_CREATED:    'CREATE',
    Order.STATE_CHANGED:    'UPDATE',
    Order.STATE_DELETED:    'DELETE'
  }

  def __init__(self, exchange):
    super(EchoBot,self).__init__(exchange)
  
  def event(self, e):
    if isinstance(e, Trade):
      self._print("TRADE\t%s" % e)
    elif isinstance(e, Order):
      self._print("%s\t%s" % ( self.ORDER_LABELS[e.order_state], e ))
  




class LogBot(BaseBot):

  PRINTABLE_NAME          = "logbot"
  DESCRIPTION             = "Logs to the Python logger system"
  HIDDEN                  = True
  
  ORDER_LABELS = {
    Order.STATE_CREATED:    'CREATE',
    Order.STATE_CHANGED:    'UPDATE',
    Order.STATE_DELETED:    'DELETE'
  }

  def __init__(self, exchange):
    super(LogBot,self).__init__(exchange)

  def event(self, e):
    if isinstance(e, Trade):
      LOG_EXCH.debug("TRADE\t%s", e)
    elif isinstance(e, Order):
      LOG_EXCH.debug("%s\t%s", self.ORDER_LABELS[e.order_state], e )

