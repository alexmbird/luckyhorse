#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import apsw
from operator import itemgetter
import pickle


DEFAULT_DAY_TS		= 1388707200
LOAD_PERIOD			= 60*5


def loadChunkedFromDB(exch_id=1, period=LOAD_PERIOD, daystart=DEFAULT_DAY_TS):
	
	db = apsw.Connection('db/ws.db')
	db.setbusytimeout(60 * 1000)				# 1 min
	
	# sql = '''
	# SELECT ROUND(ts_exec/60,0) AS min_num, AVG(price)
	# FROM HistTrades WHERE ts_exec BETWEEN 1388620800 AND 1388707200
	# GROUP BY min_num
	# ORDER BY ts_exec ASC
	# '''
	
	sql = '''
	SELECT AVG(price)
	FROM HistTrades WHERE
		exchange_id=? AND
		ts_exec BETWEEN ? AND ?
	'''
	
	cur = db.cursor()
	
	def load(ts):
		print("Loading %d+%d" % (ts, period))
		cur.execute(sql, (exch_id, ts, ts+period))
		row = cur.fetchone()
		return row[0] if row is not None else None
	
	return [	load(ts) for ts in range(daystart, daystart+86400, period)]



def loadTradesFromDB(exch_id=1, start_ts=DEFAULT_DAY_TS, seconds=86400):

	db = apsw.Connection('db/ws.db')
	db.setbusytimeout(60 * 1000)				# 1 min

	sql = '''
	SELECT ts_exec, price
	FROM HistTrades
	WHERE
	  exchange_id=? AND
	  ts_exec BETWEEN ? AND ?
	ORDER BY ts_exec ASC
	'''

	cur = db.cursor()
	cur.execute(sql, (exch_id, start_ts, start_ts+seconds))
	return list(cur.fetchall())



def loadDataFile(outfile='test_5m.pickle'):
	with open(outfile, 'rb') as fp:
		return pickle.load(fp)



def makeDataFile(outfile='test_5m.pickle'):
	data = list(loadChunkedFromDB())
	with open(outfile, 'wb') as fp:
		pickle.dump(data, fp)
	n_total		= len(data)
	n_real 		= len(list(filter(None, data)))
	n_blank 		= n_total - n_real
	print("Saved %s with %d datapoints.  %d real, %d blank." % (
		outfile, n_total, n_real, n_blank))



if __name__ == '__main__':
	makeDataFile(outfile='test_5m.pickle')
