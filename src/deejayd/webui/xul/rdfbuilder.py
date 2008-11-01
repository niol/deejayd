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
from deejayd.webui.utils import *
from deejayd.mediafilters import *


class RdfBuilder(DeejaydXMLObject):

    def __init__(self, source_name):
        self.rdf_nsp = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
        self.file_nsp = "{http://%s/rdf#}" % source_name
        self.xmlroot = ET.Element(self.rdf_nsp+"RDF")

    def build_seq(self, url, parent = None):
        if parent is None: parent = self.xmlroot
        seq = ET.SubElement(parent, self.rdf_nsp+"Seq")
        seq.attrib[self.rdf_nsp+"about"] = self._to_xml_string(url)

        return seq

    def build_li(self, parent, url = None):
        li = ET.SubElement(parent, self.rdf_nsp+"li")
        if url: li.attrib[self.rdf_nsp+"about"] = self._to_xml_string(url)

        return li

    def build_item_desc(self, parms, parent = None, url = None):
        if parent is None: parent = self.xmlroot
        desc = ET.SubElement(parent, self.rdf_nsp+"Description")
        if url: desc.attrib[self.rdf_nsp+"about"] = self._to_xml_string(url)

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
            node = ET.SubElement(desc, self.file_nsp+"%s"\
                % self._to_xml_string(p))
            node.text = value

        return desc

    def set_resource(self, elt, url):
        elt.attrib[self.rdf_nsp+"resource"] = self._to_xml_string(url)

    def to_xml(self):
        return '<?xml version="1.0" encoding="utf-8"?>' + "\n" + \
                ET.tostring(self.xmlroot)


class _DeejaydSourceRdf(DeejaydXMLObject):
    name = "unknown"
    locale_strings = None

    def __init__(self, deejayd, rdf_dir, compilation = False):
        self._deejayd = deejayd
        self._rdf_dir = rdf_dir
        self._compilation = compilation

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

    def _build_rdf_file(self, new_id):
        # get media list
        obj = getattr(self._deejayd, self.__class__.get_list_func)()
        media_list = obj.get().get_medias()

        # build xml
        rdf_builder = RdfBuilder(self.__class__.name)
        seq = rdf_builder.build_seq("http://%s/all-content" % self.name)
        for media in media_list:
            li = rdf_builder.build_li(seq)
            rdf_builder.build_item_desc(media, li,\
                "http://%s/%s" % (self.name, media["id"]))

        self._save_rdf(rdf_builder, new_id)

    def _save_rdf(self, rdf_builder, new_id):
        filename = "%s-%d.rdf" % (self.__class__.name, new_id);
        file_path = os.path.join(self._rdf_dir,filename)

        fd = open(file_path, "w")
        fd.write(rdf_builder.to_xml())
        fd.close()
        os.chmod(file_path,0644)

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

        mode = panel.get_active_list()
        if mode["type"] == "panel":
            filters = panel.get().get_filter()
            try: filter_list = filters.filterlist
            except (TypeError, AttributeError):
                filter_list = []

            panel_filter = And()
            elt.attrib["filtertext_text"] = ""
            elt.attrib["filtertext_type"] = "all"
            for ft in filter_list:
                if ft.type == "basic" and ft.get_name() == "contains":
                    elt.attrib["filtertext_text"] = ft.pattern
                    elt.attrib["filtertext_type"] = ft.tag
                    panel_filter.combine(ft)
                    break
                elif ft.type == "complex" and ft.get_name() == "or":
                    elt.attrib["filtertext_text"] = ft.filterlist[0].pattern
                    elt.attrib["filtertext_type"] = "all"
                    panel_filter.combine(ft)
                    break

    def _build_rdf_file(self, new_id):
        panel = self._deejayd.get_panel()
        mode = panel.get_active_list()
        media_list = panel.get().get_medias()

        rdf_builder = RdfBuilder(self.__class__.name)
        # build panel if needed
        if mode["type"] == "panel":
            filters = panel.get().get_filter()
            try: filter_list = filters.filterlist
            except (TypeError, AttributeError):
                filter_list = []

            panel_filter = And()
            for ft in filter_list:
                if ft.type == "basic" and ft.get_name() == "contains":
                    panel_filter.combine(ft)
                    break
                elif ft.type == "complex" and ft.get_name() == "or":
                    panel_filter.combine(ft)
                    break

            for t in ("genre", "artist", "album"):
                selected = None

                if t == "artist" and self._compilation:
                    list = []
                    # find compilation
                    for ft in filter_list:
                        if ft.get_name() == "equals" \
                                and ft.tag == "compilation"\
                                and ft.pattern == "1":
                            selected = "__compilation__"
                            break
                        elif ft.get_name() == "equals" and ft.tag == t:
                            selected = ft.pattern
                            break
                    tag_filter = And()
                    tag_filter.combine(panel_filter)
                    tag_filter.combine(Equals("compilation", "0"))
                    list = self._deejayd.mediadb_list(t, tag_filter)

                    # add filter for next panel
                    if selected is not None:
                        if selected == "__compilation__":
                            panel_filter.combine(Equals("compilation", "1"))
                        else:
                            panel_filter.combine(Equals(t, selected))

                    items = [{"name": _("All"), "value":"__all__", \
                              "class":"list-all", \
                              "sel":str(selected==None).lower()}]
                    # set various artist tag only if needed
                    tag_filter = And()
                    tag_filter.combine(panel_filter)
                    tag_filter.combine(Equals("compilation", "1"))
                    if len(self._deejayd.mediadb_list("album", tag_filter)):
                        items.append({"name": _("Various Artists"),\
                              "value":"__compilation__", "class":"", \
                              "sel":str(selected=="__compilation__").lower()})
                    items.extend([{"name": l,"value":l,\
                            "sel":str(selected==l).lower(), "class":""}\
                            for l in list if l != ""])
                    if "" in list:
                        items.append({"name": _("Unknown"), "value":"",\
                            "class":"list-unknown",\
                            "sel":str(selected=="").lower()})

                else:
                    for ft in filter_list:
                        if ft.get_name() == "equals" and ft.tag == t:
                            selected = ft.pattern
                            break
                    list = self._deejayd.mediadb_list(t, panel_filter)
                    # add filter for next panel
                    if selected is not None:
                        panel_filter.combine(Equals(t, selected))

                    items = [{"name": _("All"), "value":"__all__", \
                            "class":"list-all", \
                            "sel":str(selected==None).lower()}]
                    items.extend([{"name": l,"value":l,\
                            "sel":str(selected==l).lower(), "class":""}\
                            for l in list if l != ""])
                    if "" in list:
                        items.append({"name": _("Unknown"), "value":"",\
                            "class":"list-unknown",\
                            "sel":str(selected=="").lower()})

                self.__build_tag_list(rdf_builder, t, items, selected)

        # build medialist
        seq = rdf_builder.build_seq("http://%s/all-content" % self.name)
        for media in media_list:
            li = rdf_builder.build_li(seq)
            rdf_builder.build_item_desc(media, li,\
                "http://%s/%s" % (self.name, media["id"]))

        self._save_rdf(rdf_builder, new_id)

    def __build_tag_list(self, rdf_builder, type, items, selected = None):
        seq = rdf_builder.build_seq("http://panel/all-%s" % type)

        for idx, item in enumerate(items):
            li = rdf_builder.build_li(seq)
            rdf_builder.build_item_desc(item, li,\
                "http://panel/%s-%d" % (type, idx))

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
        rdf_builder = RdfBuilder(self.__class__.name)

        seq = rdf_builder.build_seq("http://videodir/all-content")
        self._build_dir_list(rdf_builder, seq, "")
        self._save_rdf(rdf_builder, new_id)

    def _build_dir_list(self, rdf_builder, seq_elt, dir, id = "1"):
        dir_elt = rdf_builder.build_li(seq_elt)
        dir_url = "http://videodir/%s" % os.path.join("root", dir)
        title = dir == "" and _("Root Directory") or os.path.basename(dir)
        rdf_builder.build_item_desc({"title": title}, url = dir_url)

        subdirs = self._deejayd.get_video_dir(dir).get_directories()
        if subdirs == []:
            rdf_builder.set_resource(dir_elt, dir_url)
        else:
            subdir_list =  rdf_builder.build_seq(dir_url, parent = dir_elt)
            for idx, d in enumerate(subdirs):
                new_id = id + "/%d" % (idx+1,)
                self._build_dir_list(rdf_builder, subdir_list,\
                    os.path.join(dir, d), new_id)

class DeejaydDvdRdf(_DeejaydSourceRdf):
    name = "dvd"
    locale_strings = ("%s Track", "%s Tracks")
    get_list_func = "get_dvd_content"

    def _build_rdf_file(self,new_id):
        dvd_content = self._get_media_list()
        rdf_builder = RdfBuilder(self.__class__.name)

        # general dvd infos
        seq = rdf_builder.build_seq("http://dvd/infos")

        i = 0
        infos = [{"name": "title",\
                  "value": _("DVD Title : %s") % dvd_content["title"]},\
                 {"name": "longest_track",
                  "value": _("Longest Track : %s")\
                                % dvd_content["longest_track"]}]
        for inf in infos:
            li = rdf_builder.build_li(seq)
            rdf_builder.build_item_desc(inf,li,"http://dvd/%d" % i)
            i += 1

        # dvd structure
        seq = rdf_builder.build_seq("http://dvd/all-content")
        for track in dvd_content["track"]:
            track_li = rdf_builder.build_li(seq)

            track_url = "http://dvd/%s" % track["ix"]
            track_struct = rdf_builder.build_seq(track_url,track_li)

            track_data = {"title": _("Title %s") % track["ix"],\
                             "id": track["ix"],\
                         "length": track["length"]}
            rdf_builder.build_item_desc(track_data,None,track_url)

            for chapter in track["chapter"]:
                chapter_url = track_url + "/%s" % chapter["ix"]
                chapter_li = rdf_builder.build_li(track_struct)
                rdf_builder.set_resource(chapter_li,chapter_url)

                chapter_data = {"title": _("Chapter %s") % chapter["ix"],\
                                   "id": chapter["ix"],\
                               "length": chapter["length"]}
                rdf_builder.build_item_desc(chapter_data,None,chapter_url)

        self._save_rdf(rdf_builder,new_id)

    def _get_media_list(self):
        return self._deejayd.get_dvd_content().get_dvd_contents()


modes = (
    "DeejaydPlaylistRdf",
    "DeejaydQueueRdf",
    "DeejaydPanelRdf",
    "DeejaydWebradioRdf",
    "DeejaydVideoRdf",
    "DeejaydDvdRdf",
    )
