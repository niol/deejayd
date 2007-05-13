from xml.dom import minidom


class DeejaydXML:

    def __init__(self, motherXMLObject = None):
        self.appendedXMLObjects = None
        self.__isMother = True

        if motherXMLObject == None:
            self.xmldoc = minidom.Document()
            self.xmlroot = self.xmldoc.createElement('deejayd')
            self.xmldoc.appendChild(self.xmlroot)
            self.appendedXMLObjects = [self]
        else:
            self.__isMother = False
            self.xmldoc = motherXMLObject.xmldoc
            self.xmlroot = self.xmldoc.getElementsByTagName('deejayd').pop()
            motherXMLObject.appendAnotherXMLObject(self)

        self.xmlcontent = None

    def appendAnotherXMLObject(self, xmlObject):
        self.appendedXMLObjects.append(xmlObject)

    def __reallyBuildXML(self):
        if self.__isMother:
            for xmlObject in self.appendedXMLObjects:
                xmlObject.buildXML()
                self.xmlroot.appendChild(xmlObject.xmlcontent)
        else:
            raise NotImplementedError('Do not build directly deejayd\
                                       XML that has a mother.')

    def toXML(self):
        self.__reallyBuildXML()
        return self.xmldoc.toxml('utf-8')

    def toPrettyXML(self):
        self.__reallyBuildXML()
        return self.xmldoc.toprettyxml(encoding = 'utf-8')

    def buildXML(self):
        raise NotImplementedError


class DeejaydXMLCommand(DeejaydXML):

    def __init__(self, name, motherXMLObject = None):
        DeejaydXML.__init__(self, motherXMLObject)
        self.name = name
        self.args = {}

    def addSimpleArg(self, name, value):
        self.args[name] = value

    def addMultipleArg(self, name, valuelist):
        self.addSimpleArg(name, valuelist)

    def buildXML(self):
        # Add command
        self.xmlcontent = self.xmldoc.createElement('command')
        self.xmlcontent.setAttribute('name', self.name)

        # Add args
        for arg in self.args.keys():
            xmlarg = self.xmldoc.createElement('arg')
            xmlarg.setAttribute('name', arg)
            self.xmlcontent.appendChild(xmlarg)

            argParam = self.args[arg]

            if type(argParam) is list:
                # We've got multiple args
                xmlarg.setAttribute('type', 'multiple')

                for argParamValue in argParam:
                    xmlval = self.xmldoc.createElement('value')
                    xmlval.appendChild(self.xmldoc.createTextNode(
                                str(argParamValue) ))
                    xmlarg.appendChild(xmlval)

            else:
                # We've got a simple arg
                xmlarg.setAttribute('type', 'simple')
                xmlarg.appendChild(self.xmldoc.createTextNode(str(argParam)))


class DeejaydXMLAnswer(DeejaydXML):

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXML.__init__(self, motherXMLObject)
        self.originatingCmd = originatingCmd

    def __toXMLString(self, s):
        if isinstance(s,int) or isinstance(s,float):
            return "%d" % (s,)
        elif isinstance(s,str):
            return "%s" % (s)
        elif isinstance(s,unicode):
            return "%s" % (s.encode('utf-8'))

    def buildXMLParm(self, name, value):
        xmlparm = self.xmldoc.createElement('parm')
        xmlparm.setAttribute('name', name)
        xmlparm.setAttribute('value', self.__toXMLString(value))
        return xmlparm

    def buildXMLListparm(self, name, valueList):
        xmlListParm = self.xmldoc.createElement('listparm')
        for value in valueList:
            xmlvalue = self.xmldoc.createElement('value')
            value = self.__toXMLString(value)
            xmlvalue.appendChild(xmldoc.createTextNode(value))
            xmlListParm.appendChild(xmlValue)
        return xmlListParm

    def buildXMLParmList(self, data, parentElement):
        for dataKey, dataValue in data.items():
            xmlParm = None
            if type(dataValue) is list:
                xmlParm = self.buildXMLListparm(dataKey, dataValue)
            else:
                xmlParm = self.buildXMLParm(dataKey, dataValue)
            parentElement.appendChild(xmlParm)


class DeejaydXMLError(DeejaydXMLAnswer):
    """Error notification."""

    responseType = 'error'

    def setErrorText(self, txt):
        self.errorText = txt

    def buildXML(self):
        self.xmlcontent = self.xmldoc.createElement(self.responseType)
        self.xmlcontent.setAttribute('name', self.originatingCmd)
        xmlErrorText = self.xmldoc.createTextNode(str(self.errorText))
        self.xmlcontent.appendChild(xmlErrorText)


class DeejaydXMLAck(DeejaydXMLAnswer):
    """Acknowledgement of a command."""

    responseType = 'Ack'

    def buildXML(self):
        self.xmlcontent = self.xmldoc.createElement('response')
        self.xmlcontent.setAttribute('name', self.originatingCmd)
        self.xmlcontent.setAttribute('type', self.responseType)


class DeejaydXMLKeyValue(DeejaydXMLAck):
    """A list of key, value pairs."""

    responseType = 'KeyValue'

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXMLAck.__init__(self, originatingCmd, motherXMLObject)
        self.contents = {}

    def addPair(self, key, value):
        self.contents[key] = value

    def setPairs(self, keyValue):
        self.contents = keyValue

    def buildXML(self):
        DeejaydXMLAck.buildXML(self)

        for k, v in self.contents.items():
            self.xmlcontent.appendChild(self.buildXMLParm(k, v))


class DeejaydXMLFileList(DeejaydXMLAck):
    """A list of files and directories."""

    responseType = 'FileList'

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXMLAck.__init__(self, originatingCmd, motherXMLObject)

        self.directory = None

        self.contents = {'directory' : [],
                         'file'      : [],
                         'video'     : [] }

    def setDirectory(self, directory):
        self.directory = directory

    def addDirectory(self, dirname):
        self.contents['directory'].append(dirname)

    def setDirectories(self, directories):
        self.contents['directory'] = directories

    def addFile(self, fileInfo):
        self.contents['file'].append(fileInfo)

    def setFiles(self, fileList):
        self.contents['file'] = fileList

    def addVideo(self, videoInfo):
        self.contents['video'].append(videoInfo)

    def setVideos(self, videoList):
        self.contents['video'] = videoList

    def buildXML(self):
        DeejaydXMLAck.buildXML(self)

        if self.directory != None:
            self.xmlcontent.setAttribute('directory', self.directory)

        for dirname in self.contents['directory']:
            xmldir = self.xmldoc.createElement('directory')
            xmldir.setAttribute('name', dirname)
            self.xmlcontent.appendChild(xmldir)

        for mediaType in ['file', 'video']:
            for item in self.contents[mediaType]:
                xmlitem = self.xmldoc.createElement(mediaType)
                self.buildXMLParmList(item, xmlitem)
                self.xmlcontent.appendChild(xmlitem)


class DeejaydWebradioList(DeejaydXMLAck):
    """A list of webradios with information for each webradio : id, pos, title and url."""

    responseType = 'WebradioList'

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXMLAck.__init__(self, originatingCmd, motherXMLObject)
        self.webradios = []

    def addWebradio(self, wr):
        self.webradios.append(wr)

    def setWebradios(self, wrList):
        self.webradios = wrList

    def buildXML(self):
        DeejaydXMLAck.buildXML(self)
        for wr in self.webradios:
            xmlwr = self.xmldoc.createElement('webradio')
            self.buildXMLParmList(wr, xmlwr)
            self.xmlcontent.appendChild(xmlwr)


class DeejaydXMLSongList(DeejaydXMLAck):
    """A list of songs with information for each song : artist, album, title, id, etc."""

    responseType = 'SongList'

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXMLAck.__init__(self, originatingCmd, motherXMLObject)
        self.songs = []

    def addSong(self, song):
        self.songs.append(song)

    def setSongs(self, songs):
        self.songs = songs

    def buildXML(self):
        DeejaydXMLAck.buildXML(self)
        for song in self.songs:
            xmlsong = self.xmldoc.createElement('song')
            self.buildXMLParmList(song, xmlsong)
            self.xmlcontent.appendChild(xmlsong)


class DeejaydPlaylistList(DeejaydXMLAck):
    """A list of playlist names."""

    responseType = 'PlaylistList'

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXMLAck.__init__(self, originatingCmd, motherXMLObject)
        self.playlistNames = []

    def addPlaylist(self, playlistName):
        self.playlistNames.append(playlistName)

    def buildXML(self):
        DeejaydXMLAck.buildXML(self)
        for playlistName in self.playlistNames:
            xmlpl = self.xmldoc.createElement('playlist')
            xmlpl.setAttribute('name', playlistName)
            self.xmlcontent.appendChild(xmlpl)


class DeejaydVideoList(DeejaydXMLAck):
    """A list of videos with information for each video."""

    responseType = 'VideoList'

    def __init__(self, originatingCmd, motherXMLObject = None):
        DeejaydXMLAck.__init__(self, originatingCmd, motherXMLObject)
        self.videos = []

    def addVideo(self, video):
        self.videos.append(video)

    def buildXML(self):
        DeejaydXMLAck.buildXML(self)
        for video in self.videos:
            xmlvid = self.xmldoc.createElement('video')
            self.buildXMLParmList(video, xmlvid)
            self.xmlcontent.appendChild(xmlvid)


class DeejaydXMLAnswerFactory:

    responseTypes = [ DeejaydXMLError,
                      DeejaydXMLAck,
                      DeejaydXMLKeyValue,
                      DeejaydXMLFileList,
                      DeejaydWebradioList,
                      DeejaydXMLSongList,
                      DeejaydPlaylistList,
                      DeejaydVideoList     ]

    def __init__(self):
        self.motherAnswer = None

    def setMother(self, motherAnswer):
        self.motherAnswer = motherAnswer

    def getDeejaydXMLAnswer(self, type, originatingCmd):
        iat = iter(self.responseTypes)
        try:
            while True:
                typeClass = iat.next()
                if typeClass.responseType == type:
                    ans = typeClass(originatingCmd, self.motherAnswer)
                    return ans
        except StopIteration:
            raise NotImplementedError


# vim: ts=4 sw=4 expandtab
