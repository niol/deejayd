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

from deejayd.common.component import SignalingComponent, JSONRpcComponent
from deejayd.jsonrpc.interfaces import WebradioModule, jsonrpc_module
from deejayd.webradio.IWebradioSource import IEditWebradioSource
from deejayd.webradio.local import WebradioLocalSource
from deejayd.webradio.icecast import IceCastSource
from deejayd.db.connection import Session
from deejayd.db.models import Webradio
from deejayd import DeejaydError
from deejayd.ui.config import DeejaydConfig


def require_source(editable=False):
    def require_editable_source(func):
        def impl(self, source_name, *args, **kwargs):
            if source_name not in self.wb_sources.keys():
                raise DeejaydError(_("Webradio source %s not "
                                     "supported") % source_name)
            source = self.wb_sources[source_name]
            if editable and not IEditWebradioSource.providedBy(source):
                raise DeejaydError(_("You can not edit this webradio source"))

            res = func(self, source, *args, **kwargs)
            return res

        impl.__name__ = func.__name__
        return impl

    return require_editable_source


class WebradioObject(object):
    """
    This class is passed to player and implement API of other
    medias, such as videos or songs
    """

    def __init__(self, wb_dbobject):
        self.__obj = {
            "w_id": wb_dbobject.id,
            "name": wb_dbobject.name,
            "uris": [w_entry.url for w_entry in wb_dbobject.entries]
        }

    def to_json(self):
        return self.__obj

    def played(self):
        pass

    def stopped(self, position):
        pass

    def skip(self):
        pass

    def is_seekable(self):
        return False

    def get_uris(self):
        return self.__obj['uris']

    def has_video(self):
        return False

    def need_metadata_refresh(self):
        return True


@jsonrpc_module(WebradioModule)
class DeejaydWebradio(SignalingComponent, JSONRpcComponent):

    def __init__(self, player):
        super(DeejaydWebradio, self).__init__()
        self.player = player

        self.wb_sources = {"local": WebradioLocalSource()}
        if DeejaydConfig().getboolean("webradio", "icecast"):
            self.wb_sources["icecast"] = IceCastSource()

    def get_available_sources(self):
        return [{
            "name": s.NAME,
            "editable": IEditWebradioSource.providedBy(s)
        } for s in self.wb_sources.values()]

    def play_webradio(self, w_id):
        w = Session.query(Webradio).get(w_id)
        if w is None:
            raise DeejaydError(_("Webradio with id '%s' is not found") % w_id)
        self.player.play_webradio(WebradioObject(w))

    @require_source(editable=False)
    def get_source_content(self, source, category=None, first=0, length=None):
        return source.get_webradios(category, first, length)

    @require_source(editable=False)
    def get_source_categories(self, source):
        return source.get_categories()

    @require_source(editable=False)
    def get_source_status(self, source):
        return source.get_status()

    @require_source(editable=True)
    def source_add_category(self, source, cat):
        cat = source.add_category(cat)
        if cat is not None:
            self.dispatch_signame('webradio.listupdate', 
                                  source=source.get_name())
        return cat

    @require_source(editable=True)
    def source_delete_categories(self, source, cat_ids):
        source.remove_categories(cat_ids)
        self.dispatch_signame('webradio.listupdate', source=source.get_name())

    @require_source(editable=True)
    def source_add_webradio(self, source, name, urls, cat=None):
        source.add_webradio(name, urls, cat)
        self.dispatch_signame('webradio.listupdate', source=source.get_name())

    @require_source(editable=True)
    def source_delete_webradios(self, source, wb_ids):
        source.remove_webradios(wb_ids)
        self.dispatch_signame('webradio.listupdate', source=source.get_name())

    @require_source(editable=True)
    def source_clear_webradios(self, source):
        source.clear_webradios()
        self.dispatch_signame('webradio.listupdate', source=source.get_name())

    def close(self):
        for source in self.wb_sources.values():
            source.close()
