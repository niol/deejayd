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


def build_template():
    return """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
    "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
    <head>
        <title>Deejayd Webui</title>
        <meta name="viewport" content="user-scalable=no, width=device-width">
        <link href="static/themes/mobile/theme.css"
            type= "text/css" rel="stylesheet"/>
        <link rel="apple-touch-icon" href="static/themes/mobile/deejayd.png"/>
        <!-- javascript script -->
        <script type="text/javascript" src="static/js/lib/jquery.js"/>
        <script type="text/javascript" src="static/js/lib/jquery-ui.js"/>
        <script type="text/javascript" src="static/js/ajax.js"/>
        <script type="text/javascript" src="static/js/common.js"/>
        <script type="text/javascript" src="static/mobile/base.js"/>
        <script type="text/javascript" src="static/js/main.js"/>
    </head>
    <body>
        <div id="header">
            <div class="button" id="left-button"/>
            <div id="loading" style="display: none">
                <img src=""./static/theme/mobile/images/loading.gif"/>
            </div>
            <div class="title" id="main-title"/>
            <div class="button" id="right-button"/>
        </div>
        <div class="hide" id="notification"/>
        <div id="main">
        </div>
    </body>
</html>
"""

# vim: ts=4 sw=4 expandtab
