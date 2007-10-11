from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory
from deejayd.mediadb.library import NotFoundException
from deejayd.sources.webradio import UnsupportedFormatException
from deejayd import sources
from deejayd.player._base import OptionNotFound,PlayerError

from os import path


class queueCommands:
    
    def __init__(self,deejayd_args):
        self.commands = []
        self.deejayd_args = deejayd_args
        self.__rspFactory = DeejaydXMLAnswerFactory()

    def addCommand(self,name,cmd,args):
        self.commands.append((name,cmd,args))

    def execute(self):
        motherRsp = None

        for (cmdName, cmdType, args) in self.commands:
            cmd = cmdType(cmdName, args, self.__rspFactory, self.deejayd_args)

            error = cmd.args_validation()
            if error != None:
                motherRsp = error
                self.__rspFactory.set_mother(motherRsp)
                break

            rsp = cmd.execute()
            if motherRsp == None:
                motherRsp = rsp
                self.__rspFactory.set_mother(motherRsp)

        return motherRsp.to_xml()


class UnknownCommand:
    command_args = []
    command_rvalue = 'Ack'

    def __init__(self, cmdName, args,
                 rspFactory = None, deejayd_args = None):
        self.name = cmdName
        self.args = args
        self.deejayd_args = deejayd_args
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

    def args_validation(self):
        for arg in self.__class__.command_args:
            if arg['name'] in self.args:
                # FIXME need to remove this
                if self.args[arg['name']] == None: 
                    self.args[arg['name']] = "" 

                value = self.args[arg['name']]
                if isinstance(value,list) and "mult" not in arg:
                    return self.get_error_answer(\
                        "arg %s can not be a list" % (arg['name'],))
                elif not isinstance(value,list):
                    value = [value]
                    if "mult" in arg:
                        self.args[arg['name']] = value

                for v in value:
                    if arg['type'] == "string":
                        try: v.split()
                        except AttributeError:
                            return self.get_error_answer(\
                                "arg %s (%s) is not a string" % (arg['name'],\
                                str(v)))

                    elif arg['type'] == "int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            return self.get_error_answer(\
                                "arg %s (%s) is not a int" % (arg['name'],\
                                str(v)))

                    elif arg['type'] == "enum_str":
                        if v not in arg['values']:
                            return self.get_error_answer(\
                                "arg %s is not in the possible list"\
                                % (arg['name'],))

                    elif arg['type'] == "enum_int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            return self.get_error_answer(\
                                "arg %s is not a int" % (arg['name'],))
                        else: 
                            if v not in arg['values']:
                                return self.get_error_answer(\
                                    "arg %s is not in the possible list"\
                                    % (arg['name'],))

                    elif arg['type'] == "regexp":
                        import re
                        if not re.compile(arg['value']).search(v):
                            return self.get_error_answer(\
                              "arg %s (%s) not match to the regular exp (%s)" %
                                (arg['name'],v,arg['value']))

            elif arg['req']:
                return self.get_error_answer("arg %s is mising" % arg['name'])
            else: 
                self.args[arg['name']] = arg['default']
        return None


class Close(UnknownCommand):
    """Close the connection with the server"""
    command_name = 'close'

    def execute(self):
        # Connection is closed after the answer has been written (in
        # deejaydProtocol.py).
        return self.get_ok_answer()


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
            try: self.deejayd_args["sources"].set_source(self.args["mode"])
            except sources.UnknownSourceException:
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
  * dvd : _int_ id of the current dvd
  * random : 0 (not activated) or 1 (activated)
  * repeat : 0 (not activated) or 1 (activated)
  * volume : `[0-100]` current volume value
  * state : [play-pause-stop] the current state of the player
  * mediapos : _int_ the position of the current media file (if exists)
  * mediaid : _int_ the id of the current media file
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
        status = self.deejayd_args["player"].get_status()
        status.extend(self.deejayd_args["sources"].get_status())
        status.extend(self.deejayd_args["audio_library"].get_status())
        if self.deejayd_args["video_library"]:
            status.extend(self.deejayd_args["video_library"].get_status())

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
        stats = self.deejayd_args["db"].get_stats()
        return self.get_keyvalue_answer(stats)


class GetMode(UnknownCommand):
    """For each available source, shows if it is activated or not. The answer
    consists in :
  * playlist : 0 or 1 (actually always 1 because it does not need optionnal
               dependencies)
  * webradio : 0 or 1 (needs gst-plugins-gnomevfs to be activated)
  * video : 0 or 1 (needs video dependencies, X display and needs to be
            activated in configuration)
  * dvd : 0 or 1 (media backend has to be able to read dvd)"""
    command_name = 'getMode'
    command_rvalue = 'KeyValue'

    def execute(self):
        avSources = self.deejayd_args["sources"].get_available_sources()
        modes = []
        for s in ("playlist","webradio","video","dvd"):
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
        update_id = self.deejayd_args["audio_library"].update()
        return self.get_keyvalue_answer([('audio_updating_db', update_id)])


class UpdateVideoLibrary(UnknownCommand):
    """Update the video library.
  * video_updating_db : the id of this task. It appears in the status until the
    update are completed."""
    command_name = 'videoUpdate'
    command_rvalue = 'KeyValue'


    def execute(self):
        if self.deejayd_args["video_library"]:
            update_id = self.deejayd_args["video_library"].update()
            return self.get_keyvalue_answer([('video_updating_db', update_id)])
        else: return self.get_error_answer('Video support disabled.')


class GetDir(UnknownCommand):
    """List the files of the directory supplied as argument."""
    command_name = 'getdir'
    command_args = [{"name":"directory", "type":"string", "req":False, \
                     "default":""}]
    command_rvalue = 'FileAndDirList'

    def execute(self):
        try: content = self.deejayd_args['audio_library'].\
                            get_dir_content(self.args["directory"])
        except NotFoundException:
            return self.get_error_answer('Directory not found in the database')
        else:
            rsp = self.get_answer('FileAndDirList')
            rsp.set_directory(self.args["directory"])
            rsp.set_filetype('song')

            rsp.set_files(content['files'])
            rsp.set_directories(content['dirs'])

            return rsp


class Search(UnknownCommand):
    """Search files where "type" contains "txt" content."""
    command_name = 'search'
    command_args = [{"name":"type", "type":"enum_str", 
                     "values": ('all','title','genre','filename','artist',
                                'album'),"req":True},
                    {"name":"txt", "type":"string", "req":True}]
    command_rvalue = 'FileAndDirList'

    def execute(self):
        type = "type" in self.args.keys() and self.args["type"] or ""
        if "txt" in self.args.keys() and self.args["txt"]:
            content = self.args["txt"]
        else:
            return self.get_error_answer('You have to enter text')

        try: list = self.deejayd_args["audio_library"].search(type,content)
        except NotFoundException:
            return self.get_error_answer('type %s is not supported' % (type,))
        else:
            rsp = self.get_answer('FileAndDirList')
            rsp.set_filetype('song')

            rsp.set_files(list)
            return rsp


class GetVideoDir(GetDir):
    """Lists the files in video dir "directory"."""
    command_name = 'getvideodir'
    command_args = [{"name":"directory","type":"string","req":False,\
                     "default": ""}]
    command_rvalue = 'FileAndDirList'

    def execute(self):
        if not self.deejayd_args["video_library"]:
            return self.get_error_answer('Video support disabled.')

        dir = self.args["directory"]
        try: list = self.deejayd_args["video_library"].get_dir_content(dir)
        except NotFoundException:
            return self.get_error_answer('Directory not found in the database')
        else:
            rsp = self.get_answer('FileAndDirList')
            rsp.set_filetype('video')
            rsp.set_directory(dir)

            rsp.set_files(list['files'])
            rsp.set_directories(list['dirs'])

            return rsp




###################################################
#  Video Commands                              #
###################################################

class SetVideoDir(UnknownCommand):
    """Set the current video directory to "directory"."""
    command_name = 'setvideodir'
    command_args = [{"name":"directory", "type":"string", "req":True}]

    def execute(self):
        try:
            self.deejayd_args["sources"].get_source("video").\
                    set_directory(self.args["directory"])
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
        playlistName = self.args["name"]
        if not playlistName and self.__class__.requirePlaylist:
            return self.get_error_answer('You must enter a playlist name')

        try:
            getattr(self.deejayd_args["sources"].get_source("playlist"),
                    self.__class__.funcName)(playlistName)
            return self.get_ok_answer()
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')


class PlaylistClear(SimplePlaylistCommand):
    """Clear the current playlist."""
    command_name = 'playlistClear'
    command_args = [{"name":"name","type":"string","req":False,"default":None}]

    funcName = "clear"
    requirePlaylist = False


class PlaylistShuffle(SimplePlaylistCommand):
    """Shuffle the current playlist."""
    command_name = 'playlistShuffle'
    command_args = [{"name":"name","type":"string","req":False,"default":None}]

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
                    {"name":"pos", "type":"int", "req":False,"default": None}]

    def execute(self):
        pos = self.args["pos"] and int(self.args["pos"]) or None
        try: self.deejayd_args["sources"].get_source("playlist").\
                load_playlist(self.args["name"], pos)
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')
        else: return self.get_ok_answer()


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
                self.deejayd_args["sources"].get_source("playlist").\
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
                    {"name":"pos", "type":"int", "req":False,"default":None},
                    {"name":"name", "type":"string","req":False,"default":None}]

    def execute(self):
        pos = self.args["pos"] and int(self.args["pos"]) or None
        try: self.deejayd_args["sources"].get_source("playlist").\
                add_path(self.args['path'],self.args["name"],pos)
        except sources._base.ItemNotFoundException:
            return self.get_error_answer('%s not found' % (file,))
        else: return self.get_ok_answer()


class PlaylistInfo(UnknownCommand):
    """Return the content of the playlist "name". If no name is given, return
    the content of the current playlist."""
    command_name = 'playlistInfo'
    command_args = [{"name":"name","type":"string","req":False,"default":None}]
    command_rvalue = 'MediaList'

    def execute(self):
        try: songs = self.deejayd_args["sources"].get_source("playlist").\
                get_content(self.args["name"])
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')
        else:
            rsp = self.get_answer('MediaList')
            rsp.set_mediatype("song")
            rsp.set_medias(songs)
            return rsp


class PlaylistRemove(UnknownCommand):
    """Remove songs with ids passed as argument ("id"), from the playlist
    "name". If no name are given, remove songs from current playlist."""
    command_name = 'playlistRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True},
                    {"name":"name","type":"string","req":False,"default":None}]

    def execute(self):
        for nb in self.args['id']:
            try: self.deejayd_args["sources"].get_source("playlist").\
                    delete(int(nb),"id",self.args["name"])
            except sources._base.ItemNotFoundException:
                return self.get_error_answer('Song not found')
            except sources.playlist.PlaylistNotFoundException:
                return self.get_error_answer('Playlist not found')
            else: return self.get_ok_answer()


class PlaylistMove(UnknownCommand):
    """Move song with id "id" to position "new_position"."""
    command_name = 'playlistMove'
    command_args = [{"name":"id", "type":"int", "req":True},
                    {"name":"new_position", "type":"int", "req":True}]

    def execute(self):
        try: self.deejayd_args["sources"].get_source("playlist").move(\
                int(self.args["id"]),int(self.args["new_position"]))
        except sources._base.ItemNotFoundException:
            return self.get_error_answer('Song not found')
        else: return self.get_ok_answer()


class PlaylistList(UnknownCommand):
    """Return the list of recorded playlists."""
    command_name = 'playlistList'
    command_rvalue = 'MediaList'

    def execute(self):
        playlists=self.deejayd_args["sources"].get_source("playlist").get_list()
        rsp = self.get_answer('MediaList')
        rsp.set_mediatype('playlist')
        for pl in playlists: 
            rsp.add_media({"name":pl})

        return rsp


###################################################
#  Webradios Commands                             #
###################################################
class WebradioList(UnknownCommand):
    """Return the list of recorded webradios."""
    command_name = 'webradioList'
    command_rvalue = 'MediaList'

    def execute(self):
        try: self.wr_source=self.deejayd_args["sources"].get_source("webradio")
        except sources.sources.UnknownSourceException:
            return self.get_error_answer("Webradio support not available")
        wrs = self.wr_source.get_content()

        rsp = self.get_answer('MediaList')
        rsp.set_mediatype('webradio')
        for wr in wrs:
            rsp.add_media(wr)

        return rsp


class WebradioClear(UnknownCommand):
    """Remove all recorded webradios."""
    command_name = 'webradioClear'

    def execute(self):
        try: self.wr_source=self.deejayd_args["sources"].get_source("webradio")
        except sources.sources.UnknownSourceException:
            return self.get_error_answer("Webradio support not available")
        self.wr_source.clear()

        return self.get_ok_answer()


class WebradioDel(UnknownCommand):
    """Remove webradios with id equal to "id"."""
    command_name = 'webradioRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

    def execute(self):
        try: self.wr_source=self.deejayd_args["sources"].get_source("webradio")
        except sources.sources.UnknownSourceException:
            return self.get_error_answer("Webradio support not available")

        for id in self.args["id"]:
            try: self.wr_source.delete(int(id))
            except sources.webradio.WrNotFoundException:
                return self.get_error_answer('Webradio not found')
            else: return self.get_ok_answer()


class WebradioAdd(UnknownCommand):
    """Add a webradio. Its name is "name" and the url of the webradio is
    "url". You can pass a playlist for "url" argument (.pls and .m3u format
    are supported)."""
    command_name = 'webradioAdd'
    command_args = [{"name":"url", "type":"string", "req":True},
                    {"name":"name", "type":"string", "req":True}]

    def execute(self):
        try: self.wr_source=self.deejayd_args["sources"].get_source("webradio")
        except sources.sources.UnknownSourceException:
            return self.get_error_answer("Webradio support not available")

        try: self.wr_source.add(self.args["url"],self.args["name"])
        except UnsupportedFormatException:
            return self.get_error_answer('Webradio URI not supported')
        except NotFoundException:
            return self.get_error_answer('Webradio info could not be retrieved')
        else: return self.get_ok_answer()


###################################################
#  Queue Commands                              #
###################################################
class QueueAdd(UnknownCommand):
    """Load files or directories passed as arguments ("path") at the position
    "pos" in the queue."""
    command_name = 'queueAdd'
    command_args = [{"mult":True, "name":"path", "type":"string", "req":True},
                    {"name":"pos", "type":"int", "req":False, "default":None}]

    def execute(self):
        pos = self.args["pos"] and int(self.args["pos"]) or None
        try: self.deejayd_args["sources"].get_source("queue").\
                add_path(self.args["path"],pos)
        except sources._base.ItemNotFoundException:
            return self.get_error_answer('%s not found' % (file,))
        else: return self.get_ok_answer()


class QueueLoadPlaylist(UnknownCommand):
    """Load playlists passed in arguments ("name") at the position "pos" in
    the queue."""
    command_name = 'queueLoadPlaylist'
    command_args = [{"name":"name", "type":"string", "req":True, "mult":True},
                    {"name":"pos", "type":"int", "req":False, "default":None}]

    def execute(self):
        pos = self.args["pos"] and int(self.args["pos"]) or None
        try: self.deejayd_args["sources"].get_source("queue").\
                              load_playlist(self.args["name"],pos)
        except sources.playlist.PlaylistNotFoundException:
            return self.get_error_answer('Playlist not found')
        else: return self.get_ok_answer()


class QueueInfo(PlaylistInfo):
    """Return the content of the queue."""
    command_name = 'queueInfo'
    command_rvalue = 'MediaList'

    def execute(self):
        songs = self.deejayd_args["sources"].get_source("queue").get_content()
        rsp = self.get_answer('MediaList')
        rsp.set_mediatype("song")
        rsp.set_medias(songs)
        return rsp


class QueueRemove(UnknownCommand):
    """Remove songs with ids passed as argument ("id"), from the queue."""
    command_name = 'queueRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

    def execute(self):
        for id in self.args["id"]:
            try: self.deejayd_args["sources"].get_source("queue").delete(\
                                                                int(id))
            except sources._base.ItemNotFoundException:
                return self.get_error_answer('Song not found')

        return self.get_ok_answer()


class QueueClear(UnknownCommand):
    """Remove all songs from the queue."""
    command_name = 'queueClear'

    def execute(self):
        self.deejayd_args["sources"].get_source("queue").clear()
        return self.get_ok_answer()


###################################################
#       DVD Commands                              #
###################################################
class DvdLoad(UnknownCommand):
    """Load the content of the dvd player."""
    command_name = 'dvdLoad'

    def execute(self):
        from deejayd.sources.dvd import DvdError
        try: self.deejayd_args["sources"].get_source("dvd").load()
        except DvdError,msg: return self.get_error_answer(msg)
        return self.get_ok_answer()


class DvdInfo(UnknownCommand):
    """Get the content of the current dvd."""
    command_name = 'dvdInfo'
    command_rvalue = 'DvdInfo'

    def execute(self):
        rsp = self.get_answer('DvdInfo')
        content = self.deejayd_args["sources"].get_source("dvd").get_content() \
                    or {}
        rsp.set_info(content)
        return rsp


###################################################
#    Player Commands                              #
###################################################
class SimplePlayerCommand(UnknownCommand):

    def execute(self):
        getattr(self.deejayd_args["player"],self.name)()
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
    """Begin playing at media file with id "id" or toggle play/pause."""
    command_name = 'play'
    command_args = [{"name":"id", "type":"regexp", \
                     "value":"^\w{1,}|\w{1,}\.\w{1,}$","req":False,\
                     "default":-1},
                 {"name":"id_type","type":"enum_str",\
                  "values":("dvd_id","track","chapter","id","pos"),\
                  "req":False,"default":"id"},
                 {"name":"source","type":"string","req":False,"default":None},
                 {"name":"alang","type":"int","req":False,"default":None},
                 {"name":"slang","type":"int","req":False,"default":None}]

    def execute(self):
        if self.args["id"] == -1:
            self.deejayd_args["player"].play()
        else:
            if self.args["id_type"] != "dvd_id":
                try: id = int(self.args["id"])
                except ValueError: 
                    return self.get_error_answer("Bad value for id parm")
            else: id = self.args["id"]

            self.deejayd_args["player"].go_to(id,\
                    self.args["id_type"], self.args["source"])
        return self.get_ok_answer()


class SetAlang(UnknownCommand):
    """Select audio language"""
    command_name = 'setAlang'
    command_args = [{"name":"lang_idx", "type":"int", "req":True}]

    def execute(self):
        try: self.deejayd_args["player"].set_alang(int(self.args["lang_idx"]))
        except PlayerError:
            return self.get_error_answer("Unable to change audio channel")
        return self.get_ok_answer()


class SetSlang(UnknownCommand):
    """Select subtitle language"""
    command_name = 'setSlang'
    command_args = [{"name":"lang_idx", "type":"int", "req":True}]

    def execute(self):
        try: self.deejayd_args["player"].set_slang(int(self.args["lang_idx"]))
        except PlayerError:
            return self.get_error_answer("Unable to change subtitle channel")
        return self.get_ok_answer()


class Volume(UnknownCommand):
    """Set volume to "volume". The volume range is 0-100."""
    command_name = 'setVolume'
    command_args = [{"name":"volume", "type":"enum_int", "req":True, 
                     "values": range(0,101)}]

    def execute(self):
        self.deejayd_args["player"].set_volume(int(self.args["volume"]))
        return self.get_ok_answer()


class Seek(UnknownCommand):
    """Seeks to the position "time" (in seconds) of the current song (in
    playlist mode)."""
    command_name = 'seek'
    command_args = [{"name":"time", "type":"int", "req":True}]

    def execute(self):
        self.deejayd_args["player"].set_position(int(self.args["time"]))
        return self.get_ok_answer()


class SetOption(UnknownCommand):
    """Set player options "name" to "value", "value" should be 0 or 1.
       Available options are :
       * random
       * repeat
       if you are video support:
       * fullscreen
       You can pass several options in the same command"""
    command_name = 'setOption'
    command_args = [{"name":"option_name", "type":"enum_str","req":True,
                     "values":("random","repeat","fullscreen")},
                    {"name":"option_value","type":"enum_int","req":True,
                     "values":(0,1)} ]

    def execute(self):
        try: self.deejayd_args["player"].set_option(self.args["option_name"],\
                                                 int(self.args["option_value"]))
        except OptionNotFound:
            return self.get_error_answer('option %s does not exist' % name)

        return self.get_ok_answer()


class CurrentSong(UnknownCommand):
    """Return informations on the current song, webradio or video info."""
    command_name = 'current'
    command_rvalue = 'MediaList'

    def execute(self):
        item = self.deejayd_args["player"].get_playing()
        rsp = self.get_answer('MediaList')
        if item:
            rsp.set_mediatype(item["type"])
            rsp.add_media(item)

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
