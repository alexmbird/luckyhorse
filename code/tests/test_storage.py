#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest
import os
import apsw
import time

from utils.time.period import FixedPeriod_1Day

from storage import RecordNotExistError
from storage import IndicatorStore



DBCONF = {
  'type':     'sqlite',
  'filename': '/tmp/ws_test.db'
}

FAKE_EXCH_ID    = 0
FAKE_IND_ID     = 0


class TestStoreUtils(object):
  
  def createTestDb(self):
    db = apsw.Connection(DBCONF['filename'])
    c = db.cursor()
    c.execute(IndicatorStore.CREATE_SQL['sqlite'])
    db.close()
  
  
  def removeTestDb(self):
    try:  
      os.unlink(DBCONF['filename'])
    except FileNotFoundError:
      pass

    


class TestIndicatorStore(unittest.TestCase, TestStoreUtils):

  def setUp(self):
    self.removeTestDb()
    self.createTestDb()
    
  def tearDown(self):
    self.removeTestDb()
  
  
  def test_store_load(self):
    "Store a value then load it"
    istore = IndicatorStore(dbconf=DBCONF)
    p = FixedPeriod_1Day(1000000)
    istore.store(FAKE_EXCH_ID, FAKE_IND_ID, p, 999.999)
    v = istore.load(FAKE_EXCH_ID, FAKE_IND_ID, p)
    self.assertEqual(v, 999.999)
    with self.assertRaises(RecordNotExistError):
      v = istore.load(FAKE_EXCH_ID, FAKE_IND_ID, p+10)
  
  
