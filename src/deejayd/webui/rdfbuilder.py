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
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET
from deejayd.xmlobject import DeejaydXMLObject
from deejayd.webui.utils import *
from deejayd.mediafilters import *

class _DeejaydSourceRdf(DeejaydXMLObject):
    name = "unknown"
    locale_strings = None

    def __init__(self, deejayd, rdf_dir):
        self._deejayd = deejayd
        self._rdf_dir = rdf_dir

    def update(self, xml_ans, status):
        current_id = self._get_current_id()
        try: new_id = status[self.__class__.name]
        except KeyError:
            return # this mode is not active
        new_id = int(new_id) % 10000
        if current_id != new_id:
            self._clean_rdfdir()
            self._build_rdf_file(new_id)

        # set xml
        elt = ET.SubElement(xml_ans.xmlroot, self.__class__.name,\
            id=xml_ans._to_xml_string(new_id))
        single, plural = self.__class__.locale_strings
        len = status[self.__class__.name + "length"]
        desc = self._to_xml_string(ngettext(single,plural,int(len))%str(len))
        try: time = int(status[self.__class__.name + "timelength"])
        except KeyError:
            pass
        else:
            if time > 0: desc += " (%s)" % format_time_long(time)
        elt.attrib["description"] = desc
        return elt

    def _build_root_elt(self):
        root = ET.Element("RDF:RDF")
        root.attrib["xmlns:RDF"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        root.attrib["xmlns:FILE"] = "http://%s/rdf#" % self.name

        return root

    def _build_rdf_file(self,new_id):
        medias = self._get_media_list()

        # build xml
        root = self._build_root_elt()
        seq = ET.SubElement(root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://%s/all-content" % self.name
        for media in medias:
            li = ET.SubElement(seq,"RDF:li")
            self._rdf_description(li,media,\
                "http://%s/%s" % (self.name, media["id"]))

        self._save_rdf(root,new_id)

    def _rdf_description(self, parent, parms,url = None):
        desc = ET.SubElement(parent,"RDF:Description")
        if url:
            desc.attrib["RDF:about"] = self._to_xml_string(url)
        for p in parms.keys():
            if p in ("time","length"):
                if parms[p]:
                    value = format_time(int(parms[p]))
                else:
                    value = 0
            elif p == "external_subtitle":
                value = parms[p] == "" and _("No") or _("Yes")
            elif p == "rating":
                rating = u'\u266a' * int(parms[p])
                value = self._to_xml_string(rating)
            else:
                try: value = self._to_xml_string(parms[p])
                except TypeError:
                    continue
            node = ET.SubElement(desc,"FILE:%s" % self._to_xml_string(p))
            node.text = value

    def _save_rdf(self, root_element, new_id):
        filename = "%s-%d.rdf" % (self.__class__.name, new_id);
        file_path = os.path.join(self._rdf_dir,filename)

        rs = '<?xml version="1.0" encoding="utf-8"?>' + "\n" + \
                ET.tostring(root_element,"utf-8")
        fd = open(file_path,"w")
        fd.write(rs)
        fd.close()
        os.chmod(file_path,0644)

    def _get_media_list(self):
        obj = getattr(self._deejayd, self.__class__.get_list_func)()
        return obj.get().get_medias()

    def _clean_rdfdir(self):
        for file in os.listdir(self._rdf_dir):
            path = os.path.join(self._rdf_dir,file)
            if os.path.isfile(path) and file.startswith(self.name+"-"):
                os.unlink(path)

    def _get_current_id(self):
        ids = []
        for file in os.listdir(self._rdf_dir):
            if re.compile("^"+self.name+"-[0-9]+\.rdf$").search(file):
                t = file.split("-")[1] # id.rdf
                t = t.split(".")
                try : ids.append(int(t[0]))
                except ValueError: pass

        if ids == []: return 0
        else: return max(ids)

class DeejaydPlaylistRdf(_DeejaydSourceRdf):
    name = "playlist"
    locale_strings = ("%s Songs", "%s Songs")
    get_list_func = "get_playlist"

class DeejaydPanelRdf(_DeejaydSourceRdf):
    name = "panel"
    locale_strings = ("%s Songs", "%s Songs")
    get_list_func = "get_panel"

    def update(self, xml_ans, status):
        panel = self._deejayd.get_panel()
        mode = panel.get_active_list()
        elt = super(DeejaydPanelRdf, self).update(xml_ans, status)
        elt.attrib["type"] = mode["type"]
        elt.attrib["value"] = mode["value"]

    def _build_rdf_file(self,new_id):
        root = self._build_root_elt()
        panel = self._deejayd.get_panel()
        panel_content = panel.get()

        mode = panel.get_active_list()
        if mode["type"] == "panel":
            filters = panel_content.get_filter()
            try: filter_list = filters.filterlist
            except (TypeError, AttributeError):
                filter_list = []

            panel_filter = And()
            for t in ("genre", "artist", "album"):
                selected = None
                for ft in filter_list:
                    if ft.tag == t and ft.get_name() == "equals":
                        selected = ft.pattern
                        break

                list = self._deejayd.mediadb_list(t, panel_filter)
                self.__build_tag_list(root, t, list, selected)

                # add filter for next panel
                if selected: panel_filter.combine(Equals(t, selected))

        elif mode["type"] == "playlist":
            pass

        seq = ET.SubElement(root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://%s/all-content" % self.name
        for m in panel_content.get_medias():
            li = ET.SubElement(seq,"RDF:li")
            self._rdf_description(li,m,"http://%s/%s" % (self.name, m["id"]))

        self._save_rdf(root,new_id)

    def __build_tag_list(self, root, type, list, selected = None):
        seq = ET.SubElement(root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://panel/all-%s" % type

        items = [{"name": "All", "value":"__all__", "class":"list-all",\
                  "sel":str(selected==None).lower()}]
        items.extend([{"name": l,"value":l,"sel":str(selected==l).lower(),\
                       "class":""} for l in list])
        for idx, item in enumerate(items):
            url = "http://panel/%s-%d" % (type, idx)
            elt = ET.SubElement(seq, "RDF:li")
            self._rdf_description(elt, item, url)

    def __build_filter(self, filter):
        pass

class DeejaydQueueRdf(_DeejaydSourceRdf):
    name = "queue"
    locale_strings = ("%s Songs", "%s Songs")
    get_list_func = "get_queue"

class DeejaydWebradioRdf(_DeejaydSourceRdf):
    name = "webradio"
    locale_strings = ("%s Webradios", "%s Webradios")
    get_list_func = "get_webradios"

class DeejaydVideoRdf(_DeejaydSourceRdf):
    name = "video"
    locale_strings = ("%s Videos", "%s Videos")
    get_list_func = "get_video"

class DeejaydVideoDirRdf(_DeejaydSourceRdf):
    name = "videodir"

    def update(self, new_id):
        current_id = self._get_current_id()
        new_id = int(new_id) % 10000
        if current_id != new_id:
            self._clean_rdfdir()
            self._build_rdf_file(new_id)
        return new_id

    def _build_rdf_file(self,new_id):
        # build xml
        self.root = ET.Element("RDF:RDF")
        self.root.attrib["xmlns:RDF"] =\
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        self.root.attrib["xmlns:FILE"] = "http://videodir/rdf#"

        seq = ET.SubElement(self.root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://videodir/all-content"
        self._build_dir_list(seq, "")

        self._save_rdf(self.root,new_id)

    def _build_dir_list(self, seq_elt, dir, id = "1"):
        dir_elt = ET.SubElement(seq_elt, "RDF:li")
        dir_url = "http://videodir/%s" % os.path.join("root", dir)
        title = dir == "" and _("Root Directory") or os.path.basename(dir)
        self._rdf_description(self.root, {"title": title}, dir_url)

        subdirs = self._deejayd.get_video_dir(dir).get_directories()
        if subdirs == []:
            dir_elt.attrib["RDF:resource"] = self._to_xml_string(dir_url)
        else:
            subdir_list =  ET.SubElement(dir_elt,"RDF:Seq")
            subdir_list.attrib["RDF:about"] = self._to_xml_string(dir_url)
            j = 1
            for d in subdirs:
                new_id = id + "/%d" % j
                self._build_dir_list(subdir_list, os.path.join(dir, d), new_id)
                j += 1

class DeejaydDvdRdf(_DeejaydSourceRdf):
    name = "dvd"

    def _build_rdf_file(self,new_id):
        dvd_content = self._get_media_list()

        # build xml
        root = ET.Element("RDF:RDF")
        root.attrib["xmlns:RDF"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        root.attrib["xmlns:FILE"] = "http://dvd/rdf#"

        # general dvd infos
        seq = ET.SubElement(root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://dvd/infos"
        i = 0
        infos = [{"name": "title",\
                  "value": _("DVD Title : %s") % dvd_content["title"]},\
                 {"name": "longest_track",
                  "value": _("Longest Track : %s")\
                                % dvd_content["longest_track"]}]
        for inf in infos:
            li = ET.SubElement(seq,"RDF:li")
            self._rdf_description(li,inf,"http://dvd/%d" % i)
            i += 1
        # dvd structure
        seq = ET.SubElement(root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://dvd/all-content"
        for track in dvd_content["track"]:
            track_li = ET.SubElement(seq,"RDF:li")
            track_url = "http://dvd/%s" % track["ix"]
            track_struct =  ET.SubElement(track_li,"RDF:Seq")
            track_struct.attrib["RDF:about"] = track_url
            self._rdf_description(root,\
                {"title": _("Title %s") % track["ix"],\
                    "id": track["ix"], "length": track["length"]},track_url)

            for chapter in track["chapter"]:
                chapter_url = track_url + "/%s" % chapter["ix"]
                li = ET.SubElement(track_struct,"RDF:li")
                li.attrib["RDF:resource"] = chapter_url
                self._rdf_description(root,\
                  {"title": _("Chapter %s") % chapter["ix"],\
                   "id": chapter["ix"],"length": chapter["length"]},chapter_url)

        self._save_rdf(root,new_id)

    def _get_media_list(self):
        return self._deejayd.get_dvd_content().get_dvd_contents()


modes = (
    "DeejaydPlaylistRdf",
    "DeejaydQueueRdf",
    "DeejaydPanelRdf",
    "DeejaydWebradioRdf",
    "DeejaydVideoRdf",
    )

