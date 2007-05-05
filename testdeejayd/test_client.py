"""Deejayd Client library testing"""
# -*- coding: utf-8 -*-

from testdeejayd import TestCaseWithData, TestCaseWithProvidedMusic
import testdeejayd.data

from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemon, DeejaydXMLCommand, AnswerFactory,\
                               DeejaydAnswer, DeejaydKeyValue,\
                               DeejaydFileList, DeejaydWebradioList,\
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
        self.failUnless(ans.getContents())

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

    def testAnswerFileList(self):
        """Test the client library parsing a file list answer"""
        originatingCommand = self.testdata.getRandomString()
        fileListAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="FileList">""" % originatingCommand
        howMuch = self.testdata.getRandomInt(50)
        origFiles = []
        origDirs = []

        for count in range(howMuch):

            if self.testdata.getRandomElement(['file', 'directory']) == 'file':
                file = {}

                fileListAnswer = fileListAnswer + """
        <file>
            <parm name="id" value="%s" />""" % count
                file['id'] = count

                howMuchParms = self.testdata.getRandomInt()
                for parmCount in range(howMuchParms):
                    name = self.testdata.getRandomString()
                    value =  self.testdata.getRandomString()
                    file[name] = value
                    fileListAnswer = fileListAnswer + """
            <parm name="%s" value="%s" />""" % (name, value)
                fileListAnswer = fileListAnswer + """
        </file>"""
                origFiles.append(file)
            else:
                dirname = self.testdata.getRandomString()
                fileListAnswer = fileListAnswer + """
        <directory name="%s" />""" % dirname
                origDirs.append(dirname)

        fileListAnswer = fileListAnswer + """
    </response>
</deejayd>"""

        ans = DeejaydFileList()
        self.eansq.put(ans)
        self.parseAnswer(fileListAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)

        for file in origFiles:

            # Find corresponding file in retrieved files
            filesIter = iter(ans.getFiles())
            notFound = True
            retrievedFile = None
            while notFound:
                retrievedFile = filesIter.next()
                if file['id'] == retrievedFile['id']:
                    notFound = False

            for key in file.keys():
                self.failUnless(key in retrievedFile.keys())
                self.assertEqual(file[key], retrievedFile[key])

        for dir in origDirs:
            self.failUnless(dir in ans.getDirectories())

    def testAnswerParserWebradioList(self):
        """Test the client library parsing a web radio list answer"""
        originatingCommand = 'webradioList'
        webradioListAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="WebradioList">""" % originatingCommand
        howMuch = self.testdata.getRandomInt(50)
        origWebradios = []

        for count in range(howMuch):

            webradioListAnswer = webradioListAnswer + """
        <webradio>"""
            howMuchParms = self.testdata.getRandomInt()
            webradio = {}
            for parmCount in range(howMuchParms):
                name = self.testdata.getRandomString()
                value =  self.testdata.getRandomString()
                webradio[name] = value
                webradioListAnswer = webradioListAnswer + """
            <parm name="%s" value="%s" />""" % (name, value)
            webradioListAnswer = webradioListAnswer + """
        </webradio>"""
            origWebradios.append(webradio)

        webradioListAnswer = webradioListAnswer + """
    </response>
</deejayd>"""

        ans = DeejaydWebradioList()
        self.eansq.put(ans)
        self.parseAnswer(webradioListAnswer)

        self.assertEqual(self.ansb.getOriginatingCommand(), originatingCommand)

        for webradio in origWebradios:
            self.failUnless(webradio in ans.getContents())

    def testAnswerParserPlaylist(self):
        """Test the client library parsing a song list answer"""
        originatingCommand = 'playlistInfo'
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
            self.failUnless(pl in retrievedPlList)


class TestClient(TestCaseWithProvidedMusic):
    """Completely test the DeejaydClient library"""

    def setUp(self):
        TestCaseWithProvidedMusic.setUp(self)

        # Set up the test server
        testServerPort = 23344
        dbfilename = '/tmp/testdeejayddb-' +\
                     self.testdata.getRandomString() + '.db'
        self.testserver = TestServer(testServerPort,
                                     self.testdata.getRootDir(), dbfilename)
        self.testserver.start()

        # Instanciate the server object of the client library
        self.deejaydaemon = DeejayDaemon('localhost', testServerPort, False)
        self.deejaydaemon.connect()

    def testPing(self):
        """Ping server"""
        self.failUnless(self.deejaydaemon.ping().getContents())

    def testPingAsync(self):
        """Ping server asynchroneously"""
        self.deejaydaemon.setAsync(True)
        ans = self.deejaydaemon.ping()
        self.failUnless(ans.getContents(),
                        'Server did not respond well to ping.')
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
            self.failUnless(djpl.addSong(songPath).getContents())

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejaydaemon.getStatus()['playlistlength'],
                         howManySongs)

        # Save the playlist
        self.failUnless(djpl.save(djplname).getContents())

        # Check for the saved playslit to be available
        retrievedPls = self.deejaydaemon.getPlaylistList().getContents()
        self.failUnless(djplname in retrievedPls)

        # Retrieve the saved playlist
        retrievedPl = self.deejaydaemon.getPlaylist(djplname)
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['Path'])

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""

        wrList = self.deejaydaemon.getWebradios()

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],
                       ['http://' +\
                        self.testdata.getRandomString(50) + '.pls']]:
            # FIXME : provision for the future where the same webradio may have
            # multiple urls.
            # ans = wrList.addWebradio(self.testdata.getRandomString(), badURI)
            ans = wrList.addWebradio(self.testdata.getRandomString(), badURI[0])
            self.assertRaises(DeejaydError, ans.getContents)

        testWrName = self.testdata.getRandomString()

        # FIXME : provision for the future where the same webradio may have
        # multiple urls.
        # testWrUrls = []
        # for urlCount in range(self.testdata.getRandomInt(10)):
        #     testWrUrls.append('http://' + self.testdata.getRandomString(50))
        testWrUrls = 'http://' + self.testdata.getRandomString(50)

        ans = wrList.addWebradio(testWrName, testWrUrls)
        self.failUnless(ans.getContents())

        wrList = self.deejaydaemon.getWebradios()

        # FIXME : This should not be, see the future of webradios.
        testWrName += '-1'

        self.failUnless(testWrName in self.deejaydaemon.getWebradios().names())

        retrievedWr1 = wrList.getWebradio(testWrName)
        retrievedWr2 = self.deejaydaemon.getWebradios().getWebradio(testWrName)

        for retrievedWr in [retrievedWr1, retrievedWr2]:
            # FIXME : Same provision for the future.
            # for url in testWrUrls:
            #     self.failUnless(url in retrievedWr['Url'])
            self.assertEqual(testWrUrls, retrievedWr['Url'])

        wrList.deleteWebradio(testWrName)
        wrList = self.deejaydaemon.getWebradios()
        self.failIf(testWrName in wrList.names())


# vim: ts=4 sw=4 expandtab
