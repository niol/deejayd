
from deejayd.mediadb.deejaydDB import djDB,NotFoundException,UnknownException
from deejayd.sources import sources
from deejayd.player import player 
from os import path
from xml.dom.minidom import Document

global djPlayer
global djMediaSource


class queueCommands:
    
    def __init__(self):
        self.__commandsList = []

        # Init XML Document
        self.xmlDoc = Document()
        self.xmlRoot = doc.createElement("deejayd")
        self.xmlDoc.appendChild(self.xmlRoot)

    def addCommand(self,name,cmd,args):
        self.__commandsList.append((name,cmd,args))

    def execute(self):

        for (cmdName,cmd,args) in self.__commandsList: 
            self.cmd(cmdName,args,self.xmlDoc,self.xmlRoot).execute()

        return self.xmlDoc.toxml()


class UnknownCommand:

    def __init__(self, cmdName, args, xmlDoc = None, xmlRoot = None):
        self.name = cmdName
        self.args = args
        self.xmlDoc = xmlDoc
        self.xmlRoot = xmlRoot

    def execute(self):
        self.getErrorAnswer("Unknown command : %s" % (self.name,))

    def getErrorAnswer(self, errorString):
        error = self.xmldoc.createElement("error")
        error.setAttribute("name",self.name)
        error.appendChild(self.xmlDoc.createTextNode(errorString))

        self.xmlRoot.appendChild(error)
        return False

    def getOkAnswer(self, type = "ack", answerXmlData = []):
        rsp = self.xmldoc.createElement("response")
        rsp.setAttribute("name",self.name)
        rsp.setAttribute("type",type)
        for child in answerXmlData: rsp.appendChild(child)

        self.xmlRoot.appendChild(rsp)
        return True


    def formatInfoResponse(self, resp):
        rs = [];
        for (dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt) in resp:

            if t == 'directory':
                chd = self.xmldoc.createElement("directory")
                chd.appendChild(self.xmlDoc.createTextNode(fn))
            else:
                chd = self.xmldoc.createElement("file")
                dict = [("Path",path.join(dir,fn)),("Time",lg),("Title",ti),("Artist",ar),("Album",al),("Genre",gn),("Track",tn),("Date",dt)]
                parms = self.formatResponseWithDict(dict)
                for parm in parms: chd.appendChild(parm)

            rs.append(chd)

        return rs

    def formatResponseWithDict(self,dict):
        rs = []
        for (k,v) in dict:
            parm = self.xmldoc.createElement("parm")
            parm.setAttribute("name",k)
            if isinstance(v,int) or isinstance(v,float):
                value = "%d" % (v,)
            elif isinstance(v,str):
                value = "%s" % (v)
            parm.appendChild(self.xmlDoc.createTextNode(value))
            rs.append(parm)

        return rs


class SimpleCommand(UnknownCommand):
    
    cmdFunction = None

    def execute(self):
        if self.__class__.cmdFunction:
            try: self.__class__.cmdFunction()
            except: return self.getErrorAnswer("Unable to execute the command")

        return self.getOkAnswer()


class Ping(SimpleCommand):
    cmdFunction = lambda *x: return True


class Mode(UnknownCommand):

    def execute(self):
        if "mode" not in self.args.keys():
             return self.getErrorAnswer('You have to choose a mode') 
        else:
            try: 
                djMediaSource.setSource(self.mode)
                return self.getOkAnswer()
            except sources.unknownSourceException:
                return self.getErrorAnswer('Unknown mode') 



class Status(UnknownCommand):

    def execute(self):
        status = djPlayer.getStatus()
        status.extend(djMediaSource.getStatus())
        status.extend(djDB.getStatus())

        rs = self.formatResponseWithDict(status)
        return self.getOkAnswer("keyValue",rs)


class Stats(UnknownCommand):

    def execute(self):
        stats = djDB.getStats()
        rs = self.formatResponseWithDict(stats)

        return self.getOkAnswer("keyValue",rs)


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateDB(UnknownCommand):

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: updateDBId = djDB.update(dir)
        except NotFoundException:
            self.getErrorAnswer('Directory not found in the database')

        rs = self.formatResponseWithDict([("updating_db",updateDBId)])
        self.getOkAnswer("keyValue",rs)


class GetDir(UnknownCommand):

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: list = djDB.getDir(self.dir)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')

        rs = self.formatInfoResponse(list)
        return self.getOkAnswer("FileList",rs)


class Search(UnknownCommand):

    def execute(self):
        type = "type" in self.args.keys() and self.args["type"] or ""
        content = "type" in self.args.keys() and self.args["type"] or ""
        try: list = getattr(djDB,self.name)(type,content)
        except NotFoundException:
            return self.getErrorAnswer('type %s is not supported' % (type,))

        rs = self.formatInfoResponse(list)
        return self.getOkAnswer("FileList",rs)


###################################################
#  Playlist Commands                              #
###################################################

class SimplePlaylistCommand(UnknownCommand):
    funcName = None
    requirePlaylist = True

    def execute(self):
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        if not self.playlistName and requirePlaylist:
            return self.getErrorAnswer('You must enter a playlist name')

        try: getattr(djMediaSource.getSource("playlist"),self.__class__.funcName)(playlistName)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

        self.getOkAnswer()


class PlaylistClear(SimplePlaylistCommand):
    funcName = "clear"
    requirePlaylist = False


class PlaylistShuffle(SimplePlaylistCommand):
    funcName = "shuffle"
    requirePlaylist = False


class PlaylistRemove(SimplePlaylistCommand):
    funcName = "rm"


class PlaylistLoad(SimplePlaylistCommand):
    funcName = "load"


class PlaylistSave(SimplePlaylistCommand):
    funcName = "save"


class PlaylistAdd(UnknownCommand):

    def execute(self):
        path = "path" in self.args.keys() and self.args["path"] or ""
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        try: 
            djMediaSource.getSource("playlist").addPath(path,playlistName)
            return self.getOkAnswer()
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('File or Directory not found')


class PlaylistInfo(UnknownCommand):

    def execute(self):
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        try:
            songs = djMediaSource.getSource("playlist").getContent(playlistName)
            rs = self.formatPlaylistInfo(songs)
            return self.getOkAnswer("FileList",rs)

        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

    def formatPlaylistInfo(self,songs):
        rs = []
        for s in songs:
            s["path"] = path.join(s["dir"],s["filename"])
            chd = self.xmldoc.createElement("file")
            dict = ("Path","Pos","Id","Time","Title","Artist","Album","Genre","Track","Date")

            for t in dict:
                parm = self.xmldoc.createElement("file")
                parm.setAttribute("name",t)
                if isinstance(s[t],int):
                    content = "%d" % (s[t],)
                elif isinstance(s[t],str):
                    content = s[t]
                parm.appendChild(self.xmlDoc.createTextNode(content))

                chd.appendChild(parm)

            rs.append(chd)

        return rs


class PlaylistDel(UnknownCommand):

    def execute(self):
        nb = "number" in self.args.keys() and self.args["number"] or None
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer for argument number')

        try: 
            djMediaSource.getSource("playlist").delete(nb,"Id",playlistName)
            return self.getOkAnswer()
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')
        except sources.playlist.PlaylistNotFoundException:
            self.getErrorAnswer('Playlist not found')



class PlaylistMove(UnknownCommand):

    def execute(self):
        id = "id" in self.args.keys() and self.args["id"] or None
        newPos = "newPosition" in self.args.keys() and self.args["newPosition"] or None
        try:
            id = int(id)
            newPos = int(newPos)
        except ValueError:
            return self.getErrorAnswer('Need two integers as argument : id and newPosition')

        try: 
            djMediaSource.getSource("playlist").move(id,newPos)
            return self.getOkAnswer()
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')


class PlaylistList(UnknownCommand):

    def execute(self):
        playlists = djMediaSource.getSource("playlist").getList()
        playlists.remove((djMediaSource.getSource("playlist").__class__.currentPlaylistName,))
        rs = []
        for (pl,) in playlists: 
            playlist = self.xmldoc.createDocument("playlist")
            playlist.appendChild(self.xmldoc.createTextNode(pl))
            rs.append(playlist)

        return self.getOkAnswer("FileList",rs)


###################################################
#  Webradios Commands                              #
###################################################
class WebradioList(UnknownCommand):

    def execute(self):
        wrs = djMediaSource.getSource("webradio").getList()
        rs = []
        for wr in wrs:
            webradio = self.xmldoc.createDocument("webradio")
            dict = [("Title",wr["Title"]),("Id",wr["Id"]),("Pos",wr["Pos"]),("Url",wr["uri"])]
            content = self.formatResponseWithDict(dict) 
            for c in content: webradio.appendChild(c)
            rs.append(webradio)

        return self.getOkAnswer("FileList",rs)


class WebradioClear(UnknownCommand):

    def execute(self):
        djMediaSource.getSource("webradio").clear()
        return self.getOkAnswer()


class WebradioErase(UnknownCommand):

    def execute(self):
        id = "id" in self.args.keys() and self.args["id"] or None
        try: id = int(id)
        except ValueError:
            return self.getErrorAnswer('Need an integer : id')
            
        try: djMediaSource.getSource("webradio").erase(id)
        except sources.webradio.NotFoundException:
            return self.getErrorAnswer('Webradio not found')

        return self.getOkAnswer()


class WebradioAdd(UnknownCommand):

    def execute(self):
        url = "url" in self.args.keys() and self.args["url"] or None
        wrname = "name" in self.args.keys() and self.args["name"] or None
        if not url or not wrname:
            return self.getErrorAnswer('Need two arguments : url and name')

        djMediaSource.getSource("webradio").addWebradio(url,wrname)
        return self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################

class Next(SimpleCommand):
    cmdFunction = djPlayer.next


class Previous(SimpleCommand):
    cmdFunction = djPlayer.next


class Stop(SimpleCommand):
    cmdFunction = djPlayer.next


class Pause(SimpleCommand):
    cmdFunction = djPlayer.next


class Play(UnknownCommand):

    def execute(self):
        nb = "number" in self.args.keys() and self.args["number"] or None
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        if nb == -1: djPlayer.play()
        else: djPlayer.goTo(nb,"Id")
        return self.getOkAnswer()


class Volume(UnknownCommand):

    def execute(self):
        vol = "volume" in self.args.keys() and self.args["volume"] or None
        try:vol = int(vol)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if vol < 0 or vol > 100:
            return self.getErrorAnswer('Volume must be an integer between 0 and 100')

        djPlayer.setVolume(float(vol)/100)
        return self.getOkAnswer()


class Seek(UnknownCommand):

    def execute(self):
        t = "time" in self.args.keys() and self.args["time"] or None
        try: t = int(self.t)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if t < 0:
            return self.getErrorAnswer('Need an integer > 0')

        djPlayer.setPosition(t)
        return self.getOkAnswer()


class Random(UnknownCommand):
    funcName = "random"

    def execute(self):
        val = "value" in self.args.keys() and self.args["value"] or None
        try: val = int(self.val)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')

        getattr(djPlayer,self.__class__.funcName)(val)
        return self.getOkAnswer()


class Repeat(Random):
    funcName = "repeat"


# vim: ts=4 sw=4 expandtab
