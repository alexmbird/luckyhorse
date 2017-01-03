#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os.path
import io
import gzip, bz2
import threading

from events import Order, Trade




class DataSourceBase(threading.Thread):
  
  # Label for the channel to which our events will be published
  BROKER_CHANNEL   = None
  
  # Unique ID for this source, used to store orders & trades in the DB.  Must
  # match EXCHANGE_ID of exchanges.* objects.
  EXCHANGE_ID      = None
  
  
  def __init__(self, broker):
    super(DataSourceBase,self).__init__()
    
    # Sources are stateless so can be reaped immediately
    self.daemon   = True
    
    # All datasources will publish to a Backplane channel
    self.broker   = broker
    if self.BROKER_CHANNEL is None:
      raise NotImplementedError("You need to override BROKER_CHANNEL for this datasource")
    else:
      self.channel = broker[self.BROKER_CHANNEL]
  
  
  def getStartTs(self):
    '''
    Return the time of events this source is producing.
    
    + For live sources this will be None, meaning "use the present time".  THis
      can be fed straight into HORSEYTIEM.override().
    + For historical sources with a specified start time, return that time.
    + For historical sources with no specified start time, peek at first event.
    '''
    return None
    



  
class DataSourceBitcoinExchange(DataSourceBase):
  "Any datasource that is a bitcoin exchange you can trade on"
  
  def __init__(self, broker):
    super(DataSourceBitcoinExchange,self).__init__(broker)



class DataSourceFileReader(object):

  "MixIn to support reading from files"

  def _openFile(self, filename):
    "Open a file appropriately and return a file handle"
    if not os.path.exists(filename):
      raise ValueError("No such file %s" % filename)

    if filename.lower().endswith('.gz'):
      self._fp = io.TextIOWrapper(gzip.GzipFile(filename, 'r'))
    elif filename.lower().endswith('.bz2'):
      self._fp = io.TextIOWrapper(bz2.BZ2File(filename, 'r'))
    else:
      self._fp = open(filename, 'rt')


class DataSourceCSVReader(DataSourceFileReader):
  
  "MixIn to support reading CSV's"
  
  def _openCsv(self, filename):
    "Open a CSV and return a csv.Reader object"
    self._openFile(filename)
    return csv.reader(self._fp)


