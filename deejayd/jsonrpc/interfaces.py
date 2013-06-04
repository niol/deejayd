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

from deejayd import DeejaydError
from deejayd.model.mediafilters import MediaFilter
from deejayd.jsonrpc import *
import inspect

def underscore_to_camelcase(s):
    """Take the underscore-separated string s and return a camelCase
    equivalent.  Initial and final underscores are preserved, and medial
    pairs of underscores are turned into a single underscore."""
    def camelcase_words(words):
        first_word_passed = False
        for word in words:
            if not word:
                yield "_"
                continue
            if first_word_passed:
                yield word.capitalize()
            else:
                yield word.lower()
            first_word_passed = True
    return ''.join(camelcase_words(s.split('_')))


#
# decorators and misc functions for rpc modules
#
def build_signature(answer, args):
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
    if args:
        signature = []
        opt_params = [p_dict[p["type"]] for p in args if not p["req"]]
        for i in range(len(opt_params) + 1):
            s = ["object"]
            s.extend([p_dict[p["type"]] for p in args if p["req"]])
            s.extend(opt_params[:i])
            signature.append(s)
    else:
        signature = [["object"]]

    return signature

def build_help(cmd):
    args = getattr(cmd, "args", [])
    answer = getattr(cmd, "answer", 'ack')

    p_desc = "\nNo arguments"
    if len(args) > 0:
        p_desc = "\nArguments : \n%s" % \
            "\n".join(["  * name '%s', type '%s', required '%s'" % \
                (a["name"], a["type"], a["req"]) for a in args])
    return """
Description :
%(description)s
Answer type : %(answer)s %(p_desc)s""" % {\
            "description": cmd.__doc__, \
            "answer": answer, \
            "p_desc": p_desc, \
        }

def verify_arguments(__args, args):
    __new_args = list(__args)
    for idx, arg in enumerate(args):
        try: value = __args[idx + 1]
        except IndexError:
            if arg["req"] is True:
                raise Fault(INVALID_METHOD_PARAMS, \
                    _("Arg %s is required") % arg["name"])
        else:
            if arg['type'] == "int":
                try: value = int(value)
                except (ValueError, TypeError):
                    raise Fault(INVALID_METHOD_PARAMS, \
                        _("Arg %s is not an int") % arg["name"])
            elif arg['type'] in ("bool", "list", "dict"):
                types = {
                         "bool": bool,
                         "dict": dict,
                         "list": list,
                         "string": str
                    }
                if not isinstance(value, types[arg['type']]):
                    raise Fault(INVALID_METHOD_PARAMS, \
                        _("Arg %s has wrong type") % arg["name"])
            elif arg['type'] == "int-list":
                if not isinstance(value, list):
                    raise Fault(INVALID_METHOD_PARAMS, \
                        _("Arg %s is not a list") % arg["name"])
                try: value = map(int, value)
                except (ValueError, TypeError):
                    raise Fault(INVALID_METHOD_PARAMS, \
                      _("Arg %s is not an int-list") % arg["name"])
            elif arg['type'] == 'filter':
                if value is not None:
                    value = MediaFilter.load_from_json(value)
            __new_args[idx + 1] = value
    return __new_args

def jsonrpc_func(cmd_name, rpc_cmd, func):
    def new_func(*args, **kwargs):
        args = verify_arguments(args, getattr(rpc_cmd, "args", []))
        try: res = func(*args, **kwargs)
        except DeejaydError, ex:
            raise Fault(INTERNAL_ERROR, unicode(ex))
        type = getattr(rpc_cmd, "answer", "ack")
        if type in ("medialist", "albumList", "playlist"):
            res = map(lambda m: m.to_json(), res)
        elif type == 'fileAndDirList':
            res["files"] = map(lambda m: m.to_json(), res["files"])
        elif type == "dict":
            res = dict(res)
        elif type == "media":
            res = res is not None and res.to_json() or None
        elif type == "ack":
            res = True

        return {"answer": res, "type": type}
    new_func.__doc__ = func.__doc__
    new_func.__name__ = cmd_name
    new_func.__signature__ = {
                        "answer": getattr(rpc_cmd, "answer", "ack"),
                        "args": getattr(rpc_cmd, "args", [])
                    }

    return new_func

def jsonrpc_module(module):
    def impl_func(orig_cls):
        for attr in dir(orig_cls):
            try: m = getattr(orig_cls, attr)
            except AttributeError:
                continue

            if inspect.ismethod(m):
                camel_case_attr = underscore_to_camelcase(attr)
                rpc_cmd = getattr(module, camel_case_attr, None)
                if inspect.isclass(rpc_cmd):
                    func = m.__func__
                    cmd_name = "jsonrpc_%s" % camel_case_attr
                    setattr(orig_cls, cmd_name,
                            jsonrpc_func(cmd_name, rpc_cmd, func))
        return orig_cls

    return impl_func

#
# Rpc modules
#

class IntrospectionModule(object):
    """Implement a JSON-RPC Introspection API.

    By default, the methodHelp method returns the 'help' method attribute,
    if it exists, otherwise the __doc__ method attribute, if it exists,
    otherwise the empty string.

    To enable the methodSignature method, add a 'signature' method attribute
    containing a list of lists. See methodSignature's documentation for the
    format. Note the type strings should be JSON-RPC types, not Python types.
    """

    class listMethods:
        """Return a list of the method names implemented by this server."""
        answer = 'list'

    class getMethodHelp:
        """Return a documentation string describing the use of the given method."""
        answer = 'string'
        args = [{"name":"method", "type":"string", "req":True}]

    class getMethodSignature:
        """Return a list of type signatures.

        Each type signature is a list of the form [rtype, type1, type2, ...]
        where rtype is the return type and typeN is the type of the Nth
        argument. If no signature information is available, the empty
        string is returned.
        """
        answer = 'list'
        args = [{"name":"method", "type":"string", "req":True}]

class CoreModule(object):

    class ping:
        """Does nothing, just replies with an acknowledgement that the command was received"""

    class getServerInfo:
        """Return deejayd server informations :
  * video_support : true if this server supports video, else false
  * server_version : deejayd server version
  * protocol_version : protocol version"""
        answer = 'dict'

    class close:
        """Close the connection with the server"""

    class getStatus:
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
        answer = 'dict'

    class getStats:
        """Return statistical informations :
  * audio_library_update : UNIX time of the last audio library update
  * video_library_update : UNIX time of the last video library update
  * videos : number of videos known by the database
  * songs : number of songs known by the database
  * artists : number of artists in the database
  * albums : number of albums in the database"""
        answer = 'dict'

class SignalModule:

    class setSubscription:
        """Set subscribtion to "signal" signal notifications to "value" which should be 0 or 1."""
        args = [
            {"name":"signal", "type":"string", "req":True}, \
            {"name":"value", "type":"bool", "req":True}
        ]

class LibraryModule(object):

    class update:
        """Update the library.
  * 'type'_updating_db : the id of this task. It appears in the status until the update are completed."""
        answer = 'dict'
        args = [{"name":"force", "type":"bool", "req":False}]

    class getDirContent:
        """List the files of the directory supplied as argument."""
        answer = 'fileAndDirList'
        args = [{"name":"directory", "type":"string", "req":False}]

    class search:
        """Search files in library that match "filter"
        ."""
        answer = 'medialist'
        args = [
            {"name":"filter", "type":"filter", "req":False}
        ]

    class tagList:
        """ List all the possible values for a tag according to the optional filter argument."""
        answer = 'list'
        args = [
            {"name":"tag", "type":"string", "req":True},
            {"name":"filter", "type":"filter", "req":False}
        ]

    class setRating:
        """Set rating of media file identified by filter 'filter'"""
        args = [
            {"name":"filter", "type":"filter", "req": True}, \
            {"name": "value", "type": "int", "req": True}, \
        ]


class AudioLibraryModule(LibraryModule):

    class albumList:
        """Get Albums that match the 'filter', the answer is list where each
entry has
  * id of the album
  * name of the filename
  * filename of the cover"""
        answer = 'albumList'
        args = [
            {"name":"filter", "type":"filter", "req":False}
        ]

class PlayerModule(object):

    class getStatus:
        """Return status of player
  * volume : `[0-100]` current volume value
  * state : [play-pause-stop] the current state of the player
  * current : _int_:_int_:_str_ current media pos : current media file id : playing source name
  * time : _int_:_int_ position:length of the current media file"""
        answer = 'dict'

    class playToggle:
        """Toggle play/pause."""

    class play:
        """Start playing."""

    class pause:
        """Pause playing."""

    class stop:
        """Stop playing."""

    class next:
        """Go to next song/webradio/video."""

    class previous:
        """Go to previous song/webradio/video."""

    class setVolume:
        """Set volume to "volume". The volume range is 0-100."""
        args = [{ "name": "volume",
            "type": "int",
            "desc": "new value of volume",
            "req": True, }
        ]

    class seek:
        """Seeks to the position "pos" (in seconds) of the current media set relative argument to true to set new pos in relative way"""
        args = [
          { "name": "pos",
            "type": "int",
            "desc": "new position in the media file ",
            "req": True, },
          { "name": "absolute",
            "type": "boolean",
            "desc": "set to true to set new pos in relative way",
            "req": False, },
        ]

    class goTo:
        """Begin playing at media file with id "id" or toggle play/pause."""
        args = [
          { "name": "id",
            "type": "int",
            "desc": "id of media file to play",
            "req": True, },
          { "name": "id_type",
            "type": "str",
            "desc": "id type to use : 'pos' or 'id' (default)",
            "req": False, },
          { "name": "source",
            "type": "str",
            "desc": "source to use",
            "req": False, },
        ]

    class getPlaying:
        """Return informations on the current song/webradio/video. Raise an error if no media is playing"""
        answer = "media"

    class getAvailableVideoOptions:
        """Get video options supported by the active player. the answer is a dict of option_name=is_supported where
    * option_name is in this list : "audio_lang", "sub_lang", "av_offset", "sub_offset", "zoom", "aspect_ratio"
    * is_supported is a boolean equals to True if the option is supported by the player, False else"""
        answer = "dict"

    class setVideoOption:
        """Set player video option for the current media. Possible options are :
  * zoom : set zoom, min=-85, max=400
  * audio_lang : select audio channel
  * sub_lang : select subtitle channel
  * av_offset : set audio/video offset
  * sub_offset : set subtitle/video offset
  * aspect_ratio : set video aspect ratio, available values are :
    * auto
    * 1:1
    * 16:9
    * 4:3
    * 2.11:1 (for DVB)"""
        args = [
          { "name": "option",
            "type": "str",
            "desc": "option's name",
            "req": True, },
          { "name": "value",
            "type": "str",
            "desc": "option's value",
            "req": True, },
        ]

class _SourceModule(object):

    class getStatus:
        """Return status of source. Given informations are :
  * repeat : _bool_ false (not activated) or true (activated)
  * playorder : inorder | random | onemedia | random-weighted
  * id : _int_ id of the current playlist
  * length : _int_ length of the current playlist
  * timelength : _int_ time length of the current playlist"""
        answer = 'dict'

    class get:
        """Return the content of this source."""
        answer = "playlist"
        args = [
            { "name":"first",
              "type":"int",
              "req":False}, \
            { "name":"length",
              "type":"int",
              "req":False}
        ]

    class clear:
        """Clear the current playlist."""

    class setOption:
        """Set player options "name" to "value". Available options are :
  * playorder (_str_: inorder, onemedia, random or random-weighted)
  * repeat (_bool_: True or False)"""
        args = [
            {"name":"option_name", "type":"string", "req":True}, \
            {"name":"option_value", "type":"string", "req":True}
        ]

    class loadFolders:
        """Load folders identified with their ids (dir_ids).
if queue args = True (default), selected medias are added at the end of the
playlist, else they replace current playlist
."""
        args = [
            {"name":"dir_ids", "type":"int-list", "req":True},
            {"name":"queue", "type":"bool", "req":False}
        ]

    class addMediasByIds:
        """Load files identified with ids (media_ids).
if queue args = True (default), selected medias are added at the end of the
playlist, else they replace current playlist
."""
        args = [
            {"name":"media_ids", "type":"int-list", "req":True},
            {"name":"queue", "type":"bool", "req":False}
        ]

    class addMediaByFilter:
        """Load files that match the filter argument
if queue args = True (default), selected medias are added at the end of the
playlist, else they replace current playlist
."""
        args = [
            {"name":"filter", "type":"filter", "req":True},
            {"name":"queue", "type":"bool", "req":False}
        ]

    class remove:
        """Remove songs with ids passed as argument ("ids") from the current playlist"""
        args = [{"name":"ids", "type":"int-list", "req":True}]

    class move:
        """Move songs with id in "ids" to position "pos". Set pos to -1 if you want to move song at the end of the playlist (default)"""
        args = [
            {"name":"ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}
        ]

class AudioSourceModule(_SourceModule):

    class shuffle:
        """Shuffle the current playlist."""

    class save:
        """Save the current playlist to "pls_name" in the database.
  * playlist_id : id of the recorded playlist"""
        answer = "dict"
        args = [{"name":"pls_name", "type":"string", "req":True}]

    class loadPlaylist:
        """Load recorded playlist at a specific position"""
        args = [
            {"name":"pl_ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}
        ]

class VideoSourceModule(_SourceModule):
    pass

class QueueSourceModule(_SourceModule):

    class loadPlaylist:
        """Load recorded playlist at a specific position"""
        args = [
            {"name":"pl_ids", "type":"int-list", "req":True},
            {"name":"pos", "type":"int", "req":False}
        ]

class WebradioSourceModule(object):

    class get:
        """Return the content of this mode."""
        answer = "mediaList"
        args = [
            { "name":"first",
              "type":"int",
              "req":False}, \
            { "name":"length",
              "type":"int",
              "req":False}
        ]

    class getAvailableSources:
        """Return list of available sources for webradio mode as source_name: is_editable"""
        answer = 'dict'

    class setSource:
        """Set current source to 'source_name'"""
        args = [{"name":"source_name", "type":"string", "req":True}]

    class getSourceCategories:
        """Return list of categories for webradio source 'source_name'"""
        answer = 'dict'
        args = [{"name":"source_name", "type":"string", "req":True}]

    class setSourceCategorie:
        """Set categorie to 'categorie' for current source"""
        args = [{"name":"categorie", "type":"string", "req":True}]

    class sourceAddCategorie:
        """Add a new categorie for the source 'source_name'"""
        answer = 'dict'
        args = [
            {"name":"source_name", "type":"string", "req":True},
            {"name":"cat", "type":"string", "req":True}
        ]

    class sourceDeleteCategories:
        """Remove categories with id in "cat_ids" from the 'source_name' source."""
        args = [
            {"name":"source_name", "type":"string", "req":True},
            {"name":"cat_ids", "type":"int-list", "req":True}
        ]

    class sourceClearWebradios:
        """Remove all recorded webradios from the 'source_name' source."""
        args = [{"name":"source_name", "type":"string", "req":True}]

    class sourceDeleteWebradios:
        """Remove webradios with id in "ids" from the 'source_name' source."""
        args = [
            {"name":"source_name", "type":"string", "req":True},
            {"name":"ids", "type":"int-list", "req":True}
        ]

    class sourceAddWebradio:
        """Add a webradio in 'source_name' source. Its name is "name" and the url of the webradio is "url". You can pass a playlist for "url" argument (.pls and .m3u format are supported)."""
        args = [
            {"name":"source_name", "type":"string", "req":True},
            {"name":"name", "type":"string", "req":True},
            {"name":"url", "type":"list", "req":True},
            {"name":"cat", "type":"int", "req":False},
        ]



class RecordedPlaylistModule(object):

    class getList:
        """Return the list of recorded playlists as dict with attributes :
  * pl_id : id of the created playlist
  * name : name of the created playlist
  * type : type of the created playlist"""
        answer = "list"

    class create:
        """Create recorded playlist. The answer consist on
  * pl_id : id of the created playlist
  * name : name of the created playlist
  * type : type of the created playlist"""
        answer = 'dict'
        args = [
            {"name":"name", "type":"string", "req":True}, \
            {"name":"type", "type":"string", "req":True}
        ]

    class erase:
        """Erase recorded playlists passed as arguments."""
        args = [{"name":"pl_ids", "type":"int-list", "req":True}]

    class getContent:
        """Return the content of a recorded playlist."""
        answer = 'mediaList'
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
            {"name":"first", "type":"int", "req":False}, \
            {"name":"length", "type":"int", "req":False}
        ]

    class staticAddMedia:
        """Add songs in a recorded static playlist. Argument 'type' has to be
  * 'path' (default) to specify folder/file path in values argument
  * OR 'id' to specify media ids in values argument"""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
            {"name":"values", "type":"list", "req":True}, \
            {"name":"type", "type":"string", "req":False}
        ]

    class staticRemoveMedia:
        """Remove songs in a recorded static playlist. Argument 'values' specify position of media to remove from the playlist"""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
            {"name":"values", "type":"list", "req":True}, \
        ]

    class staticClearMedia:
        """Remove all songs in a recorded static playlist."""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
        ]

    class magicAddFilter:
        """Add a filter in recorded magic playlist."""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
            {"name":"filter", "type":"filter", "req":True}
        ]

    class magicRemoveFilter:
        """Remove a filter from recorded magic playlist."""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
            {"name":"filter", "type":"filter", "req":True}
        ]

    class magicClearFilter:
        """Remove all filter from recorded magic playlist."""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
        ]

    class magicGetProperties:
        """Get properties of a magic playlist
  * use-or-filter: if equal to 1, use "Or" filter instead of "And" (0 or 1)
  * use-limit: limit or not number of songs in the playlist (0 or 1)
  * limit-value: number of songs for this playlist (integer)
  * limit-sort-value: when limit is active sort playlist with this tag
  * limit-sort-direction: sort direction for limit (ascending or descending)"""
        answer = 'dict'
        args = [{"name":"pl_id", "type":"int", "req":True}]

    class magicSetProperty:
        """Set a property for a magic playlist."""
        args = [
            {"name":"pl_id", "type":"int", "req":True}, \
            {"name":"key", "type":"string", "req":True}, \
            {"name":"value", "type":"string", "req":True}
        ]


JSONRPC_MODULES = {
    "core": CoreModule,
    "player": PlayerModule,
    "audiopls": AudioSourceModule,
    "audioqueue": QueueSourceModule,
    "videopls": VideoSourceModule,
    "webradio": WebradioSourceModule,
    "recpls": RecordedPlaylistModule,
    "audiolib": LibraryModule,
    "videolib": LibraryModule,
    "signal": SignalModule,
}

# vim: ts=4 sw=4 expandtab
