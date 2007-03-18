"""
Deejayd Client library testing
"""
# -*- coding: utf-8 -*-

from testdeejayd import TestCaseWithData, TestCaseWithProvidedMusic
import testdeejayd.data

from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemon, DeejaydXMLCommand, AnswerFactory

# FIXME : We should not need those here, this is some code duplication from the
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


class TestAnswerParser(TestCaseWithData):
    """Test the Deejayd client library answer parser"""

    def setUp(self):
        TestCaseWithData.setUp(self)

        self.ansq = Queue()
        self.parser = make_parser()
        self.ansb = AnswerFactory(self.ansq)
        self.parser.setContentHandler(self.ansb)

    def parseAnswer(self, str):
        self.parser.parse(StringIO(str))

    def testAnswerParserAck(self):
        """Test the client library parsing an ack answer"""

        originatingCommand = 'ping'
        ackAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="Ack"/>
</deejayd>""" % originatingCommand

        self.parseAnswer(ackAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        self.assertEqual(self.ansq.get(), ('Ack', True))

    def testAnswerParserError(self):
        """Test the client library parsing an error"""

        originatingCommand = 'zboub'
        errorText = 'This command is not yet part of the protocol.'
        errorAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <error name="%s">%s</error>
</deejayd>""" % (originatingCommand, errorText)

        self.parseAnswer(errorAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        self.assertEqual(self.ansq.get(), ('error', errorText))


    def testAnswerParserPlaylist(self):
        """Test the client library parsing a song list answer"""
        originatingCommand = 'getPlaylist'
        songListAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="SongList">""" % originatingCommand
        songOrder = 0
        for song in testdeejayd.data.songlibrary:
            song['plorder'] = songOrder
            songOrder = songOrder + 1

            songListAnswer = songListAnswer + """
        <song>"""
            for tag in song.keys():
                songListAnswer = songListAnswer + """
            <parm name="%s" value="%s" />""" % (tag, song[tag])

            songListAnswer = songListAnswer + """
        </song>"""

        songListAnswer = songListAnswer + """
    </response>
</deejayd>"""

        self.parseAnswer(songListAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        retrievedSongListType, retrievedSongList = self.ansq.get()

        self.assertEqual('SongList', retrievedSongListType)
        for song in testdeejayd.data.songlibrary:
            for tag in song.keys():
                songRank = song['plorder']

                if tag == 'plorder':
                    # FIXME : the answer parser should build on int here, there
                    # should be no need for a type conversion.
                    self.assertEqual(song[tag],
                                     int(retrievedSongList[songRank][tag]))
                else:
                    # FIXME : This does not work because of an utf-8 error
                    self.assertEqual(song[tag],
                                     retrievedSongList[songRank][tag])

    def testAnswerParserPlaylistList(self):
        """Test the client library parsing a playlist list answer"""
        originatingCommand = 'playlistList'

        pls = []
        for nb in range(5):
            pls.append(self.testdata.getRandomString())

        plListAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="PlaylistList">""" % originatingCommand
        for pl in pls:
            plListAnswer = plListAnswer + """
        <playlist name="%s" />""" % pl

        plListAnswer = plListAnswer + """
    </response>
</deejayd>"""

        self.parseAnswer(plListAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        retrievedPlListType, retrievedPlList = self.ansq.get()

        self.assertEqual('PlaylistList', retrievedPlListType)
        for pl in retrievedPlList:
            self.assertEqual(pl in pls, True)


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

    def testPlaylistSaveRetrieve(self):
        """Save a playlist and try to retrieve it."""

        pl = []
        djplname = self.testdata.getRandomString()

        # Get current playlist
        self.deejaydaemon.getCurrentPlaylist()
        djpl = self.deejaydaemon.getNextAnswer()

        # Add songs to playlist
        for songPath in self.testdata.getRandomSongPaths(3):
            pl.append(songPath)

            djpl.addSong(songPath)
            self.assertEqual(self.deejaydaemon.getNextAnswer(), True)

        # Save the playlist
        djpl.save(djplname)
        self.assertEqual(self.deejaydaemon.getNextAnswer(), True)

        # Check for the saved playslit to be available
        self.deejaydaemon.getPlaylistList()
        retrievedPls = self.deejaydaemon.getNextAnswer()
        self.assertEqual(djplname in retrievedPls, True)

        # Retrieve the saved playlist
        self.deejaydaemon.getPlaylist(djplname)
        retrievedPl = self.deejaydaemon.getNextAnswer()
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['Path'])


# vim: ts=4 sw=4 expandtab
