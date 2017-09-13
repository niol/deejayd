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

import time
from zope.interface import implements
from deejayd import DeejaydError
from deejayd.webradio.IWebradioSource import IWebradioSource
from deejayd.db.connection import Session
from deejayd.db.models import WebradioSource, WebradioCategory
from deejayd.db.models import Webradio
from deejayd.common.component import PersistentStateComponent
from deejayd.common.component import SignalingComponent


class _BaseWebradioSource(PersistentStateComponent, SignalingComponent):
    implements(IWebradioSource)
    NAME = ""
    state_name = ""
    initial_state = {"last_modified": -1}
    signal_name = "webradio.listupdate"

    def __init__(self):
        super(_BaseWebradioSource, self).__init__()

        source = Session.query(WebradioSource)\
                        .filter(WebradioSource.name == self.NAME)\
                        .one_or_none()
        if source is None:
            source = WebradioSource(name=self.NAME)
            Session.add(source)
            Session.commit()
        self.load_state()

    def get_categories(self):
        categories = Session.query(WebradioCategory)\
                            .join(WebradioSource)\
                            .filter(WebradioSource.name == self.NAME)\
                            .all()
        return [c.to_json() for c in categories]

    def get_webradios(self, cat_id=None, first=0, length=None):
        if cat_id is None:
            query = Session.query(Webradio)\
                           .join(WebradioSource)\
                           .filter(WebradioSource.name == self.NAME)\
                           .offset(first)
            if length is not None:
                query = query.limit(length)
            webradios = query.all()
        else:
            category = Session.query(WebradioCategory).get(cat_id)
            if category is None:
                raise DeejaydError(_("Category with id %s "
                                     "is not found") % cat_id)
            if length is not None:
                stop = min(first + int(length), len(category.webradios))
            else:
                stop = len(category.webradios)
            first = min(first, stop)
            webradios = category.webradios[first:stop]
        return [w.to_json() for w in webradios]

    def get_status(self):
        source = Session.query(WebradioSource)\
                        .filter(WebradioSource.name == self.NAME)\
                        .one()
        return {
            "last_modified": self.state["last_modified"],
            "categories_count": len(source.categories),
            "webradios_count": len(source.webradios),
        }

    def get_name(self):
        return self.NAME

    def _update_state(self):
        self.state["last_modified"] += int(time.time())

    def close(self):
        self.save_state()
