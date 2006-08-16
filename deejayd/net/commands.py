
from deejayd.mediadb.deejaydDB import DeejaydDB
from os import path

class UnknownCommandException: pass


class UnknownCommand:

    def __init__(self, cmdName):
        self.name = cmdName

    def execute(self):
        raise UnknownCommandException()

    def isUnknown(self):
        return True

    def getErrorAnswer(self, errorString):
        return 'ACK ' + errorString + "\n"

    def getOkAnswer(self, answerData = None):
        return "OK\n"


class Ping(UnknownCommand):
    def isUnknown(self):
        return False

    def execute(self):
        return self.getOkAnswer()


class Lsinfo(UnknownCommand):

    def __init__(self, cmdName, dir):
        self.name = cmdName
        self.directory = dir 

    def isUnknown(self):
        return False

    def execute(self):
        djDB = DeejaydDB()
        try:
            list = djDB.getDir(self.directory)
            if len(list) == 0:
                return self.getErrorAnswer('Directory not found in the database')

            rs = '';
            for (t,dir,fn,ti,ar,al,gn,tn,dt,lg,bt) in list:
                if t == 'directory':
                    rs += "directory: " + fn + "\n"
                else:
                    rs += "file: "+ path.join(dir,fn)+ "\n"

                    dict = [("Time",int(lg)),("Title",ti),("Artist",ar),("Album",al),("Genre",gn),("Track",tn),("Date",dt)]
                    for (k,v) in dict:
                        if isinstance(v,int):
                            rs += "%s: %d\n" % (k,v)
                        elif isinstance(v,str):
                            rs += "%s: %s\n" % (k,v)

            return rs + self.getOkAnswer()

        except:
            return self.getErrorAnswer('Unable to execute the command lsinfo')

        djDB.close()

# vim: ts=4 sw=4 expandtab
