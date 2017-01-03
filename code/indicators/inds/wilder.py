#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.time.period import FixedPeriod_1Day
from utils.hmath import exponentialMovingAverage, exponentialSmooth

from indicators.inds._base import IndicatorBase
from utils.exceptions import InsufficientDataError

import indicators.inds.simple as i_simple

from storage import RecordNotExistError



class BaseDM(IndicatorBase):
  PERIOD_TYPE     = FixedPeriod_1Day
  REQD_INDICATORS = {
    'min_1d':     (i_simple.MinTradePrice,),
    'max_1d':     (i_simple.MaxTradePrice,),
  }
  
  def _upMove(self, period):
    # UpMove = today's high − yesterday's high
    max_today   = self.indicators['max_1d'].hist(period)[0]
    max_yest    = self.indicators['max_1d'].hist(period-1)[0]
    return max_today - max_yest
  
  def _dnMove(self, period):
    # DownMove = yesterday's low − today's low
    min_today   = self.indicators['min_1d'].hist(period)[0]
    min_yest    = self.indicators['min_1d'].hist(period-1)[0]
    return min_yest - min_today

class PosDM_1Day(BaseDM):
  INDICATOR_ID    = 100
  def _calculate(self, period):
    #if UpMove > DownMove and UpMove > 0, then +DM = UpMove, else +DM = 0
    um = self._upMove(period)
    dm = self._dnMove(period)
    v = um if um > dm and um > 0 else 0
    return (v,)

class NegDM_1Day(BaseDM):
  INDICATOR_ID    = 150
  def _calculate(self, period):
    # if DownMove > UpMove and DownMove > 0, then −DM = DownMove, else −DM = 0
    um = self._upMove(period)
    dm = self._dnMove(period)
    v = dm if dm > um and dm > 0 else 0
    return (v,)

class TrueRange_1Day(IndicatorBase):
  INDICATOR_ID    = 201
  PERIOD_TYPE     = FixedPeriod_1Day
  REQD_INDICATORS = {
    'min_1d':     (i_simple.MinTradePrice,),
    'max_1d':     (i_simple.MaxTradePrice,),
    'close_1d':   (i_simple.CloseTradePrice_1Day,),
  }
  def _calculate(self, period):
    # The range of a day's trading is simply \mbox{high} - \mbox{low}. The true
    # range extends it to yesterday's closing price if it was outside of today's
    # range.
    # This is irrelevant given Bitcoin trades 24x7; yesterday's close is only
    # out of range by a few seconds so won't be that different.  I'll implement
    # it anyway for completeness.
    day_max = self.indicators['min_1d'].hist(period)[0]
    day_min = self.indicators['max_1d'].hist(period)[0]
    yest_close  = self.indicators['close_1d'].hist(period-1)[0]
    v = max([
      day_max - day_min,
      abs(day_max - yest_close),
      abs(day_min - yest_close)
    ])
    return (v,)


class BaseDI(IndicatorBase):
  REQD_INDICATORS = {
    'truerange_1d':   (TrueRange_1Day,),
  }
   
class PosDI_1Day(BaseDI):
  "Labeled _1Day because it's calculated daily - but includes 14 days hist"
  INDICATOR_ID    = 221
  PERIOD_TYPE     = FixedPeriod_1Day
  REQD_INDICATORS = {
    'posdm_1d':       (PosDM_1Day,),
  }
  def _calculate(self, period):
    try:
      pdm_14  = [self.indicators['posdm_1d'].hist(period-n)[0] for n in range(0,14)]
      tr_14   = [self.indicators['truerange_1d'].hist(period-n)[0] for n in range(0,14)]
    except RecordNotExistError:
      raise InsufficientDataError()
    pdm_14_smoothed   = exponentialSmooth(pdm_14)
    tr_14_smoothed    = exponentialSmooth(tr_14)
    v = (100*pdm_14_smoothed) / tr_14_smoothed
    return (v,)

class NegDI_1Day(BaseDI):
  "Labeled _1Day because it's calculated daily - but includes 14 days hist"
  INDICATOR_ID    = 231
  PERIOD_TYPE     = FixedPeriod_1Day
  REQD_INDICATORS = {
    'negdm_1d':       (NegDM_1Day,),
  }
  def _calculate(self, period):
    try:
      ndm_14  = [self.indicators['negdm_1d'].hist(period-n)[0] for n in range(0,14)]
      tr_14   = [self.indicators['truerange_1d'].hist(period-n)[0] for n in range(0,14)]
    except RecordNotExistError:
      raise InsufficientDataError()
    ndm_14_smoothed = exponentialSmooth(ndm_14)
    tr_14_smoothed  = exponentialSmooth(tr_14)
    v = (100*ndm_14_smoothed) / tr_14_smoothed
    return (v,)

class ADX_1Day(IndicatorBase):
  INDICATOR_ID    = 241
  PERIOD_TYPE     = FixedPeriod_1Day
  REQD_INDICATORS = {
    'posdi_1d':   (PosDI_1Day,),
    'negdi_1d':   (NegDI_1Day,),
  }
  def _calculate(self, period):
    # ADX = 100 times the exponential moving average of the absolute value of
    # (+DI − −DI) divided by (+DI + −DI)
    try:
      pdi_14 = [self.indicators['posdi_1d'].hist(period-n)[0] for n in range(0,14)]
      ndi_14 = [self.indicators['negdi_1d'].hist(period-n)[0] for n in range(0,14)]
    except RecordNotExistError:
      raise InsufficientDataError()
    
    temp = [abs(pdi_14[i]-ndi_14[i]) / (pdi_14[i]+ndi_14[i]) for i in range(0,14)]
    v = 100 * exponentialSmooth(temp)
    return (v,)
