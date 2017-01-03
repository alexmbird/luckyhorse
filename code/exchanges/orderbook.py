#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from blist import sortedlist
from decimal import Decimal as D
import threading
from operator import attrgetter

from events import Trade, Order, OrderAsk, OrderBid

from utils.hmath import round_dec_down_to_n_places as r_dec_dn
from utils.hmath import round_dec_up_to_n_places   as r_dec_up



class OrderBookBase(object):
  
  '''
  Base for a threadsafe order book.
  
  Why threadsafe?  So you can have an updater thread constantly incorporating
  fresh data from a link to the market.  Beware latency!
  
  Subclasses of this implement different sorts of orderbook, i.e. grouped and
  distinct.
  '''

  def __init__(self):
    super(OrderBookBase,self).__init__()
    
    # Control access to all our asks & bids
    self._big_lock    = threading.Lock()
    
    # Main order collections
    self._asks    = sortedlist(key=attrgetter('price'))
    self._asks_id = {}
    self._bids    = sortedlist(key=attrgetter('price'))
    self._bids_id = {}
    
    # Quick way to associate orders with their books
    self.BOOK_MAP = {
      OrderBid:   (self._bids, self._bids_id),
      OrderAsk:   (self._asks, self._asks_id)
    }

    # High & low water marks for prices we have seen.  Anything unknown (from
    # before we started looking) will have been executed so flushed out.  We can
    # be confident that within this zone we know about all existing orders.
    self._price_low_water_mark    = None
    self._price_high_water_mark   = None
    
    # Keep a reference to the last trade so its price can be used as a fallback
    # when estimating the value of some bitcoins
    self._last_trade              = None
    

  def __len__(self):
    with self._big_lock:
      return len(self._asks) + len(self._bids)
  
  
  #
  # Pretty-print our contents; valuable for debugging
  #
  def __str__(self):
    with self._big_lock:
      price_lo = self._price_low_water_mark
      price_hi = self._price_high_water_mark
      return "<%s - %d asks, %d bids.  Full info between %s and %s >" % (
        self.__class__.__name__, len(self._asks), len(self._bids),
        '-' if price_lo is None else ("%.2f" % price_lo),
        '-' if price_hi is None else ("%.2f" % price_hi)
      )
  
  
  def dumpAsks(self):
    print("%d asks" % len(self._asks))
    for o in self._asks:
      print("  %s" % o)
    
  def dumpBids(self):
    print("%d bids" % len(self._bids))
    for o in self._bids:
      print("  %s" % o)
  
  
  def __eq__(self, other):
    if other is None:
      return False
    if not isinstance(other, OrderBookBase):
      return False
    return (
      sorted(self.getBids()) == sorted(other.getBids()) and 
      sorted(self.getAsks()) == sorted(other.getAsks())
    )
  
  
  def _checkDecimals(self, price, volume):
    if not isinstance(price, Decimal) or not isinstance(volume, Decimal):
      raise TypeError("Order book is decimal-only")
    if price <= 0 or volume <= 0:
      raise ValueError("Can't have negative price or volume (%s/%s)" % (price, volume))
  
  
  
  
  #
  # ORDER MATCHING ENGINE
  #
  def estimateBid(self, volume=None, spend=None, limit=None, fallback=False):
    "Estimate the results if we issued a bid order"
    if len(self._asks):
      orders = self.getAsks(price_hi=limit)
      return self._match(orders, volume, spend)
    elif fallback and self._last_trade is not None:
      return self._matchFallback(volume, spend)
    else:
      return (D(0), D(0))
  
  
  def estimateAsk(self, volume=None, earn=None, limit=None, fallback=False):
    "Estimate the results if we issued an ask order"
    if len(self._bids):
      orders = reversed(list(self.getBids(price_lo=limit)))
      return self._match(orders, volume, earn)
    elif fallback and self._last_trade is not None:
      return self._matchFallback(volume, earn)
    else:
      return (D(0), D(0))
  
  
  def _match(self, orders, volume=None, cash=None):
    '''
    Match up a desired transaction with orders in the orderbook.
    
    `volume`    - Volume of BTC we wish to transact  OR
    `cash`      - Volume of money we wish to transact
    
    `volume` and `cash` are mutually exclusive.

    Returns a tuple of (cash, btc) where cash is the money spent and btc the
    number of coins actually bought.  Exchange fees not included.
    '''
    if bool(volume) == bool(cash):
      raise ValueError("Must specify `volume` OR `cash`")
    if volume is not None and volume < 0:
      raise ValueError("Can't have a negative volume")
    if cash is not None and cash < 0:
      raise ValueError("Can't have a negative spend")

    act_cash    = 0
    act_vol     = 0
    for o in orders:
      print("Considering %s" % o)
      if volume is not None and act_vol + o.volume >= volume:
        act_cash  += (volume - act_vol) * o.price
        act_vol   = volume
        break
      elif cash is not None and o.volume * o.price >= cash - act_cash:
        act_vol   += (cash - act_cash) / o.price
        act_cash  = cash
        break
      else:
        act_cash += o.volume * o.price
        act_vol += o.volume
      print("After: cash_spent:%s vol_bought:%s" % (act_cash, act_vol))
    return (D(act_cash), D(act_vol))

  
  def _matchFallback(self, volume=None, spend=None):
    '''
    Using only self._last_trade.price, guess what the transaction would produce
    '''
    if bool(volume) == bool(spend):
      raise ValueError("Must specify `volume` OR `spend`")

    p = self._last_trade.price
    if volume is not None:
      cash = D(volume*p)
      return ( r_dec_dn(cash, 2), D(volume) )
    elif spend is not None:
      vol = D(spend/p)
      return ( spend, r_dec_dn(vol, 8) )
    
  
  #
  # HANDLE AN EVENT STREAM FROM THE NETADAPTER INTERFACE
  #
  def event(self, e):
    "Suppoer the NetAdapter firehose"
    if isinstance(e, Trade):
      self._noteTradeBoundaries(e)
      self._last_trade = e
    elif isinstance(e, Order):
      if e.order_state == Order.STATE_CREATED:
        self.orderAdd(e)
      elif e.order_state == Order.STATE_CHANGED:
        self.orderChange(e)
      elif e.order_state == Order.STATE_DELETED:
        self.orderDelete(e)
  
  
  def orderAdd(self, o):
    raise NotImplementedError()
  
  def orderChange(self, o):
    raise NotImplementedError()
  
  def orderDelete(self, o):
    raise NotImplementedError()
  
  
  
  #
  # TRADE UPDATE INTERFACE
  #
  def _noteTradeBoundaries(self, t):
    '''
    OrderBook doesn't give a fuck about trades except that from them we can
    infer our zone of total order awareness.  If in this session we have seen
    trading between prices X and Y, we know that any invisible orders (i.e.
    created before our session started) have been flushed out.
    '''
    with self._big_lock:
      if self._price_low_water_mark is None or t.price < self._price_low_water_mark:
        self._price_low_water_mark = t.price
      if self._price_high_water_mark is None or t.price > self._price_high_water_mark:
        self._price_high_water_mark = t.price

  
  
  #
  # ORDER STATISTICAL FUNCTIONS
  #
  def priceRangeSeen(self):
    "Range of prices this OrderBook has ever seen as tuple (min,max)"
    with self._big_lock:
      return (self,_price_low_water_mark, self._price_high_water_mark)
  
  
  
  #
  # RETRIEVING SUBSETS OF THE ORDER BOOK
  #
  
  def getAsks(self, price_hi=None):
    return self._sliceBook(self._asks, price_hi=price_hi)
  
  def getBids(self, price_lo=None):
    return self._sliceBook(self._bids, price_lo=price_lo)
  
  def _sliceBook(self, book, price_lo=None, price_hi=None):
    raise NotImplementedError()






class OrderBookDistinct(OrderBookBase):
  
  '''
  An order book where every order is a unique little flower, meaning orders at
  the same price are not merged.
  '''
  
  def _sliceBook(self, book, price_lo=None, price_hi=None):
    "Return a section of an orderbook between two prices"
    orders = book
    if price_lo is not None:
      if price_lo < 0:
        raise ValueError("price_lo can't be -ve")
      orders = filter(lambda o: o.price >= price_lo, orders)
    if price_hi is not None:
      if price_hi < 0:
        raise ValueError("price_hi can't be -ve")
      orders = filter(lambda o: o.price <= price_hi, orders)
    return orders

  
  #
  # ORDER UPDATE INTERFACE.  Exchange NetAdaptors will transmit order changes to
  # these methods.
  #
  def orderAdd(self, o):
    "Add an order."
    book_list, book_dict = self.BOOK_MAP[o.__class__]
    with self._big_lock:
      book_list.add(o)
      if o.order_id is not None:
        book_dict[o.order_id] = o
    
  
  def orderChange(self, new_o):
    "Change an existing order"
    print("Changing %s" % new_o)
    book_list, book_dict = self.BOOK_MAP[new_o.__class__]
    with self._big_lock:
      old_o = book_dict[new_o.order_id]
      book_list.discard(old_o)
      book_list.add(new_o)
      book_dict[new_o.order_id] = new_o

  
  def orderDelete(self, o):
    "Remove an order.  If the order did not exist, does nothing."
    book_list, book_dict = self.BOOK_MAP[o.__class__]
    with self._big_lock:
      old_o = book_dict[o.order_id]
      book_list.discard(old_o)
      book_dict.pop(o.order_id, None)



  
  



class OrderBookGrouped(OrderBookBase):
  
  '''
  An order book where orders at the same price are grouped.
  For example if two orders to buy 1BTC at $15 come in they are merged to
  create one for 2BTC at $15.  This is how information is provided from
  BitStamp's official diff_order_book stream. 
  '''
  
  def __init__(self):
    '''
    Create a new orderbook.  Optionally takes lists of bids & asks which makes
    it easy to construct from the results of the BitStamp API call.
    '''
    raise NotImplementedError()

  
