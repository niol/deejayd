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


from deejayd import DeejaydError
from deejayd.ui import log
from deejayd.library.audio import AudioLibrary
from deejayd.library.video import VideoLibrary

try:
    from deejayd.library import inotify
except ImportError:
    log.msg("Inotify is not supported on this platform")
    inotify = None


def init(player, config):
    audio_library, video_library, lib_watcher = None, None, None
    fc = config.get("mediadb", "filesystem_charset")

    audio_dir = config.get("mediadb", "music_directory")
    try:
        audio_library = AudioLibrary(audio_dir, fc)
    except DeejaydError as msg:
        log.err(_("Unable to init audio library : %s") % msg, fatal=True)

    if config.getboolean("video", "enabled"):
        video_dir = config.get('mediadb', 'video_directory')
        try:
            video_library = VideoLibrary(video_dir, fc)
        except DeejaydError as msg:
            log.err(_("Unable to init video library : %s") % msg, fatal=True)

    if inotify is not None:
        lib_watcher = inotify.DeejaydInotify(audio_library, video_library)

    return audio_library, video_library, lib_watcher
