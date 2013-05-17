#!/usr/bin/env python

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

"""
This is the script used to test performance of mediadb update
"""

import sys
import os
import time
from optparse import OptionParser
from deejayd.ui.config import DeejaydConfig

import gettext
from deejayd.ui.i18n import DeejaydTranslations
LOCALES_PATH = os.path.join('build', 'mo')
try:
    t = gettext.translation("deejayd", LOCALES_PATH, class_=DeejaydTranslations)
except IOError:
    t = DeejaydTranslations()
t.install()

usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-c", "--conf-file", type="string", dest="conffile", \
    metavar="FILE", help="Specify a custom conf file")
(options, args) = parser.parse_args()

# add custom config parms
config = DeejaydConfig()
if options.conffile:
    if os.path.isfile(options.conffile):
        config.read([options.conffile])
    else:
        sys.exit(_("The config file does not exist."))

if __name__ == "__main__":
    from deejayd.mediadb import library
    fc = config.get("mediadb", "filesystem_charset")

    audio_dir = config.get("mediadb", "music_directory")
    try: audio_library = library.AudioLibrary(None, audio_dir, fc)
    except library.NotFoundException, msg:
        sys.exit("Unable to init audio library : %s" % msg)

    print "Test audio library performance"
    ts = time.time()
    audio_library.update(force=True, sync=True)
    delay = (time.time() - ts)
    print " --> forced: %s s " % str(delay)

    ts = time.time()
    audio_library.update(force=False, sync=True)
    delay = (time.time() - ts)
    print " --> not forced: %s s " % str(delay)


    # activated_sources = config.getlist('general', "activated_modes")
    # if "video" in activated_sources:
    #     video_dir = config.get('mediadb', 'video_directory')
    #     try: video_library = library.VideoLibrary(None, video_dir, fc)
    #     except library.NotFoundException, msg:
    #         sys.exit("Unable to init video library : %s" % msg)
