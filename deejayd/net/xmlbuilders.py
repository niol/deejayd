from xml.dom import minidom


class _DeejaydXML:

    def __init__(self, mother_xml_object = None):
        self.appended_xml_objects = None
        self.__is_mother = True
        self.__xmlbuilt = False

        if mother_xml_object == None:
            self.xmldoc = minidom.Document()
            self.xmlroot = self.xmldoc.createElement('deejayd')
            self.xmldoc.appendChild(self.xmlroot)
            self.appended_xml_objects = [self]
        else:
            self.__is_mother = False
            self.xmldoc = mother_xml_object.xmldoc
            self.xmlroot = self.xmldoc.getElementsByTagName('deejayd').pop()
            mother_xml_object.append_another_xml_object(self)

        self.xmlcontent = None

    def append_another_xml_object(self, xml_object):
        self.appended_xml_objects.append(xml_object)

    def __really_build_xml(self):
        if self.__is_mother:
            if not self.__xmlbuilt:
                for xml_object in self.appended_xml_objects:
                    xml_object.build_xml()
                    self.xmlroot.appendChild(xml_object.xmlcontent)
                self.__xmlbuilt = True
        else:
            raise NotImplementedError('Do not build directly deejayd\
                                       XML that has a mother.')

    def to_xml(self):
        self.__really_build_xml()
        return self.xmldoc.toxml('utf-8')

    def to_pretty_xml(self):
        self.__really_build_xml()
        return self.xmldoc.toprettyxml(encoding = 'utf-8')

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
        self.xmlcontent = self.xmldoc.createElement('command')
        self.xmlcontent.setAttribute('name', self.name)

        # Add args
        for arg in self.args.keys():
            xmlarg = self.xmldoc.createElement('arg')
            xmlarg.setAttribute('name', arg)
            self.xmlcontent.appendChild(xmlarg)

            arg_param = self.args[arg]

            if type(arg_param) is list:
                # We've got multiple args
                xmlarg.setAttribute('type', 'multiple')

                for arg_param_value in arg_param:
                    xmlval = self.xmldoc.createElement('value')
                    xmlval.appendChild(self.xmldoc.createTextNode(
                                str(arg_param_value) ))
                    xmlarg.appendChild(xmlval)

            else:
                # We've got a simple arg
                xmlarg.setAttribute('type', 'simple')
                xmlarg.appendChild(self.xmldoc.createTextNode(str(arg_param)))


class _DeejaydXMLAnswer(_DeejaydXML):

    def __init__(self, originating_cmd, mother_xml_object = None):
        _DeejaydXML.__init__(self, mother_xml_object)
        self.originating_cmd = originating_cmd

    def __to_xml_string(self, s):
        if isinstance(s, int) or isinstance(s, float) or isinstance(s, long):
            return "%d" % (s,)
        elif isinstance(s, str) or isinstance(s, unicode):
            return "%s" % (s.decode('utf-8'))

    def build_xml_parm(self, name, value):
        xmlparm = self.xmldoc.createElement('parm')
        xmlparm.setAttribute('name', name)
        xmlparm.setAttribute('value', self.__to_xml_string(value))
        return xmlparm

    def build_xml_list_parm(self, name, value_list):
        xml_list_parm = self.xmldoc.createElement('listparm')
        if name: xml_list_parm.setAttribute('name', name)
        for value in value_list:
            if type(value) == dict:
                xmlvalue = self.build_xml_dict_parm(None,value)
            else:
                xmlvalue = self.xmldoc.createElement('listvalue')
                xmlvalue.setAttribute('value',self.__to_xml_string(value))
            xml_list_parm.appendChild(xmlvalue)
        return xml_list_parm

    def build_xml_dict_parm(self, name, value_dict):
        xml_dict_parm = self.xmldoc.createElement('dictparm')
        if name: xml_dict_parm.setAttribute('name', name)
        for key in value_dict.keys():
            xmlitem = self.xmldoc.createElement('dictitem')
            value = self.__to_xml_string(value_dict[key])
            xmlitem.setAttribute('name', key)
            xmlitem.setAttribute('value', value)
            xml_dict_parm.appendChild(xmlitem)
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
            parent_element.appendChild(xml_parm)


class DeejaydXMLError(_DeejaydXMLAnswer):
    """Error notification."""

    response_type = 'error'

    def set_error_text(self, txt):
        self.error_text = txt

    def build_xml(self):
        self.xmlcontent = self.xmldoc.createElement(self.response_type)
        self.xmlcontent.setAttribute('name', self.originating_cmd)
        xml_error_text = self.xmldoc.createTextNode(str(self.error_text))
        self.xmlcontent.appendChild(xml_error_text)


class DeejaydXMLAck(_DeejaydXMLAnswer):
    """Acknowledgement of a command."""

    response_type = 'Ack'

    def build_xml(self):
        self.xmlcontent = self.xmldoc.createElement('response')
        self.xmlcontent.setAttribute('name', self.originating_cmd)
        self.xmlcontent.setAttribute('type', self.response_type)


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
            self.xmlcontent.appendChild(self.build_xml_parm(k, v))


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
            self.xmlcontent.setAttribute('directory', self.directory)

        for dirname in self.contents['directory']:
            xmldir = self.xmldoc.createElement('directory')
            xmldir.setAttribute('name', dirname)
            self.xmlcontent.appendChild(xmldir)

        for item in self.contents['file']:
            xmlitem = self.xmldoc.createElement('file')
            xmlitem.setAttribute('type',self.file_type)
            self.build_xml_parm_list(item, xmlitem)
            self.xmlcontent.appendChild(xmlitem)


class DeejaydXMLMediaList(DeejaydXMLAck):
    """A list of media (song, webradio,playlist or video) with information for each media : 
    * artist, album, title, id, etc. if it is a song
    * title, url, id, etc. if it is a webradio
    * artist, album, title, id, etc. if it is a video"""

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
            xmlitem = self.xmldoc.createElement('media')
            xmlitem.setAttribute("type",self.media_type)
            self.build_xml_parm_list(item, xmlitem)
            self.xmlcontent.appendChild(xmlitem)


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
        xmldvd = self.xmldoc.createElement('dvd')
        if not self.dvd_info:
            xmldvd.setAttribute('title',"DVD NOT LOADED")
            xmldvd.setAttribute('longest_track',"0")
            self.xmlcontent.appendChild(xmldvd)
            return

        xmldvd.setAttribute('title',str(self.dvd_info['title']))
        xmldvd.setAttribute('longest_track',str(self.dvd_info['longest_track']))
        # dvd's title
        for track in self.dvd_info["track"]: 
            xmltrack = self.xmldoc.createElement('track')
            for info in ('ix','length'):
                xmltrack.setAttribute(info,str(track[info]))

            # avalaible audio channels
            for audio in track["audio"]: 
                xmlaudio = self.xmldoc.createElement('audio')
                for info in ('ix','lang'):
                    xmlaudio.setAttribute(info,str(audio[info]))
                xmltrack.appendChild(xmlaudio)

            # avalaible subtitle channels
            for sub in track["subp"]: 
                xmlsub = self.xmldoc.createElement('subtitle')
                for info in ('ix','lang'):
                    xmlsub.setAttribute(info,str(sub[info]))
                xmltrack.appendChild(xmlsub)

            # chapter list
            for chapter in track["chapter"]: 
                xmlchapter = self.xmldoc.createElement('chapter')
                for info in ('ix','length'):
                    xmlchapter.setAttribute(info,str(chapter[info]))
                xmltrack.appendChild(xmlchapter)

            xmldvd.appendChild(xmltrack)

        self.xmlcontent.appendChild(xmldvd)


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
