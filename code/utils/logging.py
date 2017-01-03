#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging

from utils.time import HORSEYTIEM



# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter.formatTime = lambda rec, fmt: HORSEYTIEM.printable()
ch.setFormatter(formatter)



# === CREATE A LOGGER FOR EXCHANGE DATA ===
LOG_EXCH = logging.getLogger('exchange')
LOG_EXCH.setLevel(logging.DEBUG)
LOG_EXCH.addHandler(ch)
LOG_EXCH.propagate = False	# This stops everything appearing twice on the console


# === CREATE A LOGGER FOR INDICATORS ===
LOG_INDS = logging.getLogger('indicator')
LOG_INDS.setLevel(logging.INFO)
LOG_INDS.addHandler(ch)
LOG_INDS.propagate = False

# === CREATE A LOGGER FOR BOTS ===
LOG_BOTS		=	logging.getLogger('bots')
LOG_BOTS.setLevel(logging.INFO)
LOG_BOTS.addHandler(ch)
LOG_BOTS.propagate = False

# Make PusherSocket STFU
LOG_PUSHERSOCK = logging.getLogger('pypusher')
LOG_PUSHERSOCK.setLevel(logging.INFO)
LOG_PUSHERSOCK.addHandler(ch)
LOG_PUSHERSOCK.propagate = False
