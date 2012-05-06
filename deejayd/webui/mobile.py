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

def build(config):
    return """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<!-- The HTML 4.01 Transitional DOCTYPE declaration-->
<!-- above set at the top of the file will set     -->
<!-- the browser's rendering engine into           -->
<!-- "Quirks Mode". Replacing this declaration     -->
<!-- with a "Standards Mode" doctype is supported, -->
<!-- but may lead to some differences in layout.   -->

<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">

    <!-- Specific for mobile device -->
    <meta name="viewport" content="user-scalable=no; width=device-width">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link rel="apple-touch-icon" href="./style/deejayd.jpg"/>

    <!--                                           -->
    <!-- Any title is fine                         -->
    <!--                                           -->
    <title>Deejayd Mobile Webui</title>

    <!-- this property sets the webui lang.   -->
    <meta name="gwt:property" content="locale=%(lang)s">

    <!--                                           -->
    <!-- This script loads your compiled module.   -->
    <!-- If you add any GWT meta tags, they must   -->
    <!-- be added before this line.                -->
    <!--                                           -->
    <script type="text/javascript" language="javascript"
            src="mobile_webui/mobile_webui.nocache.js"></script>

    <style>
        .gwt-CheckBox input {
          height: 30px; width: 30px;
          padding: 0px; margin:0px;
        }
        .loading-box {
          width: %(fullwidth)s;
          font-size: 15px;
          font-weight: bold;
          text-align: center;
        }
    </style>
  </head>

  <body>

    <div id="errorMsg" style="display: none; width: 22em; position: absolute; left: %(left)s; margin-left: -11em; color: red; background-color: white; border: 1px solid red; padding: 4px; font-family: sans-serif">
      Your web browser is not supported by this application.
      You need to use a web browser based on gecko or webkit engine
      in order for this application to display correctly.
    </div>

    <script>
      var errorMsg = document.getElementById("errorMsg");
      if (errorMsg) {
        setTimeout('errorMsg.style.display = "block";', 5000);
      }
    </script>

    <noscript>
      <div style="width: 22em; position: absolute; left: %(left)s; margin-left: -11em; color: red; background-color: white; border: 1px solid red; padding: 4px; font-family: sans-serif">
        Your web browser must have JavaScript enabled
        in order for this application to display correctly.
      </div>
    </noscript>

  </body>
</html>
""" % { "lang": config.get("webui", "lang"), "left": "50%", "fullwidth": "100%" }

# vim: ts=4 sw=4 expandtab
