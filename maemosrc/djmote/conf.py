# Djmote, a graphical deejayd client designed for use on Maemo devices
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

import os

class Config:

    def __init__(self, file):
        self.file = os.path.normpath(file)
        self.contents = {}
        if not os.path.isfile(self.file):
            self.__initialize()
        else:
            self.load()

    def __initialize(self):
        self.contents['host'] = 'media'
        self.contents['port'] = 6800
        self.contents['connect_on_startup'] = False
        self.save()

    def save(self):
        f = open(self.file, 'w')
        for item in self.contents.items():
            str_item = map(lambda x: str(x), item)
            f.write('='.join(str_item) + '\n')
        f.close()

    def load(self):
        f = open(self.file, 'r')
        for line in f.readlines():
            (key, val) = line.rstrip('\n').split('=')
            if val == 'True':
                self.contents[key] = True
            elif val == 'False':
                self.contents[key] = False
            else:
                try:
                    self.contents[key] = int(val)
                except ValueError:
                    self.contents[key] = val
        f.close()

    def __getattr__(self, name):
        return getattr(self.contents, name)


# vim: ts=4 sw=4 expandtab
