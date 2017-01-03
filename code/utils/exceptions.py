#!/usr/bin/env python3
# -*- coding: utf-8 -*-



'''
A collection of exceptions used throughout the application
'''


class DataError(Exception):
	pass


class InsufficientDataError(DataError):
	"Not enough data to calculate for the requested period"



