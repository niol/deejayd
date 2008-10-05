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

from deejayd.xmlobject import ET, DeejaydXMLObject
from deejayd.webui.utils import format_time

class _Page(DeejaydXMLObject):

    def __init__(self, deejayd):
        self._core = deejayd

    def get_tpl(self):
        raise NotImplementedError

    def get(self, root):
        # set title
        title = ET.SubElement(root, "block", name = "main_title")
        title.text = self.__class__.title
        # set main template
        body = ET.SubElement(root, "block", name = "main")
        body.text = self.get_tpl()

        # set top button
        button = ET.SubElement(root, "page_btn")
        lbtn_elt = ET.SubElement(button, "btn", name = "left_button",\
                link = self.__class__.left_btn["link"])
        lbtn_elt.text = self.__class__.left_btn["title"]
        rbtn_elt = ET.SubElement(button, "btn", name = "right_button",\
                link = self.__class__.right_btn["link"])
        rbtn_elt.text = self.__class__.right_btn["title"]

    def refresh(self, root):
        raise NotImplementedError


class NowPlaying(_Page):
    name = "now_playing"
    title = _("Now Playing")
    left_btn = {"title": _("Current Mode"), "link": "current_mode"}
    right_btn = {"title": "", "link": ""}

    def __format_media_title(self, status):
        media_title = _("No playing Media")
        if status["state"] != "stop":
            current = self._core.get_current().get_medias()[0]
            if current["type"] == "song":
                return """
<div class='title'>%(title)s (%(time)s)</div>
<div class='artist album'>%(artist)s - %(album)s</div>
""" % { "title": current["title"],
        "time": format_time(int(current["length"])),
        "album": current["album"],
        "artist": current["album"]}

            elif current["type"] == "video":
                return """
<div class='title'>%(title)s (%(time)s)</div>
""" % { "title": current["title"],
        "time": format_time(int(current["length"]))}

            elif current["type"] == "webradio":
                return """
<div class='title'>%(title)s</div>
<div class='wb-url'>%(url)s</div>
""" % current

        else:
            return "<div class='title'>%s</div>" % _("No Playing Media")

    def get(self, root):
        super(NowPlaying, self).get(root)
        self.refresh(root)

    def refresh(self, root):
        status = self._core.get_status().get_contents()
        title = ET.SubElement(root, "block", name = "playing-text")
        title.text = self._to_xml_string(self.__format_media_title(status))

        player = ET.SubElement(root, "player")
        ET.SubElement(player, "volume", value = str(status['volume']))
        ET.SubElement(player, "state", value = status['state'])

    def get_tpl(self):
        return """
<div id="playing-info">
    <div id="playing-text"></div>
</div>
<div id="playing-control">
    <div class="control-button" id="previous_button"
        onclick="mobileui_ref.send_command('previous',null,true)"></div>
    <div class="control-button" id="playpause_button"
        onclick="mobileui_ref.send_command('play_toggle',null,true)"></div>
    <div class="control-button" id="stop_button"
        onclick="mobileui_ref.send_command('stop',null,true)"></div>
    <div class="control-button" id="next_button"
        onclick="mobileui_ref.send_command('next',null,true)"></div>
</div>
<div id="volume-widget">
    <div class="volume-button" id="volume-down"
        onclick="mobileui_ref.updateVolume('down')"></div>
    <div id="volume-slider">
        <div id="volume-handle"></div>
    </div>
    <div class="volume-button" id="volume-up"
        onclick="mobileui_ref.updateVolume('up')"></div>
</div>
"""


class ModeList(_Page):
    name = "mode_list"
    title = _("Mode List")
    left_btn = {"title": "", "link": ""}
    right_btn = {"title": _("Current Mode"), "link": "current_mode"}

    def refresh(self, root): pass

    def get_tpl(self):
        mode_names = {
                "playlist" : _("Playlist Mode"),
                "video" : _("Video"),
                "panel" : _("Navigation Panel"),
                "webradio" : _("Webradio"),
                "dvd" : _("Dvd Playback"),
                }
        modes = self._core.get_mode().get_contents()
        modes_tpl = ["""
<div class="mode-button"
    onclick="mobileui_ref.send_command('setMode',{mode:'%s'},true);
    return false;">%s
</div>
        """ % (m, mode_names[m]) for m in modes.keys() if modes[m]]

        return "<div id='modelist-content'>%s</div>"% "\n".join(modes_tpl)


class CurrentMode(_Page):
    name = "current_mode"
    left_btn = {"title": _("Mode List"), "link": "mode_list"}
    right_btn = {"title": "Now Playing", "link": "now_playing"}

    def __init__(self, deejayd):
        super(CurrentMode, self).__init__(deejayd)

        modes = {
            "playlist": PlaylistMode,
            "video": VideoMode,
            "panel": PanelMode,
            "dvd": DvdMode,
            "webradio": WebradioMode,
            }
        status = self._core.get_status().get_contents()
        self._source = modes[status["mode"]](deejayd)
        self.__class__.title = modes[status["mode"]].title

    def refresh(self, root):
        self._source.refresh(root)

    def get(self, root):
        super(CurrentMode, self).get(root)
        self._source.get(root)

    def get_tpl(self):
        return """
<div id="mode-toolbar">%(toolbar)s</div>
<div id="mode-body">
    <div id="mode-loading">%(loading)s</div>
    <div id="mode-content"></div>
</div>
""" % { "loading": _("Loading"),
        "toolbar": self._source.build_toolbar()}

    def custom_page(self, page, args):
        self._source.custom_page(page, args)

##########################################################################
##########################################################################

MEDIALIST_LENGTH = 15

class _Mode(DeejaydXMLObject):
    tb_objects = []
    can_select = False

    def __init__(self, deejayd):
        self._core = deejayd
        self._source = getattr(self._core, self.__class__.source)()
        self._ml_id = -1

    def build_toolbar(self):
        def format_btn(tb_obj):
            return """
      <div class="toolbar-button" id="%(id)s"
        onclick="mobileui_ref.%(cmd)s;return false;">%(text)s</div>
""" % tb_obj
        return "\n".join(map(format_btn, self.tb_objects))

    def _format_media_item(self, media):
        if media["type"] == "song":
            desc = """
<div class="media-title">%(title)s (%(time)s)</div>
<div class="media-desc">%(artist)s - %(album)s</div>
""" % { "title": media["title"],
        "time": format_time(int(media["length"])),
        "album": media["album"],
        "artist": media["artist"]}

        elif media["type"] == "webradio":
            desc = """
<div class='media-title'>%(title)s</div>
<div class="media-desc">%(url)s</div>
""" % media

        elif media["type"] == "video":
            desc = """
<div class='media-title'>%(title)s (%(time)s)</div>
<div class="media-desc">%(vres)s X %(hres)s</div>
""" % { "title": media["title"],
        "time": format_time(int(media["length"])),
        "vres": media["videoheight"], "hres": media["videowidth"],
        }

        select = ""
        if self.can_select:
            select = "<input type='checkbox'/>"
        return """
<div class='media-item'>
    <div value="%(id)s" class='media-select'>%(select)s</div>
    <div class='media-info'>%(desc)s</div>
    <div onclick="mobileui_ref.send_command('goto',{id:'%(id)s'},true);
        return false;" class="media-play-btn"></div>
</div>
""" % {"desc": desc, "id": media["id"], "select": select}

    def _build_media_list(self, root, start = 0):
        list_elt = ET.SubElement(root, "media_list")
        medias = self._source.get(start, MEDIALIST_LENGTH).get_medias()
        for m in medias:
            m_elt = ET.SubElement(list_elt, 'item')
            m_elt.text = self._to_xml_string(self._format_media_item(m))
            for k in ("id", "pos"):
                m_elt.attrib[k] = self._to_xml_string(m[k])

    def refresh(self, root):
        status = self._core.get_status().get_contents()
        if status[self.__class__.source_name] > self._ml_id:
            self._build_media_list(root)
            self._ml_id = status[self.__class__.source_name]

    def get(self, root):
        self._build_media_list(root)

    def custom_page(self, page, args):
        if page == "media_list":
            pass

class PlaylistMode(_Mode):
    source = "get_playlist"
    source_name = "playlist"
    title = _("Playlist Mode")
    can_select = True
    tb_objects = [
        {"id":"pl-add", "cmd":"customPage", "args": "{page:'plsDirectory'}",\
                "text": ""},
        {"id":"pl-clear", "cmd":"playlistClear", "args": "{}","text":""},
        {"id":"pl-shuffle", "cmd":"playlistClear", "args": "{}","text":""},
        ]

class VideoMode(_Mode):
    source = "get_video"
    source_name = "video"
    title = _("Video Mode")

class PanelMode(_Mode):
    source = "get_panel"
    source_name = "panel"
    title = _("Panel Mode")

class WebradioMode(_Mode):
    source = "get_webradios"
    source_name = "webradio"
    title = _("Webradio Mode")

class DvdMode(_Mode):
    source_name = "dvd"
    title = _("Dvd Mode")

    def __init__(self, deejayd):
        self._core = deejayd
        self._ml_id = -1

    def _build_media_list(self, root, start = 0): pass
    def refresh(self, root): pass
    def get(self, root): pass

# Build the list of available pages
page_list = {}

import sys
thismodule = sys.modules[__name__]
for item_name in dir(thismodule):
    try:
        item = getattr(thismodule, item_name)
        page_list[item.name] = item
    except AttributeError:
        pass

# vim: ts=4 sw=4 expandtab
