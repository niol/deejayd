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

class IphoneBrowser(object):

    def is_true(self, user_agent):
        if user_agent.lower().find("mobile") != -1:
            return True
        return False

    def header(self):
        return """
     <meta name="viewport" content="user-scalable=no, width=device-width">
     <link rel="apple-touch-icon" href="./static/themes/mobile/deejayd.jpg"/>
     <link href="./static/themes/mobile/iphone.css" type= "text/css"
        rel="stylesheet"/>
"""

class DefaultBrowser(object):

    def is_true(self, user_agent):
        return True

    def header(self):
        return ""

browsers = [IphoneBrowser(), DefaultBrowser()]

def build_template(user_agent):
    global browsers
    for bw in browsers:
        if bw.is_true(user_agent):
            browser = bw
            break

    return """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
    "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
   <head>
     <title>Deejayd Webui</title>
    <link href="./static/themes/mobile/default.css" type= "text/css"
        rel="stylesheet"/>
    %(header)s
    <!-- javascript script -->
    <script type="text/javascript" src="./static/js/lib/jquery.js"></script>
    <script type="text/javascript" src="./static/js/common.js"></script>
    <script type="text/javascript" src="./static/js/mobile/main.js"></script>
    <script type="text/javascript" src="./static/js/mobile/modes.js"></script>
   </head>
   <body>
        <div style="display: none;" id="notification"></div>
        <div id="header">
            <div class="button" id="left_button"></div>
            <div id="loading" style="display: none"></div>
            <div class="title" id="main_title"></div>
            <div class="button" id="right_button"></div>
        </div>
        <div id="main">
        </div>
   </body>
</html>
""" % { "header": browser.header() }

# vim: ts=4 sw=4 expandtab
