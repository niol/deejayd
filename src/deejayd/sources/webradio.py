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

from deejayd.sources._base import _BaseSource, SimpleMediaList
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


class WebradioList(SimpleMediaList):

    def _update_list_id(self):
        self._list_id += 1


class WebradioSource(_BaseSource):
    name = "webradio"

    def __init__(self, db):
        _BaseSource.__init__(self, db)
        self._media_list = WebradioList(self.get_recorded_id())

        # load recorded webradio
        wbs = self.db.get_webradios()
        medias = [{"title":w[1], "uri":w[2], "type":"webradio",\
                   "url":w[2]} for w in wbs]
        self._media_list.add_media(medias)

    def add(self,url,name):
        if url.lower().startswith("http://"):
            if url.lower().endswith(".pls"):
                uris = get_uris_from_pls(url)
            elif url.lower().endswith(".m3u"):
                uris = get_uris_from_m3u(url)
            else: uris = [url]
        else: raise UnsupportedFormatException

        i = 1
        medias = []
        for uri in uris:
            medias.append({"title":name + "-%d" % i, "uri": uri, "url": uri,\
                          "type":"webradio"})
            i += 1
        self._media_list.add_media(medias)
        self.dispatch_signame('webradio.listupdate')
        return True

    def delete(self, id):
        _BaseSource.delete(self, id)
        self.dispatch_signame('webradio.listupdate')

    def get_status(self):
        return [
            (self.name, self._media_list.get_list_id()),
            (self.name+"length", self._media_list.length())
            ]

    def close(self):
        _BaseSource.close(self)
        # save webradio
        self.db.clear_webradios()
        values = [(w["pos"],w["title"],w["uri"])\
                    for w in self._media_list.get()]
        self.db.add_webradios(values)

# vim: ts=4 sw=4 expandtab
