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

import os,re
from deejayd.xmlobject import DeejaydXMLObject, ET
from deejayd.webui.mobile import pages

class DeejaydWebAnswer(DeejaydXMLObject):

    def __init__(self,tmp_dir,compilation):
        self.__tmp_dir = tmp_dir
        self.__compilation = compilation
        self.xmlroot = ET.Element('deejayd')

    def set_config(self, config_parms):
        conf = ET.SubElement(self.xmlroot,"config")
        for parm in config_parms.keys():
            elt = ET.SubElement(conf,"arg",name=parm,\
                value=self._to_xml_string(config_parms[parm]))

    def set_page(self, deejayd_core, mode = "now_playing"):
        pages.page_list[mode](deejayd_core).get(self.xmlroot)

    def refresh_page(self, deejayd_core, mode = "now_playing"):
        pages.page_list[mode](deejayd_core).refresh(self.xmlroot)

    def update_player(self, status, cur_media):
        # Update player informations
        player  = ET.SubElement(self.xmlroot,"player")

        # update status
        status_elt = ET.SubElement(player, "status")
        for info in ("volume","time","state","current"):
            try: val = self._to_xml_string(status[info])
            except KeyError: pass
            else:
                node = ET.SubElement(status_elt, "parm")
                node.attrib["key"] = info
                node.attrib["value"] = val

        if cur_media != None:
            cur_elt = ET.SubElement(player,"cursong")
            cur_elt.attrib["type"] = cur_media["type"]
            for k in cur_media.keys():
                elt = ET.SubElement(cur_elt,k)
                if isinstance(cur_media[k], list): # listparm
                    for it in cur_media[k]:
                        if isinstance(it, dict): # dictparm
                            dict_elt = ET.SubElement(elt,"dictparm")
                            for dict_k in it.keys():
                                dict_elt.attrib[dict_k] = self._to_xml_string(\
                                    it[dict_k])
                        else:
                            val_elt = ET.SubElement(elt,"listvalue")
                            val_elt.text = self._to_xml_string(it)
                else:
                    elt.text = self._to_xml_string(cur_media[k])
            # get cover if available

    def set_msg(self,msg,type = "confirmation"):
        msg_node = ET.SubElement(self.xmlroot,"message",type = type)
        msg_node.text = self._to_xml_string(msg)

    def set_error(self, error):
        self.set_msg(error,"error")

# vim: ts=4 sw=4 expandtab
