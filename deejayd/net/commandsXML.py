from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources import sources
from deejayd.player import player 
from os import path
from xml.dom.minidom import Document

global djPlayer
global djMediaSource


class Error:

    def __init__(self,error):
        self.errorString = error
        # Init XML Document
        self.xmlDoc = Document()
        self.xmlRoot = self.xmlDoc.createElement("deejayd")
        self.xmlDoc.appendChild(self.xmlRoot)

    def execute(self):
        err = self.xmlDoc.createElement("error")
        err.setAttribute("name","unknown")
        err.appendChild(self.xmlDoc.createTextNode(self.errorString))

        self.xmlRoot.appendChild(err)
        return False


class queueCommands:
    
    def __init__(self,deejaydArgs):
        self.__commandsList = []
        self.deejaydArgs = deejaydArgs

        # Init XML Document
        self.xmlDoc = Document()
        self.xmlRoot = self.xmlDoc.createElement("deejayd")
        self.xmlDoc.appendChild(self.xmlRoot)

    def addCommand(self,name,cmd,args):
        self.__commandsList.append((name,cmd,args))

    def execute(self):

        for (cmdName,cmd,args) in self.__commandsList: 
            cmd(cmdName,args,self.deejaydArgs,self.xmlDoc,self.xmlRoot).execute()

        return self.xmlDoc.toxml("utf-8")


class UnknownCommand:

    def __init__(self, cmdName, args, deejaydArgs = None, xmlDoc = None, xmlRoot = None):
        self.name = cmdName
        self.args = args
        self.deejaydArgs = deejaydArgs
        self.xmlDoc = xmlDoc
        self.xmlRoot = xmlRoot

    def execute(self):
        self.getErrorAnswer("Unknown command : %s" % (self.name,))

    def getErrorAnswer(self, errorString):
        error = self.xmlDoc.createElement("error")
        error.setAttribute("name",self.name)
        error.appendChild(self.xmlDoc.createTextNode(errorString))

        self.xmlRoot.appendChild(error)
        return False

    def getOkAnswer(self, type = "ack", answerXmlData = []):
        rsp = self.xmlDoc.createElement("response")
        rsp.setAttribute("name",self.name)
        rsp.setAttribute("type",type)
        for child in answerXmlData: rsp.appendChild(child)

        self.xmlRoot.appendChild(rsp)
        return True

    def formatInfoResponse(self, resp):
        rs = [];
        for (dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt) in resp:

            if t == 'directory':
                chd = self.xmlDoc.createElement("directory")
                chd.setAttribute("name",fn)
            else:
                chd = self.xmlDoc.createElement("file")
                dict = [("Path",path.join(dir,fn)),("Time",lg),("Title",ti),("Artist",ar),("Album",al),("Genre",gn),("Track",tn),("Date",dt)]
                parms = self.formatResponseWithDict(dict)
                for parm in parms: chd.appendChild(parm)

            rs.append(chd)

        return rs

    def formatResponseWithDict(self,dict):
        rs = []
        for (k,v) in dict:
            parm = self.xmlDoc.createElement("parm")
            parm.setAttribute("name",k)
            if isinstance(v,int) or isinstance(v,float):
                value = "%d" % (v,)
            elif isinstance(v,str):
                value = "%s" % (v)
            parm.setAttribute("value",value)
            rs.append(parm)

        return rs


class Ping(UnknownCommand):

    def execute(self):
        return self.getOkAnswer()


class Mode(UnknownCommand):

    def execute(self):
        if "mode" not in self.args.keys():
             return self.getErrorAnswer('You have to choose a mode') 
        else:
            try: 
                self.deejaydArgs["sources"].setSource(self.mode)
                return self.getOkAnswer()
            except sources.unknownSourceException:
                return self.getErrorAnswer('Unknown mode') 



class Status(UnknownCommand):

    def execute(self):
        status = self.deejaydArgs["player"].getStatus()
        status.extend(self.deejaydArgs["sources"].getStatus())
        status.extend(self.deejaydArgs["db"].getStatus())

        rs = self.formatResponseWithDict(status)
        return self.getOkAnswer("keyValue",rs)


class Stats(UnknownCommand):

    def execute(self):
        stats = self.deejaydArgs["db"].getStats()
        rs = self.formatResponseWithDict(stats)

        return self.getOkAnswer("keyValue",rs)


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateDB(UnknownCommand):

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: updateDBId = self.deejaydArgs["db"].update(dir)
        except NotFoundException:
            self.getErrorAnswer('Directory not found in the database')

        rs = self.formatResponseWithDict([("updating_db",updateDBId)])
        self.getOkAnswer("keyValue",rs)


class GetDir(UnknownCommand):

    def getOkAnswer(self, type = "ack", answerXmlData = []):
        rsp = self.xmlDoc.createElement("response")
        rsp.setAttribute("name",self.name)
        rsp.setAttribute("type",type)

        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        rsp.setAttribute("directory",dir)

        for child in answerXmlData: rsp.appendChild(child)

        self.xmlRoot.appendChild(rsp)
        return True

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: list = self.deejaydArgs["db"].getDir(dir)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')

        rs = self.formatInfoResponse(list)
        return self.getOkAnswer("FileList",rs)


class Search(UnknownCommand):

    def execute(self):
        type = "type" in self.args.keys() and self.args["type"] or ""
        content = "txt" in self.args.keys() and self.args["txt"] or ""
        try: list = getattr(self.deejaydArgs["db"],self.name)(type,content)
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
        if not playlistName and self.__class__.requirePlaylist:
            return self.getErrorAnswer('You must enter a playlist name')

        try: getattr(self.deejaydArgs["sources"].getSource("playlist"),self.__class__.funcName)(playlistName)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

        self.getOkAnswer()


class PlaylistClear(SimplePlaylistCommand):
    funcName = "clear"
    requirePlaylist = False


class PlaylistShuffle(SimplePlaylistCommand):
    funcName = "shuffle"
    requirePlaylist = False


class PlaylistSave(SimplePlaylistCommand):
    funcName = "save"


class PlaylistLoad(UnknownCommand):
    funcName = "load"

    def execute(self):
        plsNames = "name" in self.args.keys() and self.args["name"] or ""
        if isinstance(plsNames, str):
            plsNames = [plsNames]

        for plsName in plsNames:
            try: getattr(self.deejaydArgs["sources"].getSource("playlist"),self.__class__.funcName)(plsName)
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')

        self.getOkAnswer()


class PlaylistErase(PlaylistLoad):
    funcName = "rm"


class PlaylistAdd(UnknownCommand):

    def execute(self):
        files = "path" in self.args.keys() and self.args["path"] or ""
        if isinstance(files, str):
            files = [files]
        playlistName = "name" in self.args.keys() and self.args["name"] or None

        for file in files:
            try: 
                self.deejaydArgs["sources"].getSource("playlist").\
                    addPath(file,playlistName)
            except sources.playlist.SongNotFoundException:
                return self.getErrorAnswer('%s not found' % (file,))
        return self.getOkAnswer()


class PlaylistInfo(UnknownCommand):

    def execute(self):
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        try:
            songs = self.deejaydArgs["sources"].getSource("playlist").getContent(playlistName)
            rs = self.formatPlaylistInfo(songs)
            return self.getOkAnswer("FileList",rs)

        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

    def formatPlaylistInfo(self,songs):
        rs = []
        for s in songs:
            s["Path"] = path.join(s["dir"],s["filename"])
            chd = self.xmlDoc.createElement("file")
            dict = ("Path","Pos","Id","Time","Title","Artist","Album","Genre","Track","Date")

            for t in dict:
                parm = self.xmlDoc.createElement("parm")
                parm.setAttribute("name",t)
                if isinstance(s[t],int):
                    content = "%d" % (s[t],)
                elif isinstance(s[t],str):
                    content = s[t]
                parm.setAttribute("value",content)

                chd.appendChild(parm)

            rs.append(chd)

        return rs


class PlaylistCurrent(PlaylistInfo):

    def execute(self):
        songs = self.deejaydArgs["sources"].getSource("playlist").\
                    getCurrentSong()
        rs = []
        if songs:
            rs = self.formatPlaylistInfo(songs)
        return self.getOkAnswer("FileList",rs)


class PlaylistRemove(UnknownCommand):

    def execute(self):
        numbs = "id" in self.args.keys() and self.args["id"] or []
        if isinstance(numbs, str):
            numbs = [numbs]
        playlistName = "name" in self.args.keys() and self.args["name"] or None

        for nb in numbs:
            try:nb = int(nb)
            except ValueError:
                return self.getErrorAnswer('Need an integer for argument \
                        number')

            try: 
                self.deejaydArgs["sources"].getSource("playlist").\
                    delete(nb,"Id",playlistName)
            except sources.playlist.SongNotFoundException:
                return self.getErrorAnswer('Song not found')
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')

        return self.getOkAnswer()



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
            self.deejaydArgs["sources"].getSource("playlist").move(id,newPos)
            return self.getOkAnswer()
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')


class PlaylistList(UnknownCommand):

    def execute(self):
        playlists = self.deejaydArgs["sources"].getSource("playlist").getList()
        try:
            playlists.remove((self.deejaydArgs["sources"].\
            getSource("playlist").__class__.currentPlaylistName,))
        except: pass
        rs = []
        for (pl,) in playlists: 
            playlist = self.xmlDoc.createElement("playlist")
            playlist.setAttribute("name",pl)
            rs.append(playlist)

        return self.getOkAnswer("FileList",rs)


###################################################
#  Webradios Commands                              #
###################################################
class WebradioList(UnknownCommand):

    def execute(self):
        wrs = self.deejaydArgs["sources"].getSource("webradio").getList()
        rs = []
        for wr in wrs:
            webradio = self.xmlDoc.createDocument("webradio")
            dict = [("Title",wr["Title"]),("Id",wr["Id"]),("Pos",wr["Pos"]),("Url",wr["uri"])]
            content = self.formatResponseWithDict(dict) 
            for c in content: webradio.appendChild(c)
            rs.append(webradio)

        return self.getOkAnswer("FileList",rs)


class WebradioClear(UnknownCommand):

    def execute(self):
        self.deejaydArgs["sources"].getSource("webradio").clear()
        return self.getOkAnswer()


class WebradioDel(UnknownCommand):

    def execute(self):
        id = "id" in self.args.keys() and self.args["id"] or None
        try: id = int(id)
        except ValueError:
            return self.getErrorAnswer('Need an integer : id')
            
        try: self.deejaydArgs["sources"].getSource("webradio").erase(id)
        except sources.webradio.NotFoundException:
            return self.getErrorAnswer('Webradio not found')

        return self.getOkAnswer()


class WebradioAdd(UnknownCommand):

    def execute(self):
        url = "url" in self.args.keys() and self.args["url"] or None
        wrname = "name" in self.args.keys() and self.args["name"] or None
        if not url or not wrname:
            return self.getErrorAnswer('Need two arguments : url and name')

        self.deejaydArgs["sources"].getSource("webradio").addWebradio(url,wrname)
        return self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################

class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        try: getattr(self.deejaydArgs["player"],self.name)()
        except: return self.getErrorAnswer("Unable to execute the command %s" % (self.name,))

        return self.getOkAnswer()


class Next(SimplePlayerCommand):pass


class Previous(SimplePlayerCommand):pass


class Stop(SimplePlayerCommand):pass


class Pause(SimplePlayerCommand):pass


class Play(UnknownCommand):

    def execute(self):
        nb = "id" in self.args.keys() and self.args["id"] or -1
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        if nb == -1: self.deejaydArgs["player"].play()
        else: self.deejaydArgs["player"].goTo(nb,"Id")
        return self.getOkAnswer()


class Volume(UnknownCommand):

    def execute(self):
        vol = "volume" in self.args.keys() and self.args["volume"] or None
        try:vol = int(vol)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if vol < 0 or vol > 100:
            return self.getErrorAnswer('Volume must be an integer between 0 and 100')

        self.deejaydArgs["player"].setVolume(float(vol)/100)
        return self.getOkAnswer()


class Seek(UnknownCommand):

    def execute(self):
        t = "time" in self.args.keys() and self.args["time"] or None
        try: t = int(t)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if t < 0:
            return self.getErrorAnswer('Need an integer > 0')

        self.deejaydArgs["player"].setPosition(t)
        return self.getOkAnswer()


class Random(UnknownCommand):
    funcName = "random"

    def execute(self):
        val = "value" in self.args.keys() and self.args["value"] or None
        try: val = int(val)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')

        getattr(self.deejaydArgs["player"],self.__class__.funcName)(val)
        return self.getOkAnswer()


class Repeat(Random):
    funcName = "repeat"


# vim: ts=4 sw=4 expandtab
