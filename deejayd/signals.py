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

from deejayd.dispatch import Signal

# player specific signals
player_status = Signal()      # Player status change (play/pause/stop/
                              # random/repeat/volume/manseek)
player_current = Signal()     # Currently played song change
player_plupdate = Signal()    # The stored playlist list has changed

# mediadb specific signals
mediadb_aupdate = Signal()    # Media library audio update
mediadb_vupdate = Signal()    # Media library video update
mediadb_mupdate = Signal(providing_args=["media_id", "type"])    # Media item
                                                                 # update

# source specific signals
mode_change = Signal()
playlist_listupdate = Signal()
playlist_update = Signal(providing_args=["pl_id"])
webradio_listupdate = Signal()
panel_update = Signal()
queue_update = Signal()
video_update = Signal()

SIGNALS = {
    'player.status': player_status,
    'player.current': player_current,
    'player.plupdate': player_plupdate,

    'mediadb.aupdate': mediadb_aupdate,
    'mediadb.vupdate': mediadb_vupdate,
    'mediadb.mupdate': mediadb_mupdate,

    "playlist.listupdate": playlist_listupdate,
    "playlist.update": playlist_update,
    "webradio.listupdate": webradio_listupdate,
    "panel.update": panel_update,
    "queue.update": queue_update,
    "video.update": video_update,
    "mode": mode_change,
}

# vim: ts=4 sw=4 expandtab
