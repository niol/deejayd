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

import urllib, time
from zope.interface import implements
from twisted.internet import threads, task

from deejayd.xmlobject import ET
from deejayd.ui import log
from deejayd.plugins import PluginError, IWebradioPlugin

ICECAST_YP = "http://dir.xiph.org/yp.xml"
UPDATE_INTERVAL = 7*24*60*60 # 7 days

class IceCastPlugin(object):
    implements(IWebradioPlugin)
    NAME="icecast"

    def __init__(self):
        self.__db = None
        self.__id = None
        self.__last_parse = None
        self.__task = None

    def set_db_connection(self, connection):
        self.__db = connection
        self.__id = self.__db.get_webradio_source(self.NAME)

        self.__task = task.LoopingCall(self.__check_update)
        self.__task.start(60*60) # check every hour

    def __check_update(self):
        need_reload_list = True
        # see if stations list has already been parsed
        if self.__last_parse is None:
            last_parse = self.__db.get_webradio_stats(self.__id, "last_update")
            if last_parse is not None:
                (self.__last_parse,) = last_parse

        if self.__last_parse is not None:
            if int(time.time()) < int(self.__last_parse)+UPDATE_INTERVAL:
                need_reload_list = False

        if need_reload_list:
            threads.deferToThread(self.__reload_list)\
                   .addCallback(self.__on_reload_success)\
                   .addErrback(self.__on_reload_error)

    def __on_reload_error(self, failure):
        log.err(failure.printTraceback())

    def __on_reload_success(self, *args):
        self.__last_parse = int(time.time())

        self.__db.set_webradio_stats(self.__id, "last_update", self.__last_parse)
        self.__db.set_webradio_stats(self.__id, "wb_count", len(self.get_webradios()))
        self.__db.set_webradio_stats(self.__id, "cat_count", len(self.get_categories()))

    def __reload_list(self):
        try:
            page_handle = urllib.urlopen(ICECAST_YP)
            xml_page = page_handle.read()
        except:
            raise PluginError(_("Unable to connect to icecast website"))

        # try to parse result
        try:
            root = ET.fromstring(xml_page)
        except ET.XMLSyntaxError:
            raise PluginError(_("Unable to parse icecast webradio list"))
        except:
            raise PluginError(_("Unable to read result from icecast webradio list"))
        finally:
            page_handle.close()

        # start with erase all recorded webradio
        self.__db.clear_webradio_categories(self.__id)

        categories = {}
        wb_names = {}
        for station in root:
            try:
                server_type = station.find("server_type").text
                listen_url = station.find("listen_url").text
                genre = station.find("genre").text
                name = station.find("server_name").text
            except TypeError:
                continue

            if server_type.startswith("audio") or \
                    (server_type == "application/ogg" and \
                     not listen_url.endswith("ogv")):
                if genre not in categories.keys(): # add categorie in database
                    categories[genre] = self.__db.add_webradio_category(\
                                                    self.__id, genre)
                if name in wb_names.keys():
                    self.__db.add_webradio_urls(wb_names[name], [listen_url])
                else:
                    wb_names[name] = self.__db.add_webradio(self.__id, name, \
                                        [listen_url], categories[genre])

    def get_categories(self):
        if self.__last_parse is None:
            raise PluginError("Unable to parse icecast webradio list")
        return dict(self.__db.get_webradio_categories(self.__id))

    def get_webradios(self, cat_id = None):
        if self.__last_parse is None:
            raise PluginError("Unable to parse icecast webradio list")

        streams = {}
        for (id, name, url) in self.__db.get_webradios(self.__id, cat_id):
            if id not in streams.keys():
                streams[id] = {"wb_id": id, "title": name,\
                        "urls": [url], "url-type": "urls", "uri": "",\
                        "url-index": 0, "type": "webradio"}
            else:
                streams[id]["urls"].append(url)
        return streams.values()

    def get_stats(self):
        return {
            "last_webradios_update": self.__last_parse,
            "last_categories_update": self.__last_parse,
            "webradio_count": self.__db.get_webradio_stats(self.__id, "wb_count") or 0,
            "category_count": self.__db.get_webradio_stats(self.__id, "cat_count") or 0,
        }

    def close(self):
        if self.__task is not None:
            self.__task.stop()

# vim: ts=4 sw=4 expandtab
