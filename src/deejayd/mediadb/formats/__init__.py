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

import os, glob

def get_audio_extensions(player):
    base = os.path.dirname(__file__)
    base_import = "deejayd.mediadb.formats"
    ext_dict = {}

    modules = [os.path.basename(f[:-3]) \
                for f in glob.glob(os.path.join(base, "[!_]*.py"))\
                if os.path.basename(f).startswith("audio")]
    for m in modules:
        mod = __import__(base_import+"."+m, {}, {}, base)
        inst = mod.object()
        for ext in mod.extensions:
            if player.is_supported_format(ext):
                ext_dict[ext] = inst

    return ext_dict

def get_video_extensions(player):
    ext_dict = {}

    from deejayd.mediadb.formats import video
    inst = video.object(player)
    for ext in video.extensions:
            if player.is_supported_format(ext):
                ext_dict[ext] = inst

    return ext_dict

# vim: ts=4 sw=4 expandtab
