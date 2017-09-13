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

from deejayd.jsonrpc.interfaces import AudioSourceModule, jsonrpc_module
from deejayd.sources._base import _BaseSource
from deejayd.db.models import StaticMediaList, StaticMediaListItem
from deejayd.db.connection import Session


@jsonrpc_module(AudioSourceModule)
class AudioSource(_BaseSource):
    base_medialist = "__djaudio__"
    name = "audiopls"
    source_signal = 'audiopls.update'

    def save(self, pls_name):
        pls = Session.query(StaticMediaList)\
                     .filter(StaticMediaList.name == pls_name)\
                     .one_or_none()
        if pls is None:
            pls = StaticMediaList(name=pls_name)    
            Session.add(pls)
        pls.items = [StaticMediaListItem(media_id=it["m_id"])
                     for it in self._playlist.get()]

        Session.commit()    
        self.dispatch_signame('recpls.listupdate')
        return {"playlist_id": pls.id}
