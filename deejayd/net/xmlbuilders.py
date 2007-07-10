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
        if isinstance(s,int) or isinstance(s,float):
            return "%d" % (s,)
        elif isinstance(s,str):
            return "%s" % (s)
        elif isinstance(s,unicode):
            return "%s" % (s.encode('utf-8'))

    def build_xml_parm(self, name, value):
        xmlparm = self.xmldoc.createElement('parm')
        xmlparm.setAttribute('name', name)
        xmlparm.setAttribute('value', self.__to_xml_string(value))
        return xmlparm

    def build_xml_list_parm(self, name, valueList):
        xml_list_parm = self.xmldoc.createElement('listparm')
        for value in valueList:
            xmlvalue = self.xmldoc.createElement('value')
            value = self.__to_xml_string(value)
            xmlvalue.appendChild(xmldoc.createTextNode(value))
            xml_list_parm.appendChild(xmlValue)
        return xml_list_parm

    def build_xml_parm_list(self, data, parent_element):
        for data_key, data_value in data.items():
            xml_parm = None
            if type(data_value) is list:
                xml_parm = self.build_xml_list_parm(data_key, data_value)
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


class DeejaydXMLFileList(DeejaydXMLAck):
    """A list of files and directories."""

    response_type = 'FileList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)

        self.directory = None

        self.contents = {'directory' : [],
                         'file'      : [],
                         'video'     : [] }

    def set_directory(self, directory):
        self.directory = directory

    def add_directory(self, dirname):
        self.contents['directory'].append(dirname)

    def set_directories(self, directories):
        self.contents['directory'] = directories

    def add_file(self, file_info):
        self.contents['file'].append(file_info)

    def set_files(self, file_list):
        self.contents['file'] = file_list

    def add_video(self, video_info):
        self.contents['video'].append(video_info)

    def set_videos(self, video_list):
        self.contents['video'] = video_list

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)

        if self.directory != None:
            self.xmlcontent.setAttribute('directory', self.directory)

        for dirname in self.contents['directory']:
            xmldir = self.xmldoc.createElement('directory')
            xmldir.setAttribute('name', dirname)
            self.xmlcontent.appendChild(xmldir)

        for mediaType in ['file', 'video']:
            for item in self.contents[mediaType]:
                xmlitem = self.xmldoc.createElement(mediaType)
                self.build_xml_parm_list(item, xmlitem)
                self.xmlcontent.appendChild(xmlitem)


class DeejaydWebradioList(DeejaydXMLAck):
    """A list of webradios with information for each webradio : id, pos, title and url."""

    response_type = 'WebradioList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.webradios = []

    def add_webradio(self, wr):
        self.webradios.append(wr)

    def set_webradios(self, wr_list):
        self.webradios = wr_list

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        for wr in self.webradios:
            xmlwr = self.xmldoc.createElement('webradio')
            self.build_xml_parm_list(wr, xmlwr)
            self.xmlcontent.appendChild(xmlwr)


class DeejaydXMLSongList(DeejaydXMLAck):
    """A list of songs with information for each song : artist, album, title, id, etc."""

    response_type = 'SongList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.songs = []

    def add_song(self, song):
        self.songs.append(song)

    def set_songs(self, songs):
        self.songs = songs

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        for song in self.songs:
            xmlsong = self.xmldoc.createElement('song')
            self.build_xml_parm_list(song, xmlsong)
            self.xmlcontent.appendChild(xmlsong)


class DeejaydPlaylistList(DeejaydXMLAck):
    """A list of playlist names."""

    response_type = 'PlaylistList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.playlist_names = []

    def add_playlist(self, playlist_name):
        self.playlist_names.append(playlist_name)

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        for playlist_name in self.playlist_names:
            xmlpl = self.xmldoc.createElement('playlist')
            xmlpl.setAttribute('name', playlist_name)
            self.xmlcontent.appendChild(xmlpl)


class DeejaydVideoList(DeejaydXMLAck):
    """A list of videos with information for each video."""

    response_type = 'VideoList'

    def __init__(self, originating_cmd, mother_xml_object = None):
        DeejaydXMLAck.__init__(self, originating_cmd, mother_xml_object)
        self.videos = []

    def add_video(self, video):
        self.videos.append(video)

    def build_xml(self):
        DeejaydXMLAck.build_xml(self)
        for video in self.videos:
            xmlvid = self.xmldoc.createElement('video')
            self.build_xml_parm_list(video, xmlvid)
            self.xmlcontent.appendChild(xmlvid)


class DeejaydXMLAnswerFactory:

    response_types = [ DeejaydXMLError,
                      DeejaydXMLAck,
                      DeejaydXMLKeyValue,
                      DeejaydXMLFileList,
                      DeejaydWebradioList,
                      DeejaydXMLSongList,
                      DeejaydPlaylistList,
                      DeejaydVideoList     ]

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
