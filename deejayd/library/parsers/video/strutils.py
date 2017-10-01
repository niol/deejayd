# -*- coding: utf-8 -*-
# Deejayd, a media player daemon
# Copyright 2013-2017 Mickael Royer <mickael.royer@gmail.com>
#                     Alexandre Rossi <alexandre.rossi@gmail.com>
# Copyright 2011-2012 Antoine Bertin <diaoulael@gmail.com>
# Copyright 2003-2006 Thomas Schueppel <stain@acm.org>
# Copyright 2003-2006 Dirk Meyer <dischi@freevo.org>
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

__all__ = ['str_to_bytes', 'str_to_bytes']


def str_to_bytes(s, encoding=None):
    """
    Attempts to convert a string of unknown character set
    to an encoded string.
    """
    if type(s) == str:
        return s.encode('utf-8')
    return s


def bytes_to_str(s, encoding=None):
    """
    Attempts to convert a encoded string to string
    """
    if type(s) == bytes:
        return s.decode('utf-8')
    return s
