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
from twisted.internet import threads
from deejayd.sources._base import _BaseSource, SimpleMediaList, SourceError
from deejayd.plugins import IWebradioPlugin
from deejayd.utils import get_uris_from_pls, get_uris_from_m3u


class WbLocalSource(object):
    implements(IWebradioPlugin)
    NAME = "local"
    HAS_CATEGORIE = False

    def __init__(self, db):
        self.db = db
        self.__load()

    def __load(self):
        self.__streams = {}
        for (id, name, url) in self.db.get_webradios():
            if id not in self.__streams.keys():
                self.__streams[id] = {"wb_id": id, "title": name,\
                        "urls": [url], "url-type": "urls", "uri": "",\
                        "url-index": 0, "type": "webradio"}
            else:
                self.__streams[id]["urls"].append(url)

    def add(self, urls, name):
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


        # save webradio
        self.db.add_webradio(name, set(needed_urls))
        self.__load()

    def delete(self, webradio_ids):
        self.db.remove_webradios(webradio_ids)
        self.__load()

    def clear(self):
        self.db.clear_webradios()
        self.__streams = {}

    def get_categories(self):
        raise SourceError(_("Categories not supported for this source"))

    def get_streams(self, categorie = None):
        return self.__streams.values()


class WebradioSource(_BaseSource):
    name = "webradio"
    _default_state = {"id": 1, "source": "local", "source-cat": ""}

    def __init__(self, db, plugin_manager):
        _BaseSource.__init__(self, db)
        self._state = self._load_state()
        self.wb_sources = {}
        # get plugins
        for plugin in plugin_manager.get_plugins(IWebradioPlugin):
            self.wb_sources[plugin.NAME] = plugin()
        # get local source from database
        self.wb_sources["local"] = WbLocalSource(self.db)

        # load current list
        self._media_list = SimpleMediaList(self.get_recorded_id() + 1)
        try:
            self.__source = self.wb_sources[self._state["source"]]
        except KeyError: # recorded source not found, fallback to default
            self.__source = self.wb_sources["local"]
            self._state["source"] = "local"

        # defer to thread init to avoid long delay
        # when we try to connect to shoutcast for example
        def load():
            self._media_list.set(\
                    self.__source.get_streams(self._state["source-cat"]))
        self.defered = threads.deferToThread(load)

    def get_available_sources(self):
        return [(s.NAME, s.HAS_CATEGORIE) for s in self.wb_sources.values()]

    def set_source(self, source):
        if self._state["source"] != source:
            try:
                self.__source = self.wb_sources[source]
            except KeyError:
                raise SourceError(_("Webradio source %s not supported")%source)
            self._media_list.set(self.__source.get_streams(\
                    self._state["source-cat"]))
            self._state["source"] = source
            self.dispatch_signame('webradio.listupdate')

    def get_source_categories(self, source_name):
        try: source = self.wb_sources[source_name]
        except KeyError:
            raise SourceError(_("Webradio source %s not supported")%source_name)
        if not source.HAS_CATEGORIE:
            raise SourceError(_("Categorie not supported for source %s")\
                              % source_name)
        return source.get_categories()


    def set_source_categorie(self, categorie):
        if not self.__source.HAS_CATEGORIE:
            raise SourceError(_("Categorie not supported for source %s")\
                              % categorie)
        if self._state["source-cat"] != categorie:
            self._media_list.set(self.__source.get_streams(categorie))
            self._state["source-cat"] = categorie
            self.dispatch_signame('webradio.listupdate')

    def add(self, urls, name):
        self.wb_sources["local"].add(urls, name)
        self.__reload_local_source()
        return True

    def delete(self, ids):
        webradio_ids = []
        for id in ids:
            wb = self._media_list.get_item(id)
            if wb is None:
                raise SourceError(_("Webradio with id %s not found")%str(id))
            webradio_ids.append(wb["wb_id"])

        self.wb_sources["local"].delete(webradio_ids)
        self.__reload_local_source()
        return True

    def clear(self):
        self.wb_sources["local"].clear()
        self.__reload_local_source()
        return True

    def get_status(self):
        return [
            ("webradio", self._media_list.list_id),
            ("webradiolength", len(self._media_list)),
            ("webradiosource", self._state["source"]),
            ("webradiosourcecat", self._state["source-cat"]),
            ]

    def __reload_local_source(self):
        if self.__source.NAME == "local": # reload the current medialist
            self._media_list.set(self.__source.get_streams())
            self.dispatch_signame('webradio.listupdate')

# vim: ts=4 sw=4 expandtab