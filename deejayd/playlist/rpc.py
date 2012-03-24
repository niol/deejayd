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
from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.jsonrpc.interfaces import jsonrpc_module, RecordedPlaylistModule
from deejayd.playlist.static import StaticPlaylist
from deejayd.playlist.magic import MagicPlaylist

class PlaylistFactory(object):

    def __init__(self, db, id, audio_library = None):
        self.db = db
        self.library = audio_library
        try:
            self.pl_id, self.name, self.type = db.is_medialist_exists(id)
        except TypeError:
            raise DeejaydError(_("Playlist with id %s not found.") % str(id))

    def is_static(self):
        if self.type == "magic":
            raise DeejaydError(_("The selected playlist is not static"))
        return StaticPlaylist(self.db, self.library, self.pl_id, self.name)

    def is_magic(self):
        if self.type == "static":
            raise DeejaydError(_("The selected playlist is not static"))
        return MagicPlaylist(self.db, self.library, self.pl_id, self.name)

    def get_content(self, first=0, length=-1):
        cls = self.type == "magic" and MagicPlaylist or StaticPlaylist
        medias, filt, sort = cls(self.db, self.library,\
                self.pl_id, self.name).content(first, length)
        return {"medias": medias, "sort": sort, "filter": filt}


@jsonrpc_module(RecordedPlaylistModule)
class DeejaydRecordedPlaylist(SignalingComponent, JSONRpcComponent):

    def __init__(self, db, audio_library):
        super(DeejaydRecordedPlaylist, self).__init__()

        self.db, self.library = db, audio_library

    def get_list(self):
        return [{"name": pl, "pl_id": id, "type":type}\
            for (id, pl, type) in self.db.get_medialist_list() if not \
            pl.startswith("__") or not pl.endswith("__")]

    def get_content(self, pl_id, first=0, length=-1):
        return PlaylistFactory(self.db, pl_id, self.library).get_content(first,\
                length)

    def create(self, name, type):
        if name == "":
            raise DeejaydError(_("Set a playlist name"))
        # first search if this pls already exist
        try: self.db.get_medialist_id(name, type)
        except ValueError: pass
        else: # pls already exists
            raise DeejaydError(_("This playlist already exists"))

        if type == "static":
            pl_id = self.db.set_static_medialist(name, [])
        elif type == "magic":
            pl_id = self.db.set_magic_medialist_filters(name, [])
            # set default properties for this playlist
            default = {
                    "use-or-filter": "0",
                    "use-limit": "0",
                    "limit-value": "50",
                    "limit-sort-value": "title",
                    "limit-sort-direction": "ascending"
                    }
            for (k, v) in default.items():
                self.db.set_magic_medialist_property(pl_id, k, v)
        else:
            raise DeejaydError(_("playlist type has to be 'static' or 'magic'"))
        self.dispatch_signame('playlist.listupdate')
        return {"pl_id": pl_id, "name": name, "type": type}

    def erase(self, pl_ids):
        for id in pl_ids:
            self.db.delete_medialist(id)
        if pl_ids: self.dispatch_signame('playlist.listupdate')

    def static_add_media(self, pl_id, values, type = "path"):
        PlaylistFactory(self.db, pl_id, self.library).is_static()\
                                                     .add(values, type)
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

    def static_remove_media(self, pl_id, values):
        PlaylistFactory(self.db, pl_id, self.library).is_static().remove(values)
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

    def static_clear_media(self, pl_id):
        PlaylistFactory(self.db, pl_id, self.library).is_static().clear()
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

    def magic_add_filter(self, pl_id, filter):
        PlaylistFactory(self.db, pl_id).is_magic().add_filter(filter)
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

    def magic_remove_filter(self, pl_id, filter):
        PlaylistFactory(self.db, pl_id).is_magic().remove_filter(filter)
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

    def magic_clear_filter(self, pl_id):
        PlaylistFactory(self.db, pl_id).is_magic().clear_filter()
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

    def magic_get_properties(self, pl_id):
        return PlaylistFactory(self.db, pl_id).is_magic().get_properties()

    def magic_set_property(self, pl_id, k, v):
        PlaylistFactory(self.db, pl_id).is_magic().set_property(k, v)
        self.dispatch_signame('playlist.update', {"pl_id": pl_id})

# vim: ts=4 sw=4 expandtab
