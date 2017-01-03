#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from datasource.signals.bitstamp.base import DataSourceBitStampBase

from events import Trade, Order, OrderAsk, OrderBid

from utils.time import HORSEYTIEM
import time

import collections
import threading

from decimal import Decimal as D

from pypusher.socket import PusherSocket
import websocket
from utils. logging import LOG_PUSHERSOCK




class DataSourceBitStampLive(DataSourceBitStampBase):
  
  PUSHER_KEY        = 'de504dc5763aeef9ff52'
  CHANNEL_ORDERS    = 'live_orders'
  CHANNEL_TRADES    = 'live_trades'
  
  # The Websocket client often crashes.  Work around it by reconnecting.
  RECONNECT_DELAY_SEC = 15
  
  
  # Keep reference to last N orders for latency & other sideband calculations
  # Not all orders end up in this: only ones which could be used to determine
  # latency & other exchange performance.
  RECENT_ORDER_CACHE_SIZE       = 50
  
  # BitStamp use integers to represent the type of an order, and our storage
  # module just happens to use identical ones.  These map onto subclasses of
  # Order.  With the array one can easily turn classes to ID's with
  # ORDER_TYPE_IDS.index(klass) and back again with ORDER_TYPE_IDS[id].
  #
  # THE ORDER OF THESE ELEMENTS IS CRUCIAL, DO NOT FUCK WITH THEM
  ORDER_TYPE_IDS    = [OrderBid, OrderAsk]


  def __init__(self, broker):
    super(DataSourceBitStampLive,self).__init__(broker)
    
    # Used for collecting latency and other stats
    self._recent_order_cache_lock   = threading.Lock()
    self._recent_order_cache        = collections.deque(maxlen=self.RECENT_ORDER_CACHE_SIZE)
    
    # Signal when it's time to exit
    self._time_to_die   = threading.Event()
    
    # This will hold our running Pusher socket
    self._psock  = None
    
    # Counter, needs to be visible everywhere
    self.n_published = 0
    

  def run(self, limit=None):
    "Gentlemen, start your data feeds!"
    self._connectWebSocket(limit)
  
  
  def _orderFromStreamDict(self, d, order_state):
    ts_create = ts_delete = None
    if order_state is Order.STATE_CREATED:
      ts_create = float(d['datetime'])
    elif order_state is Order.STATE_DELETED:
      ts_delete = float(d['datetime'])
  
    klass = self.ORDER_TYPE_IDS[int(d['order_type'])]
    return klass(
      price       = D(d['price']),
      volume      = D(d['amount']),
      ts_create   = ts_create,
      ts_delete   = ts_delete,
      ts_update   = HORSEYTIEM.time(),
      order_id    = int(d['id']),
      state       = order_state,
      exchange_id = self.EXCHANGE_ID
    )
  
  
  def _tradeFromStreamDict(self, d):
    return Trade(
      exchange_id = self.EXCHANGE_ID,
      trade_id    = int(d['id']),
      price       = D(d['price']),
      volume      = D(d['amount']),
      ts_exec     = HORSEYTIEM.time(),
      ts_update   = HORSEYTIEM.time()
    )
  
  
  def _connectWebSocket(self, limit=None):
    '''
    Setup a thread to watch the orders stream and signal updates to consumers
    within the rest of the application.
    '''
    def quit_maybe():
      if limit is not None:
        if self.n_published >= limit:
          self._psock.disconnect()
          self._time_to_die.set()
    
    # We can't factor these into lambdas to bind to the Pusher socket since each
    # requires a tiny bit of order state attached.
    def _dispatchOrderCreated(*args, **kwargs):
      o = self._orderFromStreamDict(args[0], Order.STATE_CREATED)
      with self._recent_order_cache_lock:
        self._recent_order_cache.append(o)
      self.broker.publish(self.channel, o)
      self.n_published += 1
      quit_maybe()
    
    def _dispatchOrderChanged(*args, **kwargs):
      o = self._orderFromStreamDict(args[0], Order.STATE_CHANGED)
      self.broker.publish(self.channel, o)
      self.n_published += 1
      quit_maybe()
    
    def _dispatchOrderDeleted(*args, **kwargs):
      o = self._orderFromStreamDict(args[0], Order.STATE_DELETED)
      self.broker.publish(self.channel, o)
      self.n_published += 1
      quit_maybe()
    
    # GET TRADE DATA
    def _dispatchTrade(*args, **kwargs):
      t = self._tradeFromStreamDict(args[0])
      self.broker.publish(self.channel, t)
      self.n_published += 1
      quit_maybe()
    
    # Run until we're signaled to exit
    while not self._time_to_die.is_set():
      # Reassemble the PusherSocket object every time - it does not seem to be
      # reusable?
      LOG_PUSHERSOCK.info("Connecting to BitStamp@pusher")
      self._psock = PusherSocket(self.PUSHER_KEY, { 'encrypted': True } )
      c_orders = self._psock.subscribe(self.CHANNEL_ORDERS)
      c_orders.bind('order_created', _dispatchOrderCreated)
      c_orders.bind('order_deleted', _dispatchOrderDeleted)
      c_orders.bind('order_changed', _dispatchOrderChanged)
      c_trades = self._psock.subscribe(self.CHANNEL_TRADES)
      c_trades.bind('trade', _dispatchTrade)
      try:
        self._psock.connect()     # could use async=True to run in own thread
      except Exception as exc:
        # Many crashes in the Websocket client.  Work around by reconnecting.
        LOG_PUSHERSOCK.error("Lost connection to BitStamp@pusher: %s" % exc)
      time.sleep(self.RECONNECT_DELAY_SEC)
      #LOG_PUSHERSOCK.error("_time_to_die set? %s" % self._time_to_die.is_set())
  
  
  def _recentOrderLatencies(self):
    "Return a list of the latencies of every order in the recent_order_cache"
    with self._recent_order_cache_lock:
      if len(self._recent_order_cache) == 0:
        raise ValueError("No orders to return latency of")
      return map(lambda o: o.latency(), self._recent_order_cache)
  
  
  def minLatency(self):
    '''
    Return an estimate for latency using the contents of
    self._recent_order_cache.  This is calculated by calling the latency()
    method of each and returning the minimum.
    '''
    return min(self._recentOrderLatencies())
  
  
  def maxLatency(self):
    '''
    Return an estimate for latency using the contents of
    self._recent_order_cache.  This is calculated by calling the latency()
    method of each and returning the minimum.
    '''
    return max(self._recentOrderLatencies())
  
  
  def meanLatency(self):
    '''
    Return an estimate for latency using the contents of
    self._recent_order_cache.  This is calculated by calling the latency()
    method of each and returning the minimum.
    '''
    return numpy.mean(list(self._recentOrderLatencies()))
  


    
  
