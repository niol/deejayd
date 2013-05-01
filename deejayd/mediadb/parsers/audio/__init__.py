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

import os
import mimetypes
import glob
from deejayd.utils import quote_uri
from deejayd import DeejaydError
from deejayd.mediadb.parsers import ParseError, NoParserError

__all__ = ["AudioParserFactory"]

class AudioParserFactory(object):

    def __init__(self):
        base = os.path.dirname(__file__)
        base_import = "deejayd.mediadb.parsers.audio"
        self.parsers = {}

        modules = [os.path.basename(f[:-3]) \
                    for f in glob.glob(os.path.join(base, "[!_]*.py"))]
        for m in modules:
            mod = __import__(base_import + "." + m, {}, {}, base)
            try: filetype_class = mod.object
            except AttributeError:
                continue
            for ext in mod.extensions:
                self.parsers[ext] = filetype_class

    def get_extensions(self):
        return self.parsers.keys()

    def parse(self, path):
        extension = os.path.splitext(path)[1]
        if extension not in self.parsers:
            raise NoParserError()
        return self.parsers[extension]().parse(path)

# vim: ts=4 sw=4 expandtab