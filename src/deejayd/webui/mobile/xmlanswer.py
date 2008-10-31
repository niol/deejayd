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

class _DeejaydWebAnswer(DeejaydXMLObject):

    def __init__(self,deejayd,tmp_dir = "",compilation = True):
        self._deejayd = deejayd
        self._tmp_dir = tmp_dir
        self._compilation = compilation
        self.xmlroot = ET.Element('deejayd')

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

    def buid(self, args):
        raise NotImplementedError


class DeejaydErrorAnswer(_DeejaydWebAnswer):

    def __init__(self, error):
        self.xmlroot = ET.Element('deejayd')
        self.set_error(error)


class _DeejaydPageAns(_DeejaydWebAnswer):

    def build(self, args):
        self.set_block("main_title", self.title) # set title
        # set top button
        button = ET.SubElement(self.xmlroot, "page_btn")
        lbtn_elt = ET.SubElement(button, "btn", name = "left_button",\
                link = self.left_btn["link"])
        lbtn_elt.text = self._to_xml_string(self.left_btn["title"])
        rbtn_elt = ET.SubElement(button, "btn", name = "right_button",\
                link = self.right_btn["link"])
        rbtn_elt.text = self._to_xml_string(self.right_btn["title"])

        self.load_templates()
        return self.get_template("%s.thtml" % self.name)

#
# Now playing page
#
class NowPlaying(_DeejaydPageAns):
    commands = ('goto',)
    name = "now_playing"
    title = _("Now Playing")
    left_btn = {"title": _("Current Mode"), "link": "current_mode"}
    right_btn = {"title": "", "link": ""}

    def _get_current(self, status):
        m = False
        if status["state"] != "stop":
            m = self._deejayd.get_current().get_medias()[0]
        return m

    def build(self, args):
        tmpl = super(NowPlaying, self).build(args)
        status = self._deejayd.get_status().get_contents()
        self.set_block("main", tmpl.generate(state=status["state"],\
                current=self._get_current(status),f=self._to_xml_string,\
                format_time=format_time).render('xhtml'))
        # set volume
        player = ET.SubElement(self.xmlroot, "player")
        ET.SubElement(player, "volume", value = str(status['volume']))

class RefreshNowPlaying(NowPlaying):
    commands = ('play_toggle', 'stop', 'next', 'previous', 'setVol')

    def build(self, args):
        self.load_templates()
        status = self._deejayd.get_status().get_contents()
        tmpl = self.get_template("playing_title.thtml").generate(\
                current = self._get_current(status),f=self._to_xml_string,\
                format_time=format_time)
        self.set_block("playing-text", tmpl.render("xhtml"))

        player = ET.SubElement(self.xmlroot, "player")
        ET.SubElement(player, "volume", value = str(status['volume']))
        ET.SubElement(player, "state", value = status['state'])

#
# mode list page
#
class ModeList(_DeejaydPageAns):
    name = "mode_list"
    title = _("Mode List")
    left_btn = {"title": "", "link": ""}
    right_btn = {"title": _("Current Mode"), "link": "current_mode"}

    def build(self, args):
        tmpl = super(ModeList, self).build(args)
        mode_names = {
                "playlist" : _("Playlist Mode"),
                "video" : _("Video"),
                "panel" : _("Navigation Panel"),
                "webradio" : _("Webradio"),
                "dvd" : _("Dvd Playback"),
                }
        modes = self._deejayd.get_mode().get_contents()
        self.set_block("main", tmpl.generate(mode_list=modes,\
                mode_names=mode_names,f=self._to_xml_string).render('xhtml'))

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
        {"id":"wb-remove", "cmd":"wb_ref.remove()", "text":""},
        {"id":"wb-clear", "cmd":"wb_ref.clear()", "text":""},
        ]

class DvdMode(_Mode):
    source_name = "dvd"
    title = _("Dvd Mode")

    def __init__(self, deejayd):
        self._core = deejayd

    def get(self, root): pass
    def get_total_page(self):
        return 1

MODES = {
    "playlist": PlaylistMode,
    "panel": PanelMode,
    "video": VideoMode,
    "webradio": WebradioMode,
    "dvd": DvdMode,
    }

class CurrentMode(_DeejaydPageAns):
    commands = ("setMode",)
    name = "current_mode"
    left_btn = {"title": _("Mode List"), "link": "mode_list"}
    right_btn = {"title": "Now Playing", "link": "now_playing"}

    def build(self, args):
        status = self._deejayd.get_status().get_contents()
        source = MODES[status["mode"]](self._deejayd)
        self.title = source.title

        tmpl = super(CurrentMode, self).build(args)
        self.set_block("main", tmpl.generate(can_select=source.can_select,\
                medias=source.get_page(), page=1,\
                page_total=source.get_total_page(),\
                f=self._to_xml_string,
                tb_objects=source.tb_objects,\
                format_time=format_time).render('xhtml'))
        # update medialist info
        ET.SubElement(self.xmlroot, "medialist",\
                source = status["mode"], id = str(status[status["mode"]]),\
                page = "1", page_total=str(source.get_total_page()))

class RefreshCurrentMode(_DeejaydWebAnswer):

    def build(self, args):
        status = self._deejayd.get_status().get_contents()
        # update medialist info
        ET.SubElement(self.xmlroot, "refresh_medialist",\
                source = status["mode"], id = str(status[status["mode"]]))

##########################################################################
##########################################################################
class PageAnswer(_DeejaydWebAnswer):
    commands = ("setPage",)

    def build(self, args):
        pages = {
            "now_playing": NowPlaying,
            "mode_list": ModeList,
            "current_mode": CurrentMode,
            }
        self._page = pages[args["page"]](self._deejayd,\
                self._tmp_dir,self._compilation)
        self._page.build(args)

    def to_xml(self):
        try: return self._page.to_xml()
        except AttributeError:
            return super(PageAnswer, self).to_xml()

class DeejaydInit(NowPlaying):
    commands = ('init',)

    def build(self, args):
        # set config
        config_parms = {}
        conf = ET.SubElement(self.xmlroot,"config")
        for parm in config_parms.keys():
            elt = ET.SubElement(conf,"arg",name=parm,\
                value=self._to_xml_string(config_parms[parm]))
        super(DeejaydInit, self).build(args)

##########################################################################
# modes answer
##########################################################################
class UpdateMedialist(_DeejaydWebAnswer):
    commands = ("mediaList", "playlistClear", "playlistShuffle",\
            "webradioClear", "playlistRemove", "webradioRemove")

    def build(self, args):
        status = self._deejayd.get_status().get_contents()
        source = MODES[status["mode"]](self._deejayd)

        try: page = int(args["page"])
        except KeyError:
            page = 1

        self.load_templates("modes")
        tmpl = self.get_template("media_list.thtml")
        self.set_block("mode-content", \
                tmpl.generate(can_select=source.can_select,\
                medias=source.get_page(page),page=page,\
                page_total=source.get_total_page(),\
                f=self._to_xml_string,
                format_time=format_time).render('xhtml'))
        # update medialist info
        ET.SubElement(self.xmlroot, "medialist",\
                source = status["mode"], id = str(status[status["mode"]]),\
                page = str(page), page_total=str(source.get_total_page()))
        # set medialist description
        # self.set_block("mode-description", "zboub")

class PlaylistAdd(UpdateMedialist):
    commands = ("playlistAdd",)

    def build(self, args):
        super(PlaylistAdd, self).build(args)
        self.set_msg(_("Files has been loaded to the playlist"))

LIB_PG_LEN = 15
class LibraryList(_DeejaydWebAnswer):
    commands = ("getdir", )

    def _build(self, args):
        func = "get_%s_dir" % args["type"]
        ans = getattr(self._deejayd, func)(args['dir'])
        items = [{"type":"directory", "name":d,\
            "path":os.path.join(args['dir'],d)} for d in ans.get_directories()]
        if args["type"] == "audio":
            items += [{"type":"file", "name":f["filename"],\
                "path":os.path.join(args['dir'],f["filename"])}\
                for f in ans.get_files()]

        self.load_templates("modes")
        tpl_name = "%s_dir.thtml" % args["type"]

        page_total = len(items) / LIB_PG_LEN + 1
        page = int(args["page"])
        content = self.get_template(tpl_name).generate(\
            items=items[LIB_PG_LEN*(page-1):LIB_PG_LEN*page],\
            page_total=page_total,page=page,root=os.path.dirname(args['dir']),\
            dir=args['dir'],f=self._to_xml_string).render('xhtml')
        return content

    def build(self, args):
        self.set_block("mode-extra-content", self._build(args))

class ExtraPage(_DeejaydWebAnswer):
    commands = ("extraPage",)

    def build(self, args):
        self.load_templates("modes")
        content = None
        if args["page"] == "options":
            status = self._deejayd.get_status().get_contents()
            title = _("Options")
            source = status["mode"]
            content = self.get_template("options.thtml").generate(s=source)
            # set form input value
            form = HTMLFormFiller(data={\
                    "select-playorder": status[source+"playorder"],\
                    "checkbox-repeat": str(status[source+"repeat"])})
            content = content | form
            content = content.render('xhtml')
        elif args["page"] == "audio_dir":
            content = LibraryList(self._deejayd)._build(\
                    {"type":"audio","dir":'',"page":1})
            title = _("Audio Library")
        elif args["page"] == "video_dir":
            content = LibraryList(self._deejayd)._build(\
                    {"type":"video","dir":'',"page":1})
            title = _("Video Library")
        elif args["page"] == "video_search":
            pass
        elif args["page"] == "wb_form":
            title = _("Add Webradio")
            content = self.get_template("wb_form.thtml").\
                    generate().render('xhtml')

        # set extra page info
        ex_elt = ET.SubElement(self.xmlroot, "extra_page", title=title)
        if content: self.set_block("mode-extra-content",content)

class Options(_DeejaydWebAnswer):
    commands = ("playorder","repeat")
    def build(self, args):
        pass

answers = {}
import sys
thismodule = sys.modules[__name__]
for itemName in dir(thismodule):
    try:
        item = getattr(thismodule, itemName)
        for name in item.commands:
            answers[name] = item
    except AttributeError:
        pass

# vim: ts=4 sw=4 expandtab
