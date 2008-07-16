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
from deejayd.webui import rdfbuilder

class DeejaydWebAnswer(DeejaydXMLObject):

    def __init__(self,rdf_dir):
        self.__rdf_dir = rdf_dir
        self.xmlroot = ET.Element('deejayd')

    def set_config(self, config_parms):
        conf = ET.SubElement(self.xmlroot,"config")
        for parm in config_parms.keys():
            elt = ET.SubElement(conf,"arg",name=parm,\
                value=self._to_xml_string(config_parms[parm]))

    def set_locale_strings(self, strings):
        elt =  ET.SubElement(self.xmlroot, "locale")
        for s in strings.keys():
            s_elt = ET.SubElement(elt, "strings", name=s,\
                value=self._to_xml_string(strings[s]))

    def set_update_library(self, id, type, first = "1"):
        el = ET.SubElement(self.xmlroot, type+"_update", \
                p = self._to_xml_string(first))
        el.text = self._to_xml_string(id)

    def set_available_modes(self, modes):
        av_elt = ET.SubElement(self.xmlroot,"availableModes")
        for (name,active) in modes.items():
            elt = ET.SubElement(av_elt,"mode")
            elt.attrib["name"] = self._to_xml_string(name)
            elt.attrib["activate"] = self._to_xml_string(active)

    def set_view_mode(self, mode):
        mode_elt = ET.SubElement(self.xmlroot,"setsource")
        mode_elt.attrib["value"] = self._to_xml_string(mode)

    def set_mode(self, status, deejayd):
        for builder in rdfbuilder.modes:
            getattr(rdfbuilder, builder)(deejayd,self.__rdf_dir)\
                .update(self, status)

    def set_videodir(self, new_id, deejayd):
        nid = rdfbuilder.DeejaydVideoDirRdf(deejayd,self.__rdf_dir).\
            update(new_id)
        ET.SubElement(self.xmlroot,"videodir", id = self._to_xml_string(nid))

    def set_audiofile_list(self, files_list, root_dir = ""):
        list_elm = ET.SubElement(self.xmlroot, "file-list",\
                                 directory = self._to_xml_string(root_dir))
        for dir in files_list.get_directories():
            it = ET.SubElement(list_elm,"item", type = "directory")
            it.text = self._to_xml_string(dir)

        for file in files_list.get_files():
            path = os.path.join(root_dir,file["filename"])
            it = ET.SubElement(list_elm,"item",\
                value_type="path",
                value=self._to_xml_string(path),\
                type=self._to_xml_string(file["type"]))
            it.text = self._to_xml_string(file["filename"])

    def set_audiosearch_list(self, medias):
        list_elm = ET.SubElement(self.xmlroot, "audiosearch-list")
        for m in medias:
            it = ET.SubElement(list_elm,"item",\
                value_type="id",
                value=self._to_xml_string(m["media_id"]),\
                type=self._to_xml_string(m["type"]))
            it.text = self._to_xml_string(m["filename"])

    def set_playlist_list(self, playlist_list):
        list_elm = ET.SubElement(self.xmlroot, "playlist-list")
        for pls in playlist_list:
            it = ET.SubElement(list_elm,"item",\
                name=self._to_xml_string(pls["name"]), type="playlist")
            desc = _("%s (%d Songs)") % (pls["name"], int(pls["length"]))
            it.text = self._to_xml_string(desc)

    def set_player(self, status, cur_media):
        # Update player informations
        player  = ET.SubElement(self.xmlroot,"player")

        # update status
        status_elt = ET.SubElement(player, "status")
        for info in ("volume","queueplayorder","playlistplayorder",\
                     "playlistrepeat","videoplayorder","videorepeat",\
                     "time","state","current"):
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
