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

VERSION="0.1.0"

def build(config):
    return """
<?xml-stylesheet href="chrome://global/skin/" type="text/css"?>

<window
    id="deejayd-webui-window"
    title="Deejayd webui"
    xmlns:html="http://www.w3.org/1999/xhtml"
    xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">

    <script>
        window.onload = function(e) {
            var element = document.createElement("deejaydExtension");
            element.setAttribute("refresh", '%(refresh)s');
            element.setAttribute("version", '%(version)s');
            document.documentElement.appendChild(element);

            var evt = document.createEvent("Events");
            evt.initEvent("deejaydEvent", true, false);
            element.dispatchEvent(evt);
            };
    </script>
    <vbox>
        <vbox id="deejayd-webui_install">
            <groupbox>
                <vbox style="padding: 10px">
                    <description>
                        %(install)s
                    </description>
                </vbox>
                <vbox align="center">
                    <html:a href="static/deejayd-webui.xpi">
                        %(clickHere)s
                    </html:a>
                </vbox>
            </groupbox>
        </vbox>
        <vbox id="deejayd-webui_upgrade" style="display:none">
            <groupbox>
                <vbox style="padding: 10px">
                    <description>
                        %(upgrade)s
                    </description>
                </vbox>
                <vbox align="center">
                    <html:a href="static/deejayd-webui.xpi">
                        %(clickHere)s
                    </html:a>
                </vbox>
            </groupbox>
        </vbox>
        <description style="display:none;color:#f00"
            id="deejayd-webui_error" value="%(error)s"/>
    </vbox>
</window>
""" % {
        "refresh": config.get('webui','refresh'),
        "version": VERSION,
        "install": _("You need to install a firefox extension in order to use the deejayd-webui XUL client. Please note that if you run a flavour of GNU/Linux, it should be available from your package manager.").\
                encode("utf-8"),
        "upgrade": _("You need to upgrade the firefox extension.").\
                encode("utf-8"),
        "clickHere": _("Install the deejayd-webui extension").encode("utf-8"),
        "error": _("ERROR : Host is not allowed to use the firefox extension.").\
                encode("utf-8"),
    }

# vim: ts=4 sw=4 expandtab
