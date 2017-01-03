#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest

from datasource.signals.bitstamp import DataSourceBitStampFile, DataSourceBitStampLive

from events import Trade, Order
from events.broker import QueuedBrokerBundle, ToyEventReceiver

import utils.logging    # which will shut the pusher log up





#
# Test individual sources
#



class TestBitStampFile(unittest.TestCase):
  
  CSV_FILE    = 'assets/bitstampUSD.csv.gz'
  
  def test_ReadCsvFile(self):
    "Read in a range of trades from a CSV file"
    b = QueuedBrokerBundle(maxsize=20)
    ds_bsf  = DataSourceBitStampFile(b, self.CSV_FILE)
    ec      = ToyEventReceiver()
    b[ds_bsf.BROKER_CHANNEL].subscribe(ec.rcv, 1)
    ds_bsf.run(limit=10)
    b.run(once=True)
    assert len(ec.events) > 0


class TestBitStampLive(unittest.TestCase):
  
  def test_ReadLiveStream(self):
    "Read ten entries from the live WebSockets stream"
    b = QueuedBrokerBundle(maxsize=20)
    ds_bsf  = DataSourceBitStampLive(b)
    ec      = ToyEventReceiver()
    b[ds_bsf.BROKER_CHANNEL].subscribe(ec.rcv, 1)
    ds_bsf.run(limit=10)
    b.run(once=True)
    assert len(ec.events) > 0

    
