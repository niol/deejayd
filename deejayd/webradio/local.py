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

from zope.interface import implementer
from deejayd.server.utils import get_uris_from_pls, get_uris_from_m3u
from deejayd.db.connection import Session
from deejayd.db.models import WebradioCategory, Webradio, WebradioEntry
from deejayd.db.models import WebradioSource
from deejayd.webradio.IWebradioSource import IEditWebradioSource
from deejayd.webradio._base import _BaseWebradioSource
from deejayd.ui import log
from deejayd import DeejaydError


def save_session(func):
    def new_func(*args, **kwargs):
        self = args[0]
        source = Session.query(WebradioSource)\
                        .filter(WebradioSource.name == self.NAME)\
                        .one()
        res = func(self, source, *args[1:], **kwargs)
        self._update_state()
        Session.commit()
        return res

    return new_func


@implementer(IEditWebradioSource)
class WebradioLocalSource(_BaseWebradioSource):
    NAME = "local"
    state_name = "webradio_local"

    @save_session
    def add_category(self, source, cat_name):
        category = Session.query(WebradioCategory)\
                          .filter(WebradioCategory.source == source)\
                          .filter(WebradioCategory.name == cat_name)\
                          .one_or_none()
        if category is not None:
            raise DeejaydError(_("Category %s already exists") % cat_name)
        category = WebradioCategory(source=source, name=cat_name)
        Session.add(category)
        return category.to_json()

    @save_session
    def remove_categories(self, source, ids):
        Session.query(WebradioCategory)\
               .filter(WebradioCategory.source == source)\
               .filter(WebradioCategory.id.in_(ids))\
               .delete(synchronize_session='fetch')

    @save_session
    def add_webradio(self, source, name, urls, cat=None):
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
                    log.err(_("Could not parse %s") % url)
                    pass

        needed_urls = []
        for url in provided_urls:
            try:
                protocol = url.split(':')[0]
                if protocol not in ('http', 'https', 'rtsp',):
                    raise ValueError
            except ValueError:
                log.err(_("Discarding %s : webradio protocol not supported.")
                          % url)
            else:
                if url not in needed_urls:
                    needed_urls.append(url)

        if len(needed_urls) < 1:
            raise DeejaydError(_("Given urls %s is not "
                                 "supported") % ",".join(urls))
        cats = cat is not None and [cat] or []

        webradio = Session.query(Webradio)\
                          .filter(Webradio.source == source)\
                          .filter(Webradio.name == name)\
                          .one_or_none()
        if webradio is not None:
            raise DeejaydError(_("Webradio %s already exists") % name)
        webradio = Webradio(source=source, name=name)
        Session.add(webradio)

        for c in cats:
            webradio.categories.append(Session.query(WebradioCategory).get(c))
        for url in needed_urls:
            webradio.entries.append(WebradioEntry(url=url))

    @save_session
    def remove_webradios(self, source, ids):
        Session.query(Webradio)\
               .filter(Webradio.source == source)\
               .filter(Webradio.id.in_(ids))\
               .delete(synchronize_session='fetch')

    @save_session
    def clear_webradios(self, source):
        Session.query(Webradio)\
               .filter(Webradio.source == source)\
               .delete(synchronize_session='fetch')
