#!/usr/bin/env python3
# -*- coding: utf-8 -*-




import time, datetime



# Set some useful constants
EPOCH             = datetime.datetime.utcfromtimestamp(0)
SEC_IN_ONE_DAY    = 60 * 60 * 24

# Helper functions
def to_epoch_timestamp(dt):
	if not isinstance(dt, datetime.datetime):
		raise TypeError("Only works with datetime.datetime objects")

	return (dt-EPOCH).total_seconds()


def timestamp_to_printable(ts):
	'''
	Format a timestamp with DT_FORMAT_ISO_WITHOUT_MS_LITTLE_T, or simply as the
	string '-' if it was None.
	'''
	if ts is None:
		return '-'
	else:
		tstruct = time.gmtime(ts)
		return time.strftime(DT_FORMAT_ISO_WITHOUT_MS_LITTLE_T, tstruct)


# Some nice formatting constants

# e.g. 2014-10-25T22:20:09  Precisely 19 chars wide.
DT_FORMAT_ISO_WITHOUT_MS            = "%FT%T"

# e.g. 2014-10-25t22:20:09  Precisely 19 chars wide.
DT_FORMAT_ISO_WITHOUT_MS_LITTLE_T   = "%Ft%T"





