from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory
from deejayd.mediadb.library import NotFoundException
from deejayd.sources.webradio import UnsupportedFormatException
from deejayd import sources
from deejayd.player import OptionNotFound

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
                self.__rspFactory.set_mother(motherRsp)

        return motherRsp.to_xml()


class UnknownCommand:

    def __init__(self, cmdName, args,
                 rspFactory = None, deejaydArgs = None):
        self.name = cmdName
        self.args = args
        self.deejaydArgs = deejaydArgs
        self.__rspFactory = rspFactory or DeejaydXMLAnswerFactory()

    def execute(self):
        return self.get_error_answer("Unknown command : %s" % (self.name,))

    def get_answer(self, type):
        return self.__rspFactory.get_deejayd_xml_answer(type, self.name)

    def get_error_answer(self, errorString):
        error = self.get_answer('error')
        error.set_error_text(errorString)
        return error

    def get_ok_answer(self):
        return self.get_answer('Ack')

    def get_keyvalue_answer(self, keyValueList):
        rsp = self.get_answer('KeyValue')
        rsp.set_pairs(dict(keyValueList))
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
        return self.get_ok_answer()


class Mode(UnknownCommand):
    """Change the player mode. Possible values are :
  * playlist : to manage and listen songs
  * video : to manage and wath video file
  * webradio : to manage and listen webradios"""
    command_name = 'setMode'
    command_args = [{"name":"mode", "type":"string", "req":True}]

    def execute(self):
        if "mode" not in self.args.keys():
             return self.get_error_answer('You have to choose a mode')
        else:
            try: self.deejaydArgs["sources"].set_source(self.args["mode"])
            except sources.sources.UnknownSourceException:
                return self.get_error_answer('Unknown mode')
            else: return self.get_ok_answer()


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
  * mode : [playlist-webradio-video] the current mode
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

        return self.get_keyvalue_answer(status)


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
        return self.get_keyvalue_answer(stats)


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

        return self.get_keyvalue_answer(modes)


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
        return self.get_keyvalue_answer([('audio_updating_db', update_id)])


class UpdateVideoLibrary(UnknownCommand):
    """Update the video library.
  * video_updating_db : the id of this task. It appears in the status until the
    update are completed."""
    command_name = 'videoUpdate'
    command_rvalue = 'KeyValue'


    def execute(self):
        if self.deejaydArgs["video_library"]:
            update_id = self.deejaydArgs["video_library"].update()
            return self.get_keyvalue_answer([('video_updating_db', update_id)])
        else: return self.get_error_answer('Video support disabled.')


class GetDir(UnknownCommand):
    """List the files of the directory supplied as argument."""
    command_name = 'getdir'
    command_args = [{"name":"directory", "type":"string", "req":False}]
    command_rvalue = 'FileList'

    def execute(self):
        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: list = self.deejaydArgs['audio_library'].get_dir_content(dir)
        except NotFoundException:
            return self.get_error_answer('Directory not found in the database')
        else:
            rsp = self.get_answer('FileList')
            rsp.set_directory(dir)

            filesAndDirs = self.getFileAndDirs(list)
            rsp.set_files(filesAndDirs['files'])
            rsp.set_directories(filesAndDirs['dirs'])

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
            return self.get_error_answer('You have to enter text')

        try: list = self.deejaydArgs["audio_library"].search(type,content)
        except NotFoundException:
            return self.get_error_answer('type %s is not supported' % (type,))
        else:
            rsp = self.get_answer('FileList')

            filesAndDirs = self.getFileAndDirs(list)
            rsp.set_files(filesAndDirs['files'])
            rsp.set_directories(filesAndDirs['dirs'])

            return rsp


class GetVideoDir(GetDir):
    """Lists the files in video dir "directory"."""
    command_name = 'getvideodir'
    command_args = [{"name":"directory", "type":"string", "req":True}]
    command_rvalue = 'FileList'

    def execute(self):
        if not self.deejaydArgs["video_library"]:
            return self.get_error_answer('Video support disabled.')

        dir = "directory" in self.args.keys() and self.args["directory"] or ""
        try: list = self.deejaydArgs["video_library"].get_dir_content(dir)
        except NotFoundException:
            return self.get_error_answer('Directory not found in the database')
        else:
            rsp = self.get_answer('FileList')
            rsp.set_directory(dir)

            videosAndDirs = self.getVideosAndDirs(list)
            rsp.set_videos(videosAndDirs['videos'])
            rsp.set_directories(videosAndDirs['dirs'])

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
            return self.get_ok_answer()
        except NotFoundException:
            return self.get_error_answer('Directory not found in the database')
        except sources.sources.UnknownSourceException:
            return self.get_error_answer('Video support disabled')


###################################################
#  Playlist Commands                              #
###################################################

class SimplePlaylistCommand(UnknownCommand):
    funcName = None
    requirePlaylist = True

    def execute(self):
        playlistName = "name" in self.args.keys() and self.args["name"] or None
        if not playlistName and self.__class__.requirePlaylist:
            return self.get_error_answer('You must enter a playlist name')

        try:
            getattr(self.deejaydArgs["sources"].get_source("playlist"),
                    self.__class__.funcName)(playlistName)
            return self.get_ok_answer()
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')


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
                return self.get_error_answer(
                    'Need an integer for position argument')
        plsNames = "name" in self.args.keys() and self.args["name"] or ""
        if isinstance(plsNames, str):
            plsNames = [plsNames]

        try:
            self.deejaydArgs["sources"].get_source("playlist").\
                                                    load_playlist(plsNames, pos)
            return self.get_ok_answer()
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')


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
                return self.get_ok_answer()
            except sources.playlist.PlaylistNotFoundException:
                return self.get_error_answer('Playlist not found')


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
                return self.get_error_answer(
                    'Need an integer for position argument')
        files = "path" in self.args.keys() and self.args["path"] or ""
        if isinstance(files, str):
            files = [files]
        playlistName = "name" in self.args.keys() and self.args["name"] or None

        try: 
            self.deejaydArgs["sources"].get_source("playlist").\
                add_path(files,playlistName,pos)
            return self.get_ok_answer()
        except sources.unknown.ItemNotFoundException:
            return self.get_error_answer('%s not found' % (file,))


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
            return self.get_error_answer('Playlist not found')
        else:
            rsp = self.get_answer('SongList')
            rsp.set_songs(self.formatSongs(songs))
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

    def execute(self):
        numbs = "id" in self.args.keys() and self.args["id"] or []
        if isinstance(numbs, str):
            numbs = [numbs]
        playlistName = "name" in self.args.keys() and self.args["name"] or None

        for nb in numbs:
            try: nb = int(nb)
            except ValueError:
                return self.get_error_answer(\
                                    'Need an integer for argument number')

            try: self.deejaydArgs["sources"].get_source("playlist").\
                    delete(nb,"Id",playlistName)
            except sources.unknown.ItemNotFoundException:
                return self.get_error_answer('Song not found')
            except sources.playlist.PlaylistNotFoundException:
                return self.get_error_answer('Playlist not found')
            else: return self.get_ok_answer()


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
            return self.get_error_answer('Need two integers as argument : id \
                and newPosition')

        try: self.deejaydArgs["sources"].get_source("playlist").move(id,newPos)
        except sources.unknown.ItemNotFoundException:
            return self.get_error_answer('Song not found')
        else: return self.get_ok_answer()


class PlaylistList(UnknownCommand):
    """Return the list of recorded playlists."""
    command_name = 'playlistList'
    command_rvalue = 'PlaylistList'

    def execute(self):
        playlists=self.deejaydArgs["sources"].get_source("playlist").get_list()
        rsp = self.get_answer('PlaylistList')
        for pl in playlists: 
            rsp.add_playlist(pl)

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
            except sources.sources.UnknownSourceException:pass


class WebradioList(WebradioCommand):
    """Return the list of recorded webradios."""
    command_name = 'webradioList'
    command_rvalue = 'WebradioList'

    def execute(self):
        if not self.wrSource:
            return self.get_error_answer("Webradio support not available")

        wrs = self.wrSource.get_content()

        rsp = self.get_answer('WebradioList')
        for wr in wrs:
            wrdict = [("Title",wr["Title"]),("Id",wr["Id"]),("Pos",wr["Pos"]),("Url",wr["uri"])]
            rsp.add_webradio(dict(wrdict))

        return rsp


class WebradioClear(WebradioCommand):
    """Remove all recorded webradios."""
    command_name = 'webradioClear'

    def execute(self):
        if not self.wrSource:
            return self.get_error_answer("Webradio support not available")

        self.wrSource.clear()
        return self.get_ok_answer()


class WebradioDel(WebradioCommand):
    """Remove webradios with id equal to "ids"."""
    command_name = 'webradioRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

    def execute(self):
        if not self.wrSource:
            return self.get_error_answer("Webradio support not available")

        numbs = "id" in self.args.keys() and self.args["id"] or []
        if isinstance(numbs, str):
            numbs = [numbs]

        for nb in numbs:
            try: id = int(nb)
            except ValueError: 
                return self.get_error_answer('Need an integer : id')
        
            try: self.wrSource.delete(id)
            except sources.webradio.WrNotFoundException:
                return self.get_error_answer('Webradio not found')
            else: return self.get_ok_answer()


class WebradioAdd(WebradioCommand):
    """Add a webradio. Its name is "name" and the url of the webradio is
    "url". You can pass a playlist for "url" argument (.pls and .m3u format
    are supported)."""
    command_name = 'webradioAdd'
    command_args = [{"name":"url", "type":"string", "req":True},
                    {"name":"name", "type":"string", "req":True}]

    def execute(self):
        if not self.wrSource:
            return self.get_error_answer("Webradio support not available")

        url = "url" in self.args.keys() and self.args["url"] or None
        wrname = "name" in self.args.keys() and self.args["name"] or None
        if not url or not wrname:
            return self.get_error_answer('Need two arguments : url and name')

        try: self.wrSource.add(url,wrname)
        except UnsupportedFormatException:
            return self.get_error_answer('Webradio URI not supported')
        except NotFoundException:
            return self.get_error_answer('Webradio info could not be retrieved')
        else: return self.get_ok_answer()


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
            return self.get_error_answer('Need an integer')

        self.deejaydArgs["player"].go_to(nb,"Id",True)
        return self.get_ok_answer()


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
                return self.get_error_answer(
                    'Need an integer for position argument')
        files = "path" in self.args.keys() and self.args["path"] or ""
        if isinstance(files, str):
            files = [files]

        try:
            self.deejaydArgs["sources"].get_source("queue").\
                add_path(files,pos)
            return self.get_ok_answer()
        except sources.unknown.ItemNotFoundException:
            return self.get_error_answer('%s not found' % (file,))


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
                return self.get_error_answer(
                    'Need an integer for position argument')
        plsNames = "name" in self.args.keys() and self.args["name"] or ""
        if isinstance(plsNames, str):
            plsNames = [plsNames]

        try: self.deejaydArgs["sources"].get_source("queue").\
                                                    load_playlist(plsNames,pos)
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')
        else: return self.get_ok_answer()


class QueueInfo(PlaylistInfo):
    """Return the content of the queue."""
    command_name = 'queueInfo'
    command_rvalue = 'SongList'

    def execute(self):
        songs = self.deejaydArgs["sources"].get_source("queue").get_content()
        rsp = self.get_answer('SongList')
        rsp.set_songs(self.formatSongs(songs))
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
                return self.get_error_answer('Need an integer for argument \
                        number')

            try: self.deejaydArgs["sources"].get_source("queue").delete(nb,"Id")
            except sources.unknown.ItemNotFoundException:
                return self.get_error_answer('Song not found')

        return self.get_ok_answer()


class QueueClear(WebradioCommand):
    """Remove all songs from the queue."""
    command_name = 'queueClear'

    def execute(self):
        self.deejaydArgs["sources"].get_source("queue").clear()
        return self.get_ok_answer()


###################################################
#    Player Commands                              #
###################################################
class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        getattr(self.deejaydArgs["player"],self.name)()
        return self.get_ok_answer()


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
    """Toggle pause on/off."""
    command_name = 'pause'


class Play(UnknownCommand):
    """Begin playing at song or webradio with id "id" or toggle play/pause."""
    command_name = 'play'
    command_args = [{"name":"id", "type":"int", "req":False}]

    def execute(self):
        nb = "id" in self.args.keys() and self.args["id"] or -1
        try:nb = int(nb)
        except ValueError:
            return self.get_error_answer('Need an integer')

        if nb == -1: self.deejaydArgs["player"].play()
        else: self.deejaydArgs["player"].go_to(nb,"Id")
        return self.get_ok_answer()


class Volume(UnknownCommand):
    """Set volume to "volume". The volume range is 0-100."""
    command_name = 'setVolume'
    command_args = [{"name":"volume", "type":"int", "req":True}]

    def execute(self):
        vol = "volume" in self.args.keys() and self.args["volume"] or None
        try:vol = int(vol)
        except ValueError:
            return self.get_error_answer('Need an integer')
        if vol < 0 or vol > 100:
            return self.get_error_answer('Volume must be an integer between 0 \
                and 100')

        self.deejaydArgs["player"].set_volume(vol)
        return self.get_ok_answer()


class Seek(UnknownCommand):
    """Seeks to the position "time" (in seconds) of the current song (in
    playlist mode)."""
    command_name = 'seek'
    command_args = [{"name":"time", "type":"int", "req":True}]

    def execute(self):
        t = "time" in self.args.keys() and self.args["time"] or None
        try: t = int(t)
        except ValueError:
            return self.get_error_answer('Need an integer')
        if t < 0:
            return self.get_error_answer('Need an integer > 0')

        self.deejaydArgs["player"].set_position(t)
        return self.get_ok_answer()


class SetOption(UnknownCommand):
    """Set player options "name" to "value", "value" should be 0 or 1.
       Available options are :
       * random
       * repeat
       if you are video support:
       * fullscreen
       * loadsubtitle
       You can pass several options in the same command"""
    command_name = 'setOption'
    command_args = [{"name":"option's name", "type":"list : 0 or 1","req":True}]

    def execute(self):
        for name in self.args.keys():
            try: value = int(self.args[name])
            except TypeError,ValueError:
                return self.get_error_answer('Need an integer')
            else:
                if value not in (0,1):
                    return self.get_error_answer('value has to be 0 or 1')

            try: self.deejaydArgs["player"].set_option(name,value)
            except OptionNotFound:
                return self.get_error_answer('option %s does not exist' % name)

        return self.get_ok_answer()


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
                rsp = self.get_answer('WebradioList')
                wrdict = [("Title",item["Title"]),("Id",item["Id"]),\
                    ("Pos",item["Pos"]),("Url",item["uri"])]
                rsp.add_webradio(dict(wrdict))
            elif source == "video":
                rsp = self.get_answer('VideoList')
                vdict = [("Title",item["Title"]),("Id",item["Id"]),\
                    ("Time",item["Time"])]
                rsp.add_video(dict(vdict))
            elif source == "playlist" or source == "queue":
                rsp = self.get_answer('SongList')
                sldict = [("Title",item["Title"]),("Id",item["Id"]),\
                    ("Pos",item["Pos"]),("Artist",item["Artist"]),\
                    ("Album",item["Album"]),("Time",item["Time"])]
                rsp.add_song(dict(sldict))
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
