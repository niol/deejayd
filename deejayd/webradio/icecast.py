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

import urllib2, time
from twisted.internet import threads, task, reactor

from deejayd import DeejaydError
from xml.etree import cElementTree as ET
from deejayd.ui import log
from deejayd.ui.config import DeejaydConfig
from deejayd.webradio._base import _BaseWebradioSource
from deejayd.database.connection import DatabaseConnection

UPDATE_INTERVAL = 7 * 24 * 60 * 60  # 7 days
TIMEOUT = 2  # 2 seconds

class IceCastSource(_BaseWebradioSource):
    NAME = "icecast"
    state_name = "webradio_icecast"

    def __init__(self):
        super(IceCastSource, self).__init__()

        self.__last_parse = None
        self.__update_running = False
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
            d = threads.deferToThread(self.__reload_list)
            d.pause()

            d.addCallback(self.__on_reload_success)
            d.addErrback(self.__on_reload_error)
            d.unpause()

    def __on_reload_error(self, failure):
        log.err(_("Unable to update icecast webradio, see execption below"))
        log.err(failure)

    def __on_reload_success(self, result, *args):
        if result is not None:
            self.__last_parse = int(time.time())
            result["last_update"] = self.__last_parse
            self.source.set_stats(result)

            self.state["id"] += 1
            reactor.callFromThread(self.dispatch_signame, self.signal_name,
                                   source_name=self.NAME)

    def __reload_list(self):
        log.msg(_("Start to reload icecast webradio source"))
        url = DeejaydConfig().get("webradio", "icecast_url")
        try:
            page_handle = urllib2.urlopen(url, timeout=TIMEOUT)
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
        self.source.clear_webradios(commit=True)
        self.source.clear_categories(commit=True)

        categories = {}
        webradios = {}
        for station in root:
            try:
                server_type = station.find("server_type").text
                listen_url = station.find("listen_url").text
                genres = station.find("genre").text
                name = station.find("server_name").text
            except TypeError:
                continue

            if server_type.startswith("audio") or \
                    (server_type == "application/ogg" and \
                     not listen_url.endswith("ogv")):
                if name not in webradios:
                    genres = genres.split(" ")
                    webradios[name] = {
                        "name": name,
                        "urls": [],
                        "categories": []
                    }
                    for genre in genres:
                        if len(genre) <= 2 or genre.startswith("."):
                            continue
                        genre = genre.capitalize()
                        if genre not in categories.keys():
                            categories[genre] = self.source\
                                                    .add_categorie(genre,
                                                                   commit=False)
                        cat_id = categories[genre]["id"]
                        webradios[name]["categories"].append(cat_id)
                webradios[name]["urls"].append(listen_url)
                log.debug('Added icecast webradio %s' % name)
        # save wb
        for wb in webradios.values():
            self.source.add_webradio(wb["name"], wb["categories"], wb["urls"],
                                     commit=False)
        DatabaseConnection().commit()
        log.msg(_("Finish to reload icecast webradio source"))
        return {
            "wb_count": len(webradios),
            "cat_count": len(categories),
        }

    def get_categories(self):
        if self.__last_parse is None:
            raise DeejaydError("Unable to parse icecast webradio list")
        return super(IceCastSource, self).get_categories()

    def get_webradios(self, cat_id=None):
        if self.__last_parse is None:
            raise DeejaydError("Unable to parse icecast webradio list")
        return super(IceCastSource, self).get_webradios(cat_id)

    def close(self):
        if self.__task is not None:
            self.__task.stop()

# vim: ts=4 sw=4 expandtab
