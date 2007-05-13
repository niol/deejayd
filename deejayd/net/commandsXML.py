from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory
from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources.webradio import UnsupportedFormatException
from deejayd import sources 

from os import path


def commandsOrders():
    return ("ping","status","stats","setMode","getMode","update","getdir",
       "search","getvideodir","play","stop","pause","next","previous",
       "setVolume","seek","random","repeat","current","fullscreen",
       "loadsubtitle","playlistInfo","playlistList","playlistAdd",
       "playlistRemove","playlistClear","playlistMove","playlistShuffle",
       "playlistErase","playlistLoad","playlistSave","webradioList",
       "webradioAdd","webradioRemove","webradioClear","playQueue","queueInfo",
       "queueAdd","queueLoadPlaylist","queueRemove","queueClear","setvideodir")

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
        "getvideodir":commandsXML.GetVideoDir,
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
        "fullscreen":commandsXML.Fullscreen,
        "loadsubtitle":commandsXML.Loadsubtitle,
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
        "webradioClear":commandsXML.WebradioClear,
        # Queue commands
        "playQueue":commandsXML.PlayQueue,
        "queueInfo":commandsXML.QueueInfo,
        "queueAdd":commandsXML.QueueAdd,
        "queueLoadPlaylist":commandsXML.QueueLoadPlaylist,
        "queueRemove":commandsXML.QueueRemove,
        "queueClear":commandsXML.QueueClear,
        # Video commands
        "setvideodir":commandsXML.SetVideoDir,
    }


class queueCommands:
    
    def __init__(self,deejaydArgs):
        self.__commandsList = []
        self.deejaydArgs = deejaydArgs
        self.__rspFactory = DeejaydXMLAnswerFactory()

    def addCommand(self,name,cmd,args):
        self.__commandsList.append((name,cmd,args))

    def execute(self):
        motherRsp = None

        for (cmdName, cmdType, args) in self.__commandsList:
            cmd = cmdType(cmdName, args, self.__rspFactory, self.deejaydArgs)
            rsp = cmd.execute()
            if motherRsp == None:
                motherRsp = rsp
                self.__rspFactory.setMother(motherRsp)

        return motherRsp.toXML()


class UnknownCommand:

    def __init__(self, cmdName, args,
                 rspFactory = None, deejaydArgs = None):
        self.name = cmdName
        self.args = args
        self.deejaydArgs = deejaydArgs
        self.__rspFactory = rspFactory or DeejaydXMLAnswerFactory()

    def execute(self):
        return self.getErrorAnswer("Unknown command : %s" % (self.name,))

    def getAnswer(self, type):
        return self.__rspFactory.getDeejaydXMLAnswer(type, self.name)

    def getErrorAnswer(self, errorString):
        error = self.getAnswer('error')
        error.setErrorText(errorString)
        return error

    def getOkAnswer(self):
        return self.getAnswer('Ack')

    def getKeyValueAnswer(self, keyValueList):
        rsp = self.getAnswer('KeyValue')
        rsp.setPairs(dict(keyValueList))
        return rsp

    # FIXME : This function should not exist, dataase structure should not
    # appear here.
    def getFileAndDirs(self, dblist):
        files = []
        dirs = []
        for (dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt) in dblist:
            if t == 'directory':
                dirs.append(fn)
            else:
                fileI = [("Path",path.join(dir,fn)),("Time",lg),("Title",ti),\
                        ("Artist",ar),("Album",al),("Genre",gn),("Track",tn),\
                        ("Date",dt)]
                files.append(dict(fileI))
        return (files, dirs)

    # FIXME : This function should not exist, dataase structure should not
    # appear here.
    def getVideosAndDirs(self, dblist):
        videos = []
        dirs = []
        for (dir,fn,t,id,ti,len,videow,videoh,sub) in dblist:

            if t == 'directory':
                dirs.append(fn)
            else:
                videoI = [("Path",path.join(dir,fn)),("Title",ti),("Id",id),\
                    ("Time",len),("Videowidth",videow),("Videoheight",videoh),\
                    ("Subtitle",sub)]
                videos.append(dict(videoI))

        return (videos, dirs)


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
            except sources.sources.unknownSourceException:
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
  * webradiolength : _int_ number of recorded webradio
  * queue : _int_ id of the current queue
  * queuelength : _int_ length of the current queue
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

        return self.getKeyValueAnswer(status)


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
        return self.getKeyValueAnswer(stats)


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
        for s in ("playlist","webradio","video"):
            act = s in avSources or 1 and 0
            modes.append((s,act))

        return self.getKeyValueAnswer(modes)


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateDB(UnknownCommand):

    def docInfos(self):
        return {
            "returnType": "KeyValue", 
            "description": """
Update the database. 
  * updating_db : the id of this task. it appears in the result of status
    command until the update are finished.
"""
        }

    def execute(self):
        try:
            updateDBId = self.deejaydArgs["db"].update()
            return self.getKeyValueAnswer([('updating_db', updateDBId)])
        except NotFoundException:
            return self.getErrorAnswer('Path not found in the music directory')


class GetDir(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"directory", "type":"string", "req":0}],
            "returnType": "FileList", 
            "description": """
lists files of "directory".
"""
        }

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try:
            list = self.deejaydArgs['db'].getDir(dir)
            rsp = self.getAnswer('FileList')
            rsp.setDirectory(dir)

            files, dirs = self.getFileAndDirs(list)
            rsp.setFiles(files)
            rsp.setDirectories(dirs)

            return rsp

        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')


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

        try:
            list = getattr(self.deejaydArgs["db"],self.name)(type,content)
            rsp = self.getAnswer('FileList')

            dirs, files = self.getFileAndDirs(list)
            rsp.setFiles(files)
            rsp.setDirectories(dirs)

            return rsp

        except NotFoundException:
            return self.getErrorAnswer('type %s is not supported' % (type,))


class GetVideoDir(GetDir):

    def docInfos(self):
        return {
            "args": [{"name":"directory", "type":"string", "req":0}],
            "returnType": "FileList", 
            "description": """
lists files of video dir "directory".
"""
        }

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try:
            list = self.deejaydArgs["db"].getDir(dir,"video")
            rsp = self.getAnswer('FileList')
            rsp.setDirectory(dir)

            videos, dirs = self.getVideosAndDirs(list)
            rsp.setVideos(videos)
            rsp.setDirectories(dirs)

            return rsp

        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')



###################################################
#  Video Commands                              #
###################################################

class SetVideoDir(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"directory", "type":"string", "req":0}],
            "returnType": "Ack", 
            "description": """
Set the current video directory at "directory"
"""
        }

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try:
            self.deejaydArgs["sources"].getSource("video").setDirectory(dir)
            return self.getOkAnswer()
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')
        #except sources.unknownSourceException:
        #    return self.getErrorAnswer('Video support disabled')


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

        try:
            getattr(self.deejaydArgs["sources"].getSource("playlist"),
                    self.__class__.funcName)(playlistName)
            return self.getOkAnswer()
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')


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

        try:
            self.deejaydArgs["sources"].getSource("playlist").load(plsNames,
                                                                   pos)
            return self.getOkAnswer()
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')


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
            try:
                self.deejaydArgs["sources"].getSource("playlist").\
                    rm(plsName)
                return self.getOkAnswer()
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')


class PlaylistAdd(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true","name":"path", "type":"string", "req":1},
                {"name":"pos", "type":"int", "req":0},
                {"name":"name", "type":"string","req":0}],
            "description": """
Load files or directories passed in arguments ("path") at the position "pos" in
the playlist "name". If no playlist name is passed, add files in the current 
playlist.
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
            return self.getOkAnswer()
        except sources.unknown.ItemNotFoundException:
            return self.getErrorAnswer('%s not found' % (file,))


class PlaylistInfo(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"name", "type":"string", "req":0}],
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
            rsp = self.getAnswer('SongList')
            rsp.setSongs(self.formatSongs(songs))
            return rsp
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')

    def formatSongs(self,songs):
        rs = []
        for s in songs:
            s["Path"] = path.join(s["dir"],s["filename"])
            dictKeys = ("Path","Pos","Id","Time","Title","Artist","Album",
                        "Genre","Track","Date")
            songInfo = {}
            for t in dictKeys:
                songInfo[t] = s[t]
            rs.append(songInfo)
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
                return self.getOkAnswer()
            except sources.unknown.ItemNotFoundException:
                return self.getErrorAnswer('Song not found')
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')


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
        except sources.unknown.ItemNotFoundException:
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
        rsp = self.getAnswer('PlaylistList')
        for pl in playlists: 
            rsp.addPlaylist(pl)

        return rsp


###################################################
#  Webradios Commands                              #
###################################################
class WebradioCommand(UnknownCommand):

    def __init__(self, cmdName, args, rspFactory, deejaydArgs = None):
        UnknownCommand.__init__(self, cmdName, args, rspFactory, deejaydArgs)

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

        wrs = self.wrSource.getContent()

        rsp = self.getAnswer('WebradioList')
        for wr in wrs:
            wrdict = [("Title",wr["Title"]),("Id",wr["Id"]),("Pos",wr["Pos"]),("Url",wr["uri"])]
            rsp.addWebradio(dict(wrdict))

        return rsp


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
        
            try:
                self.wrSource.delete(id)
                return self.getOkAnswer()
            except sources.webradio.WrNotFoundException:
                return self.getErrorAnswer('Webradio not found')


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

        try:
            self.wrSource.add(url,wrname)
            return self.getOkAnswer()
        except UnsupportedFormatException:
            return self.getErrorAnswer('Webradio URI not supported')
        except NotFoundException:
            return self.getErrorAnswer('Webradio info could not be retrieved')


###################################################
#  Queue Commands                              #
###################################################
class PlayQueue(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"id", "type":"int", "req":1}],
            "description": """
Begin playing song with id "id" in the queue.
"""
        }

    def execute(self):
        nb = "id" in self.args.keys() and self.args["id"] or None
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        self.deejaydArgs["player"].goTo(nb,"Id",True)
        return self.getOkAnswer()


class QueueAdd(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true","name":"path", "type":"string", "req":1},
                {"name":"pos", "type":"int", "req":0}],
            "description": """
Load files or directories passed in arguments ("path") at the position "pos" in
the queue
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

        try:
            self.deejaydArgs["sources"].getSource("queue").\
                add(files,pos)
            return self.getOkAnswer()
        except sources.unknown.ItemNotFoundException:
            return self.getErrorAnswer('%s not found' % (file,))


class QueueLoadPlaylist(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"name":"name", "type":"string", "req":1,\
                "mult":"true"}, {"name":"pos", "type":"int", "req":0}],
            "description": """
Load playlists passed in arguments ("name") at the position "pos" in the queue 
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

        try:
            self.deejaydArgs["sources"].getSource("queue").\
                loadPlaylist(plsNames,pos)
            return self.getOkAnswer()
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')


class QueueInfo(PlaylistInfo):

    def docInfos(self):
        return {
            "args": [],
            "returnType": "SongList", 
            "description": """
Return the content of the queue
"""
        }

    def execute(self):
        songs = self.deejaydArgs["sources"].getSource("queue").getContent()
        rsp = self.getAnswer('SongList')
        rsp.setSongs(self.formatSongs(songs))
        return rsp


class QueueRemove(UnknownCommand):

    def docInfos(self):
        return {
            "args": [{"mult":"true", "name":"id", "type":"int", "req":1}],
            "description": """
Remove songs with ids passed as argument ("id"), from the queue. 
"""
        }

    def execute(self):
        numbs = "id" in self.args.keys() and self.args["id"] or []
        if isinstance(numbs, str):
            numbs = [numbs]

        for nb in numbs:
            try:nb = int(nb)
            except ValueError:
                return self.getErrorAnswer('Need an integer for argument \
                        number')

            try:
                self.deejaydArgs["sources"].getSource("queue").delete(nb,"Id")
                return self.getOkAnswer()
            except sources.unknown.ItemNotFoundException:
                return self.getErrorAnswer('Song not found')


class QueueClear(WebradioCommand):

    def docInfos(self):
        return {
            "description": """
Remove all songs from the queue
"""
        }

    def execute(self):
        self.deejaydArgs["sources"].getSource("queue").clear()
        return self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################
class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        getattr(self.deejaydArgs["player"],self.name)()
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
            return self.getErrorAnswer('Volume must be an integer between 0 \
                and 100')

        self.deejaydArgs["player"].setVolume(vol)
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
        else:
            if val not in (0,1):
                return self.getErrorAnswer('value has to be 0 or 1')

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


class Fullscreen(Random):
    funcName = "fullscreen"

    def docInfos(self):
        return {
            "args": [{"name":"value", "type":"list 0 or 1","req":1}],
            "description": """
set video fullscreen to "value", "value" should be 0 (off) or 1 (on)
"""
        }


class Loadsubtitle(Random):
    funcName = "loadsubtitle"

    def docInfos(self):
        return {
            "args": [{"name":"value", "type":"list 0 or 1","req":1}],
            "description": """
by default, load subtitle when it is available ("value"=1) or not ("value"=0)
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
        item = self.deejaydArgs["sources"].getSource(source).\
                    getPlayingItem()
        rsp = None

        if item:
            if source == "webradio":
                rsp = self.getAnswer('WebradioList')
                wrdict = [("Title",item["Title"]),("Id",item["Id"]),\
                    ("Pos",item["Pos"]),("Url",item["uri"])]
                rsp.addWebradio(dict(wrdict))
            elif source == "video":
                rsp = self.getAnswer('VideoList')
                vdict = [("Title",item["Title"]),("Id",item["Id"]),\
                    ("Time",item["Time"])]
                rsp.addVideo(dict(vdict))
            elif source == "playlist" or source == "queue":
                rsp = self.getAnswer('SongList')
                sldict = [("Title",item["Title"]),("Id",item["Id"]),\
                    ("Pos",item["Pos"]),("Artist",item["Artist"]),\
                    ("Album",item["Album"]),("Time",item["Time"])]
                rsp.addSong(dict(sldict))
        return rsp


# vim: ts=4 sw=4 expandtab
