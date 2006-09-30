
from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources import sources
from deejayd.player import player 
from os import path

class UnknownCommand:

    def __init__(self, cmdName, deejaydArgs = {}):
        self.name = cmdName
        self.deejaydArgs = deejaydArgs

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

    def execute(self):
        return self.getOkAnswer()


class Mode(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, mode):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.mode = mode 

    def execute(self):
        if not self.mode:
            return self.getErrorAnswer('You have to choose a mode') 
        
        try: self.deejaydArgs["sources"].setSource(self.mode)
        except sources.unknownSourceException:
            return self.getErrorAnswer('Unknown mode') 

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

    def __init__(self, cmdName, deejaydArgs, dir):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.directory = dir 

    def execute(self):
        try:
            updateDBId = self.deejaydArgs["db"].update(self.directory)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')

        return "updating_db: %d\n" % (updateDBId,) + self.getOkAnswer()


class Lsinfo(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, dir):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.directory = dir 

    def execute(self):
        try: list = self.deejaydArgs["db"].getDir(self.directory)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')

        return self.formatInfoResponse(list)+self.getOkAnswer()


class Search(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, type, content):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.type = type
        self.content = content

    def execute(self):
        try: list = getattr(self.deejaydArgs["db"],self.name)(self.type,self.content)
        except NotFoundException:
            return self.getErrorAnswer('type %s is not supported' % (self.type,))

        return self.formatInfoResponse(list)+self.getOkAnswer()


###################################################
#  Playlist Commands                              #
###################################################

class AddPlaylist(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, path):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.path = path

    def execute(self):
        try: self.deejaydArgs["sources"].getSource("playlist").addPath(self.path)
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('File or Directory not found')
        return self.getOkAnswer()


class GetPlaylist(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, playlistName):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.playlistName = playlistName

    def execute(self):
        try:
            if self.name != "currentsong":
                songs = self.deejaydArgs["sources"].getSource("playlist").getContent(self.playlistName)
            else:
                songs = [self.deejaydArgs["sources"].getSource("playlist").getCurrentSong()] 
        except sources.playlist.PlaylistNotFoundException:
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

    def execute(self):
        self.deejaydArgs["sources"].getSource("playlist").clear()
        return self.getOkAnswer()


class ShufflePlaylist(UnknownCommand):

    def execute(self):
        self.deejaydArgs["sources"].getSource("playlist").shuffle()
        return self.getOkAnswer()


class DeletePlaylist(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, nb):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.nb = nb

    def execute(self):
        try:nb = int(self.nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        type = self.name.endswith("id") and "Id" or "Pos" 
        try: self.deejaydArgs["sources"].getSource("playlist").delete(nb,type)
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')

        return self.getOkAnswer()


class MoveInPlaylist(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, id, newPos):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.id = id
        self.newPos = newPos

    def execute(self):
        try:
            id = int(self.id)
            newPos = int(self.newPos)
        except ValueError:
            return self.getErrorAnswer('Need two integers')

        type = self.name.endswith("id") and "Id" or "Pos" 
        try: self.deejaydArgs["sources"].getSource("playlist").move(id,newPos,type)
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')
        return self.getOkAnswer()


class PlaylistCommands(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, playlistName):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.playlistName = playlistName

    def execute(self):
        if not self.playlistName:
            return self.getErrorAnswer('You must enter a playlist name')

        try:
            getattr(self.deejaydArgs["sources"].getSource("playlist"),self.name)(self.playlistName)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

        return self.getOkAnswer()


class PlaylistList(UnknownCommand):

    def execute(self):
        rs = self.deejaydArgs["sources"].getSource("playlist").getList()
        content = ''
        i = 0
        for (pl,) in rs: 
            if pl != self.deejaydArgs["sources"].getSource("playlist").__class__.currentPlaylistName:
                content += "%d: %s\n" % (i,pl)
                i +=1

        return content + self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################

class SimplePlayerCommands(UnknownCommand):

    def execute(self):
        getattr(self.deejaydArgs["player"],self.name)()
        return self.getOkAnswer()


class PlayCommands(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, nb):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.nb = nb

    def execute(self):
        try:nb = int(self.nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        if nb == -1:
            self.deejaydArgs["player"].play()
        else:
            type = self.name.endswith("id") and "Id" or "Pos" 
            self.deejaydArgs["player"].goTo(nb,type)
        return self.getOkAnswer()


class SetVolume(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, vol):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.name = cmdName
        self.vol = vol

    def execute(self):
        try:vol = int(self.vol)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if vol < 0 or vol > 100:
            return self.getErrorAnswer('Volume must be an integer between 0 and 100')

        self.deejaydArgs["player"].setVolume(float(vol)/100)
        return self.getOkAnswer()


class Seek(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, t):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.t = t

    def execute(self):
        try: t = int(self.t)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if t < 0:
            return self.getErrorAnswer('Need an integer > 0')

        self.deejaydArgs["player"].setPosition(t)
        return self.getOkAnswer()


class PlayerMode(UnknownCommand):

    def __init__(self, cmdName, deejaydArgs, val):
        UnknownCommand.__init__(self,cmdName, deejaydArgs)
        self.val = val

    def execute(self):
        try: val = int(self.val)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')

        getattr(self.deejaydArgs["player"],self.name)(val)
        return self.getOkAnswer()


# vim: ts=4 sw=4 expandtab
