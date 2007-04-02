"""The Deejayd python client library"""

import socket, threading

from Queue import Queue, Empty

from xml.dom import minidom, DOMException

from StringIO import StringIO
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

msgDelimiter = 'ENDXML\n'


class DeejaydError(Exception):
    pass

class DeejaydAnswer:

    def __init__(self, server = None):
        self.answerReceived = threading.Event()
        self.contents = None
        self.error = False
        self.server = server

    def wait(self):
        self.answerReceived.wait()

    def received(self, contents):
        self.contents = contents
        self.answerReceived.set()

    def setError(self, msg):
        self.contents = msg
        self.error = True
        self.answerReceived.set()

    def getContents(self):
        self.wait()
        if self.error:
            raise DeejaydError(self.contents)
        return self.contents


class DeejaydKeyValue(DeejaydAnswer):

    def __getitem__(self, name):
        self.getContents()
        return self.contents[name]


class DeejaydFileList(DeejaydAnswer):

    def __init__(self, server = None):
        DeejaydAnswer.__init__(self, server)
        self.files = []
        self.directories = []

    def addFile(self, file):
        self.files.append(file)

    def addDir(self, dir):
        self.directories.append(dir)

    def getFiles(self):
        self.getContents()
        return self.files

    def getDirectories(self):
        self.getContents()
        return self.directories


class DeejaydWebradioList(DeejaydAnswer):
    pass


class DeejaydPlaylist(DeejaydKeyValue):

    def save(self, name):
        cmd = DeejaydXMLCommand('playlistSave')
        cmd.addSimpleArg('name', name)
        return self.server.sendCommand(cmd)

    def addSong(self, path, position = None, name = None):
        return self.addSongs([path], position, name)

    def addSongs(self, paths, position = None, name = None):
        cmd = DeejaydXMLCommand('playlistAdd')
        cmd.addMultipleArg('path', paths)
        if position != None:
            cmd.addSimpleArg('pos', position)
        if name != None:
            cmd.addSimpleArg('name', name)
        return self.server.sendCommand(cmd)

    def load(self, name, loadingPosition = 0):
        cmd = DeejaydXMLCommand('playlistLoad')
        cmd.addSimpleArg('name', name)
        cmd.addSimpleArg('pos', loadingPosition)
        return self.server.sendCommand(cmd)


class DeejaydXMLCommand:

    def __init__(self, name):
        self.name = name
        self.args = {}

    def addSimpleArg(self, name, value):
        self.args[name] = value

    def addMultipleArg(self, name, valuelist):
        self.addSimpleArg(name, valuelist)

    def toXML(self):
        xmldoc = minidom.Document()

        # Add root
        xmlroot = xmldoc.createElement('deejayd')
        xmldoc.appendChild(xmlroot)

        # Add command
        xmlcmd = xmldoc.createElement('command')
        xmlcmd.setAttribute('name', self.name)
        xmlroot.appendChild(xmlcmd)

        # Add args
        for arg in self.args.keys():
            xmlarg = xmldoc.createElement('arg')
            xmlarg.setAttribute('name', arg)
            xmlcmd.appendChild(xmlarg)

            argParam = self.args[arg]

            if type(argParam) is list:
                # We've got multiple args
                xmlarg.setAttribute('type', 'multiple')

                for argParamValue in argParam:
                    xmlval = xmldoc.createElement('value')
                    xmlval.appendChild(xmldoc.createTextNode(
                                str(argParamValue) ))
                    xmlarg.appendChild(xmlval)

            else:
                # We've got a simple arg
                xmlarg.setAttribute('type', 'simple')
                xmlarg.appendChild(xmldoc.createTextNode(str(argParam)))

        return xmldoc.toxml('utf-8')


class AnswerFactory(ContentHandler):

    def __init__(self, expectedAnswersQueue):
        self.expectedAnswersQueue = expectedAnswersQueue

        self.answer = None
        self.originatingCommand = ''

        self.xmlpath = []
        self.responseType = ''
        self.parms = {}

    def startElement(self, name, attrs):
        self.xmlpath.append(name)

        if name in ['error', 'response'] and len(self.xmlpath) == 2:
            self.originatingCommand = attrs.get('name')
            self.expectedAnswer = self.expectedAnswersQueue.get()

        if name == 'response':
            self.responseType = attrs.get('type')
            if self.responseType == 'Ack':
                self.answer = True
            elif self.responseType in ['FileList', 'WebradioList',
                                       'SongList', 'PlaylistList']:
                self.answer = []
            elif self.responseType == 'KeyValue':
                self.answer = {}
        elif name == 'parm':
            # Parse value into a int if possible
            val = attrs.get('value')
            try:
                realVal = int(val)
            except(ValueError):
                realVal = val

            if self.responseType == 'KeyValue':
                self.answer[attrs.get('name')] = realVal
            else:
                self.parms[attrs.get('name')] = realVal
        elif name == 'directory':
            assert self.responseType == 'FileList'
            assert self.xmlpath == ['deejayd', 'response', 'directory']
            self.expectedAnswer.addDir(attrs.get('name'))
        elif name == 'playlist':
            assert self.responseType == 'PlaylistList'
            assert self.xmlpath == ['deejayd', 'response', 'playlist']
            self.answer.append(attrs.get('name'))
        elif name == 'error':
            self.responseType = 'error'

    def characters(self, str):
        if self.xmlpath == ['deejayd', 'error']:
            self.answer = str

    def endElement(self, name):
        self.xmlpath.pop()

        if name in ['song', 'webradio']:
            self.answer.append(self.parms)
            self.parms = {}
        elif name == 'file':
            self.expectedAnswer.addFile(self.parms)
            self.parms = {}
        elif name in ['response', 'error']:
            if name == 'response':
                self.expectedAnswer.received(self.answer)
            elif name == 'error':
                self.expectedAnswer.setError(self.answer)

            self.answer = None
            self.expectedAnswer = None

    def getOriginatingCommand(self):
        return self.originatingCommand


class DeejayDaemonSocketThread(threading.Thread):

    def __init__(self, socket):
        threading.Thread.__init__(self)

        self.shouldStop = False
        self.socketToServer = socket

    def run(self):
        try:
            while not self.shouldStop:
                try:
                    self.reallyRun()
                except StopException:
                    self.shouldStop = True
                except DOMException:
                    # XML parsing failed, simply ignore. What should we do here?
                    pass
        except socket.error:
            # Just terminate thread, this should be because the socket is
            # closed... FIXME : handle I/O errors.
            pass

    def reallyRun(self):
        # This is implemented by daughter classes. This should be a blocking
        # function.
        raise NotImplementedError


class StopException(Exception):
    pass

class DeejayDaemonCommandThread(DeejayDaemonSocketThread):

    def __init__(self, socket, commandQueue):
        DeejayDaemonSocketThread.__init__(self, socket)
        self.commandQueue = commandQueue

    def reallyRun(self):
        cmd = self.commandQueue.get()

        # If we've got a stop exception in the queue, raise it!
        if cmd.__class__ == StopException:
            raise cmd

        self.__send(cmd.toXML())

    def __send(self, buf):
        self.socketToServer.send(buf + msgDelimiter)


class DeejayDaemonAnswerThread(DeejayDaemonSocketThread):

    def __init__(self, socket, expectedAnswersQueue):
        DeejayDaemonSocketThread.__init__(self, socket)
        self.expectedAnswersQueue = expectedAnswersQueue

        self.parser = make_parser()
        self.answerBuilder = AnswerFactory(self.expectedAnswersQueue)
        self.parser.setContentHandler(self.answerBuilder)

    def reallyRun(self):
        rawmsg = self.__readmsg()
        self.parser.parse(StringIO(rawmsg))

    def __readmsg(self):
        msg = ''

        # This is dirty, but there is no msgdelim in answers...
        msgDelimiter = '</deejayd>'

        while msg[-len(msgDelimiter):len(msg)] != msgDelimiter:
            msg = msg + self.socketToServer.recv(4096)

        # We should strip the msgdelim, but in our hack, it is part of the XML,
        # so it may not be a good idea to strip it...
        #return msg[0:len(msg) - 1 - len(msgDelimiter)]
        return msg


class ConnectError(Exception):
    pass


class DeejayDaemon:

    def __init__(self, host, port, async = True):
        # Queue setup
        self.commandQueue = Queue()
        self.expectedAnswersQueue = Queue()

        # Socket setup
        self.socketToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.host = host
        self.port = port

        # Messaging threads
        self.sendingThread = DeejayDaemonCommandThread(self.socketToServer,
                                                   self.commandQueue)
        self.receivingThread = DeejayDaemonAnswerThread(self.socketToServer,
                                                   self.expectedAnswersQueue)

        # Library behavior, asynchroneous or not
        self.async = async

    def connect(self):
        self.socketToServer.connect((self.host, self.port))
        socketFile = self.socketToServer.makefile()

        # Catch version
        self.version = socketFile.readline()

        # Go in XML mode
        self.socketToServer.send('setXML\n')
        initAnswer = socketFile.readline()

        if initAnswer == 'OK\n':
            self.sendingThread.start()
            self.receivingThread.start()
        else:
            self.disconnect()
            raise ConnectError('Initialisation with server failed')

    def disconnect(self):
        # Stop our processing threads
        self.receivingThread.shouldStop = True
        # This is tricky because stopping must be notified in the queue for the
        # command thread...
        self.commandQueue.put(StopException())

        self.socketToServer.close()

    def isAsync(self):
        return self.async

    def setAsync(self, async):
        self.async = async

    def __returnAsyncOrResult(self, answer):
        if not self.async:
           answer.wait()
        return answer

    def sendCommand(self, cmd, expectedAnswer = None):
        # Set a default answer by default
        if expectedAnswer == None:
            expectedAnswer = DeejaydAnswer(self)

        self.expectedAnswersQueue.put(expectedAnswer)
        self.commandQueue.put(cmd)
        return self.__returnAsyncOrResult(expectedAnswer)

    def ping(self):
        cmd = DeejaydXMLCommand('ping')
        return self.sendCommand(cmd)

    def getStatus(self):
        cmd = DeejaydXMLCommand('status')
        return self.sendCommand(cmd, DeejaydKeyValue())

    def getPlaylist(self, name):
        cmd = DeejaydXMLCommand('playlistInfo')
        if name != None:
            cmd.addSimpleArg('name', name)
        ans = DeejaydPlaylist(self)
        return self.sendCommand(cmd, ans)

    def getCurrentPlaylist(self):
        return self.getPlaylist(None)

    def getPlaylistList(self):
        cmd = DeejaydXMLCommand('playlistList')
        return self.sendCommand(cmd)


# vim: ts=4 sw=4 expandtab
