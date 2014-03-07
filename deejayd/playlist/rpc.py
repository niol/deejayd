# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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
import deejayd.mediadb.library
from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.jsonrpc.interfaces import jsonrpc_module, RecordedPlaylistModule
from deejayd.model.playlist import PlaylistFactory


def load_playlist(type):
    def load_playlist_decorator(func):
        def load_playlist_func(self, pl_id, *__args, **__kw):
            try: pls = PlaylistFactory().load_byid(self.library, pl_id)
            except IndexError:
                raise DeejaydError(_("Playlist %s not found") % str(pl_id))
            if pls.get_type() != type:
                raise DeejaydError(_("Playlist %s has wrong type") % str(pl_id))
            rs = func(self, pls, *__args, **__kw)
            pls.save()

            if rs is None:
                self.dispatch_signame('recpls.update', pl_id=pl_id)
            return rs

        return load_playlist_func

    return load_playlist_decorator


@jsonrpc_module(RecordedPlaylistModule)
class DeejaydRecordedPlaylist(SignalingComponent, JSONRpcComponent):

    def __init__(self, audio_library):
        super(DeejaydRecordedPlaylist, self).__init__()

        self.__pl_manager = PlaylistFactory()
        self.library = audio_library

    def get_list(self):
        return self.__pl_manager.list()

    def get_content(self, pl_id, first=0, length=None):
        try: pls = self.__pl_manager.load_byid(self.library, pl_id)
        except IndexError:
            raise DeejaydError(_("Playlist with id %s does not exist"))
        medias, filter, sort = pls.get(first, length), None, None
        if pls.get_type() == "magic":
            filter = pls.get_main_filter()
            sort = pls.get_sorts()
        return {"medias": medias, "sort": sort, "filter": filter}

    def create(self, name, type):
        if name == "":
            raise DeejaydError(_("Set a playlist name"))
        if type not in ("static", "magic"):
            raise DeejaydError(_("playlist type has to be 'static' or 'magic'"))

        pls_list = self.get_list()
        for pls in pls_list:
            if pls["name"] == name and pls["type"] == type:
                raise DeejaydError(_("This playlist already exists"))

        pls = getattr(self.__pl_manager, type)(self.library, name)
        self.dispatch_signame('recpls.listupdate')
        return {"pl_id": pls.get_dbid(), "name": name, "type": type}

    def erase(self, pl_ids):
        try: pls_list = map(lambda i: self.__pl_manager.load_byid(self.library, i),
                            pl_ids)
        except IndexError:
            raise DeejaydError(_("Some playlists in the list do not exist"))

        self.__pl_manager.erase(pls_list)
        if pl_ids: self.dispatch_signame('recpls.listupdate')

    @load_playlist("static")
    def static_add_media_by_ids(self, pls, values):
        all_medias = self.library.get_file_withids(values)
        pls.add(all_medias)

    @load_playlist("static")
    def static_remove_media(self, pls, ids):
        pls.delete(ids)

    @load_playlist("static")
    def static_clear_media(self, pls):
        pls.clear()

    @load_playlist("magic")
    def magic_add_filter(self, pls, filter):
        pls.add_filter(filter)

    @load_playlist("magic")
    def magic_remove_filter(self, pls, filter):
        pls.remove_filter(filter)

    @load_playlist("magic")
    def magic_clear_filter(self, pls):
        pls.clear_filter()

    @load_playlist("magic")
    def magic_get_properties(self, pls):
        return pls.get_properties()

    @load_playlist("magic")
    def magic_set_property(self, pls, k, v):
        pls.set_property(k, v)

# vim: ts=4 sw=4 expandtab