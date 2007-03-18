"""The Deejayd python client library"""

import socket, threading

from Queue import Queue, Empty

from xml.dom import minidom, DOMException

from StringIO import StringIO
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

msgDelimiter = 'ENDXML\n'

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

    def __init__(self, answerQueue):
        self.answerQueue = answerQueue

        self.answer = None
        self.originatingCommand = ''

        self.xmlpath = []
        self.responseType = ''
        self.parms = {}

    def startElement(self, name, attrs):
        self.xmlpath.append(name)

        if name in ['error', 'response'] and len(self.xmlpath) == 2:
            self.originatingCommand = attrs.get('name')

        if name == 'response':
            self.responseType = attrs.get('type')
            if self.responseType == 'Ack':
                self.answer = True
            elif self.responseType in ['SongList']:
                self.answer = []
        elif name == 'parm':
            self.parms[attrs.get('name')] = attrs.get('value')
        elif name == 'playlist':
            assert self.responseType == 'playlistList'
            assert self.xmlpath == ['deejayd', 'response', 'playlist']
            self.answer.append(attrs.get('name'))

    def characters(self, str):
        if self.xmlpath == ['deejayd', 'error']:
            self.answer = str

    def endElement(self, name):
        self.xmlpath.pop()

        if name in ['song', 'webradio', 'file']:
            self.answer.append(self.parms)
            self.parms.clear()
        elif name in ['response', 'error']:
            self.answerQueue.put(self.answer)
            self.answer = None

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

    def __init__(self, socket, answerQueue):
        DeejayDaemonSocketThread.__init__(self, socket)
        self.answerQueue = answerQueue

        self.parser = make_parser()
        self.answerBuilder = AnswerFactory(self.answerQueue)
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

    def __init__(self, host, port):
        # Queue setup
        self.commandQueue = Queue()
        self.answerQueue = Queue()

        # Socket setup
        self.socketToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.host = host
        self.port = port

        # Messaging threads
        self.sendingThread = DeejayDaemonCommandThread(self.socketToServer,
                                                       self.commandQueue)
        self.receivingThread = DeejayDaemonAnswerThread(self.socketToServer,
                                                        self.answerQueue)

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

    def getNextAnswer(self):
        return self.answerQueue.get()

    def ping(self):
        cmd = DeejaydXMLCommand('ping')
        self.commandQueue.put(cmd)

# vim: ts=4 sw=4 expandtab
