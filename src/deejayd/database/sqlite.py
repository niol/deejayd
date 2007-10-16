# sqlite.py

from deejayd.ui import log
from deejayd.database.database import Database
from pysqlite2 import dbapi2 as sqlite
from os import path
import sys

def str_encode(data):
    """Convert a basestring to a valid UTF-8 str."""
    from deejayd.ui.config import DeejaydConfig
    filesystem_charset = DeejaydConfig().get("mediadb","filesystem_charset")
    if isinstance(data, str):
        return data.decode(filesystem_charset, "replace").encode("utf-8")
    elif isinstance(data, unicode):
        return data.encode("utf-8")

    return data


class SqliteDatabase(Database):

    def __init__(self,db_file,db_prefix = ""):
        self.db_file = db_file
        self.db_prefix = db_prefix

    def connect(self):
        # Check pysqlite version
        pysqlite_min_version = [2, 2]
        pysqlite_version = map(int, sqlite.version.split('.'))
        if pysqlite_version < pysqlite_min_version:
            sqlite_error='This program requires pysqlite version %s or later.'\
                % '.'.join(map(str, pysqlite_min_version))
            log.err(sqlite_error)
            sys.exit(sqlite_error)

        init = path.isfile(self.db_file) and (0,) or (1,)
        try: self.connection = sqlite.connect(self.db_file)
        except:
            error = "Could not connect to sqlite database."
            log.err(error)
            sys.exit(error)
        else:
            self.cursor = self.connection.cursor()

        # configure connection
        self.connection.text_factory = str
        self.connection.row_factory = sqlite.Row
        sqlite.register_adapter(str,str_encode)

        if init[0]: self.create_database()
        else: self.verify_database_version()

    def get_new_connection(self):
        return SqliteDatabase(self.db_file,self.db_prefix)

    def execute(self,query,parm = None):
        query = self.__format_query(query)
        try:
            if parm == None: self.cursor.execute(query)
            else: self.cursor.execute(query,parm)
        except sqlite.OperationalError,err:
            log.err("Unable to execute database request : %s" %(err,))

    def executemany(self,query,parm):
        try: self.cursor.executemany(self.__format_query(query),parm)
        except sqlite.OperationalError,err:
            log.err("Unable to execute database request : %s" %(err,))

    def executescript(self,query):
        try: self.cursor.executescript(self.__format_query(query))
        except sqlite.OperationalError,err:
            log.err("Unable to execute database request : %s" %(err,))

    def close(self):
        self.cursor.close()
        self.connection.close()

    def __format_query(self,query):
        return query.replace("{",self.db_prefix).replace("}","")

# vim: ts=4 sw=4 expandtab
