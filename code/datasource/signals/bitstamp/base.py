#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from datasource.signals.base import DataSourceBitcoinExchange


class DataSourceBitStampBase(DataSourceBitcoinExchange):
  
  BROKER_CHANNEL   = 'exchange:bitstamp'
  EXCHANGE_ID      = 1




