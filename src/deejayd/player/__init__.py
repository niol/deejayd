# Deejayd, a media player daemon
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

import sys
from deejayd.ui import log

class PlayerError(Exception):pass

def init(db,config):
    media_backend = config.get("general","media_backend")

    if media_backend == "gstreamer":
        from deejayd.player import gstreamer
        try: player = gstreamer.GstreamerPlayer(db,config)
        except PlayerError, err:
            log.err(str(err))
            sys.exit(str(err))

    elif media_backend == "xine":
        from deejayd.player import xine,_base
        try: player = xine.XinePlayer(db,config)
        except PlayerError, err:
            log.err(str(err))
            sys.exit(str(err))

    else: sys.exit(_("Invalid media backend"))

    return player

# vim: ts=4 sw=4 expandtab
