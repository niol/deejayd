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

from deejayd import DeejaydError, __version__
from deejayd.component import SignalingCoreComponent, JSONRpcComponent
from deejayd.jsonrpc import DEEJAYD_PROTOCOL_VERSION
from deejayd.jsonrpc.interfaces import jsonrpc_module, CoreModule, IntrospectionModule
from deejayd.ui.config import DeejaydConfig
from deejayd.database.connection import DatabaseConnection
from deejayd.database.queries import DatabaseQueries
from deejayd import player, sources, mediadb, plugins
from deejayd.playlist.rpc import DeejaydRecordedPlaylist
from deejayd.ui import log

# Exception imports
import deejayd.mediadb.library


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
            functions.extend([ prefix + name for name in obj.list_functions() ])
            todo.extend([ (obj.get_sub_handler(name),
                           prefix + name + obj.separator)
                          for name in obj.get_sub_handler_prefixes() ])
        return functions

    def method_help(self, method):
        method = self._jsonrpc_parent.get_function(method)
        return getattr(method, '__doc__', None) or ''

    def method_signature(self, method):
        method = self._jsonrpc_parent.get_function(method)
        return getattr(method, '__signature__', None) or ''


@jsonrpc_module(CoreModule)
class DeejayDaemonCore(JSONRpcComponent, SignalingCoreComponent):

    def __init__(self, start_inotify=True):
        super(DeejayDaemonCore, self).__init__()
        config = DeejaydConfig.Instance()

        self.db = DatabaseQueries(DatabaseConnection(config))
        self.plugin_manager = plugins.PluginManager(config)

        self.player = player.init(self.db, self.plugin_manager, config)
        self.player.register_dispatcher(self)
        self.put_sub_handler('player', self.player)

        self.audiolib, self.videolib, self.watcher = \
            mediadb.init(self.db, self.player, config)
        self.audiolib.register_dispatcher(self)
        self.put_sub_handler('audiolib', self.audiolib)
        if self.videolib:
            self.videolib.register_dispatcher(self)
            self.put_sub_handler('videolib', self.videolib)

        self.recpls = DeejaydRecordedPlaylist(self.db, self.audiolib)
        self.recpls.register_dispatcher(self)
        self.put_sub_handler('recpls', self.recpls)

        self.sources = sources.init(self.player, self.db, self.audiolib,
                                    self.videolib, self.plugin_manager,
                                    config)
        self.sources.register_dispatcher(self)
        for source in self.sources.sources_obj.values():
            source.register_dispatcher(self)
            self.put_sub_handler(source.name, source)
            setattr(self, source.name, source)

        if not self.db.structure_created:
            self.audiolib.update()
            if self.videolib:
                self.videolib.update()

        # enable JSON-RPC introspection
        self.put_sub_handler('introspection', JSONRPCIntrospection(self))

        # start inotify thread when we are sure that all init stuff are ok
        if self.watcher and start_inotify:
            log.debug(_("Start inotify watcher"))
            self.watcher.start()

    def close(self):
        for obj in (self.watcher,self.player,self.sources,self.audiolib,\
                    self.videolib,self.db):
            if obj != None: obj.close()

    def ping(self): # do nothing
        pass

    def set_option(self, source, option_name, option_value):
        try: self.sources.set_option(source, option_name, option_value)
        except sources.UnknownSourceException:
            raise DeejaydError(_('Mode %s not supported') % source)
        except sources._base.SourceError, ex:
            raise DeejaydError(str(ex))

    def set_mode(self, mode_name):
        try: self.sources.set_source(mode_name)
        except sources.UnknownSourceException:
            raise DeejaydError(_('Mode %s not supported') % mode_name)

    def get_modes(self):
        av_sources = self.sources.get_available_sources()
        modes = {}
        for s in self.sources.get_all_sources():
            modes[s] = s in av_sources
        return modes

    def get_status(self):
        status = self.player.get_status()
        status.extend(self.sources.get_status())
        status.extend(self.audiolib.get_status())
        if self.videolib:
            status.extend(self.videolib.get_status())
        return dict(status)

    def get_stats(self):
        ans = self.db.get_stats()
        return dict(ans)

    def get_server_info(self):
        return {
            "server_version": __version__,
            "protocol_version": DEEJAYD_PROTOCOL_VERSION
        }

    def set_rating(self, media_ids, rating, type = "audio"):
        if int(rating) not in range(0, 5):
            raise DeejaydError(_("Bad rating value"))

        try: library = getattr(self, type+"lib")
        except AttributeError:
            raise DeejaydError(_('Type %s is not supported') % (type,))
        for id in media_ids:
            try: library.set_file_info(int(id), "rating", rating)
            except TypeError:
                raise DeejaydError(_("%s library not activated") % type)
            except deejayd.mediadb.library.NotFoundException:
                raise DeejaydError(_("File with id %s not found") % str(id))

# vim: ts=4 sw=4 expandtab
