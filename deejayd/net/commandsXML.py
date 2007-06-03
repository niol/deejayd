from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory
from deejayd.mediadb.library import NotFoundException
from deejayd.sources.webradio import UnsupportedFormatException
from deejayd import sources 

from os import path


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

    # FIXME : This function should not exist, database structure should not
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
                        ("Date",dt),("Bitrate",bt)]
                files.append(dict(fileI))
        return {'files':files, 'dirs': dirs}

    # FIXME : This function should not exist, database structure should not
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

        return {'videos':videos, 'dirs':dirs}


class Ping(UnknownCommand):
    """Does nothing, just replies with an acknowledgement that the command was received"""
    command_name = 'ping'

    def execute(self):
        return self.getOkAnswer()


class Mode(UnknownCommand):
    """Change the player mode. Possible values are :
  * playlist : to manage and listen songs
  * video : to manage and wath video file
  * webradio : to manage and listen webradios"""
    command_name = 'setMode'
    command_args = [{"name":"mode", "type":"string", "req":True}]

    def execute(self):
        if "mode" not in self.args.keys():
             return self.getErrorAnswer('You have to choose a mode') 
        else:
            try: self.deejaydArgs["sources"].set_source(self.args["mode"])
            except sources.sources.UnknownSourceException:
                return self.getErrorAnswer('Unknown mode') 
            else: return self.getOkAnswer()


class Status(UnknownCommand):
    """Return status of deejayd. Given informations are :
  * playlist : _int_ id of the current playlist
  * playlistlength : _int_ length of the current playlist
  * webradio : _int_ id of the current webradio list
  * webradiolength : _int_ number of recorded webradio
  * queue : _int_ id of the current queue
  * queuelength : _int_ length of the current queue
  * random : 0 (not activated) or 1 (activated)
  * repeat : 0 (not activated) or 1 (activated)
  * volume : [0-100] current volume value
  * state : [play-pause-stop] the current state of the player
  * song : _int_ the position of the current song
  * songid : _int_ the id of the current song
  * mode : [playlist-webradio] the current mode
  * audio_updating_db : _int_ show when a audio library update is in progress  
  * audio_updating_error : _string_ error message that apppears when the 
                           audio library update has failed
  * video_updating_db : _int_ show when a video library update is in progress  
  * video_updating_error : _string_ error message that apppears when the 
                           video library update has failed"""
    command_name = 'status'
    command_rvalue = 'KeyValue'

    def execute(self):
        status = self.deejaydArgs["player"].get_status()
        status.extend(self.deejaydArgs["sources"].get_status())
        status.extend(self.deejaydArgs["audio_library"].get_status())
        if self.deejaydArgs["video_library"]:
            status.extend(self.deejaydArgs["video_library"].get_status())

        return self.getKeyValueAnswer(status)


class Stats(UnknownCommand):
    """Return statistical informations :
  * audio_library_update : UNIX time of the last audio library update
  * video_library_update : UNIX time of the last video library update
  * songs : number of songs known by the database
  * artists : number of artists in the database
  * albums : number of albums in the database"""
    command_name = 'stats'
    command_rvalue = 'KeyValue'

    def execute(self):
        stats = self.deejaydArgs["db"].get_stats()
        return self.getKeyValueAnswer(stats)


class GetMode(UnknownCommand):
    """For each available source, shows if it is activated or not. The answer
    consists in :
  * playlist : 0 or 1 (actually always 1 because it does not need optionnal
               dependencies)
  * webradio : 0 or 1 (needs gst-plugins-gnomevfs to be activated)
  * video : 0 or 1 (needs video dependencies, X display and needs to be
            activated in configuration)"""
    command_name = 'getMode'
    command_rvalue = 'KeyValue'

    def execute(self):
        avSources = self.deejaydArgs["sources"].get_available_sources()
        modes = []
        for s in ("playlist","webradio","video"):
            act = s in avSources or 1 and 0
            modes.append((s,act))

        return self.getKeyValueAnswer(modes)


###################################################
#   MediaDB Commands                              #
###################################################

class UpdateAudioLibrary(UnknownCommand):
    """Update the audio library.
  * audio_updating_db : the id of this task. It appears in the status until the
    update are completed."""
    command_name = 'audioUpdate'
    command_rvalue = 'KeyValue'

    def execute(self):
        update_id = self.deejaydArgs["audio_library"].update()
        return self.getKeyValueAnswer([('audio_updating_db', update_id)])


class UpdateVideoLibrary(UnknownCommand):
    """Update the video library.
  * video_updating_db : the id of this task. It appears in the status until the
    update are completed."""
    command_name = 'videoUpdate'
    command_rvalue = 'KeyValue'


    def execute(self):
        if self.deejaydArgs["video_library"]:
            update_id = self.deejaydArgs["video_library"].update()
            return self.getKeyValueAnswer([('video_updating_db', update_id)])
        else: return self.getErrorAnswer('Video support disabled.')


class GetDir(UnknownCommand):
    """List the files of the directory supplied as argument."""
    command_name = 'getdir'
    command_args = [{"name":"directory", "type":"string", "req":False}]
    command_rvalue = 'FileList'

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: list = self.deejaydArgs['audio_library'].get_dir_content(dir)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')
        else:
            rsp = self.getAnswer('FileList')
            rsp.setDirectory(dir)

            filesAndDirs = self.getFileAndDirs(list)
            rsp.setFiles(filesAndDirs['files'])
            rsp.setDirectories(filesAndDirs['dirs'])

            return rsp


class Search(UnknownCommand):
    """Search files where "type" contains "txt" content."""
    command_name = 'search'
    command_args = [{"name":"type", "type":"list : 'all','title',\
                    'genre','filename','artist','album'","req":True},
                    {"name":"txt", "type":"string", "req":True}]
    command_rvalue = 'FileList'

    def execute(self):
        type = "type" in self.args.keys() and self.args["type"] or ""
        if "txt" in self.args.keys() and self.args["txt"]:
            content = self.args["txt"]
        else:
            return self.getErrorAnswer('You have to enter text')

        try: list = self.deejaydArgs["audio_library"].search(type,content)
        except NotFoundException:
            return self.getErrorAnswer('type %s is not supported' % (type,))
        else:
            rsp = self.getAnswer('FileList')

            filesAndDirs = self.getFileAndDirs(list)
            rsp.setFiles(filesAndDirs['files'])
            rsp.setDirectories(filesAndDirs['dirs'])

            return rsp


class GetVideoDir(GetDir):
    """Lists the files in video dir "directory"."""
    command_name = 'getvideodir'
    command_args = [{"name":"directory", "type":"string", "req":True}]
    command_rvalue = 'FileList'

    def execute(self):
        if not self.deejaydArgs["video_library"]:
            return self.getErrorAnswer('Video support disabled.')

        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: list = self.deejaydArgs["video_library"].get_dir_content(dir)
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')
        else:
            rsp = self.getAnswer('FileList')
            rsp.setDirectory(dir)

            videosAndDirs = self.getVideosAndDirs(list)
            rsp.setVideos(videosAndDirs['videos'])
            rsp.setDirectories(videosAndDirs['dirs'])

            return rsp




###################################################
#  Video Commands                              #
###################################################

class SetVideoDir(UnknownCommand):
    """Set the current video directory to "directory"."""
    command_name = 'setvideodir'
    command_args = [{"name":"directory", "type":"string", "req":False}]

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try:
            self.deejaydArgs["sources"].get_source("video").set_directory(dir)
            return self.getOkAnswer()
        except NotFoundException:
            return self.getErrorAnswer('Directory not found in the database')
        except sources.UnknownSourceException:
            return self.getErrorAnswer('Video support disabled')


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
            getattr(self.deejaydArgs["sources"].get_source("playlist"),
                    self.__class__.funcName)(playlistName)
            return self.getOkAnswer()
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')


class PlaylistClear(SimplePlaylistCommand):
    """Clear the current playlist."""
    command_name = 'playlistClear'

    funcName = "clear"
    requirePlaylist = False


class PlaylistShuffle(SimplePlaylistCommand):
    """Shuffle the current playlist."""
    command_name = 'playlistShuffle'

    funcName = "shuffle"
    requirePlaylist = False


class PlaylistSave(SimplePlaylistCommand):
    """Save the current playlist to "name" in the database."""
    command_name = 'playlistSave'
    command_args = [{"name":"name", "type":"string", "req":True}]

    funcName = "save"


class PlaylistLoad(UnknownCommand):
    """Load playlists passed as arguments ("name") at the position "pos"."""
    command_name = 'playlistLoad'
    command_args = [{"name":"name", "type":"string", "req":True, "mult":True},
                    {"name":"pos", "type":"int", "req":False}]

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
            self.deejaydArgs["sources"].get_source("playlist").\
                                                    load_playlist(plsNames, pos)
            return self.getOkAnswer()
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')


class PlaylistErase(UnknownCommand):
    """Erase playlists passed as arguments."""
    command_name = 'playlistErase'
    command_args = [{"mult":"true","name":"name", "type":"string", "req":True}]

    def execute(self):
        plsNames = "name" in self.args.keys() and self.args["name"] or ""
        if isinstance(plsNames, str):
            plsNames = [plsNames]

        for plsName in plsNames:
            try:
                self.deejaydArgs["sources"].get_source("playlist").\
                    rm(plsName)
                return self.getOkAnswer()
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')


class PlaylistAdd(UnknownCommand):
    """Load files or directories passed as arguments ("path") at the position
    "pos" in the playlist "name". If no playlist name is provided, adds files
    in the current playlist."""
    command_name = 'playlistAdd'
    command_args = [{"mult":True,"name":"path", "type":"string", "req":True},
                    {"name":"pos", "type":"int", "req":False},
                    {"name":"name", "type":"string","req":False}]

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
            self.deejaydArgs["sources"].get_source("playlist").\
                add_path(files,playlistName,pos)
            return self.getOkAnswer()
        except sources.unknown.ItemNotFoundException:
            return self.getErrorAnswer('%s not found' % (file,))


class PlaylistInfo(UnknownCommand):
    """Return the content of the playlist "name". If no name is given, return
    the content of the current playlist."""
    command_name = 'playlistInfo'
    command_args = [{"name":"name", "type":"string", "req":True}]
    command_rvalue = 'SongList'

    def execute(self):
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        try: songs = self.deejaydArgs["sources"].get_source("playlist").\
                get_content(playlistName)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')
        else:
            rsp = self.getAnswer('SongList')
            rsp.setSongs(self.formatSongs(songs))
            return rsp

    def formatSongs(self,songs):
        rs = []
        for s in songs:
            s["Path"] = path.join(s["dir"],s["filename"])
            dictKeys = ("Path","Pos","Id","Time","Title","Artist","Album",
                        "Genre","Track","Date","Bitrate")
            songInfo = {}
            for t in dictKeys:
                songInfo[t] = s[t]
            rs.append(songInfo)
        return rs


class PlaylistRemove(UnknownCommand):
    """Remove songs with ids passed as argument ("id"), from the playlist
    "name". If no name are given, remove songs from current playlist."""
    command_name = 'playlistRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True},
                    {"name":"name", "type":"string", "req":False}]

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
            try: nb = int(nb)
            except ValueError:
                return self.getErrorAnswer(\
                                    'Need an integer for argument number')

            try: self.deejaydArgs["sources"].get_source("playlist").\
                    delete(nb,"Id",playlistName)
            except sources.unknown.ItemNotFoundException:
                return self.getErrorAnswer('Song not found')
            except sources.playlist.PlaylistNotFoundException:
                return self.getErrorAnswer('Playlist not found')
            else: return self.getOkAnswer()


class PlaylistMove(UnknownCommand):
    """Move song with id "id" to newPosition "position"."""
    command_name = 'playlistMove'
    command_args = [{"name":"id", "type":"int", "req":True},
                    {"name":"newPosition", "type":"int", "req":True}]

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

        try: self.deejaydArgs["sources"].get_source("playlist").move(id,newPos)
        except sources.unknown.ItemNotFoundException:
            return self.getErrorAnswer('Song not found')
        else: return self.getOkAnswer()


class PlaylistList(UnknownCommand):
    """Return the list of recorded playlists."""
    command_name = 'playlistList'
    command_rvalue = 'PlaylistList'

    def execute(self):
        playlists=self.deejaydArgs["sources"].get_source("playlist").get_list()
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
            try: self.wrSource = self.deejaydArgs["sources"].get_source(\
                        "webradio")
            except sources.UnknownSourceException:pass


class WebradioList(WebradioCommand):
    """Return the list of recorded webradios."""
    command_name = 'webradioList'
    command_rvalue = 'WebradioList'

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        wrs = self.wrSource.get_content()

        rsp = self.getAnswer('WebradioList')
        for wr in wrs:
            wrdict = [("Title",wr["Title"]),("Id",wr["Id"]),("Pos",wr["Pos"]),("Url",wr["uri"])]
            rsp.addWebradio(dict(wrdict))

        return rsp


class WebradioClear(WebradioCommand):
    """Remove all recorded webradios."""
    command_name = 'webradioClear'

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        self.wrSource.clear()
        return self.getOkAnswer()


class WebradioDel(WebradioCommand):
    """Remove webradios with id equal to "ids"."""
    command_name = 'webradioRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

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
        
            try: self.wrSource.delete(id)
            except sources.webradio.WrNotFoundException:
                return self.getErrorAnswer('Webradio not found')
            else: return self.getOkAnswer()


class WebradioAdd(WebradioCommand):
    """Add a webradio. Its name is "name" and the url of the webradio is
    "url". You can pass a playlist for "url" argument (.pls and .m3u format
    are supported)."""
    command_name = 'webradioAdd'
    command_args = [{"name":"url", "type":"string", "req":True},
                    {"name":"name", "type":"string", "req":True}]

    def execute(self):
        if not self.wrSource:
            return self.getErrorAnswer("Webradio support not available")

        url = "url" in self.args.keys() and self.args["url"] or None
        wrname = "name" in self.args.keys() and self.args["name"] or None
        if not url or not wrname:
            return self.getErrorAnswer('Need two arguments : url and name')

        try: self.wrSource.add(url,wrname)
        except UnsupportedFormatException:
            return self.getErrorAnswer('Webradio URI not supported')
        except NotFoundException:
            return self.getErrorAnswer('Webradio info could not be retrieved')
        else: return self.getOkAnswer()


###################################################
#  Queue Commands                              #
###################################################
class PlayQueue(UnknownCommand):
    """Begin playing song with id "id" in the queue."""
    command_name = 'playQueue'
    command_args = [{"name":"id", "type":"int", "req":True}]

    def execute(self):
        nb = "id" in self.args.keys() and self.args["id"] or None
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        self.deejaydArgs["player"].go_to(nb,"Id",True)
        return self.getOkAnswer()


class QueueAdd(UnknownCommand):
    """Load files or directories passed as arguments ("path") at the position
    "pos" in the queue."""
    command_name = 'queueAdd'
    command_args = [{"mult":True, "name":"path", "type":"string", "req":True},
                    {"name":"pos", "type":"int", "req":False}]

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
            self.deejaydArgs["sources"].get_source("queue").\
                add_path(files,pos)
            return self.getOkAnswer()
        except sources.unknown.ItemNotFoundException:
            return self.getErrorAnswer('%s not found' % (file,))


class QueueLoadPlaylist(UnknownCommand):
    """Load playlists passed in arguments ("name") at the position "pos" in
    the queue."""
    command_name = 'queueLoadPlaylist'
    command_args = [{"name":"name", "type":"string", "req":True, "mult":True},
                    {"name":"pos", "type":"int", "req":False}]

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

        try: self.deejaydArgs["sources"].get_source("queue").\
                                                    load_playlist(plsNames,pos)
        except sources.playlist.PlaylistNotFoundException:
            return self.getErrorAnswer('Playlist not found')
        else: return self.getOkAnswer()


class QueueInfo(PlaylistInfo):
    """Return the content of the queue."""
    command_name = 'queueInfo'
    command_rvalue = 'SongList'

    def execute(self):
        songs = self.deejaydArgs["sources"].get_source("queue").get_content()
        rsp = self.getAnswer('SongList')
        rsp.setSongs(self.formatSongs(songs))
        return rsp


class QueueRemove(UnknownCommand):
    """Remove songs with ids passed as argument ("id"), from the queue."""
    command_name = 'queueRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

    def execute(self):
        numbs = "id" in self.args.keys() and self.args["id"] or []
        if isinstance(numbs, str):
            numbs = [numbs]

        for nb in numbs:
            try:nb = int(nb)
            except ValueError:
                return self.getErrorAnswer('Need an integer for argument \
                        number')

            try: self.deejaydArgs["sources"].get_source("queue").delete(nb,"Id")
            except sources.unknown.ItemNotFoundException:
                return self.getErrorAnswer('Song not found')

        return self.getOkAnswer()


class QueueClear(WebradioCommand):
    """Remove all songs from the queue."""
    command_name = 'queueClear'

    def execute(self):
        self.deejaydArgs["sources"].get_source("queue").clear()
        return self.getOkAnswer()


###################################################
#    Player Commands                              #
###################################################
class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        getattr(self.deejaydArgs["player"],self.name)()
        return self.getOkAnswer()


class Next(SimplePlayerCommand):
    """Go to next song or webradio."""
    command_name = 'next'


class Previous(SimplePlayerCommand):
    """Go to previous song or webradio."""
    command_name = 'previous'


class Stop(SimplePlayerCommand):
    """Stop playing."""
    command_name = 'stop'


class Pause(SimplePlayerCommand):
    """Toggle play/pause."""
    command_name = 'pause'


class Play(UnknownCommand):
    """Begin playing at song or webradio with id "id"."""
    command_name = 'play'
    command_args = [{"name":"id", "type":"int", "req":False}]

    def execute(self):
        nb = "id" in self.args.keys() and self.args["id"] or -1
        try:nb = int(nb)
        except ValueError:
            return self.getErrorAnswer('Need an integer')

        if nb == -1: self.deejaydArgs["player"].play()
        else: self.deejaydArgs["player"].go_to(nb,"Id")
        return self.getOkAnswer()


class Volume(UnknownCommand):
    """Set volume to "volume". The volume range is 0-100."""
    command_name = 'setVolume'
    command_args = [{"name":"volume", "type":"int", "req":True}]

    def execute(self):
        vol = "volume" in self.args.keys() and self.args["volume"] or None
        try:vol = int(vol)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if vol < 0 or vol > 100:
            return self.getErrorAnswer('Volume must be an integer between 0 \
                and 100')

        self.deejaydArgs["player"].set_volume(vol)
        return self.getOkAnswer()


class Seek(UnknownCommand):
    """Seeks to the position "time" (in seconds) of the current song (in
    playlist mode)."""
    command_name = 'seek'
    command_args = [{"name":"time", "type":"int", "req":True}]

    def execute(self):
        t = "time" in self.args.keys() and self.args["time"] or None
        try: t = int(t)
        except ValueError:
            return self.getErrorAnswer('Need an integer')
        if t < 0:
            return self.getErrorAnswer('Need an integer > 0')

        self.deejaydArgs["player"].set_position(t)
        return self.getOkAnswer()


class Random(UnknownCommand):
    """Set random state to "value", "value" should be 0 or 1."""
    command_name = 'random'
    command_args = [{"name":"value", "type":"list : 0 or 1","req":True}]

    funcName = "random"

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
    """Set repeat state to "value", "value" should be 0 or 1."""
    command_name = 'repeat'
    command_args = [{"name":"value", "type":"list 0 or 1","req":True}]

    funcName = "repeat"


class Fullscreen(Random):
    """Set video fullscreen to "value", "value" should be 0 (off) or 1 (on)."""
    command_name = 'fullscreen'
    command_args = [{"name":"value", "type":"list 0 or 1","req":True}]

    funcName = "fullscreen"


class Loadsubtitle(Random):
    """By default, load subtitle when it is available ("value"=1) or don't
    ("value"=0)."""
    command_name = 'loadsubtitle'
    command_args = [{"name":"value", "type":"list 0 or 1","req":True}]

    funcName = "loadsubtitle"


class CurrentSong(UnknownCommand):
    """Return informations on the current song, webradio or video info."""
    command_name = 'current'
    command_rvalue = ['SongList', 'WebradioList', 'VideoList']

    def execute(self):
        source = self.deejaydArgs["player"].get_playing_source_name()
        item = self.deejaydArgs["sources"].get_source(source).\
                    get_playing_item()
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


# Build the list of available commands
commands = {}

import sys
thismodule = sys.modules[__name__]
for itemName in dir(thismodule):
    try:
        item = getattr(thismodule, itemName)
        commands[item.command_name] = item
    except AttributeError:
        pass


# vim: ts=4 sw=4 expandtab
