#!/usr/bin/env python

# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

"""
This is the script used to test performance of library update
"""

import sys
import os
import time
from tempfile import NamedTemporaryFile
from optparse import OptionParser
from deejayd.db import connection
from deejayd.library.audio import AudioLibrary
from deejayd.library.video import VideoLibrary
from deejayd.ui.i18n import DeejaydTranslations

# init translation
t = DeejaydTranslations()
t.install()

usage = "usage: %prog [options] <library_path>"
parser = OptionParser(usage=usage)
parser.set_defaults(video=False)
parser.get_option('-h').help = _("Show this help message and exit.")
parser.add_option("-v", "--video", action="store_true", dest="video",
                  help="test video library instead of audio library")
(options, args) = parser.parse_args()

if len(args) != 1:
    sys.exit("Wrong arg number")
library_path = args[0]
if not os.path.isdir(library_path):
    sys.exit(_("The config file does not exist."))

if __name__ == "__main__":
    db_file = NamedTemporaryFile(prefix="db_deejayd", suffix=".db")

    # init database
    connection.init("sqlite:///" + db_file.name)

    if not options.video:
        library = AudioLibrary(library_path)
    else:
        library = VideoLibrary(library_path)

    print "Test audio library performance"
    ts = time.time()
    library.update(force=True, sync=True)
    delay = (time.time() - ts)
    print " --> forced: %s s " % str(delay)

    ts = time.time()
    library.update(force=False, sync=True)
    delay = (time.time() - ts)
    print " --> not forced: %s s " % str(delay)

    # print statistics
    print(library.get_stats())
    # cleanup
    db_file.close()

