# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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

import os, re

from deejayd import __version__
from deejayd.interfaces import DeejaydError
from deejayd.mediafilters import *
from deejayd.rpc import Fault, INTERNAL_ERROR, INVALID_METHOD_PARAMS,\
                        DEEJAYD_PROTOCOL_VERSION
from deejayd.rpc.jsonbuilders import Get_json_filter
from deejayd.rpc.jsonparsers import Parse_json_filter
from deejayd.rpc.jsonrpc import JSONRPC, addIntrospection


def returns_answer(type, params = None):

    def returns_answer_instance(func):

        def returns_answer_func(*__args, **__kw):
            # verify arguments
            if params:
                for idx, p in enumerate(params):
                    try: arg = __args[idx+1]
                    except IndexError:
                        if p["req"] is True:
                            raise Fault(INVALID_METHOD_PARAMS,\
                                _("Param %s is required") % p["name"])
                        break
                    else:
                        if p['type'] == "int":
                            try: int(arg)
                            except (ValueError,TypeError):
                                raise Fault(INVALID_METHOD_PARAMS,\
                                    _("Param %s is not an int") % p["name"])
                        elif p['type'] in ("bool", "list", "dict"):
                            types = {"bool": bool, "dict": dict, "list": list}
                            if not isinstance(arg, types[p['type']]):
                                raise Fault(INVALID_METHOD_PARAMS,\
                                    _("Param %s has wrong type") % p["name"])
                        elif p['type'] == "int-list":
                            if not isinstance(arg, list):
                                raise Fault(INVALID_METHOD_PARAMS,\
                                    _("Param %s is not a list") % p["name"])
                            try: map(int, arg)
                            except (ValueError,TypeError):
                                raise Fault(INVALID_METHOD_PARAMS,\
                                  _("Param %s is not an int-list") % p["name"])
            try:
                res = func(*__args, **__kw)
            except DeejaydError, txt:
                raise Fault(INTERNAL_ERROR, str(txt))
            if type == "ack": res = True
            return {"type": type, "answer": res}

        returns_answer_func.__name__ = func.__name__
        returns_answer_func.__doc__ = func.__doc__
        returns_answer_func.answer_type = type
        returns_answer_func.params = params
        # build help
        p_desc = "\nNo arguments"
        if params:
            p_desc = "\nArguments : \n%s" %\
                "\n".join(["  * name '%s', type '%s', required '%s'" %\
                    (p["name"], p["type"], p["req"]) for p in params])
        returns_answer_func.help = """
Description :
    %(description)s
Answer type : %(answer)s %(p_desc)s""" % {\
                "description": func.__doc__,\
                "answer": type,\
                "p_desc": p_desc,\
            }
        # build signature
        p_dict = {
                "list": "array",
                "int-list": "array",
                "dict": "object",
                "string": "string",
                "int": "number",
                "bool": "boolean",
                "filter": "object",
                "sort": "array",
        }
        if params:
            signature = []
            opt_params = [p_dict[p["type"]] for p in params if not p["req"]]
            for i in range(len(opt_params)+1):
                s = ["object"]
                s.extend([p_dict[p["type"]] for p in params if p["req"]])
                s.extend(opt_params[:i])
                signature.append(s)
        else:
            signature = [["object"]]
        returns_answer_func.signature = signature

        return returns_answer_func

    return returns_answer_instance


class _DeejaydJSONRPC(JSONRPC):
    def __init__(self, deejayd = None):
        super(_DeejaydJSONRPC, self).__init__()
        self.deejayd_core = deejayd


class _DeejaydMainJSONRPC(_DeejaydJSONRPC):

    @returns_answer('ack')
    def jsonrpc_ping(self):
        """Does nothing, just replies with an acknowledgement that the
        command was received"""
        return None

    @returns_answer('ack', params=[{"name":"mode","type":"string","req":True}])
    def jsonrpc_setmode(self, mode):
        """Change the player mode. Possible values are :
  * playlist : to manage and listen songs in playlist
  * panel : to manage and listen songs in panel mode (like itunes)
  * video : to manage and wath video file
  * dvd : to wath dvd
  * webradio : to manage and listen webradios"""
        self.deejayd_core.set_mode(mode, objanswer=False)

    @returns_answer('dict')
    def jsonrpc_availablemodes(self):
        """For each available source, shows if it is activated or not.
   The answer consists in :
  * playlist : _bool_ true or false
  * panel : _bool_ true or false
  * webradio : _bool_ true or false (media backend has to be abble to read url streams)
  * video : _bool_ true or false (needs video dependencies, X display and needs to be activated in configuration)
  * dvd : _bool_ true or false (media backend has to be able to read dvd)"""
        return  dict(self.deejayd_core.get_mode(objanswer=False))

    @returns_answer('dict')
    def jsonrpc_status(self):
        """Return status of deejayd. Given informations are :
  * playlist : _int_ id of the current playlist
  * playlistlength : _int_ length of the current playlist
  * playlisttimelength : _int_ time length of the current playlist
  * playlistrepeat : _bool_ false (not activated) or true (activated)
  * playlistplayorder : inorder | random | onemedia | random-weighted
  * webradio : _int_ id of the current webradio list
  * webradiolength : _int_ number of recorded webradio
  * webradiosource : _str_ current source for webradio streams
  * webradiosourcecat : _str_ current categorie for webradio
  * queue : _int_ id of the current queue
  * queuelength : _int_ length of the current queue
  * queuetimelength : _int_ time length of the current queue
  * queueplayorder : _str_ inorder | random
  * video : _int_ id of the current video list
  * videolength : _int_ length of the current video list
  * videotimelength : _int_ time length of the current video list
  * videorepeat : _bool_ false (not activated) or true (activated)
  * videoplayorder : inorder | random | onemedia | random-weighted
  * dvd : _int_ id of the current dvd
  * dvdlength : _int_ number of tracks on the current dvd
  * volume : `[0-100]` current volume value
  * state : [play-pause-stop] the current state of the player
  * current : _int_:_int_:_str_ current media pos : current media file id : playing source name
  * time : _int_:_int_ position:length of the current media file
  * mode : [playlist-webradio-video] the current mode
  * audio_updating_db : _int_ show when a audio library update is in progress
  * audio_updating_error : _string_ error message that appears when the audio library update has failed
  * video_updating_db : _int_ show when a video library update is in progress
  * video_updating_error : _string_ error message that appears when the video library update has failed"""
        return dict(self.deejayd_core.get_status(objanswer = False))

    @returns_answer('dict')
    def jsonrpc_stats(self):
        """Return statistical informations :
  * audio_library_update : UNIX time of the last audio library update
  * video_library_update : UNIX time of the last video library update
  * videos : number of videos known by the database
  * songs : number of songs known by the database
  * artists : number of artists in the database
  * albums : number of albums in the database"""
        return dict(self.deejayd_core.get_stats(objanswer = False))

    @returns_answer('ack', [{"name":"source", "type":"string", "req":True},\
            {"name":"option_name", "type":"string","req":True},\
            {"name":"option_value","type":"string","req":True}])
    def jsonrpc_setOption(self, source, option_name, option_value):
        """Set player options "name" to "value" for mode "source", Available options are :
  * playorder (_str_: inorder, onemedia, random or random-weighted)
  * repeat (_bool_: True or False)"""
        self.deejayd_core.set_option(source, option_name,\
                option_value, objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"ids", "type":"int-list", "req": True},\
            {"name": "value", "type": "int", "req": True},\
            {"name": "type", "type": "string", "req": False}])
    def jsonrpc_setRating(self, ids, value, type = "audio"):
        """Set rating of media file with ids equal to media_id for library 'type' """
        self.deejayd_core.set_media_rating(ids, value, type, objanswer=False)


class DeejaydTcpJSONRPC(_DeejaydMainJSONRPC):

    @returns_answer('ack')
    def jsonrpc_close(self):
        """Close the connection with the server"""
        return None

class DeejaydHttpJSONRPC(_DeejaydMainJSONRPC):

    @returns_answer('dict')
    def jsonrpc_serverInfo(self):
        """Return deejayd server informations :
  * server_version : deejayd server version
  * protocol_version : protocol version"""
        return {
            "server_version": __version__,
            "protocol_version": DEEJAYD_PROTOCOL_VERSION
        }

#
# Player commands
#
class DeejaydPlayerJSONRPC(_DeejaydJSONRPC):

    @returns_answer('ack')
    def jsonrpc_playToggle(self):
        """Toggle play/pause."""
        self.deejayd_core.play_toggle(objanswer=False)

    @returns_answer('ack')
    def jsonrpc_stop(self):
        """Stop playing."""
        self.deejayd_core.stop(objanswer=False)

    @returns_answer('ack')
    def jsonrpc_previous(self):
        """Go to previous song or webradio."""
        self.deejayd_core.previous(objanswer=False)

    @returns_answer('ack')
    def jsonrpc_next(self):
        """Go to next song or webradio."""
        self.deejayd_core.next(objanswer=False)

    @returns_answer('ack', params=[{"name":"pos", "type":"int", "req":True},\
            {"name":"relative", "type":"bool", "req":False}])
    def jsonrpc_seek(self, pos, relative = False):
        """Seeks to the position "pos" (in seconds) of the current media set relative argument to true to set new pos in relative way"""
        self.deejayd_core.seek(pos, relative, objanswer=False)

    @returns_answer('mediaList')
    def jsonrpc_current(self):
        """Return informations on the current song, webradio or video info."""
        medias = self.deejayd_core.get_current(objanswer=False)
        media_type = len(medias) == 1 and medias[0]["type"] or None
        return {
                "media_type": media_type,
                "medias": medias,
                "filter": None,
                "sort": None,
                }

    @returns_answer('ack',params=[\
            {"name":"id", "type":"string", "req":True},\
            {"name":"id_type","type":"string", "req":False},\
            {"name":"source","type":"string","req":False}])
    def jsonrpc_goto(self, id, id_type = "id", source = None):
        """Begin playing at media file with id "id" or toggle play/pause."""
        if not re.compile("^\w{1,}|\w{1,}\.\w{1,}$").search(str(id)):
            raise Fault(INVALID_METHOD_PARAMS, _("Wrong id parameter"))
        self.deejayd_core.go_to(str(id), id_type, source, objanswer=False)

    @returns_answer('ack', params=[{"name":"volume", "type":"int", "req":True}])
    def jsonrpc_setVolume(self, volume):
        """Set volume to "volume". The volume range is 0-100."""
        self.deejayd_core.set_volume(volume, objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"option_name", "type":"string", "req":True},\
            {"name":"option_value", "type":"string", "req":True}])
    def jsonrpc_setPlayerOption(self, option_name, option_value):
        """Set player option for the current media. Possible options are :
  * zoom : set zoom (video only), min=-85, max=400
  * audio_lang : select audio channel (video only)
  * sub_lang : select subtitle channel (video only)
  * av_offset : set audio/video offset (video only)
  * sub_offset : set subtitle/video offset (video only)
  * aspect_ratio : set video aspect ratio (video only), available values are :
    * auto
    * 1:1
    * 16:9
    * 4:3
    * 2.11:1 (for DVB)"""
        self.deejayd_core.set_player_option(option_name, option_value,\
                objanswer=False)


#
# media library
#
class _DeejaydLibraryJSONRPC(_DeejaydJSONRPC):
    type = ""

    @returns_answer('dict', params=[{"name":"force","type":"bool","req":False}])
    def jsonrpc_update(self, force = False):
        """Update the library.
  * 'type'_updating_db : the id of this task. It appears in the status until the update are completed."""
        func = getattr(self.deejayd_core, "update_%s_library"%self.type)
        return dict(func(force=force, objanswer=False))

    @returns_answer('fileAndDirList',\
            params=[{"name":"directory","type":"string","req":False}])
    def jsonrpc_getDir(self, directory = ""):
        """List the files of the directory supplied as argument."""
        func = getattr(self.deejayd_core, "get_%s_dir"%self.type)
        root_dir, dirs, files = func(directory, objanswer=False)
        type = self.type == "audio" and "song" or self.type
        return {
                "type": type,
                "files": files,
                "directories": dirs,
                "root": root_dir,
                }

    @returns_answer('mediaList',\
            params=[{"name":"pattern", "type":"string", "req":True},\
            {"name":"type","type":"string","req":True}])
    def jsonrpc_search(self, pattern, type):
        """Search files in library where "type" contains "pattern" content."""
        func = getattr(self.deejayd_core, "%s_search"%self.type)
        medias = func(pattern, type, objanswer=False)
        type = self.type == "audio" and "song" or self.type
        return {"media_type": type, "medias": medias}

class DeejaydAudioLibraryJSONRPC(_DeejaydLibraryJSONRPC):
    type = "audio"

    @returns_answer('list',\
            params=[{"name":"tag", "type":"string", "req":True},\
                {"name":"filter","type":"filter","req":False}])
    def jsonrpc_taglist(self, tag, filter = None):
        """List all the possible values for a tag according to the optional filter argument."""
        if filter is not None:
            filter = Parse_json_filter(filter)
        tag_list = self.deejayd_core.mediadb_list(tag, filter, objanswer=False)
        return list(tag_list)

class DeejaydVideoLibraryJSONRPC(_DeejaydLibraryJSONRPC):
    type = "video"

#
# generic class for modes
#
class _DeejaydModeJSONRPC(_DeejaydJSONRPC):
    def __init__(self, deejayd):
        super(_DeejaydModeJSONRPC, self).__init__(deejayd)
        self.source = getattr(self.deejayd_core, "get_%s"%self.source_name)()

    @returns_answer('mediaList',\
            params=[{"name":"first", "type":"int", "req":False},\
            {"name":"length","type":"int","req":False}])
    def jsonrpc_get(self, first=0, length=-1):
        """Return the content of this mode."""
        res = self.source.get(first, length, objanswer=False)
        if isinstance(res, tuple):
            medias, filter, sort = res
        else:
            medias, filter, sort = res, None, None
        json_filter = filter is not None and \
                Get_json_filter(filter).dump() or None
        return {
                "media_type": self.media_type,
                "medias": medias,
                "filter": json_filter,
                "sort": sort,
                }

#
# Dvd commands
#
class DeejaydDvdModeJSONRPC(_DeejaydJSONRPC):

    @returns_answer('dvdInfo')
    def jsonrpc_get(self):
        """Get the content of the current dvd."""
        return self.deejayd_core.get_dvd_content(objanswer=False)

    @returns_answer('ack')
    def jsonrpc_reload(self):
        """Load the content of the dvd player."""
        self.deejayd_core.dvd_reload(objanswer=False)

#
# video command
#
class DeejaydVideoModeJSONRPC(_DeejaydModeJSONRPC):
    media_type = "video"
    source_name = "video"

    @returns_answer('ack',\
            params=[{"name":"value", "type":"string", "req":True},\
            {"name":"type","type":"string","req":False}])
    def jsonrpc_set(self, value, type="directory"):
        """Set content of video mode"""
        self.source.set(value, type, objanswer=False)

    @returns_answer('ack', params=[{"name":"sort", "type":"sort", "req":True}])
    def jsonrpc_sort(self, sort):
        """Sort active medialist in video mode"""
        self.source.set_sorts(sort, objanswer=False)


#
# playlist mode command
#
class DeejaydPanelModeJSONRPC(_DeejaydModeJSONRPC):
    media_type = "song"
    source_name = "panel"

    @returns_answer('list')
    def jsonrpc_tags(self):
        """Return tag list used in panel mode."""
        tags = self.source.get_panel_tags(objanswer=False)
        return list(tags)

    @returns_answer('dict')
    def jsonrpc_activeList(self):
        """Return active list in panel mode
         * type : 'playlist' if playlist is choosen as active medialist 'panel' if panel navigation is active
         * value : if 'playlist' is selected, return used playlist id"""
        return dict(self.source.get_active_list(objanswer=False))

    @returns_answer('ack', [{"name":"type", "type":"string", "req":True},\
            {"name":"value", "type":"string", "req":False}])
    def jsonrpc_setActiveList(self, type, value = ""):
        """Set the active list in panel mode"""
        self.source.set_active_list(type, value, objanswer=False)

    @returns_answer('ack', [{"name":"tag", "type":"string", "req":True},\
            {"name":"values", "type":"list", "req":True}])
    def jsonrpc_setFilter(self, tag, values):
        """Set a filter for panel mode"""
        self.source.set_panel_filters(tag, values, objanswer=False)

    @returns_answer('ack', [{"name":"tag", "type":"string", "req":True},])
    def jsonrpc_removeFilter(self, tag):
        """Remove a filter for panel mode"""
        self.source.remove_panel_filters(tag, objanswer=False)

    @returns_answer('ack')
    def jsonrpc_clearFilter(self):
        """Clear filters for panel mode"""
        self.source.clear_panel_filters(objanswer=False)

    @returns_answer('ack', [{"name":"tag", "type":"string", "req":True},\
            {"name":"value", "type":"string", "req":True}])
    def jsonrpc_setSearch(self, tag, value):
        """Set search filter in panel mode"""
        self.source.set_search_filter(tag, value, objanswer=False)

    @returns_answer('ack')
    def jsonrpc_clearSearch(self):
        """Clear search filter in panel mode"""
        self.source.clear_search_filter(objanswer=False)

    @returns_answer('ack')
    def jsonrpc_clearAll(self):
        """Clear search filter and panel filters"""
        self.source.clear_search_filter(objanswer=False)
        self.source.clear_panel_filters(objanswer=False)

    @returns_answer('ack', [{"name":"sort","type":"sort","req":True},])
    def jsonrpc_setSort(self, sort):
        """Sort active medialist in panel mode"""
        self.source.set_sorts(sort, objanswer=False)
#
# playlist mode command
#
class DeejaydPlaylistModeJSONRPC(_DeejaydModeJSONRPC):
    media_type = "song"
    source_name = "playlist"

    @returns_answer('ack')
    def jsonrpc_clear(self):
        """Clear the current playlist."""
        self.source.clear(objanswer=False)

    @returns_answer('ack')
    def jsonrpc_shuffle(self):
        """Shuffle the current playlist."""
        self.source.shuffle(objanswer=False)

    @returns_answer('dict',\
            params=[{"name":"pls_name", "type":"string", "req":True}])
    def jsonrpc_save(self, pls_name):
        """Save the current playlist to "pls_name" in the database.
  * playlist_id : id of the recorded playlist"""
        return dict(self.source.save(pls_name, objanswer=False))

    @returns_answer('ack', params=[\
            {"name":"pl_ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_loads(self, pl_ids, pos = None):
        """Load playlists passed as arguments "name" at the position "pos"."""
        self.source.loads(pl_ids, pos, objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"paths", "type":"list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_addPath(self, paths, pos = None):
        """Load files or directories passed as arguments ("paths") at the position "pos" in the current playlist."""
        self.source.add_paths(paths, pos,objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_addIds(self, ids, pos = None):
        """Load files with id passed as arguments ("ids") at the position "pos" in the current playlist."""
        self.source.add_songs(ids, pos, objanswer=False)

    @returns_answer('ack', params=[{"name":"ids","type":"int-list","req":True}])
    def jsonrpc_remove(self, ids):
        """Remove songs with ids passed as argument ("ids") from the current playlist"""
        self.source.del_songs(ids, objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_move(self, ids, pos=-1):
        """Move songs with id in "ids" to position "pos". Set pos to -1 if you want to move song at the end of the playlist (default)"""
        self.source.move(ids, pos, objanswer=False)


#
# webradios commands
#
class DeejaydWebradioModeJSONRPC(_DeejaydModeJSONRPC):
    media_type = "webradio"
    source_name = "webradios"

    @returns_answer('dict')
    def jsonrpc_getAvailableSources(self):
        """Return list of available sources for webradio mode as source_name: has_categories"""
        return self.source.get_available_sources(objanswer=False)

    @returns_answer('list',\
                    params=[{"name":"source_name","type":"string","req":True}])
    def jsonrpc_getSourceCategories(self, source_name):
        """Return list of categories for webradio source 'source_name'"""
        return self.source.get_source_categories(source_name, objanswer=False)

    @returns_answer('ack', \
                    params=[{"name":"source_name","type":"string","req":True}])
    def jsonrpc_setSource(self, source_name):
        """Set current source to 'source_name'"""
        self.source.set_source(source_name, objanswer=False)

    @returns_answer('ack', \
                    params=[{"name":"categorie","type":"string","req":True}])
    def jsonrpc_setSourceCategorie(self, categorie):
        """Set categorie to 'categorie' for current source"""
        self.source.set_source_categorie(categorie, objanswer=False)

    @returns_answer('ack')
    def jsonrpc_localClear(self):
        """Remove all recorded webradios from the 'local' source."""
        self.source.clear(objanswer=False)

    @returns_answer('ack', params=[{"name":"ids","type":"int-list","req":True}])
    def jsonrpc_localRemove(self, ids):
        """Remove webradios with id in "ids" from the 'local' source."""
        self.source.delete_webradios(ids, objanswer=False)

    @returns_answer('ack', params=[{"name":"name","type":"string","req":True},\
            {"name":"url", "type":"list", "req":True}])
    def jsonrpc_localAdd(self, name, urls):
        """Add a webradio in 'local' source. Its name is "name" and the url of the webradio is "url". You can pass a playlist for "url" argument (.pls and .m3u format are supported)."""
        self.source.add_webradio(name, urls, objanswer=False)


#
# queue commands
#
class DeejaydQueueJSONRPC(_DeejaydModeJSONRPC):
    media_type = "song"
    source_name = "queue"

    @returns_answer('ack', params=[\
            {"name":"paths", "type":"list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_addPath(self, paths, pos = None):
        """Load files or directories passed as arguments ("paths") at the position "pos" in the queue."""
        self.source.add_paths(paths, pos,objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_addIds(self, ids, pos = None):
        """Load files with id passed as arguments ("ids") at the position "pos" in the queue."""
        self.source.add_songs(ids, pos, objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"pl_ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_loads(self, pl_ids, pos = None):
        """Load playlists passed as arguments "name" at the position "pos"
        in the queue."""
        self.source.load_playlists(pl_ids, pos, objanswer=False)

    @returns_answer('ack', params=[{"name":"ids","type":"int-list","req":True}])
    def jsonrpc_remove(self, ids):
        """Remove songs with ids passed as argument ("ids") from the queue"""
        self.source.del_songs(ids, objanswer=False)

    @returns_answer('ack', params=[\
            {"name":"ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}])
    def jsonrpc_move(self, ids, pos = -1):
        """Move songs with id in "ids" to position "pos". Set pos to -1 if you want to move song at the end of the queue (default)."""
        self.source.move(ids, pos, objanswer=False)

    @returns_answer('ack')
    def jsonrpc_clear(self):
        """Clear the queue."""
        self.source.clear(objanswer=False)


#
# recorded playlist
#
class DeejaydRecordedPlaylistJSONRPC(_DeejaydJSONRPC):

    @returns_answer('mediaList')
    def jsonrpc_list(self):
        """Return the list of recorded playlists."""
        pls = self.deejayd_core.get_playlist_list(objanswer=False)
        return {
                "media_type": 'playlist',
                "medias": pls,
                "filter": None,
                "sort": None,
                }

    @returns_answer('dict', [{"name":"name", "type":"string", "req":True},\
                    {"name":"type","type":"string","req":True}])
    def jsonrpc_create(self, name, type):
        """Create recorded playlist. The answer consist on
  * pl_id : id of the created playlist
  * name : name of the created playlist
  * type : type of the created playlist"""
        pl_infos = self.deejayd_core.create_recorded_playlist(\
                name, type, objanswer=False)
        return dict(pl_infos)

    @returns_answer('ack', [{"name":"pl_ids", "type":"int-list", "req":True}])
    def jsonrpc_erase(self, pl_ids):
        """Erase recorded playlists passed as arguments."""
        self.deejayd_core.erase_playlist(pl_ids, objanswer=False)

    @returns_answer('mediaList', [{"name":"pl_id", "type":"int", "req":True},\
                    {"name":"first", "type":"int", "req":False},\
                    {"name":"length","type":"int","req":False}])
    def jsonrpc_get(self, pl_id, first = 0, length = -1):
        """Return the content of a recorded playlist."""
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type == "static":
            songs = pls.get(first, length, objanswer=False)
            filter, sort = None, None
        elif pls.type == "magic":
            songs, filter, sort = pls.get(first, length, objanswer=False)

        json_filter = filter is not None and \
                Get_json_filter(filter).dump() or None
        return {
                "media_type": 'song',
                "medias": songs,
                "filter": json_filter,
                "sort": sort,
                }

    @returns_answer('ack', params=[{"name":"pl_id", "type":"int", "req":True},\
                    {"name":"values", "type":"list", "req":True},\
                    {"name":"type","type":"string","req":False}])
    def jsonrpc_staticAdd(self, pl_id, values, type = "path"):
        """Add songs in a recorded static playlist. Argument 'type' has to be 'path' (default) or 'id'"""
        if type not in ("id", "path"):
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Param 'type' has a wrong value"))
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type == "magic":
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Selected playlist is not static."))
        if type == "id":
            try: values = map(int, values)
            except (TypeError, ValueError):
                raise Fault(INVALID_METHOD_PARAMS,\
                        _("values arg must be integer"))
            pls.add_songs(values, objanswer=False)
        else:
            pls.add_paths(values, objanswer=False)

    @returns_answer('ack', params=[{"name":"pl_id", "type":"int", "req":True},\
                    {"name":"filter","type":"filter","req":True}])
    def jsonrpc_magicAddFilter(self, pl_id, filter):
        """Add a filter in recorded magic playlist."""
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type != "magic":
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Selected playlist is not magic."))
        if filter is not None:
            filter = Parse_json_filter(filter)
        pls.add_filter(filter, objanswer=False)

    @returns_answer('ack', params=[{"name":"pl_id", "type":"int", "req":True},\
                    {"name":"filter","type":"filter","req":True}])
    def jsonrpc_magicRemoveFilter(self, pl_id, filter):
        """Remove a filter from recorded magic playlist."""
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type != "magic":
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Selected playlist is not magic."))
        if filter is not None:
            filter = Parse_json_filter(filter)
        pls.remove_filter(filter, objanswer=False)

    @returns_answer('ack', params=[{"name":"pl_id", "type":"int", "req":True}])
    def jsonrpc_magicClearFilter(self, pl_id):
        """Remove all filter from recorded magic playlist."""
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type != "magic":
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Selected playlist is not magic."))
        pls.clear_filters(objanswer=False)

    @returns_answer('dict', [{"name":"pl_id", "type":"int", "req":True}])
    def jsonrpc_magicGetProperties(self, pl_id):
        """Get properties of a magic playlist
  * use-or-filter: if equal to 1, use "Or" filter instead of "And" (0 or 1)
  * use-limit: limit or not number of songs in the playlist (0 or 1)
  * limit-value: number of songs for this playlist (integer)
  * limit-sort-value: when limit is active sort playlist with this tag
  * limit-sort-direction: sort direction for limit (ascending or descending)"""
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type != "magic":
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Selected playlist is not magic."))
        return dict(pls.get_properties(objanswer=False))

    @returns_answer('ack', [{"name":"pl_id", "type":"int", "req":True},\
            {"name":"key", "type":"string","req":True},\
            {"name":"value", "type":"string", "req":True}])
    def jsonrpc_magicSetProperty(self, pl_id, key, value):
        """Set a property for a magic playlist."""
        pls = self.deejayd_core.get_recorded_playlist(pl_id)
        if pls.type != "magic":
            raise Fault(INVALID_METHOD_PARAMS,\
                _("Selected playlist is not magic."))
        pls.set_property(key, value, objanswer=False)


def build_protocol(deejayd, main):
    # add introspection
    addIntrospection(main)

    # add common deejayd subhandler
    sub_handlers = {
            "player": DeejaydPlayerJSONRPC,
            "audiolib": DeejaydAudioLibraryJSONRPC,
            "videolib": DeejaydVideoLibraryJSONRPC,
            "recpls": DeejaydRecordedPlaylistJSONRPC,
            }
    for key in sub_handlers:
        main.putSubHandler(key, sub_handlers[key](deejayd))
    # add mode deejayd subhandler
    mode_handlers = {
            "panel": DeejaydPanelModeJSONRPC,
            "webradio": DeejaydWebradioModeJSONRPC,
            "video": DeejaydVideoModeJSONRPC,
            "playlist": DeejaydPlaylistModeJSONRPC,
            "dvd": DeejaydDvdModeJSONRPC,
            "queue": DeejaydQueueJSONRPC,
            }
    for key in mode_handlers:
        try: mode = mode_handlers[key](deejayd)
        except DeejaydError: # this mode is not activated
            pass
        else:
            main.putSubHandler(key, mode)

    return main


#############################################################################
## part specific for jsonrpc over a TCP connecion : signals
#############################################################################
class DeejaydSignalJSONRPC(_DeejaydJSONRPC):

    def __init__(self, deejayd, connector):
        super(DeejaydSignalJSONRPC, self).__init__(deejayd)
        self.connector = connector

    @returns_answer('ack', [{"name":"signal", "type":"string", "req":True},\
            {"name":"value", "type":"bool", "req":True}])
    def jsonrpc_setSubscription(self, signal, value):
        """Set subscribtion to "signal" signal notifications to "value" which should be 0 or 1."""
        if value is False:
            self.connector.set_not_signaled(signal)
        elif value is True:
            self.connector.set_signaled(signal)

def set_signal_subhandler(deejayd, protocol):
    protocol.putSubHandler("signal", DeejaydSignalJSONRPC(deejayd, protocol))
    return protocol

#############################################################################
## part specific for jsonrpc over a http connecion
#############################################################################
class DeejaydWebJSONRPC(_DeejaydJSONRPC):
    def __init__(self, deejayd, tmp_dir):
        super(DeejaydWebJSONRPC, self).__init__(deejayd)
        self._tmp_dir = tmp_dir

    def __find_ids(self, pattern):
        ids = []
        for file in os.listdir(self._tmp_dir):
            if re.compile("^%s-[0-9]+" % pattern).search(file):
                t = file.split("-")[1] # id.ext
                t = t.split(".")
                try : ids.append(int(t[0]))
                except ValueError: pass
        return ids

    @returns_answer('dict', params=[{"name":"mid","type":"int","req":True}])
    def jsonrpc_writecover(self, mid):
        """ Record requested cover in the temp directory """
        try:
            cover = self.deejayd_core.get_audio_cover(mid,objanswer=False)
        except (TypeError, DeejaydError, KeyError):
            return {"cover": None}

        cover_ids = self.__find_ids("cover")
        ext = cover["mime"] == "image/jpeg" and "jpg" or "png"
        filename = "cover-%s.%s" % (str(cover["id"]), ext)
        if cover["id"] not in cover_ids:
            file_path = os.path.join(self._tmp_dir,filename)
            fd = open(file_path, "w")
            fd.write(cover["cover"])
            fd.close()
            os.chmod(file_path,0644)
            # erase unused cover files
            for id in cover_ids:
                try:
                    os.unlink(os.path.join(self._tmp_dir,\
                            "cover-%s.jpg" % id))
                    os.unlink(os.path.join(self._tmp_dir,\
                            "cover-%s.png" % id))
                except OSError:
                    pass
        return {"cover": os.path.join('tmp', filename), "mime": cover["mime"]}

    @returns_answer('dict',[{"name":"updated_tag","type":"string","req":False}])
    def jsonrpc_buildPanel(self, updated_tag = None):
        """ Build panel list """
        panel = self.deejayd_core.get_panel()

        medias, filters, sort = panel.get(objanswer=False)
        try: filter_list = filters.filterlist
        except (TypeError, AttributeError):
            filter_list = []

        answer = {"panels": {}}
        panel_filter = And()
        # find search filter
        for ft in filter_list:
            if ft.type == "basic" and ft.get_name() == "contains":
                panel_filter.combine(ft)
                answer["search"] = Get_json_filter(ft).dump()
                break
            elif ft.type == "complex" and ft.get_name() == "or":
                panel_filter.combine(ft)
                answer["search"] = Get_json_filter(ft).dump()
                break

        # find panel filter list
        for ft in filter_list:
            if ft.type == "complex" and ft.get_name() == "and":
                filter_list = ft
                break

        tag_list = panel.get_panel_tags(objanswer=False)
        try: idx = tag_list.index(updated_tag)
        except ValueError:
            pass
        else:
            tag_list = tag_list[idx+1:]

        for t in panel.get_panel_tags(objanswer=False):
            selected = []

            for ft in filter_list: # OR filter
                try: tag = ft[0].tag
                except (IndexError, TypeError): # bad filter
                    continue
                if tag == t:
                    selected = [t_ft.pattern for t_ft in ft]
                    tag_filter = ft
                    break

            if t in tag_list:
                list = self.deejayd_core.mediadb_list(t,\
                        panel_filter, objanswer=False)
                items = [{"name": _("All"), "value":"__all__", \
                    "class":"list-all", "sel":str(selected==[]).lower()}]
                if t == "various_artist" and "__various__" in list:
                    items.append({"name": _("Various Artist"),\
                        "value":"__various__",\
                        "class":"list-unknown",\
                        "sel":str("__various__" in selected).lower()})
                items.extend([{"name": l,"value":l,\
                    "sel":str(l in selected).lower(), "class":""}\
                    for l in list if l != "" and l != "__various__"])
                if "" in list:
                    items.append({"name": _("Unknown"), "value":"",\
                        "class":"list-unknown",\
                        "sel":str("" in selected).lower()})
                answer["panels"][t] = items
            # add filter for next panel
            if len(selected) > 0:
                panel_filter.combine(tag_filter)

        return answer

def set_web_subhandler(deejayd, tmp_dir, main):
    main.putSubHandler("web", DeejaydWebJSONRPC(deejayd, tmp_dir))
    return main

# vim: ts=4 sw=4 expandtab
