#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os.path
import csv

from itertools import islice
from collections import deque
from decimal import Decimal as D
import numpy as np

from utils.monkeyseq import MonkeySequence

from utils.time import HORSEYTIEM

from utils.hmath import round_dec_down_to_n_places as rd2n
from utils.hmath import weighted_avg_and_std, CumulativeWeightedMean

from bots.positions import SimplePosition


class SfBotHandler(object):
  
  '''
  Base class for an MonkeyTreeBot event handler.
  '''
  
  CSV_FIELDS = (
    'timestamp',
    'trade_price',
    'I_bought_at',
    'I_sold_at',
    'wmetric'
  )
  
  def __init__(self, myvars, stats, exchange, indicators):
    self.vars         = myvars
    self.stats        = stats
    self.exch         = exchange
    self.indicators   = indicators
    
    csv_fp = open(self.vars['output_stats_csv'], 'w')
    self._csv = csv.DictWriter(csv_fp, self.CSV_FIELDS)

  
  def _csvlog(self, d):
    "Log a dict of values to the csv file with timestamp added"
    if not self.CSV_FIELDS:
      raise RuntimeError("You can't use _csvlog in a bot without CSV logging")
    d['timestamp'] = HORSEYTIEM.time()
    self._csv.writerow(d)


  def handleBucketUpdate(self, ind, t):
    pass
  
  def handleTrade(self, t):
    pass
  
  def shutdown(self):
    pass
  
  def _print(self, s):
    "Print a string, formatted with the current time"
    print("%s %s" % (HORSEYTIEM.printable(), s))




    
class SfBotHandlerAnalyze(SfBotHandler):
  '''
  Consider all trades and print some data on them
  '''
  def __init__(self, *args, **kwargs):
    super(SfBotHandlerAnalyze,self).__init__(*args, **kwargs)
    self._analysis_metrics    = []
    self._trade_intervals     = []
    self._trade_prices        = []
    self._trade_volumes       = []
    self._last_trade_ts       = None

  
  def handleTrade(self, t):
    self._trade_prices.append(float(t.price))
    self._trade_volumes.append(float(t.volume))
    if self._last_trade_ts is not None:
      self._trade_intervals.append( t.ts_exec - self._last_trade_ts )
    self._last_trade_ts = t.ts_exec
  
  
  def handleBucketUpdate(self, ind, t):
    try:
      w = self.fwm['bucket_window']
      raw_metric = ind.value()
      self._analysis_metrics.append(raw_metric)
    except ValueError:
      pass

  
  def shutdown(self):
    self.printAnalysisStats()


  def printAnalysisStats(self):
    print("Analysis of %d metric datapoints" % len(self._analysis_metrics))
    trade_mean, trade_std = weighted_avg_and_std(self._trade_prices, self._trade_volumes)
    print("Weighted mean trade price: %.2f" % trade_mean)
    print("Weighted STD trade price: %.2f" % trade_std)
    
    mean  = np.average(list(map(abs, self._analysis_metrics)))
    print("Metric mean of abs: %s" % mean)
    std   = np.std(self._analysis_metrics)
    print("Metric standard deviation: %f" % std)
    n_sigma = 2
    faktor = 5 / (n_sigma * std)
    print("Best quantization factor: %f" % faktor)
    
    mean, sd = weighted_avg_and_std(self._trade_intervals)
    print("Mean gap between trades: %.2fs" % mean)
    print("SD of trade gaps: %.2fs" % sd)

  




class SfBotHandlerTrain(SfBotHandler):
  
  def __init__(self, *args, **kwargs):
    super(SfBotHandlerTrain,self).__init__(*args, **kwargs)
    self.mseq = MonkeySequence()
    

  def handleBucketUpdate(self, ind, t):
    # metric = self._pimpMyMetric(w)
    metric = ind.value()
    self.mseq.append(metric)


  def shutdown(self):
    # Persist the probabiity tree to disk
    self.mseq.save(self.vars['match_tree_file'])
    self.printTrainingStats()


  def printTrainingStats(self):
    # Print coverage figures for the probability space
    print("Trained; %d metrics in history" % len(self.mseq))





class SfBotHandlerTrade(SfBotHandler):

  def __init__(self, *args, **kwargs):
    super(SfBotHandlerTrade,self).__init__(*args, **kwargs)
    self.mseq         = MonkeySequence.load(self.vars['match_tree_file'])
    self._position    = None
    self._window_hist = deque(maxlen=self.vars['match_buckets'])

  
  def handleTrade(self, t):
    '''
    A trade came in.  We won't trigger trade opens from this but it might cause
    us to close one.
    '''
    
    # All trades go in the csv for graphing
    self._csvlog({'trade_price':t.price})

    if self._position:
      if t.price <= self._position.cost_stop:
        self._closePosition(t, "failed")
        self.stats['position_fail'] += 1
      elif t.price >= self._position.cost_target:
        if self.indicators['grad_5m'].value() < 0:
          self._closePosition(t, "win")
          self.stats['position_win'] += 1

  
  def _priceAfterWindows(self, price, window_grads, w_len_sec):
    '''
    Where will the price be after a sequence of window-gradients?
    
    `price`         - starting price
    `window_grads`  - gradient for each window, in currency/sec
    `w_len_sec`     - seconds length of each window
    '''
    
    price = float(price)
    for g in window_grads:
      price += price * g * w_len_sec
    return price
  
  
  def handleBucketUpdate(self, ind, t):
    "A new prediction should be available.  Shall we trade?"
    metric = ind.value()
    self._csvlog({'wmetric':metric})
    self._window_hist.append(metric)
    n_buckets = self._window_hist.maxlen
    
    # In position, irrelevant
    if self._position:
      return
    
    # Starting up, not enough history yet
    if len(self._window_hist) != n_buckets:
      return
    
    # Flat lines bring confusion
    if self._window_hist.count(0) == n_buckets:
      return
    
    # Just started to fall
    # if self.fwm['short_window'].linearRegressionGradient() < 0.0001:
    #   return

    # Okay, we can play!
    match = self.mseq.match(self._window_hist)
    if match:
      #b2p = self.vars['buckets_to_profit']
      # target_price = t.price + (t.price * D(self.vars['profit_margin']))
      # future_price = self._priceAfterWindows(
      #   t.price, match.following(int(self.vars['buckets_to_profit'])),
      #   self.vars['match_window_len_sec']
      # )
      # if future_price >= float(target_price):
      #   self._openPosition(t, reason='rising')
      match.dump()
      self._openPosition(t)
  
  
  def _openPosition(self, t, reason=''):
    "Open a position"
    funds_available = self.exch.balance.cash * D(0.99)
    cash_to_spend = D(0.5) * funds_available
    if cash_to_spend < 10:
      return
    volume = rd2n(cash_to_spend / t.price, 8)
    fee = self.exch.calculateFee(cash_to_spend)
    p_target  = t.price + (t.price * D(self.vars['profit_margin']))
    p_stop    = t.price - (t.price * D(self.vars['loss_margin']))
    self._position = SimplePosition(
      self.exch, volume, t.price, p_target, p_stop
    )
    self._print("%s" % self._position)
    self.exch.executeBid(volume, fallback=True)
    self._csvlog({'I_bought_at':t.price})
    self.stats['total_buys'] += 1
    self._print("BOUGHT @ %.2f\t%s\t%s" % (t.price, self.exch.balance, reason))
  
  
  def _closePosition(self, t, reason=''):
    "Close our position"
    self.exch.executeAsk(self._position.volume, fallback=True)
    self._position = None
    self._csvlog({'I_sold_at':t.price})
    self.stats['total_sells'] += 1
    self._print("SOLD @ %.2f\t%s\t%s" % (t.price, self.exch.balance, reason) )






class SfBotHandlerTest(SfBotHandler):
  
  def __init__(self, *args, **kwargs):
    super(SfBotHandlerTest,self).__init__(*args, **kwargs)
    self._loadTree()
    self._last_prediction   = None
    self._window_hist       = deque(maxlen=self.vars['match_buckets'])
  
  
  def handleBucketUpdate(self, ind, t):
    '''
    A bucket has ended.  Compare the last prediction to what actially happened.
    '''
    # Compare the prediction to reality
    if self._last_prediction is not None:
      metric = self._hist[-1]
      #print("%s\t%s" % (self._last_prediction, metric))
      if simplifyMet(self._last_prediction) == simplifyMet(metric):
        self.stats['predict_correct'] += 1
      else:
        self.stats['predict_wrong'] += 1
    
    s = deque( islice(self._hist, 1, None) )
    prediction = self.tree.predict(s, closest=True)
    self._last_prediction = prediction


  def shutdown(self):
    self.printTestStats()
  
  
  def printTestStats(self):
    # Add to stats a real percentage of success
    total_predictions = self.stats['predict_correct'] + self.stats['predict_wrong']
    pcp = (self.stats['predict_correct'] / total_predictions) * 100
    self.stats['predict_correct_%'] = "%.1f" % pcp


