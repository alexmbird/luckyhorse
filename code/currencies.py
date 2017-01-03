#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class CurrencyBase(object):
  
  NAME      = 'UNDEF'
  SYMBOL    = '?'
  ID        = None


class CurrencyBTC(object):

  NAME      = 'BITCOIN'
  SYMBOL    = 'B⃦'
  ID        = 0


class CurrencyUSD(CurrencyBase):
  
  NAME      = 'USD'
  SYMBOL    = '$'
  ID        = 1


class CurrencyEUR(CurrencyBase):
  
  NAME      = 'EUR'
  SYMBOL    = '€'
  ID        = 2

