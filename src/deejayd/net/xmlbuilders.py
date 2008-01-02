# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET

class _DeejaydXML:

    def __init__(self, mother_xml_object = None):
        self.appended_xml_objects = None
        self.__is_mother = True
        self.__xmlbuilt = False

        if mother_xml_object == None:
            self.xmlroot = ET.Element('deejayd')
            self.appended_xml_objects = [self]
        else:
            self.__is_mother = False
            self.xmlroot = mother_xml_object.xmlroot
            mother_xml_object.append_another_xml_object(self)

        self.xmlcontent = None

    def append_another_xml_object(self, xml_object):
        self.appended_xml_objects.append(xml_object)

    def __really_build_xml(self):
        if self.__is_mother:
            if not self.__xmlbuilt:
                for xml_object in self.appended_xml_objects:
                    xml_object.build_xml()
                    self.xmlroot.append(xml_object.xmlcontent)
                del self.appended_xml_objects
                self.__xmlbuilt = True
        else:
            raise NotImplementedError('Do not build directly deejayd\
                                       XML that has a mother.')

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
        self.__really_build_xml()
        return '<?xml version="1.0" encoding="utf-8"?>' + \
            ET.tostring(self.xmlroot,'utf-8')

    def _indent(self,elem, level=0):
        indent_char = "\t"
        i = "\n" + level*indent_char
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_char
            for e in elem:
                self._indent(e, level+1)
                if not e.tail or not e.tail.strip():
                    e.tail = i + indent_char
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def to_pretty_xml(self):
        self.__really_build_xml()
        self._indent(self.xmlroot)
        return '<?xml version="1.0" encoding="utf-8"?>' + "\n" +\
            ET.tostring(self.xmlroot,'utf-8') + "\n"

    def build_xml(self):
        raise NotImplementedError


class DeejaydXMLCommand(_DeejaydXML):

    def __init__(self, name, mother_xml_object = None):
        _DeejaydXML.__init__(self, mother_xml_object)
        self.name = name
        self.args = {}

    def add_simple_arg(self, name, value):
        self.args[name] = value

    def add_multiple_arg(self, name, valuelist):
        self.add_simple_arg(name, valuelist)

    def build_xml(self):
        # Add command
        self.xmlcontent = ET.Element('command', name = self.name)

        # Add args
        for arg in self.args.keys():
            xmlarg = ET.SubElement(self.xmlcontent, 'arg', name = arg)

            arg_param = self.args[arg]
            if type(arg_param) is list:
                # We've got multiple args
                xmlarg.attrib['type'] = 'multiple'

                for arg_param_value in arg_param:
                    xmlval = ET.SubElement(xmlarg,'value')
                    xmlval.text = self._to_xml_string(arg_param_value)

            else:
                # We've got a simple arg
                xmlarg.attrib['type'] = 'simple'
                xmlarg.text = self._to_xml_string(arg_param)


class _DeejaydXMLAnswer(_DeejaydXML):

    def __init__(self, originating_cmd, mother_xml_object = None):
        _DeejaydXML.__init__(self, mother_xml_object)
        self.originating_cmd = originating_cmd

    def build_xml_parm(self, name, value):
        xmlparm = ET.Element('parm', name = name)
        xmlparm.attrib['value'] = self._to_xml_string(value)
        return xmlparm

    def build_xml_list_parm(self, name, value_list):
        xml_list_parm = ET.Element('listparm')
        if name: xml_list_parm.attrib['name'] = name
        for value in value_list:
            if type(value) == dict:
                xmlvalue = self.build_xml_dict_parm(None,value)
            else:
                xmlvalue = ET.Element('listvalue')
                xmlvalue.attrib['value'] = self._to_xml_string(value)
            xml_list_parm.append(xmlvalue)
        return xml_list_parm

    def build_xml_dict_parm(self, name, value_dict):
        xml_dict_parm = ET.Element('dictparm')
        if name: xml_dict_parm.attrib['name'] = name
        for key in value_dict.keys():
            xmlitem = ET.SubElement(xml_dict_parm, 'dictitem', name = key)
            xmlitem.attrib['value'] = self._to_xml_string(value_dict[key])
        return xml_dict_parm

    def build_xml_parm_list(self, data, parent_element):
        for data_key in data.keys():
            data_value = data[data_key]
            xml_parm = None
            if type(data_value) is list:
                xml_parm = self.build_xml_list_parm(data_key, data_value)
            elif type(data_value) is dict:
                xml_parm = self.build_xml_dict_parm(data_key, data_value)
            else:
                xml_parm = self.build_xml_parm(data_key, data_value)
            parent_element.append(xml_parm)


class DeejaydXMLError(_DeejaydXMLAnswer):
    """Error notification."""

    response_type = 'error'

    def set_error_text(self, txt):
        self.error_text = txt

    def build_xml(self):
        self.xmlcontent = ET.Element(self.response_type, \
                            name=self.originating_cmd)
        self.xmlcontent.text = str(self.error_text)


class DeejaydXMLAck(_DeejaydXMLAnswer):
    """Acknowledgement of a command."""

    response_type = 'Ack'

    def build_xml(self):
        self.xmlcontent = ET.Element('response',name = self.originating_cmd,\
            type = self.response_type)


class DeejaydXMLKeyValue(DeejaydXMLAck):
    """A list of key, value pairs."""

    response_type = 'KeyValue'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.contents = {}

    def add_pair(self, key, value):
        self.contents[key] = value

    def set_pairs(self, key_value):
        self.contents = key_value

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)

        for k, v in self.contents.items():
            self.xmlcontent.append(self.build_xml_parm(k, v))


class DeejaydXMLFileDirList(DeejaydXMLAck):
    """A list of files and directories."""

    response_type = 'FileAndDirList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)

        self.directory = None
        self.file_type = None

        self.contents = {'directory' : [],
                         'file'      : []}

    def set_directory(self, directory):
        self.directory = directory

    def set_filetype(self, file_type):
        self.file_type = file_type

    def add_directory(self, dirname):
        self.contents['directory'].append(dirname)

    def set_directories(self, directories):
        self.contents['directory'] = directories

    def add_file(self, file_info):
        self.contents['file'].append(file_info)

    def set_files(self, file_list):
        self.contents['file'] = file_list

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)

        if self.directory != None:
            self.xmlcontent.attrib['directory'] = \
                self._to_xml_string(self.directory)

        for dirname in self.contents['directory']:
            ET.SubElement(self.xmlcontent, 'directory', \
                name = self._to_xml_string(dirname))

        for item in self.contents['file']:
            xmlitem = ET.SubElement(self.xmlcontent,'file',type=self.file_type)
            self.build_xml_parm_list(item, xmlitem)


class DeejaydXMLMediaList(DeejaydXMLAck):
    """A list of media (song, webradio,playlist or video) with information for each media :
    * artist, album, title, id, etc. if it is a song
    * title, url, id, etc. if it is a webradio
    * title, id, length, subtitle, audio, etc. if it is a video"""

    response_type = 'MediaList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.media_items = []

    def set_mediatype(self,type):
        self.media_type = type

    def add_media(self, media):
        self.media_items.append(media)

    def set_medias(self, medias):
        self.media_items = medias

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        for item in self.media_items:
            xmlitem = ET.SubElement(self.xmlcontent,'media',\
                type=self.media_type)
            self.build_xml_parm_list(item, xmlitem)


class DeejaydXMLDvdInfo(DeejaydXMLAck):
    """Format dvd content."""

    response_type = 'DvdInfo'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.dvd_info = None

    def set_info(self,dvd_info):
        self.dvd_info = dvd_info

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        xmldvd = ET.SubElement(self.xmlcontent,'dvd')

        xmldvd.attrib['title'] = self._to_xml_string(self.dvd_info['title'])
        xmldvd.attrib['longest_track'] = \
            self._to_xml_string(self.dvd_info['longest_track'])
        # dvd's title
        for track in self.dvd_info["track"]:
            xmltrack = ET.SubElement(xmldvd,'track')
            for info in ('ix','length'):
                xmltrack.attrib[info] = self._to_xml_string(track[info])

            # avalaible audio channels
            for audio in track["audio"]:
                xmlaudio = ET.SubElement(xmltrack, 'audio')
                for info in ('ix','lang'):
                    xmlaudio.attrib[info] = self._to_xml_string(audio[info])

            # avalaible subtitle channels
            for sub in track["subp"]:
                xmlsub = ET.SubElement(xmltrack, 'subtitle')
                for info in ('ix','lang'):
                    xmlsub.attrib[info] = self._to_xml_string(sub[info])

            # chapter list
            for chapter in track["chapter"]:
                xmlchapter = ET.SubElement(xmltrack, 'chapter')
                for info in ('ix','length'):
                    xmlchapter.attrib[info] = self._to_xml_string(chapter[info])


class DeejaydXMLAnswerFactory:

    response_types = [ DeejaydXMLError,
                      DeejaydXMLAck,
                      DeejaydXMLKeyValue,
                      DeejaydXMLFileDirList,
                      DeejaydXMLMediaList,
                      DeejaydXMLDvdInfo    ]

    def __init__(self):
        self.mother_answer = None

    def set_mother(self, mother_answer):
        self.mother_answer = mother_answer

    def get_deejayd_xml_answer(self, type, originating_cmd):
        iat = iter(self.response_types)
        try:
            while True:
                type_class = iat.next()
                if type_class.response_type == type:
                    ans = type_class(originating_cmd, self.mother_answer)
                    return ans
        except StopIteration:
            raise NotImplementedError


# vim: ts=4 sw=4 expandtab
