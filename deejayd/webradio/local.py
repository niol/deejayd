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
from deejayd.utils import get_uris_from_pls, get_uris_from_m3u
from deejayd.webradio.IWebradioSource import IEditWebradioSource
from deejayd.webradio._base import _BaseWebradioSource
from deejayd.ui import log
from deejayd import DeejaydError

class WebradioLocalSource(_BaseWebradioSource):
    implements(IEditWebradioSource)
    NAME = "local"

    def add_categorie(self, cat):
        return self.source.add_categorie(cat)

    def remove_categories(self, ids):
        return self.source.delete_categories(ids)

    def add_webradio(self, name, urls, cat=None):
        provided_urls = []
        for url in urls:
            if url.lower().startswith("http://"):
                try:
                    if url.lower().endswith(".pls"):
                        provided_urls.extend(get_uris_from_pls(url))
                    elif url.lower().endswith(".m3u"):
                        provided_urls.extend(get_uris_from_m3u(url))
                    else:
                        provided_urls.append(url)
                except IOError:
                    log.debug(_("Could not parse %s") % url)
                    pass

        needed_urls = []
        for url in provided_urls:
            try:
                protocol = url.split(':')[0]
                if protocol not in ('http', 'https', 'rtsp',):
                    raise ValueError
            except ValueError:
                log.debug(_("Discarding %s : webradio protocol not supported.")
                          % url)
            else:
                needed_urls.append(url)

        if len(needed_urls) < 1:
            raise DeejaydError(_("Given url %s is not supported") % url)
        self.source.add_webradio(name, cat, needed_urls)

    def remove_webradios(self, ids):
        self.source.delete_webradios(ids)

    def clear_webradios(self):
        self.source.clear_webradios()

    def get_stats(self):
        return {
            "last_webradios_update": "",
            "last_categories_update": "",
            "webradio_count": "",
            "category_count": "",
        }

# vim: ts=4 sw=4 expandtab