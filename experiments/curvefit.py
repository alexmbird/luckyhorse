#!/usr/bin/env python3
# -*- coding: utf-8 -*-


'''
See http://stackoverflow.com/a/20824134/2401932
'''


import csv
from operator import itemgetter

import numpy as np
import numpy.ma as ma

import matplotlib.pyplot as plt
import scipy.optimize as optimize

import sys
sys.path.append('.')

from experiments.data import loadDataFile, loadTradesFromDB

def fit(x, a, b, c, d):
	return a*np.sin(b*x + c) + d

def fit_with_gradient(x, a, b, c, d, e):
	return (a*np.sin(b*x + c) + d) + (e*x)


FIT_FN			= fit
PERIOD			= 60*60*12
CUTOFF			= 10000
DAYSTART		= 1388707200 + 11500 + 13000

trades 		= loadTradesFromDB(daystart=DAYSTART, seconds=PERIOD)
trades 		= [(ts-DAYSTART, price) for ts, price in trades]

# Select the subset of trades we'll use for prediction
trades_w		= [(ts, price) for ts, price in trades if ts < CUTOFF]
xs, ys			= zip(*trades_w)

# A linearly increasing sigma; most recent trades get the most weight
s 					= np.fromiter(range(1, len(xs)+1), int)

# Find our curve fit
fitting_parameters, covariance = optimize.curve_fit(FIT_FN, xs, ys, p0=None, sigma=s)
print("Fitting params: %s" % (fitting_parameters,))


fig, ax = plt.subplots()
ax.grid()

# Plot the full line
full_xs, full_ys 	= zip(*trades)
ax.plot(full_xs, full_ys)

# Then in a different colour plot the section we actually used for the curve fit
ax.plot(xs, ys)

# Plot the sine wave
sample_xs 	= np.linspace(0, PERIOD, PERIOD/1000)
sample_ys	= FIT_FN(sample_xs, *fitting_parameters)

ax.plot(sample_xs, sample_ys)



# plt.xlim(xs.min(), xs.max())
plt.show()
