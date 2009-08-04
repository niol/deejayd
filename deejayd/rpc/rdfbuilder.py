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
from deejayd.utils import *


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
                    value = self._to_xml_string(0)
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
    locale_strings = ("%d Song", "%d Songs")

    def __init__(self, deejayd, rdf_dir):
        self._deejayd = deejayd
        self._rdf_dir = rdf_dir

    def update(self):
        current_id = self._get_current_id()
        try:
            status = self._deejayd.get_status(objanswer=False)
            new_id = status[self.__class__.name]
        except KeyError:
            return {"desc": ""}# this mode is not active
        new_id = int(new_id) % 10000
        # get media list
        obj = getattr(self._deejayd, self.__class__.get_list_func)()
        res = obj.get(objanswer=False)
        if isinstance(res, tuple):
            medias, filter, sort = res
        else:
            medias, filter, sort = res, None, None

        if current_id != new_id:
            self._build_rdf_file(medias, new_id)
        # build description
        single, plural = self.__class__.locale_strings
        len = status[self.__class__.name + "length"]
        desc = ngettext(single,plural,int(len))%int(len)
        try: time = int(status[self.__class__.name + "timelength"])
        except KeyError:
            pass
        else:
            if time > 0: desc += " (%s)" % format_time_long(time)
        return {"desc": desc, "sort": sort}

    def _build_rdf_file(self, media_list, new_id):
        # build xml
        rdf_builder = RdfBuilder(self.__class__.name)
        seq = rdf_builder.build_seq("http://%s/all-content" % self.name)
        for media in media_list:
            li = rdf_builder.build_li(seq)
            rdf_builder.build_item_desc(media, li,\
                "http://%s/%s" % (self.name, media["id"]))

        self._save_rdf(rdf_builder, new_id)

    def _save_rdf(self, rdf_builder, new_id, name = None):
        name = name or self.__class__.name
        # first clean rdf dir
        for file in os.listdir(self._rdf_dir):
            path = os.path.join(self._rdf_dir,file)
            if os.path.isfile(path) and file.startswith(name+"-"):
                os.unlink(path)

        filename = "%s-%d.rdf" % (name, new_id);
        file_path = os.path.join(self._rdf_dir,filename)

        fd = open(file_path, "w")
        fd.write(rdf_builder.to_xml())
        fd.close()
        os.chmod(file_path,0644)

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
    get_list_func = "get_playlist"

class DeejaydPanelRdf(_DeejaydSourceRdf):
    name = "panel"
    get_list_func = "get_panel"

class DeejaydQueueRdf(_DeejaydSourceRdf):
    name = "queue"
    get_list_func = "get_queue"

class DeejaydWebradioRdf(_DeejaydSourceRdf):
    name = "webradio"
    locale_strings = ("%d Webradio", "%d Webradios")
    get_list_func = "get_webradios"

class DeejaydVideoRdf(_DeejaydSourceRdf):
    name = "video"
    locale_strings = ("%d Video", "%d Videos")
    get_list_func = "get_video"

class DeejaydVideoDirRdf(_DeejaydSourceRdf):
    name = "videodir"

    def update(self):
        try:
            stats = self._deejayd.get_stats()
            new_id = stats["video_library_update"]
        except KeyError:
            return {"id": None}# this mode is not active
        current_id = self._get_current_id()
        new_id = int(new_id) % 10000
        if current_id != new_id:
            self._build_rdf_file(new_id)
        return {"id": new_id}

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
    locale_strings = ("%d Track", "%d Tracks")

    def update(self):
        current_id = self._get_current_id()
        try:
            status = self._deejayd.get_status(objanswer=False)
            new_id = status[self.__class__.name]
        except KeyError:
            return {"desc": ""}# this mode is not active
        dvd_content = self._deejayd.get_dvd_content(objanswer=False)
        new_id = int(new_id) % 10000
        if current_id != new_id:
            self._build_rdf_file(dvd_content, new_id)
        # build description
        single, plural = self.__class__.locale_strings
        len = status[self.__class__.name + "length"]
        desc = ngettext(single,plural,int(len))%int(len)
        return {"desc": desc, "title": dvd_content["title"],\
                "longest_track": dvd_content["longest_track"]}

    def _build_rdf_file(self, dvd_content, new_id):
        rdf_builder = RdfBuilder(self.__class__.name)

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


ngettext("%d Song", "%d Songs", 0)
ngettext("%d Video", "%d Videos", 0)
ngettext("%d Webradio", "%d Webradios", 0)
ngettext("%d Track", "%d Tracks", 0)

modes = {
        "playlist": DeejaydPlaylistRdf,
        "queue": DeejaydQueueRdf,
        "panel": DeejaydPanelRdf,
        "webradio": DeejaydWebradioRdf,
        "video": DeejaydVideoRdf,
        "dvd": DeejaydDvdRdf,
        "videodir": DeejaydVideoDirRdf,
    }

# vim: ts=4 sw=4 expandtab
