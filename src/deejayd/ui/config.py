# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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

import ConfigParser, os, sys, string

class DeejaydConfig:

    custom_conf = None
    __global_conf = '/etc/deejayd.conf'
    __user_conf = '~/.deejayd.conf'
    __config = None

    def __init__(self):

        if DeejaydConfig.__config == None:
            DeejaydConfig.__config = ConfigParser.ConfigParser()

            default_config_path = os.path.abspath(os.path.dirname(__file__))
            DeejaydConfig.__config.readfp(open(default_config_path\
                                        + '/defaults.conf'))

            conf_files = [DeejaydConfig.__global_conf,\
                         os.path.expanduser(DeejaydConfig.__user_conf)]
            if DeejaydConfig.custom_conf:
                conf_files.append(DeejaydConfig.custom_conf)
            DeejaydConfig.__config.read(conf_files)

    def __getattr__(self, name):
        return getattr(DeejaydConfig.__config, name)

    def set(self, section, variable, value):
        self.__config.set(section, variable, value)

    def get_bind_addresses(self, service = 'net'):
        bind_addresses = self.__config.get(service, 'bind_addresses').split(',')
        clean_bind_addresses = map(string.strip, bind_addresses)
        if 'all' in clean_bind_addresses:
            return ['']
        else:
            return map(string.strip, bind_addresses)

# vim: ts=4 sw=4 expandtab
