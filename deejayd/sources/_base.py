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

from sqlalchemy.orm import with_polymorphic
from deejayd import DeejaydError
from deejayd.common.component import SignalingComponent, JSONRpcComponent
from deejayd.common.component import PersistentStateComponent
from deejayd.sources._playorder import orders
from deejayd.sources._playlist import Playlist
from deejayd.db.connection import Session
from deejayd.db.models import MediaList


class _BaseSource(SignalingComponent, JSONRpcComponent,
                  PersistentStateComponent):
    name = ""
    available_playorder = ("inorder", "random", "onemedia", "random-weighted")
    has_repeat = True
    initial_state = {"id": 1, "playorder": "inorder", "repeat": False}
    source_signal = ''
    mlist_name = ''

    def __init__(self, library):
        super(_BaseSource, self).__init__()
        self.state_name = "%s_state" % self.name
        self.load_state()

        self._current = None
        self._playlist = Playlist(self.name, self.state["id"])
        self._library = library

        if self.has_repeat:
            self._playlist.repeat = self.state["repeat"]
        self._playorder = orders[self.state["playorder"]]

    def get(self, start=0, length=None):
        return self._playlist.get(start, length)

    def get_current(self):
        return self._current

    def go_to(self, plitem_id, id_type="id"):
        if id_type == "pos":
            try:
                self._current = self._playlist.get_item_with_pos(plitem_id)
            except IndexError: 
                self._current = None
            return self._current
        self._current = self._playorder.set_explicit(self._playlist, plitem_id)
        return self._current

    def get_status(self):
        status = [
            ("id", self._playlist.get_plid()),
            ("playorder", self._playorder.name),
            ("length", len(self._playlist)),
            ("timelength", self._playlist.get_time_length())
        ]
        if self.has_repeat:
            status.append(("repeat", self._playlist.repeat))
        return dict(status)

    def remove(self, plitem_ids):
        self._playlist.remove(plitem_ids)
        self.dispatch_signame(self.source_signal)

    def clear(self):
        self._playlist.clear()
        self._playorder.reset(self._playlist)
        self.dispatch_signame(self.source_signal)

    def next(self, explicit=True):
        if explicit:
            self._current = self._playorder.next_explicit(self._playlist,
                                                          self._current)
        else:
            self._current = self._playorder.next_implicit(self._playlist,
                                                          self._current)
        return self._current

    def previous(self):
        self._current = self._playorder.previous_explicit(self._playlist,
                                                          self._current)
        return self._current

    def set_option(self, name, value):
        if name == "playorder":
            try: 
                self._playorder = orders[value]
            except KeyError:
                raise DeejaydError(_("Unable to set %s order, not "
                                     "supported") % value)
            else:
                self.state["playorder"] = value
        elif name == "repeat" and self.has_repeat:
            if not isinstance(value, bool):
                raise DeejaydError(_("Option value has to be a boolean"))
            self._playlist.repeat = value
            self.state["repeat"] = value
        else:
            raise DeejaydError(_("Option %s not supported"))
        self.dispatch_signame(self.source_signal)

    def load_medias(self, media_ids, queue=True):
        medias = self._library.get_file_withids(media_ids)
        if len(media_ids) != len(medias):
            raise DeejaydError(_("Some medias has not been "
                                 "found in the library."))
        self._playlist.load(medias, queue)
        self.dispatch_signame(self.source_signal)

    def load_folders(self, f_ids, queue=True):
        self._playlist.load(self._library.get_all_files(f_ids), queue)
        self.dispatch_signame(self.source_signal)

    def load_playlist(self, pl_ids, queue=True):
        pls_type = with_polymorphic(MediaList, "*")
        medias = []
        for pl_id in pl_ids:
            pls = Session.query(pls_type).filter(MediaList.id == pl_id).one()
            medias += pls.get_medias(Session)
        self._playlist.load(medias, queue)
        self.dispatch_signame(self.source_signal)

    def shuffle(self):
        self._playlist.shuffle(self._current)
        self.dispatch_signame(self.__class__.source_signal)

    def move(self, plitem_ids, new_pos=-1):
        self._playlist.move(plitem_ids, new_pos)
        self.dispatch_signame(self.source_signal)
        
    def close(self):
        self.state["id"] = self._playlist.get_plid()
        self._playlist.save()
        self.save_state()
