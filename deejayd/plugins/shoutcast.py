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

import urllib
from zope.interface import implements
from deejayd.xmlobject import ET
from deejayd.plugins import PluginError, IWebradioPlugin

# Without arg return genre list
# with genre= return station list
SHOUTCAST_URL_QUERY = "http://www.shoutcast.com/sbin/newxml.phtml"

# Use id= to select stream
SHOUTCAST_URL_STREAM = "http://www.shoutcast.com"
SHOUTCAST_TUNEIN_BASE = "/sbin/tunein-station.pls"

class ShoutcastPlugin(object):
    implements(IWebradioPlugin)
    NAME="shoutcast"
    HAS_CATEGORIE = True

    def __init__(self):
        self.__tunein = {}
        self.__categories = None
        self.__streams = {}

    def get_xml_page(self, url):
        try:
            page_handle = urllib.urlopen(url)
            xml_page = page_handle.read()
        except:
            raise PluginError(_("Unable to connect to shoutcast website"))

        # try to parse result
        try:
            root = ET.fromstring(xml_page)
        except ET.XMLSyntaxError:
            raise PluginError(_("Unable to parse shoutcast website page: %s")\
                              %xml_page)
        except:
            raise PluginError(_("Unable to read result from shoutcast website"))
        finally:
            page_handle.close()

        return root

    def get_categories(self):
        if self.__categories is None:
            root = self.get_xml_page(SHOUTCAST_URL_QUERY)
            if root is None:
                return []
            self.__categories = []
            for genre_elt in root.getchildren():
                if "name" in genre_elt.attrib:
                    self.__categories.append(genre_elt.attrib["name"])

        return self.__categories

    def get_streams(self, categorie):
        if categorie == "":
            return []

        if categorie not in self.__streams.keys():
            # get streams for this cat
            root = self.get_xml_page(SHOUTCAST_URL_QUERY+"?genre="+categorie)
            if root is None:
                return []

            self.__streams[categorie] = []
            for station in root.getchildren():
                if station.tag == "tunein":
                    self.__tunein[categorie] = station.attrib["base"]
                elif station.tag == "station":
                    tunein = categorie in self.__tunein.keys() and \
                        self.__tunein[categorie] or SHOUTCAST_TUNEIN_BASE
                    self.__streams[categorie].append({
                        "title": station.attrib["name"],
                        "type": "webradio",
                        "url": SHOUTCAST_URL_STREAM + tunein + "?id="\
                             + station.attrib["id"],
                        "url-type": "pls",
                        "uri": "",
                        })

        return self.__streams[categorie]

# vim: ts=4 sw=4 expandtab