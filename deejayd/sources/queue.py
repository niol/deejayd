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

from deejayd.jsonrpc.interfaces import QueueSourceModule, jsonrpc_module
from deejayd.sources._base import _BaseLibrarySource
from deejayd.model.playlist import PlaylistFactory
from deejayd import DeejaydError

@jsonrpc_module(QueueSourceModule)
class QueueSource(_BaseLibrarySource):
    mlist_name = "__djqueue__"
    name = "audioqueue"
    source_signal = 'audioqueue.update'
    available_playorder = ("inorder", "random")
    has_repeat = False

    def load_playlist(self, pl_ids, pos=None):
        try:
            pls_list = [PlaylistFactory().load_byid(self.library, pl_id)
                        for pl_id in pl_ids]
        except IndexError:
            raise DeejaydError(_("Some asked playlist are not found."))
        self._media_list.add(reduce(lambda ms, p: ms + p.get(), pls_list, []))
        self.dispatch_signame(self.source_signal)

    def go_to(self, nb, type = "id"):
        self._current = super(QueueSource, self).go_to(nb, type)
        if self._current != None:
            self._media_list.delete([self._current["id"],])
            self.dispatch_signame(self.source_signal)
        return self._current

    def next(self, explicit = True):
        self._current = None
        super(QueueSource, self).next(explicit)
        if self._current != None:
            self._media_list.delete([self._current["id"],])
            self.dispatch_signame(self.source_signal)
        return self._current

    def previous(self,rd,rpt):
        # Have to be never called
        raise NotImplementedError

    def reset(self):
        self._current = None

# vim: ts=4 sw=4 expandtab
