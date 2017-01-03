#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from data import loadTradesFromDB

import numpy as np
import time
from operator import itemgetter
from collections import defaultdict
import csv


# 1st Jan 2014		1388534400
# 1st Oct 2014		1412121600
START_TS 			=	1388534400
STOP_TS				= 1417392000



wday_stdevs		= defaultdict(list)


period = 60*60

for ts in range(START_TS, STOP_TS, period):
	
	wday				= time.gmtime(ts)[6]		# hour is 3, weekday is 6
	trades 		= loadTradesFromDB(start_ts=ts, seconds=period)
	prices			= np.fromiter(map(itemgetter(1), trades), float)
	
	if len(prices):
		avg		= np.average(prices)
		std		= np.std(prices)
		wday_stdevs[wday].append( std / avg )
	

with open('hour_std.csv', 'w') as fp:
	out = csv.DictWriter(
		fp,
		fieldnames = ['wday', 'stdev']
	)
	
	for wday, stdevs in wday_stdevs.items():
		row = {'wday':wday, 'stdev':np.average(stdevs)}
		out.writerow(row)

