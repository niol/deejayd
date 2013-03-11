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

from zope.interface import implements
from deejayd.webradio.IWebradioSource import IWebradioSource
from deejayd.model.webradio import WebradioFactory

class _BaseWebradioSource(object):
    implements(IWebradioSource)
    NAME = ""

    def __init__(self):
        self.source = WebradioFactory().get_source(self.NAME)

    def get_categories(self):
        return self.source.get_categories()

    def get_webradios(self, cat_id=None):
        return self.source.get_webradios(cat_id)

    def get_stats(self):
        return self.source.get_stats()

    def close(self):
        pass

# vim: ts=4 sw=4 expandtab