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


import os
import pkgutil
import importlib


from deejayd import DeejaydError
from deejayd.ui import log


DEFAULT_BACKEND = 'vlc'
AVAILABLE_BACKENDS = [m[1]
                      for m in pkgutil.iter_modules([os.path.dirname(__file__)])
                      if not m[1].startswith('_')]


class PlayerError(DeejaydError):
    pass


def get_backend_module(backend_name):
    return importlib.import_module('.'.join(('deejayd', 'player',
                                             backend_name,)))

def init(config):
    media_backend = config.get("general", "media_backend")

    if media_backend == "auto":
        backend_it = iter([DEFAULT_BACKEND] + AVAILABLE_BACKENDS)
        media_backend = None
        try:
            while not media_backend:
                backend = next(backend_it)
                try:
                    backend_module = get_backend_module(backend)
                except ImportError:
                    # Do nothing, simply ignore
                    pass
                else:
                    media_backend = backend
                    config.set('general', 'mediabackend', backend)
                    log.msg(_("Autodetected %s backend." % backend))
        except StopIteration:
            log.err(_("Could not find suitable media backend."), fatal=True)
    elif media_backend in AVAILABLE_BACKENDS:
        backend_module = get_backend_module(media_backend)
    else:
        log.err(_("Invalid media backend %s" % media_backend), fatal=True)

    try:
        player_class = getattr(backend_module,
                               '%sPlayer' % media_backend.capitalize())
        player = player_class(config)
    except PlayerError as err:
        log.err(str(err), fatal=True)

    return player
