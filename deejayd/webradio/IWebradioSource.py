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

from zope.interface import Interface, Attribute

class IWebradioSource(Interface):
    NAME = Attribute("Name of the plugin")

    def get_categories(self):
        """return list of categories supported by this plugin
            raise an exception if no categorie has been supported"""

    def get_webradios(self, categorie=None):
        """return list of streams for a given categories """

    def get_stats(self):
        """return statistic informations about this source"""


class IEditWebradioSource(IWebradioSource):

    def add_categorie(self, cat):
        """add a new categorie"""

    def remove_categories(self, ids):
        """remove a list of categories"""

    def add_webradio(self, name, urls, cat=None):
        """add a new webradio"""

    def update_webradios_categorie(self, wb_ids, cat=None):
        """Change webradio category"""

    def remove_webradios(self, ids):
        """remove webradios from the source"""

    def clear_webradios(self):
        """remove all webradios from the source"""

# vim: ts=4 sw=4 expandtab