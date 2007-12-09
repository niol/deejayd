import os,re
from string import Template
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET


class _DeejaydXML:

    def _to_xml_string(self, s):
        if isinstance(s, int) or isinstance(s, float) or isinstance(s, long):
            return "%d" % (s,)
        elif isinstance(s, str):
            return "%s" % (s.decode('utf-8'))
        elif isinstance(s, unicode):
            rs = s.encode("utf-8")
            return "%s" % (rs.decode('utf-8'))
        else:
            raise TypeError

    def to_xml(self):
        return '<?xml version="1.0" encoding="utf-8"?>' + \
            ET.tostring(self.xmlroot,'utf-8')

############################################################################
#### build web interface from templates
############################################################################
def build_web_interface(language):
    default_path = os.path.abspath(os.path.dirname(__file__))
    # get templates
    template_dir = os.path.join(default_path,"templates")

    templates = {}
    #get source template
    for temp in ("dvd","playlist","webradio","video","queue"):
        fd = open(os.path.join(template_dir,temp+".xml"))
        templates[temp] = fd.read()
        fd.close()
    # open main template
    fd = open(os.path.join(template_dir,"main.xml"))
    tpl = Template(fd.read())
    fd.close()
    return tpl.substitute(templates)

############################################################################
#### rdf builder
############################################################################
class _DeejaydSourceRdf(_DeejaydXML):
    name = "unknown"

    def __init__(self, deejayd, rdf_dir):
        self._deejayd = deejayd
        self._rdf_dir = rdf_dir

    def update(self,new_id):
        current_id = self._get_current_id()
        if current_id < new_id:
            self._clean_rdfdir()
            self._build_rdf_file(new_id)

    def _build_rdf_file(self,new_id):
        medias = self._get_media_list()

        # build xml
        root = ET.Element("RDF:RDF")
        root.attrib["xmlns:RDF"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        root.attrib["xmlns:FILE"] = "http://%s/rdf#" % self.name

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
            desc.attrib["RDF:about"] = url
        for p in parms.keys():
            node = ET.SubElement(desc,"FILE:%s" % self._to_xml_string(p))
            node.text = self._to_xml_string(parms[p])

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
        raise NotImplementedError

    def _clean_rdfdir(self):
        for file in os.listdir(self._rdf_dir):
            path = os.path.join(self._rdf_dir,file)
            if os.path.isfile(path) and file.startswith(self.name):
                os.unlink(path)

    def _get_current_id(self):
        ids = []
        for file in os.listdir(self._rdf_dir):
            if re.compile("/^"+self.name+"-[0-9]+\.rdf$/").search(file):
                t = file.split("-")[1] # id.rdf
                t = t.split(".")
                try : ids.append(int(t[0]))
                except ValueError: pass

        if ids == []: return 0
        else: return ids.max()

class DeejaydPlaylistRdf(_DeejaydSourceRdf):
    name = "playlist"

    def _get_media_list(self):
        pl_obj = self._deejayd.get_playlist()
        return pl_obj.get().get_medias()

class DeejaydQueueRdf(_DeejaydSourceRdf):
    name = "queue"

    def _get_media_list(self):
        q_obj = self._deejayd.get_queue()
        return q_obj.get().get_medias()

class DeejaydWebradioRdf(_DeejaydSourceRdf):
    name = "webradio"

    def _get_media_list(self):
        wb_obj = self._deejayd.get_webradios()
        return wb_obj.get().get_medias()

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
                  "value": "DVD Title : %s" % dvd_content["title"]},\
                 {"name": "longest_track",
                  "value": "Longest Track : %s" % dvd_content["longest_track"]}]
        for inf in infos:
            li = ET.SubElement(seq,"RDF:li")
            self._rdf_description(li,inf,"http://dvd/%d" % i)
            i += 1
        # dvd structure
        seq = ET.SubElement(root,"RDF:Seq")
        seq.attrib["RDF:about"] = "http://dvd/all-content"
        for track in dvd_content["tracks"]:
            track_li = ET.SubElement(seq,"RDF:li")
            track_url = "http://dvd/%s" % track["id"]
            track_struct =  ET.SubElement(track_li,"RDF:Seq")
            track_struct.attrib["RDF:about"] = track_url
            self._rdf_description(root,\
                {"title": "Title %s" % track["id"],\
                    "id": track["id"], "length": track["length"]},track_url)

            for chapter in track["chapters"]:
                chapter_url = track_url + "/%s" % chapter["id"]
                li = ET.SubElement(track_struct,"RDF:li")
                li.attrib["RDF:resource"] = chapter_url
                self._rdf_description(root,\
                  {"title": "Chapter %s" % chapter["id"],\
                   "id": chapter["id"],"length": chapter["length"]},chapter_url)

        self._save_rdf(root,new_id)

    def _get_media_list(self):
        return self._deejayd.get_dvd_content().get_dvd_contents()


############################################################################
#########  Main Answer
############################################################################
class DeejaydWebAnswer(_DeejaydXML):

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
            s_elt = ET.SubElement(elt, "strings", name=s, value=strings[s])

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

    def set_playlist(self,status,deejayd):
        pls = ET.SubElement(self.xmlroot,"playlist",\
            id = self._to_xml_string(status["playlist"]),\
            description = "%s Songs" % str(status["playlistlength"]),\
            length = self._to_xml_string(status["playlistlength"]));
        DeejaydPlaylistRdf(deejayd,self.__rdf_dir).update(status["playlist"])

    def set_queue(self,status,deejayd):
        queue = ET.SubElement(self.xmlroot,"queue",\
            id = self._to_xml_string(status["queue"]),\
            description = "%s Songs" % str(status["queuelength"]),\
            length = self._to_xml_string(status["queuelength"]));
        DeejaydQueueRdf(deejayd,self.__rdf_dir).update(status["queue"])

    def set_webradio(self,status,deejayd):
        wb = ET.SubElement(self.xmlroot,"webradio",\
            id = self._to_xml_string(status["webradio"]),\
            description = "%s Webradios" % str(status["webradiolength"]),\
            length = self._to_xml_string(status["webradiolength"]));
        DeejaydWebradioRdf(deejayd,self.__rdf_dir).update(status["webradio"])

    def set_dvd(self,status,deejayd):
        dvd = ET.SubElement(self.xmlroot,"dvd",\
            id = self._to_xml_string(status["dvd"]))
        DeejaydDvdRdf(deejayd,self.__rdf_dir).update(status["dvd"])

    def set_video(self,status):
        video = ET.SubElement(self.xmlroot,"video", id = status["video_dir"])

    def __build_file_list(self, parent, list):
        for dir in list.get_directories():
            it = ET.SubElement(parent,"item", type = "directory")
            it.text = dir

        for file in list.get_files():
            it = ET.SubElement(parent,"item")
            it.text = file["filename"]
            for key in [k for k in file.keys() if k not in ("filename","dir")]:
                it.attrib[key] = self._to_xml_string(file[key])

    def set_audiofile_list(self, files_list, dir = ""):
        list_elm = ET.SubElement(self.xmlroot, "file-list", directory = dir)
        self.__build_file_list(list_elm,files_list)

    def set_videofile_list(self, files_list, dir = ""):
        list_elm = ET.SubElement(self.xmlroot, "video-list", directory = dir)
        self.__build_file_list(list_elm,files_list)

    def set_playlist_list(self, playlist_list):
        list_elm = ET.SubElement(self.xmlroot, "playlist-list")
        for pls in playlist_list:
            it = ET.SubElement(list_elm,"item", type = "playlist")
            it.text = pls["name"]

    def set_player(self, status, cur_media):
        # Update player informations
        player  = ET.SubElement(self.xmlroot,"player")
        for info in ("volume","fullscreen","random","repeat","time","state"):
            try: val = self._to_xml_string(status[info])
            except KeyError: pass
            else:
                node = ET.SubElement(player,info)
                node.text = val

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

    def set_msg(self,msg,type = "confirmation"):
        msg_node = ET.SubElement(self.xmlroot,"message",type = type)
        msg_node.text = msg

    def set_error(self, error):
        self.set_msg(error,"error")


# vim: ts=4 sw=4 expandtab