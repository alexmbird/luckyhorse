#!/usr/bin/env python3
# -*- coding: utf-8 -*-





#  SELECT ROUND(ts_exec/60,0) AS min_num, AVG(price) FROM HistTrades WHERE ts_exec BETWEEN 1388534400 AND 1388620800  GROUP BY min_num ORDER BY ts_exec ASC;


import sys
import numpy as np
import sklearn

import csv
import pickle



with open('train.pickle', 'rb') as fp:
	X = pickle.load(fp)

from scipy.fftpack import rfft, irfft, fftfreq

time   	= np.linspace(0,86400,len(X))
time2  	= np.linspace(0,86400*2,len(X)*2)
signal 	= np.array(X)

# W = fftfreq(signal.size, d=time[1]-time[0])
W = fftfreq(signal.size)
f_signal = rfft(signal)

# If our original signal time was in seconds, this is now in Hz    
cut_f_signal = f_signal.copy()

# cut_f_signal[(W<6)] = 0
print("Init bands: %s" % len(list(filter(None, cut_f_signal))))
cut_f_signal[20:]		= 0
print("Remaining bands: %s" % len(list(filter(None, cut_f_signal))))
print("Max band: %.2f" % max(cut_f_signal))
print("Min band: %.2f" % min(cut_f_signal))
cut_signal = irfft(cut_f_signal)
print("Cut is %s" % cut_signal) 

import pylab as plt
plt.subplot(221)
plt.plot(time,signal)
plt.subplot(222)
plt.plot(W,f_signal)
plt.xlim(0,10)
plt.subplot(223)
plt.plot(W,cut_f_signal)
plt.xlim(0,10)
plt.subplot(224)
# longer_signal	= np.zeros(len(time)*2)
# longer_signal[:1083] = cut_signal
# longer_signal[1083:] = cut_signal
# print(len(cut_signal))
# print(len(longer_signal))
# print(len(time2))
plt.plot(time,cut_signal)
# plt.plot(time2,longer_signal)
plt.show()


# 
# dw = csv.DictWriter(
#   open('fft.csv', 'w'),
#   ['timestamp', 'price_real', 'price_predict']
# )
# 
# for i, price in enumerate(series):
#   dw.writerow({'timestamp':60*5*i, 'price_real':price})
# 
# for i, price in enumerate(series_fft):
#   dw.writerow({'timestamp':60*5*i, 'price_predict':price})

