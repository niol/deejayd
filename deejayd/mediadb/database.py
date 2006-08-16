"""
 Class and methods to manage database
"""

from deejayd.ui.config import DeejaydConfig
from os import path

class databaseExeption:
    pass

class UnknownDatabase:

    def __init__(self):
        pass

    def _initialise(self):
        pass

    def connect(self):
        pass

    def execute(self,cur,query,parm = None):
        pass

    def close(self):
        pass


class sqliteDatabase(UnknownDatabase):

    def _initialise(self):
        # creation of tables
        self.execute("CREATE TABLE {library}(dir TEXT,filename TEXT,type TEXT,title TEXT,artist TEXT,album TEXT,\
            genre TEXT, tracknumber INT, date TEXT, length INT, bitrate INT, PRIMARY KEY (dir,filename))")
        self.execute("CREATE TABLE {radio}(name TEXT,url1 TEXT, url2 TEXT, url3 TEXT,PRIMARY KEY (name))")
        self.execute("CREATE TABLE {stat}(name TEXT,value INT,PRIMARY KEY (name))")

        self.execute("INSERT INTO {stat}(name,value)VALUES('last_updatedb_time',0)")
        self.connection.commit()

    def connect(self):
        from pysqlite2 import dbapi2 as sqlite
        db_file = DeejaydConfig().get("mediadb","db_file")
        init = path.isfile(db_file) and (0,) or (1,)
        try:
            self.connection = sqlite.connect(db_file)
            self.cursor = self.connection.cursor() 
        except :
            sys.exit("Unable to connect at the sqlite database. Verify your config file.")
        if init[0]:
            self._initialise()

    def execute(self,query,parm = None):
        try:
            prefix = DeejaydConfig().get("mediadb","db_prefix") + "_"
        except:
            prefix = ""

        query = query.replace("{",prefix).replace("}","") 
        if parm == None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query,parm)

    def close(self):
        self.cursor.close()
        self.connection.close()

# vim: ts=4 sw=4 expandtab
