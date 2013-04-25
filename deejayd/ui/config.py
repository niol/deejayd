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

import ConfigParser, os, string
from deejayd import Singleton

@Singleton
class DeejaydConfig(ConfigParser.SafeConfigParser):
    __global_conf = '/etc/deejayd.conf'
    __user_conf = '~/.deejayd.conf'

    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)

        default_config_path = os.path.abspath(os.path.dirname(__file__))
        conf_files = [
            os.path.join(default_config_path, 'defaults.conf'),
            self.__global_conf,
            os.path.expanduser(self.__user_conf),
        ]
        self.read(conf_files)

    def getlist(self, section, variable):
        list_items = self.get(section, variable).split(',')
        return map(string.strip, list_items)

    def get_bind_addresses(self, service='net'):
        bind_addresses = self.getlist(service, 'bind_addresses')
        if 'all' in bind_addresses:
            return ['']
        else:
            return bind_addresses

# vim: ts=4 sw=4 expandtab