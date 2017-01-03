#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Ugly test hack
if __name__ == '__main__':
  import sys
  sys.path.append('./')
  sys.path.append('code/')



from storage._base import BaseStore
from storage._base import RecordNotExistError, RecordAlreadyExistError

from events import Order, OrderBid, OrderAsk

import time
from decimal import Decimal as D


  
  
class OrderStore(BaseStore):
  
  
  # Some database notes...
  #
  # It is not practical to get a complete order history for an exchange.  But we
  # can get a point-in-time snapshot then use the WebSockets API to monitor
  # changes from that.  If we lose connectivity for a while and need to restart
  # our tailing of the exchange, how do we represent in the DB that history is
  # starting again from a new snapshot?  Answer: session_id.
  #
  # An order may be revised during its lifetime - typically because it has been
  # partially fulfilled.  Because of this we store revisions rather than 
  # distinct orders.  This is slightly inefficient (fields are duplicated) but
  # revisions are relatively uncommon and normalisation isn't worth the cost.
  # `revision_id` is the key to the table so the id's for revivions within an
  # order won't be sequential, but we can guarantee they'll always go up.
  CREATE_SQL    = {
  
    'sqlite':         '''

CREATE TABLE HistOrderRevisions (
  revision_id   INTEGER NOT NULL,
  order_id      INTEGER NOT NULL,
  order_type    INTEGER NOT NULL,
  order_state   TINYINT DEFAULT NULL,
  price         DECIMAL(10,2) NOT NULL,
  volume        DECIMAL(10,8) NOT NULL,
  ts_update     NUMERIC,
  ts_create     INTEGER,
  ts_delete     INTEGER,
  PRIMARY KEY   (revision_id ASC AUTOINCREMENT)
);
CREATE INDEX idx_HOR_ord_rev ON HistOrderRevisions (order_id, revision_id);
  '''.strip(),
  
    'mysql':          '''
    
    '''.strip()

  }  
  
  
  # DB (and BitStamp themselves) use integers to represent the type of an
  # order.  These map onto subclasses of Order.  With the array one can
  # easily turn classes to ID's with ORDER_TYPE_IDS.index(klass) and back again
  # with ORDER_TYPE_IDS[id].
  #
  # Another copy of this exists in the BitStamp NetAdapter class.
  #
  # THE ORDER OF THESE ELEMENTS IS CRUCIAL, DO NOT FUCK WITH THEM
  ORDER_TYPE_IDS    = [OrderBid, OrderAsk]


  def __init__(self, session_id=None, dbconf=None):
    "Setup storage for orders within a given session"
    # We can't collect orders when offline.  When we come back online again
    # we'll start a new session, representing a new 'thread' of history
    # beginning at a snapshot.  self.session_id is the ID of the session we are
    # presently recording.
    #
    # NB: this has no effect on methods that reconstruct an OrderBook from
    # history; those will locate and use the appropriate session_id.
    self.session_id    = session_id
    
    super(OrderStore,self).__init__(dbconf)
  
  
  def __str__(self):
    return "<%s exch:%s sid:%s>" % (
      self.__class__.__name__,
      self.session_id
    )
  
  
  def orderBookAtPoint(self, dt, ob_type):
    '''
    Try to reconstruct the order book for our exchange at a point in time
    described by 'dt'.  If possible return an OrderBook containing the data;
    otherwise return None.  We have many different kinds of orderbooks so it
    is necessary to specify the type you want returned with `ob_type`
    '''
    raise NotImplementedError()
  
  
  def _store(self, o):
    '''
    Store an Order.  This can be new, or a fresh revision of an existing one
    '''
    
    # Sqlite DB was created with 'not null' on ts_create field but we want to
    # use nulls to signify it wasn't a creation.  As a hack we store 0 instead
    # of null and will set all the 0's to NULLs when we fix the DB.
    ts_create_hack = 0 if o.ts_create is None else o.ts_create
    
    sql = '''
    BEGIN;
    INSERT INTO HistOrderRevisions (
      session_id, order_id, order_type, price, volume,
      ts_update, ts_create, ts_delete, order_state
    )
    VALUES(?,?,?,?,?,?,?,?,?);
    COMMIT;
    SELECT last_insert_rowid();
    '''
    
    db_type_id = self.ORDER_TYPE_IDS.index(type(o))
    
    # "Bad binding argument type supplied - argument #4: type decimal.Decimal"
    # oh fuck off we'll str() it again then
    cur = self.db.cursor()
    cur.execute(sql, (
      self.session_id, o.order_id, db_type_id,
      str(o.price), str(o.volume),
      time.time(), ts_create_hack, o.ts_delete, o.order_state
    ))
    revision_id   = cur.fetchone()[0]
    return revision_id
  
  
  def event(self, e):
    '''
    Modern event streaming framework.  We get a firehose of events from a 
    NetAdapter source.  It's down to us to identify and process them
    appropriately.
    
    A queue for store()s might not go amiss so as not to block the NetAdapter
    thread from communicating new Orders/Trades to the rest of the system.
    '''
    if isinstance(e, Order):
      self._store(e)
  
  
  def fetch(self, ts_start=None, ts_end=None):
    '''
    Retrieve this session's orders from storage.  Returns Order() objects.  An
    individual order may be returned more than once since they have a create-
    change-delete lifecycle.
    
    `ts_start`  - if set, limit to orders after this point
    `ts_end`    - if set, limit to orders before this point
    '''
    sql = [
      "SELECT %s FROM HistOrderRevisions" % self.ALL_ORDER_FIELDS,
      "WHERE session_id=?",
    ]
    qargs = [self.session_id,]
    if ts_start is not None:
      sql.append("AND ts_update >= ?")
      qargs.append(ts_start)
    if ts_end is not None:
      sql.append("AND ts_update <= ?")
      qargs.append(ts_end)
    sql.append("ORDER BY ts_update ASC")
    cur = self.db.cursor()
    cur.execute(' '.join(sql), qargs)
    for row in cur.fetchall():
      yield self._HistOrderRevisionsRow2Order(row)
  
    
  def getOrder(self, order_id, ts=None):
    '''
    Try to retrieve from the present session the state of order with id `id` at
    timestamp `ts`.
    '''
    
    # Explicit about columns because for sake of speed we're going to access row
    # fields by id, not name
    cur = self.db.cursor()
    if ts is None:
      sql = '''
        SELECT %s
        FROM HistOrderRevisions
        WHERE session_id = ? AND order_id = ?
        ORDER BY revision_id DESC
        LIMIT 1
      ''' % self.ALL_ORDER_FIELDS
      cur.execute(sql, (self.session_id, order_id))
    else:
      sql = '''
        SELECT %s
        FROM HistOrderRevisions
        WHERE session_id = ? AND order_id = ? AND ts_update <= ?
        ORDER BY revision_id DESC
        LIMIT 1
      ''' % self.ALL_ORDER_FIELDS
      cur.execute(sql, (self.session_id, order_id, ts))
    
    row = cur.fetchone()
    if row is None:
      raise RecordNotExistError("Order %s not known within session %s" % (order_id, self.session_id))
    if row[7] is not None:      # Catch deleted orders
      raise RecordNotExistError("Order with id %s was deleted at %s" % (order_id, row[7]))
    
    return self._HistOrderRevisionsRow2Order( row )
  
  
  # Used whenever we load orders; must match tuple elements below.  Why the
  # casting?  It's a shameful hack to stop Python turning our fixed-point
  # decimals into floats and causing all sorts of rounding errors.
  ALL_ORDER_FIELDS = '''
    revision_id, order_id, order_type,
    CAST(price AS TEXT), CAST(volume AS TEXT),
    ts_update, ts_create, ts_delete, order_state
  '''.strip()
  
  def _HistOrderRevisionsRow2Order(self, row):
    "Convert a row from the HistOrderRevisions table into an Order object"
    # Sqlite NB:
    # For conversions between TEXT and REAL storage classes, SQLite considers
    # the conversion to be lossless and reversible if the first 15 significant
    # decimal digits of the number are preserved.
    # ...but you do have to fuck around casting them to a str first.
    
    # HCAK HACK HACK - see _store() for why.  Plz fix me.
    ts_create_hack = None if row[6] == 0 else row[6]
    
    try:
      order_klass = self.ORDER_TYPE_IDS[row[2]]
      return order_klass(
        price       = D(str(row[3])),
        volume      = D(str(row[4])),
        ts_update   = row[5],
        ts_create   = ts_create_hack,
        ts_delete   = row[7],
        order_id    = int(row[1]) if row[1] else None,
        state       = row[8]
      )
    except Exception:
      print("%s" % (row,))
      raise
  

