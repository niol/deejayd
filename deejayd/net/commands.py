
from deejayd.mediadb.deejaydDB import djDB,NotFoundException,UnknownException
from deejayd.playlist.deejaydPlaylist import djPlaylist,PlaylistNotFoundException,PlaylistUnknownException
from deejayd.player.player import djPlayer
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

    def formatInfoResponse(self, resp):
        rs = '';
        for (dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt) in resp:
            if t == 'directory':
                rs += "directory: " + fn + "\n"
            else:
                rs += "file: "+ path.join(dir,fn)+ "\n"

                dict = [("Time",lg),("Title",ti),("Artist",ar),("Album",al),("Genre",gn),("Track",tn),("Date",dt)]
                for (k,v) in dict:
                    if isinstance(v,int):
                        rs += "%s: %d\n" % (k,v)
                    elif isinstance(v,str):
                        rs += "%s: %s\n" % (k,v)

        return rs


class Ping(UnknownCommand):
    def isUnknown(self):
        return False

    def execute(self):
        return self.getOkAnswer()


###################################################
#   MediaDB Commands                              #
###################################################

class Lsinfo(UnknownCommand):

    def __init__(self, cmdName, dir):
        self.name = cmdName
        self.directory = dir 

    def isUnknown(self):
        return False

    def execute(self):
        try:
            list = djDB.getDir(self.directory)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')

        return self.formatInfoResponse(list)+self.getOkAnswer()


class Search(UnknownCommand):

    def __init__(self, cmdName, type, content):
        self.name = cmdName
        self.type = type
        self.content = content

    def isUnknown(self):
        return False

    def execute(self):
        try:
            list = getattr(djDB,self.name)(self.type,self.content)
        except NotFoundException:
            return self.getErrorAnswer('type %s is not supported' % (self.type,))

        return self.formatInfoResponse(list)+self.getOkAnswer()


###################################################
#  Playlist Commands                              #
###################################################

class PlayerCommands(UnknownCommand):

    def isUnknown(self):
        return False

    def execute(self):
        getattr(djPlaylist,self.name)()
        return self.getOkAnswer()


class AddPlaylist(UnknownCommand):

    def __init__(self, cmdName, path):
        self.name = cmdName
        self.path = path

    def isUnknown(self):
        return False

    def execute(self):
        try:
            djPlaylist.addPath(self.path)
        except NotFoundException:
            return self.getErrorAnswer('File or Directory not found')
        return self.getOkAnswer()


class GetPlaylist(UnknownCommand):

    def __init__(self, cmdName, playlistName = None):
        self.name = cmdName
        self.playlistName = playlistName

    def isUnknown(self):
        return False

    def execute(self):
        try:
            songs = djPlaylist.getContent(self.playlistName)
        except PlaylistNotFoundException:
            return self.getErrorAnswer('File or Directory not found')

        return self.__formatPlaylistInfo(songs) + self.getOkAnswer()

    def __formatPlaylistInfo(self,songs):
        content = ''
        if self.name == "playlist":
            for s in songs:
                content += "%d:%s\n" % (s["Pos"],path.join(s["dir"],s["filename"]))
        else:
            for s in songs:
                content += "file: "+ path.join(s["dir"],s["filename"])+ "\n"
                dict = ("Pos","Id","Time","Title","Artist","Album","Genre","Track","Date")
                for t in dict:
                    if isinstance(s[t],int):
                        content += "%s: %d\n" % (t,s[t])
                    elif isinstance(s[t],str):
                        content += "%s: %s\n" % (t,s[t])

        return content


class ClearPlaylist(UnknownCommand):

    def isUnknown(self):
        return False

    def execute(self):
        djPlaylist.clear()
        return self.getOkAnswer()


# vim: ts=4 sw=4 expandtab
