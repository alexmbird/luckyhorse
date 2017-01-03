#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dateutil.parser import parse as date_parse
from utils.time.tools import to_epoch_timestamp as dt2epock

from utils.time import HORSEYTIEM
from utils.hmath import round_dec_down_to_n_places

from decimal import Decimal as D

from datasource.signals.base import DataSourceCSVReader
from datasource.signals.bitstamp.base import DataSourceBitStampBase

from events import Trade


class DataSourceBitStampFile(DataSourceBitStampBase, DataSourceCSVReader):
  
  '''
  Ingest data from CSV files of BitStamp trades.  These come from
  http://api.bitcoincharts.com/v1/csv/
  '''
  
  
  def __init__(self, broker, filename='assets/bitstampUSD.csv.gz', start=None, stop=None):
    super(DataSourceBitStampFile,self).__init__(broker)
    
    # Are we fetching the lot of just a window out of it?
    self._ts_start = dt2epock(date_parse(start)) if start is not None else None
    self._ts_stop  = dt2epock(date_parse(stop))  if stop  is not None else None
    
    self._csv = self._openCsv(filename)
    self._fake_trade_id   = 0
    
    # Add an always-incrementing number of msec on to each integer ts_exec to
    # make a ts_update.  This means no trades have identical ts_updates, which
    # raises merry hell in the algorithms.
    self._last_exec_ts    = None
    self._fake_msec       = None
    
    # Peek ahead at the first entry to get the start timestamp
    if self._ts_start is None:
      row = next(self._csv)
      self._ts_start  = self._makeTradeFromRow(row).ts_update
      self._fp.seek(0)
    
  
  def getStartTs(self):
    "Return the timestamp at which this datasource is starting"
    return self._ts_start
  
  
  def _makeTradeFromRow(self, row):
    '''
    Turn a row from the CSV file into a Trade object.  Since the CSV does not
    have as much data as we would like we have to make sensible guesses.  In
    particular we don't have real trade ID's, so fake our own with incrementing
    numbers.  At least they go up.
    '''
    
    ts_exec = int(row[0])   # Only do the conversion once
  
    # Fake a few fields.  See above notes on self._fake_msec
    if self._last_exec_ts != ts_exec:
      self._fake_msec = 0
      self._last_exec_ts = ts_exec
    
    self._fake_trade_id     += 1
    self._fake_msec         += 0.0000001
    
    return Trade(
      exchange_id = self.EXCHANGE_ID,
      price       = round_dec_down_to_n_places(D(row[1]), 2),
      volume      = round_dec_down_to_n_places(D(row[2]), 8),
      ts_exec     = ts_exec,
      ts_update   = ts_exec + self._fake_msec,
      trade_id    = self._fake_trade_id
    )
  
  
  def fetch(self, ts_start=None, ts_end=None):
    "Yield trades"
    self._fp.seek(0)
    for row in self._csv:
      ts_exec = int(row[0])
      if self._ts_start and ts_exec < self._ts_start:
        continue
      if self._ts_stop and self._ts_exec > ts_stop:
        break   # Assuming entries are in order
      # Turn into a trade and publish
      try:
        yield self._makeTradeFromRow(row)
      except ValueError:
        pass        # Some trades in the dump file have wtfnegative volumes
  
    
  def run(self, limit=None):
    
    n_published = 0
    
    for row in self._csv:
      
      # Check this is in-range, if we are limiting by window
      ts_exec = int(row[0])
      if ts_exec < self._ts_start:
        continue
      if self._ts_stop is not None and ts_exec > self._ts_stop:
        break   # Assuming entries are in order
      
      # Turn into a trade and publish
      try:
        t = self._makeTradeFromRow(row)
      except ValueError:
        pass        # Some trades in the dump file have wtfnegative volumes
      else:
        self.broker.publish(self.channel, t)
        n_published += 1
        if limit is not None and n_published >= limit:
          break

  
