"""
Deejayd Client library testing
"""

from testdeejayd import TestCaseWithProvidedMusic
from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemon, DeejaydXMLCommand, AnswerFactory

# FIXME : We should not nee dthose here, this is some code duplication from the
# client code.
from Queue import Queue
from StringIO import StringIO
from xml.sax import make_parser

import re, unittest

class TestCommandBuildParse(unittest.TestCase):
    """Test the Deejayd client library command building"""

    def trimXML(self, xml):
        return re.sub('(\s{2,})|(\\n)','', xml)

    def testCommandBuilder(self):
        """Client library builds commands according to protocol scheme"""
        cmd = DeejaydXMLCommand('command1')
        cmd.addSimpleArg('argName1', 'bou')
        cmd.addSimpleArg('argName2', 'bou2')
        cmd.addSimpleArg('argName3', ['bou2', 'haha', 'aza'])
        cmd.addSimpleArg('argName4', 'bou3')
        cmd.addSimpleArg('argName5', ['bou2', 'hihi', 'aza'])

        expectedAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <command name="command1">
        <arg name="argName5" type="multiple">
            <value>bou2</value>
            <value>hihi</value>
            <value>aza</value>
        </arg>
        <arg name="argName4" type="simple">bou3</arg>
        <arg name="argName3" type="multiple">
            <value>bou2</value>
            <value>haha</value>
            <value>aza</value>
        </arg>
        <arg name="argName2" type="simple">bou2</arg>
        <arg name="argName1" type="simple">bou</arg>
    </command>
</deejayd>"""

        self.assertEqual(cmd.toXML(), self.trimXML(expectedAnswer))


class TestAnswerParser(unittest.TestCase):
    """Test the Deejayd client library answer parser"""

    def setUp(self):
        self.ansq = Queue()
        self.parser = make_parser()
        self.ansb = AnswerFactory(self.ansq)
        self.parser.setContentHandler(self.ansb)

    def parseAnswer(self, str):
        self.parser.parse(StringIO(str))

    def testAnswerParserAck(self):
        """Test the client library parsing an ack answer"""

        # FIXME : Handle the negative case
        originatingCommand = 'cmdName1'
        ackAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="Ack"/>
</deejayd>""" % originatingCommand

        self.parseAnswer(ackAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        self.assertEqual(self.ansq.get(), True)


class TestClient(TestCaseWithProvidedMusic):
    """Completely test the DeejaydClient library"""

    def setUp(self):
        TestCaseWithProvidedMusic.setUp(self)

        # Set up the test server
        testServerPort = 23344
        dbfilename = '/tmp/testdeejayddb-' + self.testdata.getRandomString()
        self.testserver = TestServer(testServerPort,
                                     self.testdata.getRootDir(), dbfilename)
        self.testserver.start()

        # Instanciate the server object of the client library
        self.deejaydaemon = DeejayDaemon('localhost', testServerPort)
        self.deejaydaemon.connect()

    def testPing(self):
        """Ping server"""
        self.deejaydaemon.ping()
        self.assertEqual(self.deejaydaemon.getNextAnswer(), True)

    def tearDown(self):
        self.deejaydaemon.disconnect()
        self.testserver.stop()


# vim: ts=4 sw=4 expandtab
