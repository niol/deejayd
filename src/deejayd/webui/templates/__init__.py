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
from string import Template

__all__ = ( "build_template", )

TRANSLATE = {
    # common
    "remove": _("Remove"),
    "play": _("Play"),
    "playlist": _("Playlist"),
    "search": _("Search"),
    "title": _("Title"),
    "album": _("Album"),
    "artist": _("Artist"),
    "genre": _("Genre"),
    "time": _("Time"),
    "bitrate": _("Bitrate"),
    "all": _("All"),
    "ok": _("Ok"),
    "cancel": _("Cancel"),
    "curSong": _("Go to current song"),
    "rating": _("Rating"),
    # main
    "mode": _("Mode"),
    "webradio": _("Webradio"),
    "video": _("Video"),
    "dvd": _("Dvd"),
    "panel": _("Navigation Panel"),
    "showDebug": _("Show debug zone"),
    "repeat": _("Repeat"),
    "playorder": _("Play Order"),
    "inorder": _("In Order"),
    "random": _("Random"),
    "randomWeighted": _("Weighted"),
    "onemedia": _("One Media"),
    "advancedOption": _("Advanced Option"),
    "audio_channel": _("Audio Channel:"),
    "subtitle_channel": _("Subtitle Channel:"),
    "av_offset": _("Audio/Video Offset:"),
    "sub_offset": _("Subtitle Offset:"),
    "zoom": _("Zoom:"),
    # playlist
    "load": _("Load"),
    "loadQueue": _("Load in the queue"),
    "plAdd": _("Add to playlist"),
    "plName": _("Playlist name"),
    "directory": _("Directory"),
    "updateAudioDB": _("update audio library"),
    "updateVideoDB": _("update video library"),
    "clear": _("Clear"),
    "save": _("Save"),
    "shuffle": _("Shuffle"),
    # webradio
    "wbAdd": _("Add a Webradio"),
    "wbUrl": _("URL (.pls and .m3u are supported)"),
    "name": _("Name"),
    "add": _("Add"),
    "url": _("URL"),
    "action": _("Actions"),
    # panel
    "magicPlaylist": _("Magic Playlist"),
    "staticPlaylist": _("Static Playlist"),
    "chooseAll": _("Choose All"),
    "enterPlsName": _("Enter Playlist Name"),
    "create": _("Create"),
    # queue
    "queue": _("Song Queue"),
    # dvd
    "reload": _("Reload"),
    # video
    "videoInfo": _("Video Informations"),
    "length": _("Length"),
    "width": _("Width"),
    "height": _("Height"),
    "subtitle": _("Subtitle"),
    }

def build_template(deejayd, config):
    dtd = "\n"
    for k, v in TRANSLATE.iteritems():
        dtd += "<!ENTITY %s \"%s\">\n" % (k, v)
    templates = {"dtd": dtd}

    template_dir = os.path.abspath(os.path.dirname(__file__))

    #get source template
    sources = deejayd.get_mode()
    for temp in sources.keys():
        fd = open(os.path.join(template_dir,temp+".xml"))
        templates[temp+"_box"] = fd.read()
        fd.close()
    # open main template
    fd = open(os.path.join(template_dir,"main.xml"))
    tpl = Template(fd.read())
    fd.close()

    return tpl.substitute(templates)

# vim: ts=4 sw=4 expandtab
