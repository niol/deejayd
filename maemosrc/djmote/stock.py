# Djmote, a graphical deejayd client designed for use on Maemo devices
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

import os
import gtk

# 72x72 icons
DJMOTE_PLAY = "play_button"
DJMOTE_PAUSE = "pause_button"
DJMOTE_STOP = "stop_button"
DJMOTE_NEXT = "forward_button"
DJMOTE_PREVIOUS = "backward_button"
DJMOTE_VOLUME = "volume_button"

# 24x24 icons
DJMOTE_SHUFFLE = "player-shuffle"
DJMOTE_REPEAT = "player-repeat"

_ICONS_72 = [DJMOTE_PLAY,DJMOTE_PAUSE,DJMOTE_STOP,DJMOTE_NEXT,DJMOTE_PREVIOUS,\
          DJMOTE_VOLUME]
_ICONS_24 = [DJMOTE_SHUFFLE,DJMOTE_REPEAT]

def init():
    factory = gtk.IconFactory()
    # Add new icons
    pixmaps_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),\
                               'pixmaps')
    for fn in _ICONS_72:
        dir = os.path.join(pixmaps_dir,"72x72")
        icon_filename = os.path.join(dir, fn + ".png")
        pb = gtk.gdk.pixbuf_new_from_file(icon_filename)
        factory.add(fn, gtk.IconSet(pb))

    for fn in _ICONS_24:
        dir = os.path.join(pixmaps_dir,"24x24")
        icon_filename = os.path.join(dir, fn + ".png")
        pb = gtk.gdk.pixbuf_new_from_file(icon_filename)
        factory.add(fn, gtk.IconSet(pb))

    factory.add_default()

# vim: ts=4 sw=4 expandtab
