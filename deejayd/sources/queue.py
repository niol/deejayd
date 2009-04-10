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

import random
from deejayd.sources._base import _BaseAudioLibSource, SourceError

class QueueSource(_BaseAudioLibSource):
    base_medialist = "__djqueue__"
    name = "queue"
    source_signal = 'queue.update'
    available_playorder = ("inorder", "random")
    has_repeat = False

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
