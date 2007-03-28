"""
Deejayd Client library testing
"""
# -*- coding: utf-8 -*-

from testdeejayd import TestCaseWithData, TestCaseWithProvidedMusic
import testdeejayd.data

from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemon, DeejaydXMLCommand, AnswerFactory,\
                               DeejaydAnswer, DeejaydKeyValue,\
                               DeejaydPlaylist, DeejaydError

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

        self.eansq = Queue()
        self.parser = make_parser()
        self.ansb = AnswerFactory(self.eansq)
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

        ans = DeejaydAnswer()
        self.eansq.put(ans)
        self.parseAnswer(ackAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        self.assertEqual(ans.getContents(), True)

    def testAnswerParserError(self):
        """Test the client library parsing an error"""

        originatingCommand = 'zboub'
        errorText = 'This command is not yet part of the protocol.'
        errorAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <error name="%s">%s</error>
</deejayd>""" % (originatingCommand, errorText)

        ans = DeejaydAnswer()
        self.eansq.put(ans)
        self.parseAnswer(errorAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        # FIXME : find a way to test the errorText
        self.assertRaises(DeejaydError, ans.getContents)

    def testAnswerParserKeyValue(self):
        """Test the client library parsing a key value answer"""
        originatingCommand = 'status'
        keyValueAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="KeyValue">""" % originatingCommand
        howMuch = 10
        origKeyValue = {}
        for count in range(howMuch):
            key = self.testdata.getRandomString()
            value =  self.testdata.getRandomString()
            origKeyValue[key] = value
            keyValueAnswer = keyValueAnswer + """
        <parm name="%s" value="%s" />""" % (key, value)
        keyValueAnswer = keyValueAnswer + """
    </response>
</deejayd>"""

        ans = DeejaydKeyValue()
        self.eansq.put(ans)
        self.parseAnswer(keyValueAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        retrievedKeyValues = ans.getContents()

        for key in origKeyValue.keys():
            self.assertEqual(origKeyValue[key], retrievedKeyValues[key])

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

        ans = DeejaydPlaylist(None)
        self.eansq.put(ans)
        self.parseAnswer(songListAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        retrievedSongList = ans.getContents()

        for song in testdeejayd.data.songlibrary:
            for tag in song.keys():
                songRank = song['plorder']

                if tag == 'plorder':
                    self.assertEqual(song[tag],
                                     retrievedSongList[songRank][tag])
                else:
                    self.assertEqual(song[tag].decode('utf-8'),
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

        ans = DeejaydAnswer()
        self.eansq.put(ans)
        self.parseAnswer(plListAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)
        retrievedPlList = ans.getContents()

        for pl in pls:
            self.assertEqual(pl in retrievedPlList, True)


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
        self.deejaydaemon = DeejayDaemon('localhost', testServerPort, False)
        self.deejaydaemon.connect()

    def testPing(self):
        """Ping server"""
        self.assertEqual(self.deejaydaemon.ping().getContents(), True)

    def testPingAsync(self):
        """Ping server asynchroneously"""
        self.deejaydaemon.setAsync(True)
        ans = self.deejaydaemon.ping()
        self.assertEqual(ans.getContents(), True)
        self.deejaydaemon.setAsync(False)

    def tearDown(self):
        self.deejaydaemon.disconnect()
        self.testserver.stop()

    def testPlaylistSaveRetrieve(self):
        """Save a playlist and try to retrieve it."""

        pl = []
        djplname = self.testdata.getRandomString()

        # Get current playlist
        djpl = self.deejaydaemon.getCurrentPlaylist()
        self.assertEqual(djpl.getContents(), [])

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.testdata.getRandomSongPaths(howManySongs):
            pl.append(songPath)
            self.assertEqual(djpl.addSong(songPath).getContents(), True)

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejaydaemon.getStatus()['playlistlength'],
                         howManySongs)

        # Save the playlist
        self.assertEqual(djpl.save(djplname).getContents(), True)

        # Check for the saved playslit to be available
        retrievedPls = self.deejaydaemon.getPlaylistList().getContents()
        self.assertEqual(djplname in retrievedPls, True)

        # Retrieve the saved playlist
        retrievedPl = self.deejaydaemon.getPlaylist(djplname)
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['Path'])


# vim: ts=4 sw=4 expandtab
