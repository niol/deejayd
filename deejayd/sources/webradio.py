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

from zope.interface import implements
from deejayd.ui import log
from deejayd.jsonrpc.interfaces import WebradioSourceModule, jsonrpc_module
from deejayd.sources._base import _BaseSource, SourceError
from deejayd.webradio.IWebradioSource import IEditWebradioSource
from deejayd.model.playlist import SimplePlaylist
from deejayd.webradio.local import WebradioLocalSource
from deejayd.webradio.icecast import IceCastPlugin
from deejayd import DeejaydError
from deejayd.ui.config import DeejaydConfig


def require_editable_source(func):
    def impl(self, source_name, *args, **kwargs):
        if source_name not in self.wb_sources.keys():
            raise SourceError(_("Webradio source %s not supported") % source_name)
        source = self.wb_sources[source_name]
        if not IEditWebradioSource.providedBy(source):
            raise SourceError(_("You can not edit this webradio source"))

        res = func(self, source_name, *args, **kwargs)
        if source_name == self.state["source"]:
            self._reload()
        return res

    impl.__name__ = func.__name__
    return impl


@jsonrpc_module(WebradioSourceModule)
class WebradioSource(_BaseSource):
    name = "webradio"
    initial_state = {"id": 1, "source": "local", "source-cat": None}

    def __init__(self):
        _BaseSource.__init__(self, None)
        self.wb_sources = { "local": WebradioLocalSource() }
        if DeejaydConfig().getboolean("webradio", "icecast"):
            self.wb_sources["icecast"] = IceCastPlugin()

        # load current list
        self._media_list = SimplePlaylist(self.get_recorded_id() + 1)
        self._media_list.set_source("webradio")
        try:
            self.__source = self.wb_sources[self.state["source"]]
        except KeyError:  # recorded source not found, fallback to default
            self.__source = self.wb_sources["local"]
            self.state["source"] = "local"

        try: self._reload(sig=False)
        except DeejaydError:  # fallback to default
            self.__source = self.wb_sources["local"]
            self.state["source"] = "local"
            self._reload(sig=False)

    def get_available_sources(self):
        return [(s.NAME, IEditWebradioSource.providedBy(s)) \
                    for s in self.wb_sources.values()]

    def set_source(self, source):
        if self.state["source"] != source:
            try: self.__source = self.wb_sources[source]
            except KeyError:
                raise SourceError(_("Webradio source %s not supported") % source)
            self.state["source"] = source
            self._reload()

    def set_source_categorie(self, categorie):
        if self.state["source-cat"] != categorie:
            self._media_list.set(self.__source.get_webradios(categorie))
            self.state["source-cat"] = categorie
            self.dispatch_signame('webradio.listupdate')

    def get_source_categories(self, source_name):
        try: source = self.wb_sources[source_name]
        except KeyError:
            raise SourceError(_("Webradio source %s not supported") % source_name)
        return source.get_categories()

    def get_source_stats(self, source_name):
        try: source = self.wb_sources[source_name]
        except KeyError:
            raise SourceError(_("Webradio source %s not supported") % source_name)
        return source.get_stats()

    @require_editable_source
    def source_add_categorie(self, source_name, cat):
        return self.wb_sources[source_name].add_categorie(cat)

    @require_editable_source
    def source_delete_categories(self, source_name, cat_ids):
        self.wb_sources[source_name].remove_categories(cat_ids)
        if self.state["source"] == source_name \
                and self.state["source-cat"] in cat_ids:
            self.set_source_categorie(None)

    @require_editable_source
    def source_add_webradio(self, source_name, name, urls, cat=None):
        self.wb_sources[source_name].add_webradio(name, urls, cat)

    @require_editable_source
    def source_delete_webradios(self, source_name, wb_ids):
        self.wb_sources[source_name].remove_webradios(wb_ids)

    @require_editable_source
    def source_clear_webradios(self, source_name):
        self.wb_sources[source_name].clear_webradios()

    def get_status(self):
        return [
            ("webradio", self._media_list.get_id()),
            ("webradiolength", len(self._media_list)),
            ("webradiosource", self.state["source"]),
            ("webradiosourcecat", self.state["source-cat"]),
            ]

    def _reload(self, sig=True):
        self._media_list.set(self.__source.get_webradios(self.state["source-cat"]))
        if sig:
            self.dispatch_signame('webradio.listupdate')

# vim: ts=4 sw=4 expandtab