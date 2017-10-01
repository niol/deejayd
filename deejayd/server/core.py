# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

from deejayd import __version__
from deejayd.common.component import JSONRpcComponent
from deejayd.jsonrpc import DEEJAYD_PROTOCOL_VERSION
from deejayd.jsonrpc.interfaces import jsonrpc_module, CoreModule
from deejayd.jsonrpc.interfaces import IntrospectionModule
from deejayd.ui.config import DeejaydConfig
from deejayd.db.connection import Session
from deejayd import player, sources, library
from deejayd.playlist.rpc import DeejaydRecordedPlaylist
from deejayd.ui import log
from deejayd.webradio.rpc import DeejaydWebradio


@jsonrpc_module(IntrospectionModule)
class JSONRPCIntrospection(JSONRpcComponent):

    def __init__(self, parent):
        super(JSONRPCIntrospection, self).__init__()
        self._jsonrpc_parent = parent

    def list_methods(self):
        functions = []
        todo = [(self._jsonrpc_parent, '')]
        while todo:
            obj, prefix = todo.pop(0)
            functions.extend([prefix + name for name in obj.list_functions()])
            todo.extend([(obj.get_sub_handler(name),
                         prefix + name + obj.separator)
                         for name in obj.get_sub_handler_prefixes()])
        return functions

    def method_help(self, method):
        method = self._jsonrpc_parent.get_function(method)
        return getattr(method, '__doc__', None) or ''

    def method_signature(self, method):
        method = self._jsonrpc_parent.get_function(method)
        return getattr(method, '__signature__', None) or ''


@jsonrpc_module(CoreModule)
class DeejayDaemonCore(JSONRpcComponent):

    def __init__(self, start_inotify=True, library_update=True):
        super(DeejayDaemonCore, self).__init__()
        config = DeejaydConfig()

        self.player = player.init(config)
        self.put_sub_handler('player', self.player)

        self.audiolib, self.videolib, self.watcher = library.init(self.player,
                                                                  config)
        self.put_sub_handler('audiolib', self.audiolib)
        if self.videolib is not None:
            self.put_sub_handler('videolib', self.videolib)

        self.recpls = DeejaydRecordedPlaylist(self.audiolib)
        self.put_sub_handler('recpls', self.recpls)

        # add audio queue/playlist and video playlist
        self.sources = sources.init(self.player, self.audiolib,
                                    self.videolib, config)
        for source in list(self.sources.sources.values()):
            self.put_sub_handler(source.name, source)
            setattr(self, source.name, source)

        # add webradio if player can play http stream
        if self.player.is_supported_uri("http"):
            self.webradio = DeejaydWebradio(self.player)
            self.put_sub_handler('webradio', self.webradio)
        else:
            log.err(_("Player is not able to play http streams"))
            self.webradio = None

        if library_update:
            self.audiolib.update()
            if self.videolib is not None:
                self.videolib.update()

        # enable JSON-RPC introspection
        self.put_sub_handler('introspection', JSONRPCIntrospection(self))

        # start inotify thread when we are sure that all init stuff are ok
        if self.watcher and start_inotify:
            log.debug(_("Start inotify watcher"))
            self.watcher.start()
        # record changes and close session after the initialization
        Session.commit()
        Session.remove()

    def close(self):
        for obj in (self.watcher, self.player, self.sources, self.audiolib,
                    self.videolib, self.webradio):
            if obj is not None:
                obj.close()
        Session.commit()
        Session.remove()

    def ping(self):  # do nothing
        pass

    def get_status(self):
        status = self.player.get_status()

        def update_status(s, prefix=""):
            for k in s:
                status[prefix+"_"+k] = s[k]

        update_status(self.audiolib.get_status(), "audiolib")
        update_status(self.audiopls.get_status(), "audiopls")
        update_status(self.audioqueue.get_status(), "audioqueue")
        if self.videolib is not None:
            update_status(self.videolib.get_status(), "videolib")
            update_status(self.videopls.get_status(), "videopls")
        return status

    def get_stats(self):
        stats = self.audiolib.get_stats()
        if self.videolib is not None:
            stats.update(self.videolib.get_stats())
        return stats

    def get_server_info(self):
        config = DeejaydConfig()
        return {
            "server_version": __version__,
            "protocol_version": DEEJAYD_PROTOCOL_VERSION,
            "video_support": config.getboolean("video", "enabled")
        }
