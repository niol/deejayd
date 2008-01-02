#!/usr/bin/env python

# Djmote, a graphical deejayd client designed for use on Maemo devices
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

from distutils.core import setup
from djmote import __version__ as version

inst_icons_26   = [ 'data/icons/26x26/djmote.png' ]
inst_icons_40   = [ 'data/icons/40x40/djmote.png' ]
inst_icons_64   = [ 'data/icons/64x64/djmote.png' ]
data_files = [
    ('share/icons/hicolor/26x26/hildon', inst_icons_26),
    ('share/icons/hicolor/40x40/hildon', inst_icons_40),
    ('share/icons/hicolor/64x64/hildon', inst_icons_64),
    ('share/applications/hildon', [ 'data/djmote.desktop' ]),
    ('share/dbus-1/services', [ 'data/djmote.service' ]),
    ]

if __name__ == "__main__":
    setup( name="djmote", version=version,
           url="http://mroy31.dyndns.org/~roy/wiki/doku.php?id=djmote",
           description="djmote is a maemo client for deejayd",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/djmote"],
           packages=["deejayd","deejayd.net","djmote",\
                     "djmote.widgets","djmote.utils"],
           package_data={'djmote': ['pixmaps/24x24/*','pixmaps/72x72/*']},
           data_files=data_files
        )
# vim: ts=4 sw=4 expandtab
