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

from deejayd.xmlobject import DeejaydXMLObject, ET


class _DeejaydXML(DeejaydXMLObject):

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

    def to_xml(self):
        self.__really_build_xml()
        return super(_DeejaydXML, self).to_xml()

    def to_pretty_xml(self):
        self.__really_build_xml()
        return super(_DeejaydXML, self).to_pretty_xml()

    def build_xml(self):
        raise NotImplementedError


class DeejaydXMLCommand(_DeejaydXML):

    def __init__(self, name, mother_xml_object = None):
        _DeejaydXML.__init__(self, mother_xml_object)
        self.name = name
        self.args = {}

    def add_simple_arg(self, name, value):
        self.args[name] = ('simple', value)

    def add_multiple_arg(self, name, valuelist):
        self.args[name] = ('multiple', valuelist)

    def add_filter_arg(self, name, filter):
        self.args[name] = ('filter', filter)

    def add_sort_arg(self, name, sort):
        self.args[name] = ('sort', sort)

    def build_xml(self):
        # Add command
        self.xmlcontent = ET.Element('command', name = self.name)

        # Add args
        for arg in self.args.keys():
            xmlarg = ET.SubElement(self.xmlcontent, 'arg', name = arg)

            arg_type, arg_param = self.args[arg]

            xmlarg.attrib['type'] = arg_type
            if arg_type == 'multiple':
                for arg_param_value in arg_param:
                    xmlval = ET.SubElement(xmlarg,'value')
                    xmlval.text = self._to_xml_string(arg_param_value)
            elif arg_type == 'filter':
                Get_xml_filter(arg_param).element(xmlarg)
            elif arg_type == 'sort':
                XMLSort(arg_param).element(xmlarg)
            elif arg_type == 'simple':
                xmlarg.text = self._to_xml_string(arg_param)


class DeejaydXMLSignal(_DeejaydXML):

    def __init__(self, signal=None, mother_xml_object=None):
        _DeejaydXML.__init__(self, mother_xml_object)
        self.name = signal is not None and signal.get_name() or ""
        self.attrs = signal is not None and signal.get_attrs() or {}

    def set_name(self, name):
        self.name = name

    def build_xml(self):
        self.xmlcontent = ET.Element('signal', name=self.name)
        for k in self.attrs.keys():
            attr = ET.SubElement(self.xmlcontent, "signal_attr", key=k)
            attr.text = self._to_xml_string(self.attrs[k])


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
        self.xmlcontent.text = self._to_xml_string(self.error_text)


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


class DeejaydXMLList(DeejaydXMLAck):
    """A list of string values."""

    response_type = 'List'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.contents = []

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)

        for v in self.contents:
            self.xmlcontent.append(self.build_xml_parm('item', v))


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
    * title, id, length, subtitle, audio, etc. if it is a video
For magic playlist and panel, MediaList object return filters and sorts used
to build the medialist"""

    response_type = 'MediaList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.media_items = []
        self.total_length = None
        self.filter = None
        self.sort = None

    def set_total_length(self, length):
        self.total_length = length

    def set_mediatype(self,type):
        self.media_type = type

    def add_media(self, media):
        self.media_items.append(media)

    def set_medias(self, medias):
        self.media_items = medias

    def set_filter(self, filter):
        self.filter = filter

    def set_sort(self, sort):
        self.sort = sort

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        if self.total_length:
            self.xmlcontent.attrib["total_length"] = \
                self._to_xml_string(self.total_length)
        for item in self.media_items:
            xmlitem = ET.SubElement(self.xmlcontent,'media',\
                type=self.media_type)
            self.build_xml_parm_list(item, xmlitem)
        if self.filter:
            xmlfilter_element = ET.SubElement(self.xmlcontent,'filter')
            xmlfilter = Get_xml_filter(self.filter)
            xmlfilter.element(xmlfilter_element)
        if self.sort:
            sort_element = ET.SubElement(self.xmlcontent,'sort')
            XMLSort(self.sort).element(sort_element)


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


class DeejaydXMLAnswerFactory(object):

    response_types = (
                       DeejaydXMLError,
                       DeejaydXMLAck,
                       DeejaydXMLKeyValue,
                       DeejaydXMLList,
                       DeejaydXMLFileDirList,
                       DeejaydXMLMediaList,
                       DeejaydXMLDvdInfo,
                     )

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


class XMLFilter(DeejaydXMLObject):

    def __init__(self, filter):
        self.filter = filter

    def _get_element(self, parent_element):
        element_name = self.filter.get_identifier()
        return ET.SubElement(parent_element, element_name)

    def element(self, parent_element):
        return self._get_element(parent_element)


class XMLBasicFilter(XMLFilter):

    def element(self, parent_element):
        e = super(XMLBasicFilter, self).element(parent_element)
        e.attrib['tag'] = self.filter.tag
        e.text = self._to_xml_string(self.filter.pattern)
        return e


class XMLComplexFilter(XMLFilter):

    def element(self, parent_element):
        e = super(XMLComplexFilter, self).element(parent_element)
        for filter in self.filter.filterlist:
            Get_xml_filter(filter).element(e)


def Get_xml_filter(filter):
    if filter.type == 'basic':
        xml_filter_class = XMLBasicFilter
    elif filter.type == 'complex':
        xml_filter_class = XMLComplexFilter
    return xml_filter_class(filter)


class XMLSort(DeejaydXMLObject):

    def __init__(self, sort):
        self.sort = sort

    def element(self, parent_element):
        for tag, direction in self.sort:
            sort_elt = ET.SubElement(parent_element, "sortitem")
            sort_elt.attrib["tag"] = self._to_xml_string(tag)
            sort_elt.attrib["direction"] = self._to_xml_string(direction)
        return parent_element

# vim: ts=4 sw=4 expandtab
