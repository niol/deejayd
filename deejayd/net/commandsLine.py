from deejayd.mediadb.library import NotFoundException
from deejayd import sources
from os import path


def commandsOrders():
    return ("ping","status","audio_update","lsinfo","play","stop",\
            "pause","next","previous","setvol","seek","random","repeat")

def commandsList(commandsLine):
    return {
        # General Commmands
        "ping":commandsLine.Ping,
        "status":commandsLine.Status,
        "stats":commandsLine.Stats,
        "audio_update":commandsLine.UpdateDB,
        "lsinfo":commandsLine.LsInfo,
        "play":commandsLine.Play,
        "stop":commandsLine.Stop,
        "pause":commandsLine.Pause,
        "next":commandsLine.Next,
        "previous":commandsLine.Previous,
        "setvol":commandsLine.SetVolume,
        "seek":commandsLine.Seek,
        "random":commandsLine.Random,
        "repeat":commandsLine.Repeat
    }


class UnknownCommand:

    def __init__(self, cmdName, deejaydArgs = {}, args = None):
        self.name = cmdName
        self.deejaydArgs = deejaydArgs
        self.args = args

    def execute(self):
        return "ACK Unknown command : %s\n" % (self.name,)

    def getErrorAnswer(self, errorString):
        return 'ACK {%s} ' % (self.name,) + errorString + "\n"

    def getOkAnswer(self, answerData = None):
        return "OK\n"

    def formatInfoResponse(self, resp):
        rs = '';
        for (dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt) in resp:
            if t == 'directory':
                rs += "directory: " + fn + "\n"
            else:
                rs += "file: "+ path.join(dir,fn)+ "\n"
                dict = [("Time",lg),("Title",ti),("Artist",ar),("Album",al),
                    ("Genre",gn),("Track",tn),("Date",dt)]
                rs += self.formatResponseWithDict(dict)

        return rs

    def formatResponseWithDict(self,dict):
        rs = ''
        for (k,v) in dict:
            if isinstance(v,int):
                rs += "%s: %d\n" % (k,v)
            elif isinstance(v,str):
                rs += "%s: %s\n" % (k,v)
            elif isinstance(v,float):
                rs += "%s: %d\n" % (k,int(v))
            elif isinstance(v,unicode):
                rs += "%s: %s\n" % (k,v.encode("utf-8"))

        return rs


class Ping(UnknownCommand):

    def execute(self):
        return self.getOkAnswer()


class Status(UnknownCommand):

    def execute(self):
        status = self.deejaydArgs["player"].getStatus()
        status.extend(self.deejaydArgs["sources"].getStatus())
        status.extend(self.deejaydArgs["db"].getStatus())

        rs = self.formatResponseWithDict(status)
        return rs + self.getOkAnswer()


class Stats(UnknownCommand):

    def execute(self):
        stats = self.deejaydArgs["db"].getStats()
        rs = self.formatResponseWithDict(stats)

        return rs + self.getOkAnswer()


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateDB(UnknownCommand):

    def execute(self):
        try: updateDBId = self.deejaydArgs["db"].update()
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the music \
                library')

        return "updating_db: %d\n" % (updateDBId,) + self.getOkAnswer()


class LsInfo(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"directory", "type":"string", "req":0}],
            "returnType": "FileList", 
            "description": """
lists files of "directory".
"""
        }

    def execute(self):
        dir = ""
        if self.args != None:
            dir = self.args

        try: list = self.deejaydArgs["db"].getDir(dir)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')
        rs = self.formatInfoResponse(list)

        if dir == "":
            plist = self.deejaydArgs["sources"].getSource("playlist").getList()
            for (pl,) in plist: 
                if pl != self.deejaydArgs["sources"].getSource("playlist").\
                         __class__.currentPlaylistName:
                    rs += "playlist: %s\n" % (pl,)

        return rs+self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################

class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        getattr(self.deejaydArgs["player"],self.name)()
        return self.getOkAnswer()


class Stop(SimplePlayerCommand): pass


class Next(SimplePlayerCommand): pass


class Previous(SimplePlayerCommand): pass


class Pause(SimplePlayerCommand): pass


class Play(UnknownCommand):

    def execute(self):
        try:nb = int(self.args)
        except TypeError,ValueError:
            nb = -1

        if nb == -1:
            self.deejaydArgs["player"].play()
        else:
            self.deejaydArgs["player"].goTo(nb,"Id")
        return self.getOkAnswer()


class SetVolume(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"volume", "type":"int", "req":1}],
            "description": """
set volume to "volume".
The range of volume is 0-100
"""
        }

    def execute(self):
        try:vol = int(self.args)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')
        if vol < 0 or vol > 100:
            return self.getErrorAnswer('Volume must be an integer between 0\
                                        and 100')

        self.deejaydArgs["player"].setVolume(float(vol)/100)
        return self.getOkAnswer()


class Seek(UnknownCommand):

    def execute(self):
        try: t = int(self.args)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')
        if t < 0:
            return self.getErrorAnswer('Need an integer > 0')

        self.deejaydArgs["player"].setPosition(t)
        return self.getOkAnswer()


class PlayerMode(UnknownCommand):

    def execute(self):
        try: val = int(self.args)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')

        getattr(self.deejaydArgs["player"],self.name)(val)
        return self.getOkAnswer()


class Random(PlayerMode):pass


class Repeat(PlayerMode):pass

# vim: ts=4 sw=4 expandtab
