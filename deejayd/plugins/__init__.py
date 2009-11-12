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

import os, glob
from zope.interface import Interface, Attribute
from deejayd.interfaces import DeejaydError

class PluginError(DeejaydError): pass

class PluginManager(object):

    def __init__(self, config):
        self.enabled_plugins = config.getlist("general", "enabled_plugins")

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
    HAS_CATEGORIE = Attribute("Set to true if this module support categorie")

    def get_categories(self):
        """ return list of categories supported by this plugin
            raise an exception if no categorie has been supported"""

    def get_streams(self, categorie = None):
        """ return list of streams for a given categories """

# vim: ts=4 sw=4 expandtab