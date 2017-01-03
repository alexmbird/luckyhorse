#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import configparser



# Default values, overridden when a config file is read
CONFIG_DEFAULTS    = """

[database]
type        = sqlite
filename    = ./db/ws.db


[bitstamp]
username    = mocky
api_key     = xxxxyz
secret      = 1233495234578923465896

"""


CONFIG = configparser.ConfigParser()


# Seemingly a dict of dicts won't work for default config so we'll have it all
# long-form instead.
CONFIG.read_string(CONFIG_DEFAULTS)


