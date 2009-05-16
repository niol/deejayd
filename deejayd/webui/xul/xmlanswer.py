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

import os,re
from deejayd.xmlobject import DeejaydXMLObject, ET
from deejayd.webui.xul import rdfbuilder
from deejayd.ui import log
from deejayd.mediafilters import *

class DeejaydWebAnswer(DeejaydXMLObject):

    def __init__(self,rdf_dir):
        self.__rdf_dir = rdf_dir
        self.xmlroot = ET.Element('deejayd')

    def set_config(self, config_parms):
        conf = ET.SubElement(self.xmlroot,"config")
        for parm in config_parms.keys():
            elt = ET.SubElement(conf,"arg",name=parm,\
                value=self._to_xml_string(config_parms[parm]))

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
            if builder.name in status.keys():
                builder(deejayd,self.__rdf_dir).update(self, status)

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
                id=self._to_xml_string(pls["id"]), type="playlist",\
                pls_type=self._to_xml_string(pls["type"]))
            it.text = self._to_xml_string(pls["name"])

    def set_magic_playlist_infos(self, id, filters, properties):
        magic_playlist = ET.SubElement(self.xmlroot, "magic-playlist", \
                id = self._to_xml_string(id))

        root_filter = ET.SubElement(magic_playlist, "filters")
        for filter in filters:
            if filter.type != 'basic': continue
            filter_elt = ET.SubElement(root_filter, "filter")
            attrs = {'tag': filter.tag, 'operator': filter.get_name(),\
                    'value': filter.pattern}
            for k, v in attrs.items():
                attr_elt = ET.SubElement(filter_elt, k)
                attr_elt.text = self._to_xml_string(v)

        root_properties = ET.SubElement(magic_playlist, "properties")
        for k, v in properties.items():
            prop_elt = ET.SubElement(root_properties, "property")
            prop_elt.attrib['id'] = k
            prop_elt.text = self._to_xml_string(v)

    def init_panel_tags(self, deejayd):
        panel = deejayd.get_panel()
        tags = panel.get_panel_tags().get_contents()
        tags_elt = ET.SubElement(self.xmlroot, "panelTags")
        for tag in tags:
            tag_elt = ET.SubElement(tags_elt, "tag")
            tag_elt.text = self._to_xml_string(tag)

    def set_panel(self, deejayd, updated_tag = None):
        panel = deejayd.get_panel()
        mode = panel.get_active_list()

        # build panel if needed
        if mode["type"] == "panel":
            filters = panel.get().get_filter()
            try: filter_list = filters.filterlist
            except (TypeError, AttributeError):
                filter_list = []

            panel_filter = And()
            # find search filter
            for ft in filter_list:
                if ft.type == "basic" and ft.get_name() == "contains":
                    panel_filter.combine(ft)
                    break
                elif ft.type == "complex" and ft.get_name() == "or":
                    panel_filter.combine(ft)
                    break

            # find panel filter list
            for ft in filter_list:
                if ft.type == "complex" and ft.get_name() == "and":
                    filter_list = ft
                    break

            tag_list = panel.get_panel_tags().get_contents()
            try: idx = tag_list.index(updated_tag)
            except ValueError:
                pass
            else:
                tag_list = tag_list[idx+1:]
            for t in panel.get_panel_tags().get_contents():
                selected = []

                for ft in filter_list: # OR filter
                    try: tag = ft[0].tag
                    except (IndexError, TypeError): # bad filter
                        continue
                    if tag == t:
                        selected = [t_ft.pattern for t_ft in ft]
                        tag_filter = ft
                        break

                if t in tag_list:
                    list = deejayd.mediadb_list(t, panel_filter)
                    items = [{"name": _("All"), "value":"__all__", \
                        "class":"list-all", "sel":str(selected==[]).lower()}]
                    if t == "various_artist" and "__various__" in list:
                        items.append({"name": _("Various Artist"),\
                            "value":"__various__",\
                            "class":"list-unknown",\
                            "sel":str("__various__" in selected).lower()})
                    items.extend([{"name": l,"value":l,\
                        "sel":str(l in selected).lower(), "class":""}\
                        for l in list if l != "" and l != "__various__"])
                    if "" in list:
                        items.append({"name": _("Unknown"), "value":"",\
                            "class":"list-unknown",\
                            "sel":str("" in selected).lower()})
                    self.__build_tag_list(t, items)
                # add filter for next panel
                if len(selected) > 0:
                    panel_filter.combine(tag_filter)

    def __build_tag_list(self, tag, items):
        list = ET.SubElement(self.xmlroot,"panel-list", tag = tag)
        for item in items:
            listitem = ET.SubElement(list,"item", label = item["name"],\
                    value = item["value"], selected = item["sel"])

    def set_player(self, status, cur_media):
        # Update player informations
        player  = ET.SubElement(self.xmlroot,"player")

        # update status
        status_elt = ET.SubElement(player, "status")
        for info in ("volume","queueplayorder","playlistplayorder",\
                     "playlistrepeat","videoplayorder","videorepeat",\
                     "panelplayorder","panelrepeat","time","state","current"):
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
                    try: elt.text = self._to_xml_string(cur_media[k])
                    except TypeError: # someting strange happends
                        log.err(_("Unable to get key %s value for current")%k)
                        elt.text = ""
            # get cover if available
            try: cover = cur_media.get_cover()
            except AttributeError:
                return
            # save cover in the tmp dir if not already exists
            cover_ids = self.__find_cover_ids()
            ext = cover["mime"] == "image/jpeg" and "jpg" or "png"
            filename = "cover-%s.%s" % (str(cover["id"]), ext)
            if cover["id"] not in cover_ids:
                file_path = os.path.join(self.__rdf_dir,filename)
                fd = open(file_path, "w")
                fd.write(cover["cover"])
                fd.close()
                os.chmod(file_path,0644)
                # erase unused cover files
                for id in cover_ids:
                    try:
                        os.unlink(os.path.join(self.__rdf_dir,\
                                "cover-%s.jpg" % id))
                        os.unlink(os.path.join(self.__rdf_dir,\
                                "cover-%s.png" % id))
                    except OSError:
                        pass
            # let client to know cover availability
            elt = ET.SubElement(cur_elt, "cover")
            elt.text = self._to_xml_string(filename)

    def set_msg(self,msg,type = "confirmation"):
        msg_node = ET.SubElement(self.xmlroot,"message",type = type)
        msg_node.text = self._to_xml_string(msg)

    def set_error(self, error):
        self.set_msg(error,"error")

    def __find_cover_ids(self):
        ids = []
        for file in os.listdir(self.__rdf_dir):
            if re.compile("^cover-[0-9]+").search(file):
                t = file.split("-")[1] # id.ext
                t = t.split(".")
                try : ids.append(int(t[0]))
                except ValueError: pass
        return ids

# vim: ts=4 sw=4 expandtab
