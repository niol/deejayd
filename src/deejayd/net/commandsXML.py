# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from os import path

from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory
from deejayd import sources
from deejayd.interfaces import DeejaydError, DeejaydSignal


class queueCommands:

    def __init__(self, deejayd_core):
        self.commands = []
        self.deejayd_core = deejayd_core
        self.__rspFactory = DeejaydXMLAnswerFactory()
        self.__connector = None

    def addCommand(self,name,cmd,args):
        self.commands.append((name,cmd,args))

    def register_connector(self, connector):
        self.__connector = connector

    def execute(self):
        motherRsp = None

        for (cmdName, cmdType, args) in self.commands:
            cmd = cmdType(cmdName, args, self.__rspFactory, self.deejayd_core,
                          self.__connector)

            error = cmd.args_validation()
            if error != None:
                motherRsp = error
                self.__rspFactory.set_mother(motherRsp)
                break

            rsp = cmd.execute()
            if motherRsp == None:
                motherRsp = rsp
                self.__rspFactory.set_mother(motherRsp)

        del self.__rspFactory
        return motherRsp.to_xml()


class UnknownCommand:
    command_args = []
    command_rvalue = 'Ack'

    def __init__(self, cmdName, args, rspFactory=None,
                 deejayd_core=None, connector=None):
        self.name = cmdName
        self.args = args
        self.connector = connector
        self.deejayd_core = deejayd_core
        self.__rspFactory = rspFactory or DeejaydXMLAnswerFactory()

    def execute(self):
        try: rsp = self._execute()
        except DeejaydError, err:
            return self.get_error_answer(str(err))
        else:
            if rsp == None:
                return self.get_ok_answer()
            return rsp

    def _execute(self):
        return self.get_error_answer(_("Unknown command : %s") % self.name)

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
                        _("Arg %s can not be a list") % arg['name'])
                elif not isinstance(value,list):
                    value = [value]
                    if "mult" in arg:
                        self.args[arg['name']] = value

                for v in value:
                    if arg['type'] == "string":
                        try: v.split()
                        except AttributeError:
                            return self.get_error_answer(\
                                _("Arg %s (%s) is not a string") % \
                                    (arg['name'], str(v)))

                    elif arg['type'] == "int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            return self.get_error_answer(\
                                _("Arg %s (%s) is not a int") % (arg['name'],\
                                str(v)))

                    elif arg['type'] == "enum_str":
                        if v not in arg['values']:
                            return self.get_error_answer(\
                                _("Arg %s (%s) is not in the possible list")\
                                % (arg['name'],str(v)))

                    elif arg['type'] == "enum_int":
                        try: v = int(v)
                        except (ValueError,TypeError):
                            return self.get_error_answer(\
                                _("Arg %s (%s) is not a int") %\
                                (arg['name'],str(v)))
                        else:
                            if v not in arg['values']:
                                return self.get_error_answer(\
                                _("Arg %s (%s) is not in the possible list")\
                                % (arg['name'],str(v)))

                    elif arg['type'] == "regexp":
                        import re
                        if not re.compile(arg['value']).search(v):
                            return self.get_error_answer(\
                            _("Arg %s (%s) not match to the regular exp (%s)") %
                                (arg['name'],v,arg['value']))

            elif arg['req']:
                return self.get_error_answer(_("Arg %s is mising")%arg['name'])
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
  * dvd : to wath dvd
  * webradio : to manage and listen webradios"""
    command_name = 'setMode'
    command_args = [{"name":"mode", "type":"string", "req":True}]

    def _execute(self):
        self.deejayd_core.set_mode(self.args["mode"], objanswer=False)


class Status(UnknownCommand):
    """Return status of deejayd. Given informations are :
  * playlist : _int_ id of the current playlist
  * playlistlength : _int_ length of the current playlist
  * playlisttimelength : _int_ time length of the current playlist
  * webradio : _int_ id of the current webradio list
  * webradiolength : _int_ number of recorded webradio
  * queue : _int_ id of the current queue
  * queuelength : _int_ length of the current queue
  * queuetimelength : _int_ time length of the current queue
  * video : _int_ id of the current video list
  * videolength : _int_ length of the current video list
  * videotimelength : _int_ time length of the current video list
  * dvd : _int_ id of the current dvd
  * random : 0 (not activated) or 1 (activated)
  * repeat : 0 (not activated) or 1 (activated)
  * volume : `[0-100]` current volume value
  * state : [play-pause-stop] the current state of the player
  * current : _int_:_int_:_str_ current media pos : current media file id :
                                playing source name
  * time : _int_:_int_ position:length of the current media file
  * mode : [playlist-webradio-video] the current mode
  * audio_updating_db : _int_ show when a audio library update is in progress
  * audio_updating_error : _string_ error message that apppears when the
                           audio library update has failed
  * video_updating_db : _int_ show when a video library update is in progress
  * video_updating_error : _string_ error message that apppears when the
                           video library update has failed"""
    command_name = 'status'
    command_rvalue = 'KeyValue'

    def _execute(self):
        status = self.deejayd_core.get_status(objanswer=False)
        return self.get_keyvalue_answer(status)


class Stats(UnknownCommand):
    """Return statistical informations :
  * audio_library_update : UNIX time of the last audio library update
  * video_library_update : UNIX time of the last video library update
  * videos : number of videos known by the database
  * songs : number of songs known by the database
  * artists : number of artists in the database
  * albums : number of albums in the database"""
    command_name = 'stats'
    command_rvalue = 'KeyValue'

    def _execute(self):
        status = self.deejayd_core.get_stats(objanswer=False)
        return self.get_keyvalue_answer(status)


class GetMode(UnknownCommand):
    """For each available source, shows if it is activated or not. The answer
    consists in :
  * playlist : 0 or 1 (actually always 1 because it does not need optionnal
               dependencies)
  * queue : 0 or 1 (actually always 1 because it does not need optionnal
               dependencies)
  * webradio : 0 or 1 (needs gst-plugins-gnomevfs to be activated)
  * video : 0 or 1 (needs video dependencies, X display and needs to be
            activated in configuration)
  * dvd : 0 or 1 (media backend has to be able to read dvd)"""
    command_name = 'getMode'
    command_rvalue = 'KeyValue'

    def _execute(self):
        modes = self.deejayd_core.get_mode(objanswer=False)
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

    def _execute(self):
        rsp = self.deejayd_core.update_audio_library(objanswer=False)
        return self.get_keyvalue_answer(rsp)


class UpdateVideoLibrary(UnknownCommand):
    """Update the video library.
  * video_updating_db : the id of this task. It appears in the status until the
    update are completed."""
    command_name = 'videoUpdate'
    command_rvalue = 'KeyValue'


    def _execute(self):
        rsp = self.deejayd_core.update_video_library(objanswer=False)
        return self.get_keyvalue_answer(rsp)


class GetDir(UnknownCommand):
    """List the files of the directory supplied as argument."""
    command_name = 'getdir'
    command_args = [{"name":"directory", "type":"string", "req":False, \
                     "default":""}]
    command_rvalue = 'FileAndDirList'

    def _execute(self):
        root_dir, dirs, files = self.deejayd_core.get_audio_dir(\
                                    self.args["directory"], objanswer=False)
        rsp = self.get_answer('FileAndDirList')
        rsp.set_directory(root_dir)
        rsp.set_filetype('song')

        rsp.set_files(files)
        rsp.set_directories(dirs)

        return rsp


class Search(UnknownCommand):
    """Search files where "type" contains "txt" content."""
    command_name = 'search'
    command_args = [{"name":"type", "type":"enum_str",
                     "values": ('all','title','genre','filename','artist',
                                'album'),"req":True},
                    {"name":"txt", "type":"string", "req":True}]
    command_rvalue = 'FileAndDirList'

    def _execute(self):
        root_dir, dirs, files = self.deejayd_core.audio_search(\
            self.args['txt'], self.args['type'], objanswer=False)
        rsp = self.get_answer('FileAndDirList')
        rsp.set_filetype('song')
        rsp.set_files(files)
        return rsp


class GetVideoDir(GetDir):
    """Lists the files in video dir "directory"."""
    command_name = 'getvideodir'
    command_args = [{"name":"directory","type":"string","req":False,\
                     "default": ""}]
    command_rvalue = 'FileAndDirList'

    def _execute(self):
        root_dir, dirs, files = self.deejayd_core.get_video_dir(\
                                    self.args["directory"], objanswer=False)
        rsp = self.get_answer('FileAndDirList')
        rsp.set_filetype('video')
        rsp.set_directory(root_dir)

        rsp.set_files(files)
        rsp.set_directories(dirs)

        return rsp


###################################################
#  Video Commands                              #
###################################################

class SetVideo(UnknownCommand):
    """Set the current video directory to "directory"."""
    command_name = 'setvideo'
    command_args = [{"name":"type", "type":"enum_str",\
      "values": ("directory", "search"), "req":False, "default": "directory"},\
      {"name":"value", "type":"str", "req": False, "default": ""}]

    def _execute(self):
        self.deejayd_core.get_video().set(self.args['value'],\
            self.args['type'], objanswer=False)


class VideoInfo(UnknownCommand):
    """Set the current video directory to "directory"."""
    command_name = 'videoInfo'
    command_rvalue = 'MediaList'
    command_args = [{"name":"first","type":"int","req":False,"default":0},\
                    {"name":"length","type":"int","req":False,"default":-1}]

    def _execute(self):
        videos = self.deejayd_core.get_video().get(self.args["first"],\
            self.args["length"], objanswer=False)

        rsp = self.get_answer('MediaList')
        rsp.set_mediatype('video')
        rsp.set_medias(videos)
        if self.args["length"] != -1:
            status = self.deejayd_core.get_status(objanswer=False)
            rsp.set_total_length(status["videolength"])

        return rsp


###################################################
#  Playlist Commands                              #
###################################################

class SimplePlaylistCommand(UnknownCommand):
    func_name = None

    def _execute(self):
        pls = self.deejayd_core.get_playlist(self.args["name"])
        getattr(pls, self.func_name)(objanswer=False)


class PlaylistClear(SimplePlaylistCommand):
    """Clear the current playlist."""
    command_name = 'playlistClear'
    command_args = [{"name":"name","type":"string","req":False,"default":None}]
    func_name = "clear"


class PlaylistShuffle(SimplePlaylistCommand):
    """Shuffle the current playlist."""
    command_name = 'playlistShuffle'
    command_args = [{"name":"name","type":"string","req":False,"default":None}]
    func_name = "shuffle"


class PlaylistSave(UnknownCommand):
    """Save the current playlist to "name" in the database."""
    command_name = 'playlistSave'
    command_args = [{"name":"name", "type":"string", "req":True}]

    def _execute(self):
        pls = self.deejayd_core.get_playlist()
        pls.save(self.args["name"], objanswer=False)


class PlaylistLoad(UnknownCommand):
    """Load playlists passed as arguments ("name") at the position "pos"."""
    command_name = 'playlistLoad'
    command_args = [{"name":"name", "type":"string", "req":True, "mult":True},
                    {"name":"pos", "type":"int", "req":False,"default": None}]

    def _execute(self):
        pls = self.deejayd_core.get_playlist()
        pls.loads(self.args["name"], self.args["pos"], objanswer=False)


class PlaylistErase(UnknownCommand):
    """Erase playlists passed as arguments."""
    command_name = 'playlistErase'
    command_args = [{"mult":"true","name":"name", "type":"string", "req":True}]

    def _execute(self):
        self.deejayd_core.erase_playlist(self.args["name"], objanswer=False)


class PlaylistAdd(UnknownCommand):
    """Load files or directories passed as arguments ("path") at the position
    "pos" in the playlist "name". If no playlist name is provided, adds files
    in the current playlist."""
    command_name = 'playlistAdd'
    command_args = [{"mult":True,"name":"path", "type":"string", "req":True},
                    {"name":"pos", "type":"int", "req":False,"default":None},
                    {"name":"name", "type":"string","req":False,"default":None}]

    def _execute(self):
        pls = self.deejayd_core.get_playlist(self.args["name"])
        pls.add_songs(self.args["path"], self.args["pos"], objanswer=False)


class PlaylistInfo(UnknownCommand):
    """Return the content of the playlist "name". If no name is given, return
    the content of the current playlist."""
    command_name = 'playlistInfo'
    command_args = [{"name":"name","type":"string","req":False,"default":None},\
                    {"name":"first","type":"int","req":False,"default":0},\
                    {"name":"length","type":"int","req":False,"default":-1}]
    command_rvalue = 'MediaList'

    def _execute(self):
        pls = self.deejayd_core.get_playlist(self.args["name"])
        songs = pls.get(self.args["first"], self.args["length"], \
                        objanswer=False)

        rsp = self.get_answer('MediaList')
        rsp.set_mediatype("song")
        rsp.set_medias(songs)
        if self.args["length"] != -1:
            status = self.deejayd_core.get_status(objanswer=False)
            rsp.set_total_length(status["playlistlength"])
        return rsp


class PlaylistRemove(UnknownCommand):
    """Remove songs with ids passed as argument ("id"), from the playlist
    "name". If no name are given, remove songs from current playlist."""
    command_name = 'playlistRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True},
                    {"name":"name","type":"string","req":False,"default":None}]

    def _execute(self):
        pls = self.deejayd_core.get_playlist(self.args["name"])
        pls.del_songs(self.args['id'], objanswer=False)


class PlaylistMove(UnknownCommand):
    """Move song with id "id" to position "new_position"."""
    command_name = 'playlistMove'
    command_args = [{"name":"ids", "type":"int", "req":True, "mult": True},
                    {"name":"new_pos", "type":"int", "req":True}]

    def _execute(self):
        pls = self.deejayd_core.get_playlist()
        pls.move(self.args['ids'], self.args['new_pos'], objanswer=False)


class PlaylistList(UnknownCommand):
    """Return the list of recorded playlists."""
    command_name = 'playlistList'
    command_rvalue = 'MediaList'

    def _execute(self):
        pls = self.deejayd_core.get_playlist_list(objanswer=False)
        rsp = self.get_answer('MediaList')
        rsp.set_mediatype('playlist')
        rsp.set_medias(pls)
        return rsp


###################################################
#  Webradios Commands                             #
###################################################
class WebradioList(UnknownCommand):
    """Return the list of recorded webradios."""
    command_name = 'webradioList'
    command_rvalue = 'MediaList'
    command_args = [{"name":"first","type":"int","req":False,"default":0},\
                    {"name":"length","type":"int","req":False,"default":-1}]

    def _execute(self):
        wrs = self.deejayd_core.get_webradios().get(self.args["first"],\
            self.args["length"], objanswer=False)

        rsp = self.get_answer('MediaList')
        rsp.set_mediatype('webradio')
        rsp.set_medias(wrs)
        if self.args["length"] != -1:
            status = self.deejayd_core.get_status(objanswer=False)
            rsp.set_total_length(status["webradiolength"])
        return rsp


class WebradioClear(UnknownCommand):
    """Remove all recorded webradios."""
    command_name = 'webradioClear'

    def _execute(self):
        self.deejayd_core.get_webradios().clear(objanswer=False)


class WebradioDel(UnknownCommand):
    """Remove webradios with id equal to "id"."""
    command_name = 'webradioRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

    def _execute(self):
        wr = self.deejayd_core.get_webradios()
        wr.delete_webradios(self.args['id'], objanswer=False)


class WebradioAdd(UnknownCommand):
    """Add a webradio. Its name is "name" and the url of the webradio is
    "url". You can pass a playlist for "url" argument (.pls and .m3u format
    are supported)."""
    command_name = 'webradioAdd'
    command_args = [{"name":"url", "type":"string", "req":True},
                    {"name":"name", "type":"string", "req":True}]

    def _execute(self):
        wr = self.deejayd_core.get_webradios()
        wr.add_webradio(self.args['name'], self.args['url'], objanswer=False)


###################################################
#  Queue Commands                              #
###################################################
class QueueAdd(UnknownCommand):
    """Load files or directories passed as arguments ("path") at the position
    "pos" in the queue."""
    command_name = 'queueAdd'
    command_args = [{"mult":True, "name":"path", "type":"string", "req":True},
              {"name":"pos", "type":"int", "req":False, "default":None}]

    def _execute(self):
        queue = self.deejayd_core.get_queue()
        queue.add_medias(self.args["path"], self.args["pos"], objanswer=False)


class QueueLoadPlaylist(UnknownCommand):
    """Load playlists passed in arguments ("name") at the position "pos" in
    the queue."""
    command_name = 'queueLoadPlaylist'
    command_args = [{"name":"name", "type":"string", "req":True, "mult":True},
                    {"name":"pos", "type":"int", "req":False, "default":None}]

    def _execute(self):
        queue = self.deejayd_core.get_queue()
        queue.load_playlists(self.args["name"],\
            self.args["pos"], objanswer=False)


class QueueInfo(PlaylistInfo):
    """Return the content of the queue."""
    command_name = 'queueInfo'
    command_rvalue = 'MediaList'
    command_args = [{"name":"first","type":"int","req":False,"default":0},\
                    {"name":"length","type":"int","req":False,"default":-1}]

    def _execute(self):
        medias = self.deejayd_core.get_queue().get(self.args["first"],\
            self.args["length"], objanswer=False)

        rsp = self.get_answer('MediaList')
        rsp.set_mediatype("song")
        rsp.set_medias(medias)
        if self.args["length"] != -1:
            status = self.deejayd_core.get_status(objanswer=False)
            rsp.set_total_length(status["queuelength"])
        return rsp


class QueueRemove(UnknownCommand):
    """Remove songs with ids passed as argument ("id"), from the queue."""
    command_name = 'queueRemove'
    command_args = [{"mult":True, "name":"id", "type":"int", "req":True}]

    def _execute(self):
        queue = self.deejayd_core.get_queue()
        queue.del_songs(self.args['id'], objanswer=False)


class QueueClear(UnknownCommand):
    """Remove all songs from the queue."""
    command_name = 'queueClear'

    def _execute(self):
        self.deejayd_core.get_queue().clear(objanswer=False)


###################################################
#       DVD Commands                              #
###################################################
class DvdLoad(UnknownCommand):
    """Load the content of the dvd player."""
    command_name = 'dvdLoad'

    def _execute(self):
        self.deejayd_core.dvd_reload(objanswer=False)


class DvdInfo(UnknownCommand):
    """Get the content of the current dvd."""
    command_name = 'dvdInfo'
    command_rvalue = 'DvdInfo'

    def _execute(self):
        content = self.deejayd_core.get_dvd_content(objanswer=False)
        rsp = self.get_answer('DvdInfo')
        rsp.set_info(content)
        return rsp


###################################################
#    Player Commands                              #
###################################################
class SimplePlayerCommand(UnknownCommand):

    def _execute(self):
        getattr(self.deejayd_core, self.name)(objanswer=False)


class Next(SimplePlayerCommand):
    """Go to next song or webradio."""
    command_name = 'next'


class Previous(SimplePlayerCommand):
    """Go to previous song or webradio."""
    command_name = 'previous'


class Stop(SimplePlayerCommand):
    """Stop playing."""
    command_name = 'stop'


class PlayToggle(UnknownCommand):
    """Toggle play/pause."""
    command_name = 'playToggle'

    def _execute(self):
        self.deejayd_core.play_toggle(objanswer=False)


class GoTo(UnknownCommand):
    """Begin playing at media file with id "id" or toggle play/pause."""
    command_name = 'goto'
    command_args = [{"name":"id", "type":"regexp", \
                     "value":"^\w{1,}|\w{1,}\.\w{1,}$","req":True},
                 {"name":"id_type","type":"enum_str",\
                  "values":("dvd_id","track","chapter","id","pos"),\
                  "req":False,"default":"id"},
                 {"name":"source","type":"string","req":False,"default":None},]

    def _execute(self):
        self.deejayd_core.go_to(self.args['id'], self.args['id_type'],\
            self.args['source'], objanswer=False)


class SetPlayerOption(UnknownCommand):
    """Set player option for the current media
       Possible options are :
         * zoom : set zoom (video only), min=-85, max=400
         * audio_lang : select audio channel (video only)
         * sub_lang : select subtitle channel (video only)
         * av_offset : set audio/video offset (video only)
         * sub_offset : set subtitle/video offset (video only)"""
    command_name = 'setPlayerOption'
    command_args = [{"name":"option_name", "type":"string", "req":True},\
        {"name":"option_value", "type":"int", "req":True}]

    def _execute(self):
        self.deejayd_core.set_player_option(self.args['option_name'],\
            self.args['option_value'], objanswer=False)


class Volume(UnknownCommand):
    """Set volume to "volume". The volume range is 0-100."""
    command_name = 'setVolume'
    command_args = [{"name":"volume", "type":"enum_int", "req":True,
                     "values": range(0,101)}]

    def _execute(self):
        self.deejayd_core.set_volume(self.args['volume'], objanswer=False)


class Seek(UnknownCommand):
    """Seeks to the position "time" (in seconds) of the current song (in
    playlist mode)."""
    command_name = 'seek'
    command_args = [{"name":"time", "type":"int", "req":True}]

    def _execute(self):
        self.deejayd_core.seek(self.args['time'], objanswer=False)


class SetOption(UnknownCommand):
    """Set player options "name" to "value", "value" should be 0 or 1.
       Available options are :
       * random
       * qrandom (queue random)
       * repeat
       You can pass several options in the same command"""
    command_name = 'setOption'
    command_args = [{"name":"option_name", "type":"enum_str","req":True,
                     "values":("random","qrandom","repeat")},
                    {"name":"option_value","type":"enum_int","req":True,
                     "values":(0,1)} ]

    def _execute(self):
        self.deejayd_core.set_option(self.args['option_name'],\
            self.args['option_value'], objanswer=False)


class CurrentSong(UnknownCommand):
    """Return informations on the current song, webradio or video info."""
    command_name = 'current'
    command_rvalue = 'MediaList'

    def _execute(self):
        item = self.deejayd_core.get_current(objanswer=False)
        rsp = self.get_answer('MediaList')
        if len(item) == 1:
            rsp.set_mediatype(item[0]["type"])
        rsp.set_medias(item)

        return rsp


class SetSubscription(UnknownCommand):
    """Set subscribtion to "signal" signal notifications to "value" which should be 0 or 1."""
    command_name = 'setSubscription'
    command_args = ({"name":"signal", "type":"enum_str", "req":True,
                     "values":DeejaydSignal.SIGNALS},
                    {"name":"value", "type":"enum_int", "req":True,
                     "values":(0,1)} )

    def _execute(self):
        if self.args['value'] == '0':
            self.connector.set_not_signaled(self.args['signal'])
        elif self.args['value'] == '1':
            self.connector.set_signaled(self.args['signal'])
        return self.get_ok_answer()


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
