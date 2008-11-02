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

import os,re, StringIO
from genshi.template import TemplateLoader
from genshi.filters import HTMLFormFiller

from deejayd.xmlobject import DeejaydXMLObject, ET
from deejayd.webui.utils import format_time

class DeejaydWebAnswer(DeejaydXMLObject):

    def __init__(self, deejayd, tmp_dir = "", compilation = True):
        self._deejayd = deejayd
        self._tmp_dir = tmp_dir
        self._compilation = compilation
        self.xmlroot = ET.Element('deejayd')

    def set_config(self, config_parms = {}):
        conf = ET.SubElement(self.xmlroot,"config")
        for parm in config_parms.keys():
            elt = ET.SubElement(conf,"arg",name=parm,\
                value=self._to_xml_string(config_parms[parm]))

    def load_templates(self, subdir = None):
        directory = os.path.join(os.path.dirname(__file__), 'templates')
        if subdir: directory = os.path.join(directory, subdir)
        self._loader = TemplateLoader( directory, auto_reload = True)

    def get_template(self, tpl):
        if not self._loader:
            raise ValueError
        return self._loader.load(tpl)

    def set_block(self, nm, value):
        str_io = StringIO.StringIO(value)
        block_node = ET.SubElement(self.xmlroot,"block",name = nm)

        content = str_io.read(3500)
        while (content):
            part = ET.SubElement(block_node, "part")
            part.text = self._to_xml_string(content)
            content = str_io.read(3500)

    def set_msg(self,msg,type = "confirmation"):
        msg_node = ET.SubElement(self.xmlroot,"message",type = type)
        msg_node.text = self._to_xml_string(msg)

    def set_error(self, error):
        self.set_msg(error,"error")

    def set_player_infos(self, status, state = True):
        player = ET.SubElement(self.xmlroot, "player")
        ET.SubElement(player, "volume", value = str(status['volume']))
        if state:
            ET.SubElement(player, "state", value = status['state'])

    def set_page(self, page_name):
        self.load_templates()
        page = PAGES[page_name]()
        page.build(self, self._deejayd)
        self.set_block("main_title", page.title) # set title

        # set top button
        button = ET.SubElement(self.xmlroot, "page_btn")
        lbtn_elt = ET.SubElement(button, "btn", name = "left_button",\
                link = page.left_btn["link"])
        lbtn_elt.text = self._to_xml_string(page.left_btn["title"])
        rbtn_elt = ET.SubElement(button, "btn", name = "right_button",\
                link = page.right_btn["link"])
        rbtn_elt.text = self._to_xml_string(page.right_btn["title"])

    def refresh_page(self, page_name):
        page = PAGES[page_name]
        page().refresh(self, self._deejayd)

    def build_medialist(self, page = 1):
        status = self._deejayd.get_status().get_contents()
        source = MODES[status["mode"]](self._deejayd)

        # update medialist info
        self.load_templates("modes")
        tmpl = self.get_template("media_list.thtml")
        self.set_block("mode-content", \
                tmpl.generate(can_select=source.can_select,\
                medias=source.get_page(page),page=page,\
                page_total=source.get_total_page(),\
                f=self._to_xml_string,
                format_time=format_time).render('xhtml'))
        self.medialist_infos(status, source, str(page),\
                str(source.get_total_page()))

    def medialist_infos(self, status, source, page, page_total):
        ET.SubElement(self.xmlroot, "medialist",\
                source = status["mode"], id = str(status[status["mode"]]),\
                page = page, page_total=str(source.get_total_page()))
        # set medialist description
        # self.set_block("mode-description", "zboub")

    def build_library(self, type, dir, page = 1):
        LIB_PG_LEN = 15
        func = "get_%s_dir" % type
        ans = getattr(self._deejayd, func)(dir)
        items = [{"type":"directory", "name":d,\
            "path":os.path.join(dir,d)} for d in ans.get_directories()]
        if type == "audio":
            items += [{"type":"file", "name":f["filename"],\
                "path":os.path.join(dir,f["filename"])}\
                for f in ans.get_files()]

        self.load_templates("modes")
        tpl_name = "%s_dir.thtml" % type

        page_total = len(items) / LIB_PG_LEN + 1
        content = self.get_template(tpl_name).generate(\
            items=items[LIB_PG_LEN*(page-1):LIB_PG_LEN*page],\
            page_total=page_total,page=page,root=os.path.dirname(dir),\
            dir=dir,f=self._to_xml_string).render('xhtml')
        self.set_block("mode-extra-content", content)

    def extra_page(self, title):
        ET.SubElement(self.xmlroot, "extra_page",\
                title=self._to_xml_string(title))

#
# Now playing page
#
class NowPlaying:
    commands = ('goto',)
    name = "now_playing"
    title = _("Now Playing")
    left_btn = {"title": _("Current Mode"), "link": "current_mode"}
    right_btn = {"title": "", "link": ""}

    def _get_current(self, status, deejayd):
        m = False
        if status["state"] != "stop":
            m = deejayd.get_current().get_medias()[0]
        return m

    def refresh(self, ans, deejayd):
        ans.load_templates()
        status = deejayd.get_status().get_contents()
        tmpl = ans.get_template("playing_title.thtml").generate(\
                current = self._get_current(status, deejayd),\
                f=ans._to_xml_string, format_time=format_time)
        ans.set_block("playing-text", tmpl.render("xhtml"))
        ans.set_player_infos(status)

    def build(self, ans, deejayd):
        tmpl = ans.get_template("now_playing.thtml")
        status = deejayd.get_status().get_contents()
        ans.set_block("main", tmpl.generate(state=status["state"],\
                current=self._get_current(status, deejayd),\
                f=ans._to_xml_string,\
                format_time=format_time).render('xhtml'))
        ans.set_player_infos(status, state = False)

#
# mode list page
#
class ModeList:
    name = "mode_list"
    title = _("Mode List")
    left_btn = {"title": "", "link": ""}
    right_btn = {"title": _("Current Mode"), "link": "current_mode"}

    def refresh(self, ans, deejayd):
        pass

    def build(self, ans, deejayd):
        tmpl = ans.get_template("mode_list.thtml")
        mode_names = {
                "playlist" : _("Playlist Mode"),
                "video" : _("Video"),
                "panel" : _("Navigation Panel"),
                "webradio" : _("Webradio"),
                "dvd" : _("Dvd Playback"),
                }
        modes = deejayd.get_mode().get_contents()
        ans.set_block("main", tmpl.generate(mode_list=modes,\
                mode_names=mode_names,f=ans._to_xml_string).render('xhtml'))

#
# mode page
#
MEDIALIST_LENGTH = 15
class _Mode:
    tb_objects = []
    can_select = False

    def __init__(self, deejayd):
        self._deejayd = deejayd
        self._source = getattr(self._deejayd, self.__class__.source)()

    def get_total_page(self):
        status = self._deejayd.get_status().get_contents()
        return int(status[self.source_name+"length"]) / MEDIALIST_LENGTH + 1

    def get_page(self, page = 1):
        return self._source.get(MEDIALIST_LENGTH*(page-1), MEDIALIST_LENGTH)\
                .get_medias()

class PlaylistMode(_Mode):
    source = "get_playlist"
    source_name = "playlist"
    title = _("Playlist Mode")
    can_select = True
    tb_objects = [
        {"id":"pl-opt", "cmd":"mobileui_ref.send_command('extraPage',\
                {page:'options'},true)", "text": ""},
        {"id":"pl-add", "cmd":"mobileui_ref.send_command('extraPage',\
                {page:'audio_dir'},true)", "text": ""},
        {"id":"pl-shuffle", "cmd":"playlist_ref.shuffle()","text":""},
        {"id":"pl-remove", "cmd":"playlist_ref.remove()", "text":""},
        {"id":"pl-clear", "cmd":"playlist_ref.clear()", "text":""},
        ]

class VideoMode(_Mode):
    source = "get_video"
    source_name = "video"
    title = _("Video Mode")
    tb_objects = [
        {"id":"video-opt", "cmd":"mobileui_ref.send_command('extraPage',\
                {page:'options'},true)", "text": ""},
        {"id":"video-set", "cmd":"mobileui_ref.send_command('extraPage',\
                {page:'video_dir'},true)", "text": ""},
        {"id":"video-search", "cmd":"mobileui_ref.send_command('extraPage',\
                {page:'video_search'},true)", "text": ""},
        ]

class PanelMode(_Mode):
    source = "get_panel"
    source_name = "panel"
    title = _("Panel Mode")
    tb_objects = [
        {"id":"panel-opt", "cmd":"mobileui_ref.send_command('extraPage',\
                {page:'options'},true)", "text": ""},
        ]

class WebradioMode(_Mode):
    source = "get_webradios"
    source_name = "webradio"
    title = _("Webradio Mode")
    can_select = True
    tb_objects = [
        {"id":"wb-add", "cmd":"mobileui_ref.send_command('extraPage',\
                {page: 'wb_form'},true)", "text": ""},
        {"id":"wb-remove", "cmd":"webradio_ref.remove()", "text":""},
        {"id":"wb-clear", "cmd":"webradio_ref.clear()", "text":""},
        ]

class DvdMode(_Mode):
    source_name = "dvd"
    title = _("Dvd Mode")
    tb_objects = [
        {"id":"dvd-load", "cmd":"mobileui_ref.send_command('dvdLoad',\
                {},true)", "text": ""},
        ]

    def __init__(self, deejayd):
        self._deejayd = deejayd

    def get_total_page(self):
        return 1

    def get_page(self, page = 1):
        content = self._deejayd.get_dvd_content().get_dvd_contents()
        return [{"title": _("Title %s") % track["ix"],\
                 "id": track["ix"],\
                 "type": "dvd_track",
                 "length": track["length"]} for track in content["track"]]

MODES = {
    "playlist": PlaylistMode,
    "panel": PanelMode,
    "video": VideoMode,
    "webradio": WebradioMode,
    "dvd": DvdMode,
    }

class CurrentMode:
    commands = ("setMode",)
    name = "current_mode"
    left_btn = {"title": _("Mode List"), "link": "mode_list"}
    right_btn = {"title": "Now Playing", "link": "now_playing"}

    def refresh(self, ans, deejayd):
        pass # TODO

    def build(self, ans, deejayd):
        status = deejayd.get_status().get_contents()
        source = MODES[status["mode"]](deejayd)
        self.title = source.title

        tmpl = ans.get_template("current_mode.thtml")
        ans.set_block("main", tmpl.generate(can_select=source.can_select,\
                medias=source.get_page(), page=1,\
                page_total=source.get_total_page(),\
                f=ans._to_xml_string,
                tb_objects=source.tb_objects,\
                format_time=format_time).render('xhtml'))
        # update medialist info
        ans.medialist_infos(status, source, "1", str(source.get_total_page()))

PAGES = {
    "now_playing": NowPlaying,
    "current_mode": CurrentMode,
    "mode_list": ModeList,
    }

# vim: ts=4 sw=4 expandtab
