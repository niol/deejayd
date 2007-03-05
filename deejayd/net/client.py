"""The Deejayd python client library"""

from types import ListType

import socket, threading
from Queue import Queue, Empty
from xml.dom import minidom, DOMException

msgDelimiter = 'ENDXML\n'

class DeejaydXMLCommand:

    def __init__(self, name):
        self.name = name
        self.args = {}

    def addSimpleArg(self, name, value):
        self.args[name] = value

    def addMultipleArg(self, name, valuelist):
        self.addSimpleArg(self, name, valuelist)

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

            if type(argParam) is ListType:
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


class AnswerFactory:

    def __init__(self, buffer):
        self.buffer = buffer
        self.parsed = False
        self.xmlTree = None
        self.responses = None

    def parse(self):
        if self.parsed:
            return

        self.xmlTree = minidom.parseString(self.buffer)
        self.responses = self.xmlTree.getElementsByTagName('response')

    def getOriginatingCommand(self):
        self.parse()

        # FIXME : This should handle multiple responses
        return self.responses[0].attributes['name'].value

    def getAnswer(self):
        self.parse()

        # FIXME : This should also handle multiple responses
        resp =  self.responses[0].attributes['type'].value

        if resp == 'Ack':
            return True


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


class DeejayDaemonCommandThread(DeejayDaemonSocketThread):

    def __init__(self, socket, commandQueue):
        DeejayDaemonSocketThread.__init__(self, socket)
        self.commandQueue = commandQueue

    def reallyRun(self):
        # FIXME : There should be a better method that non-blocking wait to be
        # able to cleanly terminate the thread
        try:
            self.__send(self.commandQueue.get(False,1).toXML())
        except Empty:
            # If the queue is empty, simply ignore
            pass

    def __send(self, buf):
        self.socketToServer.send(buf + msgDelimiter)


class DeejayDaemonAnswerThread(DeejayDaemonSocketThread):

    def __init__(self, socket, answerQueue):
        DeejayDaemonSocketThread.__init__(self, socket)
        self.answerQueue = answerQueue

    def reallyRun(self):
        rawmsg = self.__readmsg()
        self.answerQueue.put(AnswerFactory(rawmsg).getAnswer())

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
        self.sendingThread.shouldStop = True

        self.socketToServer.close()

    def getNextAnswer(self):
        return self.answerQueue.get()

    def ping(self):
        cmd = DeejaydXMLCommand('ping')
        self.commandQueue.put(cmd)

# vim: ts=4 sw=4 expandtab
