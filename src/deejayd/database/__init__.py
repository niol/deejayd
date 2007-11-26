
class DatabaseFactory:
    supported_database = ("sqlite")

    def __init__(self,config):
        self.config = config

        try: self.db_type =  config.get("database","db_type")
        except:
            raise SystemExit(\
                "You do not choose a database.Verify your config file.")
        else:
            if self.db_type not in self.__class__.supported_database:
                raise SystemExit(\
       "You chose a database which is not supported. Verify your config file.")

    def get_db(self):
        if self.db_type == "sqlite":
            db_file = self.config.get("database","db_file")
            try: prefix = self.config.get("database","db_prefix") + "_"
            except NoOptionError: prefix = ""

            from deejayd.database.sqlite import SqliteDatabase
            return SqliteDatabase(db_file,prefix)

        return None


def init(config):
    database = DatabaseFactory(config)
    return database

# vim: ts=4 sw=4 expandtab
