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

import os, glob, ConfigParser
from zope.interface import Interface, Attribute
from deejayd import DeejaydError

class PluginError(DeejaydError): pass

class PluginManager(object):

    def __init__(self, config):
        try:
            self.enabled_plugins = config.getlist("general", "enabled_plugins")
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.enabled_plugins = []

    def get_plugins(self, interface):
        plugins = []

        base = os.path.dirname(__file__)
        base_import = "deejayd.plugins"
        modules = [os.path.basename(f[:-3]) \
                   for f in glob.glob(os.path.join(base, "[!_]*.py"))]
        for m in modules:
            mod = __import__(base_import+"."+m, {}, {}, base)
            for cls_name in dir(mod):
                cls = getattr(mod, cls_name)
                try:
                    if interface.implementedBy(cls) \
                        and cls.NAME in self.enabled_plugins:
                        plugins.append(cls)
                except:
                    continue

        return plugins

class IWebradioPlugin(Interface):
    NAME = Attribute("Name of the plugin")

    def set_db_connection(self, connection):
        """Allow webradio plugin to use connection to the database"""

    def get_categories(self):
        """return list of categories supported by this plugin
            raise an exception if no categorie has been supported"""

    def get_webradios(self, categorie = None):
        """return list of streams for a given categories """

    def get_stats(self):
        """return statistic informations about this source"""

class IEditWebradioPlugin(IWebradioPlugin):

    def add_categorie(self, cat):
        """add a new categorie"""

    def remove_categories(self, ids):
        """remove a list of categories"""

    def add_webradio(self, name, urls, cat = None):
        """add a new webradio"""

    def update_webradios_categorie(self, wb_ids, cat = None):
        """Change webradio category"""

    def remove_webradios(self, ids):
        """remove webradios from the source"""

    def clear_webradios(self):
        """remove all webradios from the source"""


class IPlayerPlugin(Interface):
    NAME = Attribute("Name of the plugin")

    def on_media_played(self, media):
        """ Call when a track has been played """

    def close(self):
        """ Call when we closed the player """

# vim: ts=4 sw=4 expandtab