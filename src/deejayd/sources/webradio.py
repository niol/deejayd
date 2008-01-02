# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

from deejayd.sources._base import ItemNotFoundException,UnknownSource,\
                            UnknownSourceManagement
import urllib

class UnsupportedFormatException: pass
class UrlNotFoundException: pass

def get_playlist_file_lines(URL):
    try:
        pls_handle = urllib.urlopen(URL)
        playlist = pls_handle.read()
    except IOError:
        raise UrlNotFoundException

    return playlist.splitlines()

def get_uris_from_pls(URL):
    uris = []
    lines = get_playlist_file_lines(URL)
    for line in lines:
        if line.lower().startswith("file") and line.find("=")!=-1:
            uris.append(line[line.find("=")+1:].strip())

    return uris

def get_uris_from_m3u(URL):
    uris = []
    lines = get_playlist_file_lines(URL)
    for line in lines:
        if not line.startswith("#") and line.strip()!="":
            uris.append(line.strip())

    return uris


class Webradio(UnknownSource):

    def __init__(self,db,id):
        UnknownSource.__init__(self,db,None,id)

        webradios = self.db.get_webradios()
        self.source_content = [{"pos":webradio[0],"id":self.set_item_id(), \
            "title":webradio[1], "uri":webradio[2], "type":"webradio",\
            "url":webradio[2]} for webradio in webradios]

    def add(self,uri,name):
        pos = len(self.source_content)
        self.source_content.append({"pos":pos,"id":self.set_item_id(),\
            "title":name,"uri":uri,"url":uri,"type":"webradio"})

        # Increment webradioId
        self.source_id += 1

    def save(self):
        self.db.clear_webradios()
        values = [(webradio["pos"],webradio["title"],webradio["uri"]) \
            for webradio in self.source_content]
        self.db.add_webradios(values)


class WebradioSource(UnknownSourceManagement):
    name = "webradio"

    def __init__(self, db):
        UnknownSourceManagement.__init__(self,db)

        # Init parms
        self.current_source = Webradio(self.db,self.get_recorded_id())

    def add(self,url,name):
        if url.lower().startswith("http://"):
            if url.lower().endswith(".pls"):
                uris = get_uris_from_pls(url)
            elif url.lower().endswith(".m3u"):
                uris = get_uris_from_m3u(url)
            else: uris = [url]
        else: raise UnsupportedFormatException

        i = 1
        for uri in uris:
            self.current_source.add(uri,name + "-%d" % (i,))
            i += 1
        return True

# vim: ts=4 sw=4 expandtab
