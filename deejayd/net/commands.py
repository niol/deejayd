
from deejayd.mediadb.deejaydDB import djDB,NotFoundException,UnknownException
from deejayd.sources import playlist,sources
from deejayd.player import player 
from os import path

global djPlayer
djPlayer = player.deejaydPlayer()

global djMediaSource
djMediaSource = sources.sourcesFactory(djPlayer)

class UnknownCommand:

    def __init__(self, cmdName):
        self.name = cmdName

    def execute(self):
        return "ACK Unknown command : %s\n" % (self.name,)

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
            elif isinstance(v,float):
                rs += "%s: %d\n" % (k,int(v))

        return rs


class queueCommands(UnknownCommand):
    
    def __init__(self, cmdName,cmdClass):
        self.name = cmdName
        self.cmdClass = cmdClass
        self.__executeCommands = False
        self.__commandsList = []

    def isUnknown(self):
        return False

    def addCommand(self,cmd):
        self.__commandsList.append(cmd)

    def endCommand(self):
        self.__executeCommands = True

    def execute(self):
        if self.__executeCommands:
            content = ''
            st = self.name == 'command_list_ok_begin' and "list_ok\n" or ""

            for cmd in self.__commandsList: 
                rs = self.cmdClass.createCmd(cmd).execute()
                if rs.endswith("OK\n"):
                    content += rs.replace('OK\n',st)
                else: return rs

            return content + self.getOkAnswer()

        else: return ''


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
        status.extend(djMediaSource.getSource("playlist").getStatus())
        status.extend(djDB.getStatus())

        rs = self.formatResponseWithDict(status)
        return rs + self.getOkAnswer()


class Stats(UnknownCommand):
    def isUnknown(self):
        return False

    def execute(self):
        stats = djDB.getStats()
        rs = self.formatResponseWithDict(stats)

        return rs + self.getOkAnswer()


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateDB(UnknownCommand):

    def __init__(self, cmdName, dir):
        self.name = cmdName
        self.directory = dir 

    def isUnknown(self):
        return False

    def execute(self):
        try:
            updateDBId = djDB.update(self.directory)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')

        return "updating_db: %d\n" % (updateDBId,) + self.getOkAnswer()


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
            djMediaSource.getSource("playlist").addPath(self.path)
        except NotFoundException:
            return self.getErrorAnswer('File or Directory not found')
        return self.getOkAnswer()


class GetPlaylist(UnknownCommand):

    def __init__(self, cmdName, playlistName):
        self.name = cmdName
        self.playlistName = playlistName

    def isUnknown(self):
        return False

    def execute(self):
        try:
            if self.name != "currentsong":
                songs = djMediaSource.getSource("playlist").getContent(self.playlistName)
            else:
                songs = [djMediaSource.getSource("playlist").getCurrentSong()] 
        except playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

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
        djMediaSource.getSource("playlist").clear()
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
        try: djMediaSource.getSource("playlist").delete(nb,type)
        except playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')

        return self.getOkAnswer()


class PlaylistCommands(UnknownCommand):

    def __init__(self, cmdName, playlistName):
        self.name = cmdName
        self.playlistName = playlistName

    def isUnknown(self):
        return False

    def execute(self):
        if not self.playlistName:
            return self.getErrorAnswer('You must enter a playlist name')

        try:
            getattr(djMediaSource.getSource("playlist"),self.name)(self.playlistName)
        except playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

        return self.getOkAnswer()


class PlaylistList(UnknownCommand):

    def isUnknown(self):
        return False

    def execute(self):
        rs = djMediaSource.getSource("playlist").getList()
        content = ''
        i = 0
        for (pl,) in rs: 
            if pl != djMediaSource.getSource("playlist").__class__.currentPlaylistName:
                content += "%d: %s\n" % (i,pl)
                i +=1

        return content + self.getOkAnswer()


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

        if nb == -1:
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


class Seek(UnknownCommand):

    def __init__(self, cmdName, t):
        self.name = cmdName
        self.t = t

    def isUnknown(self):
        return False

    def execute(self):
        try: t = int(self.t)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if t < 0:
            return self.getErrorAnswer('Need an integer > 0')

        djPlayer.setPosition(t)
        return self.getOkAnswer()


class PlayerMode(UnknownCommand):

    def __init__(self, cmdName, val):
        self.name = cmdName
        self.val = val

    def isUnknown(self):
        return False

    def execute(self):
        try: val = int(self.val)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')

        getattr(djPlayer,self.name)(val)
        return self.getOkAnswer()


# vim: ts=4 sw=4 expandtab
