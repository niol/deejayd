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

#from deejayd.utils import str_encode

class IphoneBrowser(object):

    def is_true(self, user_agent):
        if user_agent.lower().find("iphone") != -1:
            return True
        return False

    def header(self):
        return """
     <meta name="viewport" content="user-scalable=no, width=device-width">
     <link rel="apple-touch-icon" href="./../static/themes/mobile/deejayd.jpg"/>
     <link href="./../static/themes/mobile/webkit.css" type= "text/css"
        rel="stylesheet"/>
"""

class WebkitBrowser(object):

    def is_true(self, user_agent):
        if user_agent.lower().find("applewebkit") != -1:
            return True
        return False

    def header(self):
        return """
     <link href="./../static/themes/mobile/webkit.css" type= "text/css"
        rel="stylesheet"/>
"""

class DefaultBrowser(object):

    def is_true(self, user_agent):
        return True

    def header(self):
        return ""

browsers = [IphoneBrowser(), WebkitBrowser(), DefaultBrowser()]

def build_template(deejayd, user_agent):
    global browsers
    for bw in browsers:
        if bw.is_true(user_agent):
            browser = bw
            break

    # build modelist
    mode_list = deejayd.get_mode().get_contents()
    av_modes = [k for (k, v) in mode_list.items() if int(v) == 1]
    mode_title = {
        "playlist": _("Playlist Mode"),
        "panel": _("Panel Mode"),
        "video": _("Video Mode"),
        "webradio": _("Webradio Mode"),
        "dvd": _("DVD Mode"),
    }
    modes = []
    button = """
        <div class="mode-button"
             onclick="mobileui_ref.rpc.setMode('%(mode)s'); return false;">
            %(title)s
        </div>
    """
    for m in av_modes:
        modes.append(button % {"mode": m, "title": mode_title[m]})

    tpl = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
    "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
   <head>
    <title>Deejayd Webui</title>
    <meta http-equiv="Content-Style-Type" content="text/css" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link href="./../static/themes/mobile/default.css" type= "text/css"
        rel="stylesheet"/>
    %(header)s
    <!-- javascript script -->
    <script type="text/javascript" src="./../static/js/lib/jquery.js"></script>
    <script type="text/javascript" src="./../static/js/lib/jquery.json.js">
    </script>
    <script type="text/javascript" src="./../static/js/common.js"></script>
    <script type="text/javascript" src="./../static/js/rpc.js"></script>
    <script type="text/javascript" src="./../static/js/mobile/widget.js">
    </script>
    <script type="text/javascript" src="./../static/js/mobile/ui.js"></script>
    <script type="text/javascript" src="./../static/js/mobile/main.js"></script>
   </head>
   <body>
        <div style="display: none;" id="notification"></div>
        <div id="loading" style="display: none"></div>

        <!-- now playing page -->
        <div class="page" id="now_playing_page">
            <div class="header">
                <div class="button left"
                     onclick="mobileui_ref.updateMode();return false;">
                     %(current-mode)s
                </div>
                <div id="playing-title" class="title">
                    %(no-playing-media)s
                </div>
                <div class="button right"
                onclick="mobileui_ref.updateStatus();return false;">
                    %(refresh)s
                </div>
            </div>
            <div id="playing-block">
                <div style="display: none" id="playing-time-control">
                    <div class="time-control-button" id="time-fast-back"
                        onclick="mobileui_ref.rpc.seek(-60, true)"></div>
                    <div class="time-control-button" id="time-back"
                        onclick="mobileui_ref.rpc.seek(-10, true)"></div>
                    <div id="time-control-position"></div>
                    <div class="time-control-button" id="time-forward"
                        onclick="mobileui_ref.rpc.seek(10, true)"></div>
                    <div class="time-control-button" id="time-fast-forward"
                        onclick="mobileui_ref.rpc.seek(60, true)"></div>
                </div>
                <image id="playing-cover" src=""/>
                <div id="playing-control">
                    <div class="control-button" id="previous_button"
                        onclick="mobileui_ref.rpc.previous()"></div>
                    <div class="control-button stop" id="playpause_button"
                        onclick="mobileui_ref.rpc.playToggle()"></div>
                    <div class="control-button" id="stop_button"
                        onclick="mobileui_ref.rpc.stop()"></div>
                    <div class="control-button" id="next_button"
                        onclick="mobileui_ref.rpc.next()"></div>
                </div>
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
        </div>

        <!-- current mode page -->
        <div class="page" id="current_mode_page" style="display: none;">
            <div class="header">
                <div class="button left"
                onclick="mobileui_ref.ui.buildPage('modelist');return false;">
                    %(mode-list)s
                </div>
                <div id="mode-title" class="title"></div>
                <div class="button right"
                onclick="mobileui_ref.updateStatus(null); return false;">
                    %(now-playing)s
                </div>
            </div>
            <div id="mode-extra" style="display:none;">
                <div id="mode-extra-header">
                    <div id="mode-extra-title"></div>
                    <div id="mode-extra-close"
                      onclick="mobileui_ref.ui.getCurrentMode().closeExtra();">
                        %(close)s
                    </div>
                </div>
                <div id="mode-extra-content" style="display: none;"></div>
                <div id="mode-extra-options" style="display: none;">
                    <form><div id="playorder-box">
                        %(play-order)s :
                        <select name="select-playorder" id="playorder-option">
                            <option value="inorder">%(in-order)s</option>
                            <option value="random"> %(random)s</option>
                            <option value="random-weighted">%(wrandom)s</option>
                            <option value="onemedia">%(one-media)s</option>
                        </select>
                    </div>
                    <div id="repeat-box">
                        %(repeat)s : <input type="checkbox" id="repeat-option"
                                            name="checkbox-repeat" value="1"/>
                    </div></form>
                    <div class="center">
                        <input class="form-submit" type="submit"
                          value="%(save-options)s"
                          onclick="mobileui_ref.ui.setOptions();return false;"/>
                    </div>
                </div>
            </div>
            <div id="mode-main">
                <div id="mode-toolbar"></div>
                <div id="mode-content">
                    <div class="media-item content-list-pager">
                        <div class="pager-first pager-btn"></div>
                        <div class="pager-previous pager-btn"></div>
                        <div class="pager-desc"></div>
                        <div class="pager-next pager-btn"></div>
                        <div class="pager-last pager-btn"></div>
                    </div>
                    <div id="mode-content-list"></div>
                    <div class="media-item content-list-pager">
                        <div class="pager-first pager-btn"></div>
                        <div class="pager-previous pager-btn"></div>
                        <div class="pager-desc"></div>
                        <div class="pager-next pager-btn"></div>
                        <div class="pager-last pager-btn"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- mode list page -->
        <div class="page" id="modelist_page" style="display: none;">
            <div class="header">
                <div class="title">%(mode-list)s</div>
                <div class="button right"
                onclick="mobileui_ref.updateMode();return false;">
                    %(current-mode)s
                </div>
            </div>
            <div id="modelist-content">
                %(modelist-content)s
            </div>
        </div>


        <!-- only use for localisation -->
        <div id="messages" style="display: none;">
            <div id="i18n-no-media">%(no-playing-media)s</div>
            <div id="i18n-loading">%(loading)s</div>
            <div id="i18n-load-files">%(load-files)s</div>
            <div id="i18n-audio-library">%(audio-library)s</div>
            <div id="i18n-video-library">%(video-library)s</div>
            <div id="i18n-search">%(search)s</div>
            <div id="i18n-pls-mode">%(pls-mode)s</div>
            <div id="i18n-video-mode">%(video-mode)s</div>
            <div id="i18n-wb-mode">%(wb-mode)s</div>
            <div id="i18n-panel-mode">%(panel-mode)s</div>
            <div id="i18n-dvd-mode">%(dvd-mode)s</div>
            <div id="i18n-wb-name">%(wb-name)s</div>
            <div id="i18n-add">%(add)s</div>
            <div id="i18n-wb-add">%(wb-add)s</div>
            <div id="i18n-all">%(all)s</div>
            <div id="i18n-various">%(various)s</div>
            <div id="i18n-unknown">%(unknown)s</div>
            <div id="i18n-genre">%(genre)s</div>
            <div id="i18n-artist">%(artist)s</div>
            <div id="i18n-album">%(album)s</div>
            <div id="i18n-__various__">%(artist)s</div>
        </div>
   </body>
</html>
""" % {
    "header": browser.header(),
    "now-playing": _("Now Playing"),
    "no-playing-media": _("No Playing Media"),
    "mode-list": _("Mode List"),
    "current-mode": _("Current Mode"),
    "modelist-content": "\n".join(modes),
    "close": _("Close"),
    "refresh": _("Refresh"),
    # options
    "in-order": _("In Order"),
    "random": _("Random"),
    "wrandom": _("Weighted Random"),
    "one-media": _("One Media"),
    "repeat": _("Repeat"),
    "save-options": _("Save Options"),
    "play-order": _("Play Order"),
    # js localisation
    "loading": _("Loading..."),
    "load-files": _("Load Files"),
    "audio-library": _("Audio Library"),
    "video-library": _("Video Library"),
    "search": _("Search"),
    "pls-mode": _("Playlist Mode"),
    "video-mode": _("Video Mode"),
    "wb-mode": _("Webradio Mode"),
    "panel-mode": _("Panel Mode"),
    "dvd-mode": _("DVD Mode"),
    "wb-name": _("Webradio Name"),
    "wb-url": _("Webradio URL"),
    "add": _("Add"),
    "wb-add": _("Add a Webradio"),
    "all": _("All"),
    "various": _("Various Artist"),
    "unknown": _("Unknown"),
    "genre": _("Genre"),
    "artist": _("Artist"),
    "album": _("Album"),
}
    return str(tpl.encode('utf-8'))

# vim: ts=4 sw=4 expandtab
