#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from decimal import Decimal as D
from collections import defaultdict
from operator import attrgetter
from numbers import Number

from storage._base import BaseStore, EventCacheBase
from storage._base import RecordNotExistError, RecordAlreadyExistError

from events import Trade
from utils.data import LRUCache
from utils.time import HORSEYTIEM
from utils.time.period import PeriodBase, TemporalError

from warnings import warn



class TradeCache(EventCacheBase):
  '''
  Fast cache for recent Trade events
  '''
  TS_ATTRIB   = 'ts_exec'



class TradeStore(BaseStore):
  
  CREATE_SQL = {
    
    'sqlite':       '''
  
CREATE TABLE HistTrades(
  exchange_id   TINYINT NOT NULL,
  trade_id      INTEGER NOT NULL,
  ts_exec       INTEGER NOT NULL,
  ts_update     NUMERIC NOT NULL,
  price         DECIMAL(10,2) NOT NULL,
  volume        DECIMAL(8,8)  NOT NULL,
  PRIMARY KEY   (exchange_id, ts_exec)
);

'''.strip(),
    
    'mysql':        '''
    WRITE ME
'''.strip()

  }

  
  
  
  def __init__(self, *args, **kwargs):
    super(TradeStore,self).__init__(*args, **kwargs)
    
    # Note the newest trade timestamp we've seen.  Anything younger than this
    # will be dropped by the _store() method as it clashes with existing data.
    # Stored in a dict, key of exchange_id.
    self._latest_ts_exec_cache   = {}
    
    # Exchange-specific caches of recent events
    self._caches  = defaultdict(TradeCache)
    
  
  def event(self, e):
    '''
    Comply with the NetAdapter interface.  We can safely ignore everything
    except trades.
    '''
    if isinstance(e, Trade):
      self.store(e)
      cache = self._caches[e.exchange_id]
      cache.addLatest(e)
  
  
  def fetch(self, exchange_id, period=None):
    '''
    Load some trades.  First try cache then fall back to storage.
    '''
    if not isinstance(period, PeriodBase):
      raise TypeError("`period` must be a PeriodBase-derivative")
    if period.rhs_ts > HORSEYTIEM.time():
      raise TemporalError("I can't see the future")
    
    try:
      cache = self._caches[exchange_id]
      yield from cache.get(period)
    except RecordNotExistError:
      yield from self._fetchFromDB(exchange_id, period)
  
  
  def _fetchFromDB(self, exchange_id, period=None):
    '''
    Retrieve this session's trades from storage.  Returns Trade() objects. 
    Since trades are unique each should be returned precisely once.
    
    `exchange_id` - ID of the exch we are fetching trades for
    `period`      - FixedPeriodBase-derivative representing period to search.
                    If unspecified we fetch from all of history.
    '''
    sql = [
      "SELECT %s FROM HistTrades" % self.ALL_TRADE_FIELDS,
      "WHERE exchange_id=?",
    ]
    qargs = [exchange_id,]
    if period is not None:
      sql.append("AND ts_exec >= ? AND ts_exec < ?")
      qargs.append(period.lhs_ts)
      qargs.append(period.rhs_ts)
    sql.append("ORDER BY ts_exec ASC")
    cur = self.db.cursor()
    cur.execute(' '.join(sql), qargs)
    
    for row in cur.fetchall():
      yield self._HistTradesRow2Trade(row, exchange_id)
    
  
  def fetchOne(self, exchange_id, before_ts):
    '''
    Load the most recent trade prior to `before_ts`.  First try cache then
    fall back to storage.
    '''
    if not isinstance(before_ts, Number):
      raise TypeError("`before_ts` must be a number")
    if before_ts > HORSEYTIEM.time():
      raise TemporalError("I can't see the future")
    
    try:
      cache = self._caches[exchange_id]
      return cache.getBeforeTs(before_ts)
    except RecordNotExistError:
      return self._fetchOneFromDB(exchange_id, before_ts)
  
  
  def _fetchOneFromDB(self, exchange_id, before_ts):
    '''
    Return the most recent trade before `timestamp`.
    
    `exchange_id` - ID of the exch we are fetching trades for
    `before_ts`   - Timestamp
    '''
    sql = [
      "SELECT %s FROM HistTrades" % self.ALL_TRADE_FIELDS,
      "WHERE exchange_id=? AND ts_exec<=?",
      "ORDER BY ts_exec DESC",
      "LIMIT 1"
    ]
    cur = self.db.cursor()
    cur.execute(' '.join(sql), (exchange_id, before_ts) )
    row = cur.fetchone()
    if row is None:
      raise RecordNotExistError()
    return self._HistTradesRow2Trade(row, exchange_id)


  def _getLatestTsExec(self, exchange_id):
    '''
    Return the ts_exec of the newest trade we've seen for this exchange.
    
    `exchange_id` - ID of the exch we are fetching trades for
    '''
    if exchange_id not in self._latest_ts_exec_cache:
      sql = "SELECT MAX(ts_exec) FROM HistTrades WHERE exchange_id=?"
      cur = self.db.cursor()
      cur.execute(sql, (exchange_id,))
      v = cur.fetchone()[0]
      self._latest_ts_exec_cache[exchange_id] = 0 if v is None else v
    return self._latest_ts_exec_cache[exchange_id]
  
  
  def deleteAll(self, exchange_id, yes_I_mean_it=False):
    '''
    Delete ALL trades held for exchange with id `exchange_id`.  This is useful
    when you're about to batch-load a new set.
    '''
    if not yes_I_mean_it:
      raise RuntimeError("Cowardly refusing to delete all an exch's history without the 'yes_I_mean_it' flag")
    sql = "DELETE FROM HistTrades WHERE exchange_id=?"
    cur = self.db.cursor()
    cur.execute(sql, (exchange_id,))
    
    
  def store(self, t):
    "Place a fresh trade in the database"
    
    if t.ts_exec < self._getLatestTsExec(t.exchange_id):
      return
    
    # warn("Storing trade %s" % t)
    sql = '''
    INSERT OR REPLACE INTO HistTrades(
      exchange_id, trade_id, ts_exec, ts_update, price, volume
    )
    VALUES(?,?,?,?,?,?)
    '''
    cur = self.db.cursor()
    cur.execute(sql, self.trade2tuple(t))
    
    # Update our cached version of the newest trade we've seen
    self._latest_ts_exec_cache[t.exchange_id] = t.ts_exec
  
  
  def storeMany(self, exchange_id, trades):
    '''
    Batch-insert many trades at once.
    '''
    sql = '''
    INSERT OR REPLACE INTO HistTrades(
      exchange_id, trade_id, ts_exec, ts_update, price, volume
    )
    VALUES(?,?,?,?,?,?)
    '''
    cur = self.db.cursor()
    cur.executemany(sql, map(self.trade2tuple, trades))
    
    # Update our cached version of the newest trade we've seen
    self._latest_ts_exec_cache[exchange_id] = max(map(attrgetter('ts_exec'), trades))
  
    
  # Select rows with fields in the following order then feed them straight into
  # _HistTradesRow2Trade() to get a Trade object out.
  ALL_TRADE_FIELDS = "trade_id, ts_exec, ts_update, CAST(price AS TEXT), CAST(volume AS TEXT)"
  def _HistTradesRow2Trade(self, row, exchange_id):
    return Trade(
      exchange_id = exchange_id,
      price       = D(row[3]),
      volume      = D(row[4]),
      ts_exec     = int(row[1]),
      ts_update   = float(row[2]),
      trade_id    = int(row[0])
    )
  
  @staticmethod
  def trade2tuple(t):
    "Turn a single trade into a tuple suitable for storage"
    return (
      t.exchange_id, t.trade_id, t.ts_exec, t.ts_update,
      str(t.price), str(t.volume)
    )
