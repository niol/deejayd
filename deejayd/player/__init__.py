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

from deejayd import DeejaydError
from deejayd.ui import log


AVAILABLE_BACKENDS = ('xine', 'gstreamer', )


class PlayerError(DeejaydError):pass

def init(db, plugin_manager, config):
    media_backend = config.get("general","media_backend")

    if media_backend == "auto":
        backend_it = iter(AVAILABLE_BACKENDS)
        media_backend = None
        try:
            while not media_backend:
                backend = backend_it.next()
                try:
                    __import__('.'.join(('deejayd', 'player', backend, )))
                except ImportError:
                    # Do nothing, simply ignore
                    pass
                else:
                    media_backend = backend
                    config.set('general', 'mediabackend', backend)
                    log.msg(_("Autodetected %s backend." % backend))
        except StopIteration:
            log.err(_("Could not find suitable media backend."), fatal=True)

    if media_backend == "gstreamer":
        from deejayd.player import gstreamer
        try: player = gstreamer.GstreamerPlayer(db, plugin_manager, config)
        except PlayerError, err:
            log.err(str(err), fatal=True)

    elif media_backend == "xine":
        from deejayd.player import xine
        try: player = xine.XinePlayer(db, plugin_manager, config)
        except PlayerError, err:
            log.err(str(err), fatal=True)

    else: log.err(_("Invalid media backend"), fatal=True)

    return player

# vim: ts=4 sw=4 expandtab