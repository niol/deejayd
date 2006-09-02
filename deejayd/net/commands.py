
from deejayd.mediadb.deejaydDB import djDB,NotFoundException,UnknownException
from deejayd.playlist import deejaydPlaylist
from deejayd.player import player 
from os import path

global djPlayer
djPlayer = player.deejaydPlayer()

global djPlaylist
djPlaylist = deejaydPlaylist.PlaylistManagement(djPlayer)
djPlayer.setSource(djPlaylist)


class UnknownCommandException: pass


class UnknownCommand:

    def __init__(self, cmdName):
        self.name = cmdName

    def execute(self):
        raise UnknownCommandException()

    def isUnknown(self):
        return True

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
                dict = [("Time",lg),("Title",ti),("Artist",ar),("Album",al),("Genre",gn),("Track",tn),("Date",dt)]
                rs += self.formatResponseWithDict(dict)

        return rs

    def formatResponseWithDict(self,dict):
        rs = ''
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


class Status(UnknownCommand):
    def isUnknown(self):
        return False

    def execute(self):
        status = djPlayer.getStatus()
        status.extend(djPlaylist.getStatus())

        rs = self.formatResponseWithDict(status)
        return rs + self.getOkAnswer()


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


class DeletePlaylist(UnknownCommand):

    def __init__(self, cmdName, nb):
        self.name = cmdName
        self.nb = nb

    def isUnknown(self):
        return False

    def execute(self):
        try:nb = int(self.nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        type = self.name == "deleteid" and "Id" or "Pos"
        try: djPlaylist.delete(nb,type)
        except deejaydPlaylist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')

        return self.getOkAnswer()


class SavePlaylist(UnknownCommand):

    def __init__(self, cmdName, playlistName):
        self.name = cmdName
        self.playlistName = playlistName

    def isUnknown(self):
        return False

    def execute(self):
        djPlaylist.save(self.playlistName)
        return self.getOkAnswer()

###################################################
#    Player Commands                              #
###################################################

class SimplePlayerCommands(UnknownCommand):

    def isUnknown(self):
        return False

    def execute(self):
        getattr(djPlayer,self.name)()
        return self.getOkAnswer()


class PlayCommands(UnknownCommand):

    def __init__(self, cmdName, nb):
        self.name = cmdName
        self.nb = nb

    def isUnknown(self):
        return False

    def execute(self):
        try:nb = int(self.nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        if nb == 0:
            djPlayer.play()
        else:
            type = self.name == "playid" and "Id" or "Pos"
            djPlayer.goTo(nb,type)
        return self.getOkAnswer()


class SetVolume(UnknownCommand):

    def __init__(self, cmdName, vol):
        self.name = cmdName
        self.vol = vol

    def isUnknown(self):
        return False

    def execute(self):
        try:vol = int(self.vol)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if vol < 0 or vol > 100:
            return self.getErrorAnswer('Volume must be an integer between 0 and 100')

        djPlayer.setVolume(float(vol)/100)
        return self.getOkAnswer()


# vim: ts=4 sw=4 expandtab
