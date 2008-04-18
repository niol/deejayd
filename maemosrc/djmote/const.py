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
dir = os.path.abspath(os.path.dirname(__file__))

# KEY Values
KEY_ENTER = 65293
KEY_LEFT = 65361
KEY_RIGHT = 65363
KEY_FULLSCREEN = 65475
KEY_VOLUME_UP = 65476
KEY_VOLUME_DOWN = 65477

# Volume Step
VOLUME_STEP = 5

# Playlist Constants
PL_PAGER_LENGTH = 30

# show Timeout
SHOW_TIMEOUT = 5000 # 5s

# default font for djmote
FONT_DESC = "Sans Normal 13"

GTKRC_FILE = os.path.join(dir, 'data', 'gtkrc')
# vim: ts=4 sw=4 expandtab
