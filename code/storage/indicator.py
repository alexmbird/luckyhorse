#!/usr/bin/env python3
# -*- coding: utf-8 -*-




# Ugly test hack
if __name__ == '__main__':
  import sys
  sys.path.append('./')
  sys.path.append('code/')


from operator import itemgetter

import apsw
from storage._base import BaseStore
from storage._base import RecordNotExistError, RecordAlreadyExistError

from events import Order, OrderBid, OrderAsk

from decimal import Decimal as D

from utils.time.period import FixedPeriodBase




class IndicatorStore(BaseStore):
  
  '''
  Store & retrieve indicator values 
  '''
  
  # Persist and load indicator data.  Note the `start_ts` - this refers to the
  # START of the time window this indicator handles.
  
  CREATE_SQL  = {
  
    'sqlite':    '''
CREATE TABLE HistIndicatorValues (
  exchange_id     TINYINT NOT NULL,
  indicator_id    TINYINT NOT NULL,
  start_ts        NUMERIC NOT NULL,
  period          NUMERIC NOT NULL,
  field_num       TINYINT NOT NULL,
  value           NUMERIC,
  PRIMARY KEY     (exchange_id, indicator_id, start_ts, period, field_num)
);
    '''.strip(),
    
    'mysql':      '''
    
    '''.strip()
    
  }
  
  
  def __init__(self, dbconf=None):
    super(IndicatorStore,self).__init__(dbconf=dbconf)
    
  
  def store(self, exchange_id, indicator_id, period, values):
    "Persist an indicator sample to the database"
    if not isinstance(period, FixedPeriodBase):
      raise TypeError("period must be a child of FixedPeriodBase")
    if not isinstance(values, tuple):
      raise TypeError("store() takes a tuple of values")
    # OR REPLACE
    sql = '''
    INSERT INTO HistIndicatorValues(
      exchange_id, indicator_id, start_ts, period, field_num, value
    )
    VALUES(?,?,?,?,?,?)
    '''
    def v2r(i, v):
      return (
        exchange_id, indicator_id, period.lhs_ts,
        period.PERIOD_SEC, i, v
      )
    rows = [v2r(i,v) for i,v in enumerate(values)]
    cur = self.db.cursor()
    cur.executemany(sql, rows)
    # for r in rows:
    #   try:
    #     cur.execute(sql, r)
    #   except apsw.ConstraintError:
    #     print("Error in row %s" % (r,))
    #     raise
    #   else:
    #     print("stored: %s" % (r,))
  
  
  
  def load(self, exchange_id, indicator_id, period):
    '''
    Load a tuple representing an indicator's values for a given period, or raise
    RecordNotExistError() if none is stored.
    '''
    if not isinstance(period, FixedPeriodBase):
      raise TypeError("period must be a child of FixedPeriodBase")

    sql = '''
    SELECT value FROM HistIndicatorValues
    WHERE exchange_id=? AND indicator_id=? AND start_ts=? AND period=?
    ORDER BY field_num ASC
    '''
    qvals = (exchange_id, indicator_id, period.lhs_ts, period.PERIOD_SEC)
    cur = self.db.cursor()
    cur.execute(sql, qvals)
    result  = cur.fetchall()
    value   = tuple(float(v[0]) for v in result)
    if not len(value):
      # print("absent: %s" % (qvals,))
      raise RecordNotExistError()
    # print("loaded: %s" % (qvals,))
    return value
  
    
