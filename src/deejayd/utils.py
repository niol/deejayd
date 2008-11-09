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

import urllib
from deejayd.ui import log

def quote_uri(path):
    if type(path) is unicode:
        path = path.encode('utf-8')
    return "file://%s" % urllib.quote(path)

def str_encode(data, charset = 'utf-8'):
    if type(data) is unicode: return data
    try: rs = data.decode(charset, "strict")
    except UnicodeError:
        log.err(_("%s string has wrong characters, skip it") %\
          data.decode(charset, "ignore").encode("utf-8","ignore"))
        raise UnicodeError
    return unicode(rs)

# vim: ts=4 sw=4 expandtab
