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
from deejayd.jsonrpc.interfaces import WebradioSourceModule, jsonrpc_module
from deejayd.sources._base import _BaseSource, SimpleMediaList, SourceError
from deejayd.plugins import IWebradioPlugin, IEditWebradioPlugin, PluginError
from deejayd.utils import get_uris_from_pls, get_uris_from_m3u


class WbLocalSource(object):
    implements(IEditWebradioPlugin)
    NAME = "local"

    def __init__(self):
        self.__db = None
        self.__id = None

    def set_db_connection(self, connection):
        self.__db = connection
        self.__id = self.__db.get_webradio_source(self.NAME)

    def get_categories(self):
        return dict(self.__db.get_webradio_categories(self.__id))

    def get_webradios(self, cat_id = None):
        streams = {}
        for (id, name, url) in self.__db.get_webradios(self.__id, cat_id):
            if id not in streams.keys():
                streams[id] = {"wb_id": id, "title": name,\
                        "urls": [url], "url-type": "urls", "uri": "",\
                        "url-index": 0, "type": "webradio"}
            else:
                streams[id]["urls"].append(url)
        return streams.values()

    def add_categorie(self, cat):
        return {
            "id": self.__db.add_webradio_category(self.__id, cat),
            "name": cat
        }

    def remove_categories(self, ids):
        self.__db.remove_webradio_categories(self.__id, ids)

    def add_webradio(self, name, urls, cat = None):
        needed_urls = []
        for url in urls:
            if url.lower().startswith("http://"):
                try:
                    if url.lower().endswith(".pls"):
                        needed_urls.extend(get_uris_from_pls(url))
                    elif url.lower().endswith(".m3u"):
                        needed_urls.extend(get_uris_from_m3u(url))
                    else:
                        needed_urls.append(url)
                except IOError:
                    raise SourceError(_("Given url %s is not supported") % url)
            else:
                raise SourceError(_("Given url %s is not supported") % url)
        self.__db.add_webradio(self.__id, name, needed_urls, cat)

    def remove_webradios(self, ids):
        self.__db.remove_webradios(self.__id, ids)

    def clear_webradios(self):
        self.__db.clear_webradios(self.__id)

    def get_stats(self):
        return {
            "last_webradios_update": "",
            "last_categories_update": "",
            "webradio_count": "",
            "category_count": "",
        }

############################################################################
############################################################################

def require_editable_source(func):
    def impl(self, source_name, *args, **kwargs):
        if source_name not in self.wb_sources.keys():
            raise SourceError(_("Webradio source %s not supported")%source_name)
        source = self.wb_sources[source_name]
        if not IEditWebradioPlugin.providedBy(source):
            raise SourceError(_("You can not edit this webradio source"))

        res = func(self, source_name, *args, **kwargs)
        if source_name == self._state["source"]:
            self._reload()
        return res

    impl.__name__ = func.__name__
    return impl


@jsonrpc_module(WebradioSourceModule)
class WebradioSource(_BaseSource):
    name = "webradio"
    _default_state = {"id": 1, "source": "local", "source-cat": None}

    def __init__(self, db, plugin_manager):
        _BaseSource.__init__(self, db)
        self._state = self._load_state()
        self.wb_sources = {}
        # get plugins
        for plugin in plugin_manager.get_plugins(IWebradioPlugin):
            self.wb_sources[plugin.NAME] = plugin()
            self.wb_sources[plugin.NAME].set_db_connection(db)
        # get local source from database
        self.wb_sources["local"] = WbLocalSource()
        self.wb_sources["local"].set_db_connection(db)

        # load current list
        self._media_list = SimpleMediaList(self.get_recorded_id() + 1)
        try:
            self.__source = self.wb_sources[self._state["source"]]
        except KeyError: # recorded source not found, fallback to default
            self.__source = self.wb_sources["local"]
            self._state["source"] = "local"

        try: self._reload(sig = False)
        except PluginError: # fallback to default
            self.__source = self.wb_sources["local"]
            self._state["source"] = "local"
            self._reload(sig = False)

    def get_available_sources(self):
        return [(s.NAME, IEditWebradioPlugin.providedBy(s)) \
                    for s in self.wb_sources.values()]

    def set_source(self, source):
        if self._state["source"] != source:
            try: self.__source = self.wb_sources[source]
            except KeyError:
                raise SourceError(_("Webradio source %s not supported")%source)
            self._state["source"] = source
            self._reload()

    def set_source_categorie(self, categorie):
        if self._state["source-cat"] != categorie:
            self._media_list.set(self.__source.get_webradios(categorie))
            self._state["source-cat"] = categorie
            self.dispatch_signame('webradio.listupdate')

    def get_source_categories(self, source_name):
        try: source = self.wb_sources[source_name]
        except KeyError:
            raise SourceError(_("Webradio source %s not supported")%source_name)
        return source.get_categories()

    def get_source_stats(self, source_name):
        try: source = self.wb_sources[source_name]
        except KeyError:
            raise SourceError(_("Webradio source %s not supported")%source_name)
        return source.get_stats()

    @require_editable_source
    def source_add_categorie(self, source_name, cat):
        return self.wb_sources[source_name].add_categorie(cat)

    @require_editable_source
    def source_delete_categories(self, source_name, cat_ids):
        self.wb_sources[source_name].remove_categories(cat_ids)
        if self._state["source"] == source_name \
                and self._state["source-cat"] in cat_ids:
            self.set_source_categorie(None)

    @require_editable_source
    def source_add_webradio(self, source_name, name, urls, cat = None):
        self.wb_sources[source_name].add_webradio(name, urls, cat)

    @require_editable_source
    def source_delete_webradios(self, source_name, wb_ids):
        self.wb_sources[source_name].remove_webradios(wb_ids)

    @require_editable_source
    def source_clear_webradios(self, source_name):
        self.wb_sources[source_name].clear_webradios()

    def get_status(self):
        return [
            ("webradio", self._media_list.list_id),
            ("webradiolength", len(self._media_list)),
            ("webradiosource", self._state["source"]),
            ("webradiosourcecat", self._state["source-cat"]),
            ]

    def _reload(self, sig = True):
        self._media_list.set(self.__source.get_webradios(self._state["source-cat"]))
        if sig:
            self.dispatch_signame('webradio.listupdate')

# vim: ts=4 sw=4 expandtab
