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


from ConfigParser import NoOptionError
from deejayd.ui import log
from deejayd.mediadb import library,inotify
import sys

def init(db, player, config):
    audio_library,video_library,lib_watcher = None, None, None
    fc = config.get("mediadb","filesystem_charset")

    try: audio_dir = config.get("mediadb","music_directory")
    except NoOptionError:
        sys.exit(_("You have to choose a music directory"))
    else:
        try: audio_library = library.AudioLibrary(db, player, audio_dir, fc)
        except library.NotFoundException,msg:
            sys.exit(_("Unable to init audio library : %s") % msg)

    if not config.getboolean('general', 'video_support'):
        log.info(_("Video support disabled."))
        video_library = None
    else:
        try: video_dir = config.get('mediadb', 'video_directory')
        except NoOptionError:
            log.err(\
              _('Supplied video directory not found. Video support disabled.'))
            video_library = None
        else:
            try: video_library = library.VideoLibrary(db,player,video_dir,fc)
            except library.NotFoundException,msg:
                sys.exit(_("Unable to init video library : %s") % msg)

    if inotify.inotify_support:
        lib_watcher = inotify.DeejaydInotify(db, audio_library, video_library)
    else: log.info(_("Inotify support disabled"))

    return audio_library,video_library,lib_watcher

# vim: ts=4 sw=4 expandtab
