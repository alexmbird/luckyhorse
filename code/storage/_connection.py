#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os




class DbConnectionFactory(object):
  

  def connect(self, dbopts):
    '''
    Return a connection to our database using the options from dict dbopts.
    Keys in this dict match those in our config file so you can dump the .ini
    file's [database] section straight in.
    '''
    
    DBTYPE_MAP = {
      'mysql':    None,
      'sqlite':   self._connectSqlite
    }

    funk = DBTYPE_MAP[dbopts['type']]
    return funk(dbopts)
  
  
  
  
  
  #
  # LOCAL SQLITE DATABASE.  Good for testing without the hassle of running a
  # MySQL instance.
  #
  
  SQLITE_APWS_BUSY_TIMEOUT_MS   = 60 * 1000   # 1m
  
  def _connectSqlite(self, dbopts):
    "Create a connection to a Sqlite database"
    import apsw
    f = dbopts['filename']
    if not os.path.isfile(f):
      raise FileNotFoundError("DB '%s' does not exist - look at the --initdb option" % f)
    
    db = apsw.Connection(f)
    db.setbusytimeout(self.SQLITE_APWS_BUSY_TIMEOUT_MS)
    return db
    




if __name__ == '__main__':
  
  opts = {
    'type':     'sqlite',
    'filename': '/tmp/wankstein_test.db'
  }
  
  fact = DbConnectionFactory()
  
  db = fact.connect(opts)
  
  print("Made a connection: %s" % db)
  
