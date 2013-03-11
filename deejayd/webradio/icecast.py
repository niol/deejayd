# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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
from twisted.internet import threads, task

from deejayd import DeejaydError
from deejayd.xmlobject import ET
from deejayd.ui import log
from deejayd.ui.config import DeejaydConfig
from deejayd.webradio._base import _BaseWebradioSource
from deejayd.database.connection import DatabaseConnection

UPDATE_INTERVAL = 7 * 24 * 60 * 60  # 7 days

class IceCastPlugin(_BaseWebradioSource):
    NAME = "icecast"

    def __init__(self):
        super(IceCastPlugin, self).__init__()

        self.__last_parse = None
        self.__task = task.LoopingCall(self.__check_update)
        self.__task.start(60 * 60)  # check every hour

    def __check_update(self):
        need_reload_list = True
        # see if stations list has already been parsed
        if self.__last_parse is None:
            stats = self.source.get_stats()
            if "last_update" in stats:
                self.__last_parse = stats["last_update"]

        if self.__last_parse is not None:
            if int(time.time()) < int(self.__last_parse) + UPDATE_INTERVAL:
                need_reload_list = False

        if need_reload_list:
            threads.deferToThread(self.__reload_list)\
                   .addCallback(self.__on_reload_success)\
                   .addErrback(self.__on_reload_error)

    def __on_reload_error(self, failure):
        log.err(failure.printTraceback())

    def __on_reload_success(self, *args):
        self.__last_parse = int(time.time())
        self.source.set_stats({
            "last_update": self.__last_parse,
            "wb_count": len(self.get_webradios()),
            "cat_count": len(self.get_categories()),
        })

    def __reload_list(self):
        log.msg("start to reload icecast webradio source")
        url = DeejaydConfig().get("webrdio", "icecast_url")
        try:
            page_handle = urllib.urlopen(url)
            xml_page = page_handle.read()
            log.debug("ICECAST - receive xml content %s" % xml_page.decode("utf-8"))
        except:
            raise DeejaydError(_("Unable to connect to icecast website"))

        # try to parse result
        try:
            root = ET.fromstring(xml_page)
        except ET.XMLSyntaxError:
            raise DeejaydError(_("Unable to parse icecast webradio list"))
        except:
            raise DeejaydError(_("Unable to read result from icecast webradio list"))
        finally:
            page_handle.close()

        # start with erase all recorded webradio
        self.source.clear_categories(commit=False)

        categories = {}
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
                if genre not in categories.keys():  # add categorie in database
                    categories[genre] = self.source.add_categorie(genre,
                                                                commit=False)
                    categories[genre]["webradios"] = {}

                cat = categories[genre]
                if name not in cat["webradios"].keys():
                    cat["webradios"][name] = [listen_url]
                else:
                    cat["webradios"][name].append(listen_url)
                log.debug('Added icecast webradio %s' % name)
        # save wb
        for cat in categories.values():
            for wb, urls in cat["webradios"].items():
                self.source.add_webradio(wb, cat["id"], urls, commit=False)
        DatabaseConnection().commit()
        log.msg("finish to reload icecast webradio source")

    def get_categories(self):
        if self.__last_parse is None:
            raise DeejaydError("Unable to parse icecast webradio list")
        return self.source.get_categories()

    def get_webradios(self, cat_id=None):
        if self.__last_parse is None:
            raise DeejaydError("Unable to parse icecast webradio list")
        return self.source.get_webradios(cat_id)

    def close(self):
        if self.__task is not None:
            self.__task.stop()

# vim: ts=4 sw=4 expandtab