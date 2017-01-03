#!/usr/bin/env python3
# -*- coding: utf-8 -*-





#
# THREAD TO WATCH A WEBSOCKETS CONNECTION AND RUN AN ARBITRARY HANDLER WHEN DATA
# COMES THROUGH.
#

import threading
from pypusher.socket import PusherSocket
import websocket

from events import Trade, Order

from utils.time import HORSEYTIEM



class PusherSocketThread(threading.Thread):

  '''
  A thin wrapper around the PusherSocket library that runs the connection in its
  own thread.  Handlers will call back to the main code WHICH MUST BE THREADSAFE
  '''
  
  # How long we will pause between reconnection attempts
  RECONNECT_DELAY_SEC      = 10
  
  
  def __init__(self, key):

    super(PusherSocketThread, self).__init__()

    self.daemon     = True

    self.key        = key

    self.sock = PusherSocket(key, { 'encrypted': True } )
  
  
  def subscribe(self, channel):
    self.sock.subscribe(channel)


  def bind(self, channel, event, handler):
    self.sock[channel].bind(event, handler)


  def run(self):
    '''
    Connect to WebSockets endpoint and deliver events through the relevant
    callbacks.
    '''
    while True:
      try:
        self.sock.connect()
      except (TypeError, websocket.WebSocketConnectionClosedException):
        print("Lost connection to the exchange.  Will reconnect in %d seconds" % (self.RECONNECT_DELAY_SEC,))
        HORSEYTIEM.sleep(self.RECONNECT_DELAY_SEC)








