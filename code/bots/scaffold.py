#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import copy
from importlib import import_module
from collections import defaultdict

from bots.bots._base import EchoBot, LogBot
from bots.bots.shapefit import ShapeFitBot
from bots.bots.futurebot import FutureBot
from bots.bots.fuzzbot import FuzzBot
from bots.bots.hodlbot import HodlBot

from utils.time import HORSEYTIEM
from utils.time.tools import timestamp_to_printable as ts2p
from utils.data import chunker

from storage import StorageEngine, TradeStore
from indicators.factory import IndicatorFactory
from inhablers.factory import InhablerFactory

from events.broker import QueuedBrokerBundle
from datasource.signals.base import DataSourceBase




class Scaffold(object):
  
  '''
  Construct bots and all the facilities they need to run; manage them through a
  live or backtesting life cycle.
  '''
  
  ALL_BOTS = [
    EchoBot, LogBot, 
    ShapeFitBot,
    FutureBot,
    FuzzBot,
    HodlBot
  ]
  
  
  def __init__(self, bot_name, bot_vars, 
    source_descriptor=None, exch_descriptor=None,
    verbose=False):
    
    super(Scaffold,self).__init__()
    botklass        = self.findBot(bot_name)
    self._verbose   = verbose

    # set the clock before any bots or indicators are created
    self.broker     = QueuedBrokerBundle(maxsize=10)
    sources         = self.createSources(
      source_descriptor, botklass.REQD_DATASOURCES, self.broker
    )
    self._setClock(sources.values())
    
    exchanges   = self.createExchanges(exch_descriptor, botklass.REQD_EXCHANGES, self.broker)

    self.storage  = StorageEngine()
    self.ifakt    = IndicatorFactory(self.storage, sources)
    indicators    = self.ifakt.createFromReqd(botklass, sources)
    
    self.infakt   = InhablerFactory(self.ifakt, self.storage, sources)
    inhablers     = self.infakt.createFromReqd(botklass.REQD_INHABLERS)
    
    self.bot    = botklass(
      sources=sources, indicators=indicators, exchanges=exchanges,
      inhablers=inhablers,
      override_vars=bot_vars, ifakt=self.ifakt, storage=self.storage
    )
    print("Setup indicator tree for bot:")
    self.bot.indicators.dumpIndicatorTree()

    
    # Save sources for later so run() can be triggered
    self._sources = sources
  
  
  @classmethod
  def createSources(cls, source_descriptor, required, broker):
    "Make the datasources required by a bot."
    sources = copy.deepcopy(required)  # dict of label -> (klass, kwargs)
    
    # Apply CLI overrides, if any
    if source_descriptor is not None:
      for s in source_descriptor.split('|'):
        parts = s.split(':')
        label, source_module, klassname = parts[0:3]
        ds_kwarg_pairs  = parts[3].split(',') if len(parts) >= 4 else {}
        ds_kwargs       = dict( [p.split('=') for p in ds_kwarg_pairs] )
        ds_module       = import_module('.'+source_module, 'datasource.signals')
        ds_klass        = getattr(ds_module, klassname)
        sources[label]  = (ds_klass, ds_kwargs)

    # Make the sources
    for label in sources.keys():
      if sources[label] is None:
        raise Exception("Source '%s' needs to be specified on the command line" % (label,))
      ds_klass, ds_kwargs = sources[label]
      try:
        sources[label] = ds_klass(broker=broker, **ds_kwargs)
      except TypeError as e:
        print(e)
        print("Class was %s" % (ds_klass,))
        raise
    
    return sources
    
  
  @classmethod
  def createExchanges(cls, exch_descriptor, required, broker):
    "Make the exchanges required by a bot"
    exchanges = copy.deepcopy(required)
    
    # Apply CLI overrides
    if exch_descriptor is not None:
      for s in exch_descriptor.split('|'):
        parts = s.split(':')
        label, source_module, klassname = parts[0:3]
        ex_kwarg_pairs    = parts[3].split(',') if len(parts) >= 4 else {}
        ex_kwargs         = dict( [p.split('=') for p in ex_kwarg_pairs] )
        ex_module         = import_module('.'+source_module, 'exchanges')
        ex_klass          = getattr(ex_module, klassname)
        exchanges[label]  = (ex_klass, ex_kwargs)

    # Make the exchanges
    for label in exchanges.keys():
      if exchanges[label] is None:
        raise Exception("Exchange '%s' needs specifying on the command line" % (label,))
      exch_klass, exch_kwargs = exchanges[label]
      exchanges[label] = exch_klass(broker=broker, **exch_kwargs)
    return exchanges
    
  
    
  
  def findBot(self, bot_name):
    "Locate the class for a bot given its printable name"
    bot_name = bot_name.lower()
    matches = list( filter(
      lambda b: b.PRINTABLE_NAME.lower() == bot_name,
      self.ALL_BOTS
    ) )
    
    try:
      return matches[0]
    except (KeyError, IndexError):
      raise ValueError("No such bot '%s'" % (bot_name,))
    
  
  @classmethod
  def listBots(cls, hidden=False):
    '''
    Return all the bot classes in a list.  Default is to exclude 'hidden' ones.
    '''
    if hidden:
      return list(cls.ALL_BOTS)
    else:
      return list(filter(lambda b: not b.HIDDEN, cls.ALL_BOTS))

  
  @classmethod
  def _setClock(cls, sources):
    '''
    Take the earliest time returned from the dict of sources and use it to
    set the clock.
    '''
    start_times = list( map(lambda s: s.getStartTs(), sources) )
    if None in start_times:
      print("At least one live source detected; no clock override")
      HORSEYTIEM.override(None)
    else:
      s_time = min(start_times)
      print("Historical sources detected; setting clock to %s" % ts2p(s_time))
      HORSEYTIEM.override(s_time)
  
  
  def backtest(self):
    "run() all of the sources"
    self.bot.setup()
    
    datasources = list(self._sources.values())
    for s in datasources:
      if self._verbose:
        self.broker[s.BROKER_CHANNEL].subscribe(lambda e: print("EVENT:\t%s" % e), 0)
      self.broker[s.BROKER_CHANNEL].subscribe(self.storage.event, 1)
      s.start()
    
    # Have backplane dispatch events, using ts_update attributes to fake the
    # wallclock time.
    self.broker.run(src_thread_group=datasources, fake_time=True)
    
  
  @classmethod
  def batchLoad(cls, source_descriptor):
    '''
    Batch-insert an exchange's trade history into the storage engine
    '''
    broker          = QueuedBrokerBundle(maxsize=10)
    reqd            = {'market':(DataSourceBase, {})}
    sources         = cls.createSources(source_descriptor, reqd, broker)
    cls._setClock(sources.values())
    src             = sources['market']
    tstore          = TradeStore()
    
    tstore.deleteAll(src.EXCHANGE_ID, yes_I_mean_it=True)
    
    it_all = src.fetch()
    for chunk in chunker(10000, it_all):
      print("Storing chunk of %d trades" % len(chunk))
      tstore.storeMany(src.EXCHANGE_ID, chunk)
    
