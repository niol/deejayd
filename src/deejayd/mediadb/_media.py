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

import os

class SongMedia(dict):

    def __init__(self, db, infos):
        self.__db = db
        #infos : (id,dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt,rg_gain,rg_peak)
        self.__replaygain = {"track_gain":infos[12] , "track_peak":infos[13]}

        self["path"] = os.path.join(infos[1],infos[2])
        self["length"] = infos[10]
        self["media_id"] = infos[0]
        self["filename"] = infos[2]
        self["dir"] = infos[1]
        self["title"] = infos[4]
        self["artist"] = infos[5]
        self["album"] = infos[6]
        self["genre"] = infos[7]
        self["track"] = infos[8]
        self["date"] = infos[9]
        self["bitrate"] = infos[11]
        self["type"] = "song"

    def replay_gain(self):
        """Return the recommended Replay Gain scale factor."""
        try:
            db = float(self.__replaygain["track_gain"].split()[0])
            peak = self.__replaygain["track_peak"] and\
                     float(self.__replaygain["track_peak"]) or 1.0
        except (KeyError, ValueError, IndexError):
            return 1.0
        else:
            scale = 10.**(db / 20)
            if scale * peak > 1:
                scale = 1.0 / peak # don't clip
            return min(15, scale)

# vim: ts=4 sw=4 expandtab
