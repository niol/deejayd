from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources import sources
from deejayd.player import player 
from os import path
from xml.dom.minidom import Document


def commandsOrders():
    return ("ping","status","stats","setMode","getMode","update","getdir",
       "search","play","stop","pause","next","previous","setVolume","seek",
       "random","repeat","current","playlistInfo","playlistList","playlistAdd",
       "playlistRemove","playlistClear","playlistMove","playlistShuffle",
       "playlistShuffle","playlistErase","playlistLoad","playlistSave",
       "webradioList","webradioAdd","webradioRemove","webradioClear")

def commandsList(commandsXML):
    return {
        # General Commmands
        "ping":commandsXML.Ping,
        "status":commandsXML.Status,
        "stats":commandsXML.Stats,
        "setMode":commandsXML.Mode,
        "getMode":commandsXML.GetMode,
        # MediaDB Commmands
        "update":commandsXML.UpdateDB,
        "getdir":commandsXML.GetDir,
        "search":commandsXML.Search,
        # Player commands
        "play":commandsXML.Play,
        "stop":commandsXML.Stop,
        "pause":commandsXML.Pause,
        "next":commandsXML.Next,
        "previous":commandsXML.Previous,
        "setVolume":commandsXML.Volume,
        "seek":commandsXML.Seek,
        "random":commandsXML.Random,
        "repeat":commandsXML.Repeat,
        "current":commandsXML.CurrentSong,
        # Playlist commands
        "playlistInfo":commandsXML.PlaylistInfo,
        "playlistList":commandsXML.PlaylistList,
        "playlistAdd":commandsXML.PlaylistAdd,
        "playlistRemove":commandsXML.PlaylistRemove,
        "playlistClear":commandsXML.PlaylistClear,
        "playlistMove":commandsXML.PlaylistMove,
        "playlistShuffle":commandsXML.PlaylistShuffle,
        "playlistErase":commandsXML.PlaylistErase,
        "playlistLoad":commandsXML.PlaylistLoad,
        "playlistSave":commandsXML.PlaylistSave,
        # Webradios commands
        "webradioList":commandsXML.WebradioList,
        "webradioAdd":commandsXML.WebradioAdd,
        "webradioRemove":commandsXML.WebradioDel,
        "webradioClear":commandsXML.WebradioClear
        # Panel commands
    }


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
            cmd(cmdName,args,self.deejaydArgs,self.xmlDoc,self.xmlRoot).\
                execute()

        return self.xmlDoc.toxml("utf-8")


class UnknownCommand:

    def __init__(self, cmdName, args, deejaydArgs = None, xmlDoc = None,\
                 xmlRoot = None):
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

    def getOkAnswer(self, type = "Ack", answerXmlData = []):
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
                dict = [("Path",path.join(dir,fn)),("Time",lg),("Title",ti),\
                        ("Artist",ar),("Album",al),("Genre",gn),("Track",tn),\
                        ("Date",dt)]
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
            elif isinstance(v,unicode):
                value = "%s" % (v.encode("utf-8"))
            parm.setAttribute("value",value)
            rs.append(parm)

        return rs


class Ping(UnknownCommand):

    def docInfos(self):
        return {
            "description": """
Does nothing, just to test the connextion with the server
"""
        }

    def execute(self):
        return self.getOkAnswer()


class Mode(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"mode", "type":"string", "req":1}],
            "description": """
Change the player mode. Possible values are :
  * playlist : to manage and listen songs in playlist mode
  * webradio : to manage and listen webradio
"""
        }

    def execute(self):
        if "mode" not in self.args.keys():
             return self.getErrorAnswer('You have to choose a mode') 
        else:
            try: 
                self.deejaydArgs["sources"].setSource(self.args["mode"])
                return self.getOkAnswer()
            except sources.unknownSourceException:
                return self.getErrorAnswer('Unknown mode') 



class Status(UnknownCommand):

    def docInfos(self):
        return {
            "returnType": "KeyValue", 
            "description": """
Return status of deejayd. Given informations are :
  * playlist : _int_ id of the current playlist
  * playlistlength : _int_ length of the current playlist
  * webradio : _int_ id of the current webradio list
  * random : 0 (not activate) or 1 (activate) 
  * repeat : 0 (not activate) or 1 (activate) 
  * volume : [0-100] current volume value  
  * state : [play-pause-stop] the current state of deejayd
  * song : _int_ the position of the current song
  * songid : _int_ the id of the current song
  * mode : [playlist-webradio] the current mode
  * updating_db : _int_ show when an database update is in progress  
  * updating_error : _string_ error message that apppears when the database
                     update has failed
"""
        }

    def execute(self):
        status = self.deejaydArgs["player"].getStatus()
        status.extend(self.deejaydArgs["sources"].getStatus())
        status.extend(self.deejaydArgs["db"].getStatus())

        rs = self.formatResponseWithDict(status)
        return self.getOkAnswer("KeyValue",rs)


class Stats(UnknownCommand):

    def docInfos(self):
        return {
            "returnType": "KeyValue", 
            "description": """
Return statistic informations :
  * db_update : UNIX time of the last database update
  * songs : songs number in the database
  * artists : number of artists in the database
  * albums : number of albums in the database
"""
        }

    def execute(self):
        stats = self.deejaydArgs["db"].getStats()
        rs = self.formatResponseWithDict(stats)

        return self.getOkAnswer("KeyValue",rs)


class GetMode(UnknownCommand):

    def docInfos(self):
        return {
            "returnType": "KeyValue", 
            "description": """
For each possible sources, show if it activate or not. The answer returns :
playlist : 0 or 1 (actually always 1 because it does not need optionnal
                   requirements)
webradio : 0 or 1 (needs gst-plugins-gnomevfs to be activate)
"""
        }

    def execute(self):
        avSources = self.deejaydArgs["sources"].getAvailableSources()
        modes = []
        for s in ("playlist","webradio"):
            act = s in avSources or 1 and 0
            modes.append((s,act))

        rs = self.formatResponseWithDict(modes)
        return self.getOkAnswer("KeyValue",rs)


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateDB(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"directory", "type":"string", "req":0}],
            "returnType": "KeyValue", 
            "description": """
Update the database. "directory" argument is optional and allow to update just
a particular directory.
  * updating_db : the id of this task. it appears in the result of status
    command until the update are finished.
"""
        }

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: updateDBId = self.deejaydArgs["db"].update(dir)
        except NotFoundException:
            self.getErrorAnswer('Path not found in the music directory')

        rs = self.formatResponseWithDict([("updating_db",updateDBId)])
        self.getOkAnswer("KeyValue",rs)


class GetDir(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"directory", "type":"string", "req":0}],
            "returnType": "FileList", 
            "description": """
lists files of "directory".
"""
        }

    def getOkAnswer(self, type, answerXmlData):
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

    def docInfos(self):
        return {
            "args": [{"name":"type", "type":"list : 'all','title',\
                    'genre','filename','artist','album'","req":1}, 
                    {"name":"txt", "type":"string", "req":1}],
            "returnType": "FileList", 
            "description": """
Search file where "type" contains "txt" content
"""
        }

    def execute(self):
        type = "type" in self.args.keys() and self.args["type"] or ""
        if "txt" in self.args.keys() and self.args["txt"]:
            content = self.args["txt"]
        else:
            return self.getErrorAnswer('You have to enter text')

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

        try: getattr(self.deejaydArgs["sources"].getSource("playlist"),
            self.__class__.funcName)(playlistName)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

        self.getOkAnswer()


class PlaylistClear(SimplePlaylistCommand):
    funcName = "clear"
    requirePlaylist = False

    def docInfos(self):
        return {
            "description": """
Clear the current playlist.
"""
        }


class PlaylistShuffle(SimplePlaylistCommand):
    funcName = "shuffle"
    requirePlaylist = False

    def docInfos(self):
        return {
            "args": [],
            "description": """
Shuffle the current playlist.
"""
        }


class PlaylistSave(SimplePlaylistCommand):
    funcName = "save"

    def docInfos(self):
        return {
            "args": [{"name":"name", "type":"string", "req":1}],
            "description": """
Save the current playlist to "name" in the database
"""
        }


class PlaylistLoad(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"name", "type":"string", "req":1,\
                "mult":"true"}, {"name":"pos", "type":"int", "req":0}],
            "description": """
Load playlists passed in arguments ("name") at the position "pos"  
"""
        }

    def execute(self):
        pos = "pos" in self.args.keys() and self.args["pos"] or None
        if pos:
            try:
                pos = int(pos)
                if pos < 0:
                    raise ValueError 
            except ValueError:
                return self.getErrorAnswer(
                    'Need an integer for position argument')
        plsNames = "name" in self.args.keys() and self.args["name"] or ""
        if isinstance(plsNames, str):
            plsNames = [plsNames]

        try: self.deejaydArgs["sources"].getSource("playlist").load(plsNames,
                pos)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

        self.getOkAnswer()


class PlaylistErase(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true","name":"name", "type":"string", "req":1}],
            "description": """
Erase playlists passed in arguments 
"""
        }

    def execute(self):
        plsNames = "name" in self.args.keys() and self.args["name"] or ""
        if isinstance(plsNames, str):
            plsNames = [plsNames]

        for plsName in plsNames:
            try: self.deejaydArgs["sources"].getSource("playlist").\
                    rm(plsName)
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')

        self.getOkAnswer()


class PlaylistAdd(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true","name":"path", "type":"string", "req":1},
                {"name":"pos", "type":"int", "req":0}],
            "description": """
Load files or directories passed in arguments ("path") at the position "pos"  
"""
        }

    def execute(self):
        pos = "pos" in self.args.keys() and self.args["pos"] or None
        if pos:
            try:
                pos = int(pos)
                if pos < 0:
                    raise ValueError 
            except ValueError:
                return self.getErrorAnswer(
                    'Need an integer for position argument')
        files = "path" in self.args.keys() and self.args["path"] or ""
        if isinstance(files, str):
            files = [files]
        playlistName = "name" in self.args.keys() and self.args["name"] or None

        try: 
            self.deejaydArgs["sources"].getSource("playlist").\
                addPath(files,playlistName,pos)
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('%s not found' % (file,))
        return self.getOkAnswer()


class PlaylistInfo(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"path", "type":"string", "req":0}],
            "returnType": "SongList", 
            "description": """
Return the content of the playlist "name". 
If no name are given, return the content of the current playlist
"""
        }

    def execute(self):
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        try:
            songs = self.deejaydArgs["sources"].getSource("playlist").\
                getContent(playlistName)
            rs = self.formatPlaylistInfo(songs)
            return self.getOkAnswer("SongList",rs)

        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

    def formatPlaylistInfo(self,songs):
        rs = []
        for s in songs:
            s["Path"] = path.join(s["dir"],s["filename"])
            chd = self.xmlDoc.createElement("file")
            dict = ("Path","Pos","Id","Time","Title","Artist","Album",
                "Genre","Track","Date")

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


class PlaylistRemove(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true", "name":"id", "type":"int", "req":1},
                {"name":"name", "type":"string", "req":0}],
            "description": """
Remove songs with ids passed as argument ("id"), from the playlist "name". 
If no name are given, remove songs from current playlist 
"""
        }

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

    def docInfos(self):
        return {
            "args": [{"name":"id", "type":"int", "req":1},
                {"name":"newPosition", "type":"int", "req":1}],
            "description": """
Move song with id equal to "id" to "newPosition "position 
"""
        }

    def execute(self):
        id = "id" in self.args.keys() and self.args["id"] or None
        newPos = "newPosition" in self.args.keys() and \
            self.args["newPosition"] or None
        try:
            id = int(id)
            newPos = int(newPos)
        except ValueError:
            return self.getErrorAnswer('Need two integers as argument : id \
                and newPosition')

        try: 
            self.deejaydArgs["sources"].getSource("playlist").move(id,newPos)
            return self.getOkAnswer()
        except sources.playlist.SongNotFoundException:
            return self.getErrorAnswer('Song not found')


class PlaylistList(UnknownCommand):

    def docInfos(self):
        return {
            "returnType": "PlaylistList", 
            "description": """
Return the list of recorded playlists
"""
        }

    def execute(self):
        playlists = self.deejaydArgs["sources"].getSource("playlist").getList()
        # Remove current playlist from the list
        try: playlists.remove((self.deejaydArgs["sources"].\
            getSource("playlist").__class__.currentPlaylistName,))
        except: pass

        rs = []
        for (pl,) in playlists: 
            playlist = self.xmlDoc.createElement("playlist")
            playlist.setAttribute("name",pl)
            rs.append(playlist)

        return self.getOkAnswer("PlaylistList",rs)


###################################################
#  Webradios Commands                              #
###################################################
class WebradioCommand(UnknownCommand):

    def __init__(self, cmdName, args, deejaydArgs = None, xmlDoc = None,\
                 xmlRoot = None):
        UnknownCommand.__init__(self,cmdName,args,deejaydArgs,xmlDoc,xmlRoot)

        self.wrSource = None
        if deejaydArgs:
            try: self.wrSource = self.deejaydArgs["sources"].getSource(\
                        "webradio")
            except sources.unknownSourceException:pass


class WebradioList(WebradioCommand):

    def docInfos(self):
        return {
            "returnType": "WebradioList", 
            "description": """
Return the list of recorded webradios
"""
        }

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        wrs = self.wrSource.getList()
        rs = []
        for wr in wrs:
            webradio = self.xmlDoc.createElement("webradio")
            dict = [("Title",wr["Title"]),("Id",wr["Id"]),("Pos",wr["Pos"]),("Url",wr["uri"])]
            content = self.formatResponseWithDict(dict) 
            for c in content: webradio.appendChild(c)
            rs.append(webradio)

        return self.getOkAnswer("WebradioList",rs)


class WebradioClear(WebradioCommand):

    def docInfos(self):
        return {
            "description": """
Remove all recorded webradios
"""
        }

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        self.wrSource.clear()
        return self.getOkAnswer()


class WebradioDel(WebradioCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true", "name":"id", "type":"int", "req":1}],
            "description": """
Remove webradios with id equal to "ids"
"""
        }

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        numbs = "id" in self.args.keys() and self.args["id"] or []
        if isinstance(numbs, str):
            numbs = [numbs]

        for nb in numbs:
            try: id = int(nb)
            except ValueError: 
                return self.getErrorAnswer('Need an integer : id') 
        
            try: self.wrSource.erase(id)
            except sources.webradio.WrNotFoundException:
                return self.getErrorAnswer('Webradio not found')

        return self.getOkAnswer()


class WebradioAdd(WebradioCommand):

    def docInfos(self):
        return {
            "args": [{"name":"url", "type":"string", "req":1},
                {"name":"name", "type":"string", "req":1}],
            "description": """
Add a webradio. It's name is "name" and the url of the webradio is "url".
You can pass a playlist for "url" argument (.pls and .m3u format are supported) 
"""
        }

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        url = "url" in self.args.keys() and self.args["url"] or None
        wrname = "name" in self.args.keys() and self.args["name"] or None
        if not url or not wrname:
            return self.getErrorAnswer('Need two arguments : url and name')

        self.wrSource.addWebradio(url,wrname)
        return self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################

class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        try: getattr(self.deejaydArgs["player"],self.name)()
        except: return self.getErrorAnswer("Unable to execute the command %s" % (self.name,))

        return self.getOkAnswer()


class Next(SimplePlayerCommand):

    def docInfos(self):
        return {
            "description": """
Go to next song or webradio
"""
        }


class Previous(SimplePlayerCommand):

    def docInfos(self):
        return {
            "description": """
Go to previous song or webradio
"""
        }


class Stop(SimplePlayerCommand):

    def docInfos(self):
        return {
            "description": """
Stop playing
"""
        }


class Pause(SimplePlayerCommand):

    def docInfos(self):
        return {
            "description": """
Toggle pause/resume playing
"""
        }


class Play(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"id", "type":"int", "req":0}],
            "description": """
Begin playing at song or webradio with id "id".
"""
        }

    def execute(self):
        nb = "id" in self.args.keys() and self.args["id"] or -1
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        if nb == -1: self.deejaydArgs["player"].play()
        else: self.deejaydArgs["player"].goTo(nb,"Id")
        return self.getOkAnswer()


class Volume(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"volume", "type":"int", "req":1}],
            "description": """
set volume to "volume".
The range of volume is 0-100
"""
        }

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

    def docInfos(self):
        return {
            "args": [{"name":"time", "type":"int", "req":1}],
            "description": """
seeks to the position "time" (in seconds) of the current song \
(in playlist mode).
"""
        }

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

    def docInfos(self):
        return {
            "args": [{"name":"value", "type":"list : 0 or 1","req":1}],
            "description": """
set random state to "value", "value" should be 0 or 1
"""
        }

    def execute(self):
        val = "value" in self.args.keys() and self.args["value"] or None
        try: val = int(val)
        except TypeError,ValueError:
            return self.getErrorAnswer('Need an integer')

        getattr(self.deejaydArgs["player"],self.__class__.funcName)(val)
        return self.getOkAnswer()


class Repeat(Random):
    funcName = "repeat"

    def docInfos(self):
        return {
            "args": [{"name":"value", "type":"list 0 or 1","req":1}],
            "description": """
set repeat state to "value", "value" should be 0 or 1
"""
        }


class CurrentSong(UnknownCommand):

    def docInfos(self):
        return {
            "returnType": "SongList or WebradioList", 
            "description": """
Return informations on the current song or webradio.
"""
        }

    def execute(self):
        source = self.deejaydArgs["player"].getPlayingSourceName()
        song = self.deejaydArgs["sources"].getSource(source).\
                    getPlayingSong()
        rs = []
        returnType = "SongList"
        if song:
            chdName = source=="webradio" and "webradio" or "file"
            chd = self.xmlDoc.createElement(chdName) 
            chd.setAttribute("type",source)
            dict = []
            if source == "webradio":
                returnType = "WebradioList"
                dict = [("Title",song["Title"]),("Id",song["Id"]),\
                    ("Pos",song["Pos"]),("Url",song["uri"])]
            elif source == "playlist":
                returnType = "SongList"
                dict = [("Title",song["Title"]),("Id",song["Id"]),\
                    ("Pos",song["Pos"]),("Artist",song["Artist"]),\
                    ("Album",song["Album"]),("Time",song["Time"])]

            content = self.formatResponseWithDict(dict) 
            for c in content: chd.appendChild(c)
            rs = [chd]

        return self.getOkAnswer(returnType,rs)

# vim: ts=4 sw=4 expandtab
