"""Deejayd Client library testing"""
# -*- coding: utf-8 -*-

from testdeejayd import TestCaseWithData, TestCaseWithMediaData
import testdeejayd.data

from testdeejayd.server import TestServer
from deejayd.net.client import DeejayDaemon, DeejaydXMLCommand, _AnswerFactory,\
                               DeejaydAnswer, DeejaydKeyValue,\
                               DeejaydFileList, DeejaydWebradioList,\
                               DeejaydPlaylist, DeejaydError

# FIXME : We should not need those here, this is some code duplication from the
# client code.
from Queue import Queue
from StringIO import StringIO
from xml.sax import make_parser

import re, unittest, threading

class TestCommandBuildParse(unittest.TestCase):
    """Test the Deejayd client library command building"""

    def trimXML(self, xml):
        return re.sub('(\s{2,})|(\\n)','', xml)

    def testCommandBuilder(self):
        """Client library builds commands according to protocol scheme"""
        cmd = DeejaydXMLCommand('command1')
        cmd.add_simple_arg('argName1', 'bou')
        cmd.add_simple_arg('argName2', 'bou2')
        cmd.add_simple_arg('argName3', ['bou2', 'haha', 'aza'])
        cmd.add_simple_arg('argName4', 'bou3')
        cmd.add_simple_arg('argName5', ['bou2', 'hihi', 'aza'])

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

        self.assertEqual(self.trimXML(cmd.to_xml()),self.trimXML(expectedAnswer))


class TestAnswerParser(TestCaseWithData):
    """Test the Deejayd client library answer parser"""

    def setUp(self):
        TestCaseWithData.setUp(self)

        self.eansq = Queue()
        self.parser = make_parser()
        self.ansb = _AnswerFactory(self.eansq)
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

        self.assertEqual(self.ansb.get_originating_command(), originatingCommand)
        self.failUnless(ans.get_contents())

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

        self.assertEqual(self.ansb.get_originating_command(), originatingCommand)
        # FIXME : find a way to test the errorText
        self.assertRaises(DeejaydError, ans.get_contents)

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

        self.assertEqual(self.ansb.get_originating_command(), originatingCommand)
        retrievedKeyValues = ans.get_contents()

        for key in origKeyValue.keys():
            self.assertEqual(origKeyValue[key], retrievedKeyValues[key])

    def testAnswerFileAndDirList(self):
        """Test the client library parsing a file/dir list answer"""
        originatingCommand = self.testdata.getRandomString()
        fileListAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="FileAndDirList">""" % originatingCommand
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

        self.assertEqual(self.ansb.get_originating_command(), originatingCommand)

        for file in origFiles:

            # Find corresponding file in retrieved files
            filesIter = iter(ans.get_files())
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
            self.failUnless(dir in ans.get_directories())

    def testAnswerParserMediaList(self):
        """Test the client library parsing a media list answer"""
        originatingCommand = 'webradioList'
        webradioListAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="MediaList">""" % originatingCommand
        howMuch = self.testdata.getRandomInt(50)
        origWebradios = []

        for count in range(howMuch):

            webradioListAnswer = webradioListAnswer + """
        <media type="webradio">"""
            howMuchParms = self.testdata.getRandomInt()
            webradio = {}
            for parmCount in range(howMuchParms):
                name = self.testdata.getRandomString()
                value =  self.testdata.getRandomString()
                webradio[name] = value
                webradioListAnswer = webradioListAnswer + """
            <parm name="%s" value="%s" />""" % (name, value)
            webradioListAnswer = webradioListAnswer + """
        </media>"""
            origWebradios.append(webradio)

        webradioListAnswer = webradioListAnswer + """
    </response>
</deejayd>"""

        ans = DeejaydWebradioList()
        self.eansq.put(ans)
        self.parseAnswer(webradioListAnswer)

        self.assertEqual(self.ansb.get_originating_command(),
                         originatingCommand)

        for webradio in origWebradios:
            self.failUnless(webradio in ans.get_contents())


class TestClient(TestCaseWithMediaData):
    """Completely test the DeejaydClient library"""

    def setUp(self):
        TestCaseWithMediaData.setUp(self)
        self.testdata.build_audio_library_directory_tree()

        # Set up the test server
        testServerPort = 23344
        dbfilename = '/tmp/testdeejayddb-' +\
                     self.testdata.getRandomString() + '.db'
        self.testserver = TestServer(testServerPort,
                                     self.testdata.getRootDir(), dbfilename)
        self.testserver.start()

        # Instanciate the server object of the client library
        self.deejaydaemon = DeejayDaemon(False)
        self.deejaydaemon.connect('localhost', testServerPort)

    def testPing(self):
        """Ping server"""
        self.failUnless(self.deejaydaemon.ping().get_contents())

    def testPingAsync(self):
        """Ping server asynchroneously"""
        self.deejaydaemon.set_async(True)
        ans = self.deejaydaemon.ping()
        self.failUnless(ans.get_contents(),
                        'Server did not respond well to ping.')
        self.deejaydaemon.set_async(False)

    def test_answer_callback(self):
        """Ping server asynchroneously and check for the callback to be triggered"""
        cb_called = threading.Event()
        def tcb(answer):
            cb_called.set()

        self.deejaydaemon.set_async(True)

        ans = self.deejaydaemon.ping()
        ans.add_callback(tcb)
        cb_called.wait()
        self.failUnless(cb_called.isSet(), 'Answer callback was not triggered.')

        self.deejaydaemon.set_async(False)

    def tearDown(self):
        self.deejaydaemon.disconnect()
        self.testserver.stop()
        TestCaseWithMediaData.tearDown(self)

    def testSetMode(self):
        """Test setMode command"""

        # ask an unknown mode
        mode_name = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, self.deejaydaemon.set_mode, mode_name) 

        # ask a known mode
        known_mode = 'playlist'
        ans = self.deejaydaemon.set_mode(known_mode)
        self.failUnless(ans.get_contents(),
                        'Server did not respond well to setMode command.')

        # Test if the mode has been set
        status = self.deejaydaemon.get_status()
        self.assertEqual(status['mode'], known_mode)

    def testPlaylistSaveRetrieve(self):
        """Save a playlist and try to retrieve it."""

        pl = []
        djplname = self.testdata.getRandomString()

        # Get current playlist
        djpl = self.deejaydaemon.get_current_playlist()
        self.assertEqual(djpl.get_contents(), [])

        # Add songs to playlist
        howManySongs = 3
        for songPath in self.testdata.getRandomSongPaths(howManySongs):
            pl.append(songPath)
            self.failUnless(djpl.add_song(songPath).get_contents())

        # Check for the playlist to be of appropriate length
        self.assertEqual(self.deejaydaemon.get_status()['playlistlength'],
                         howManySongs)

        # Save the playlist
        self.failUnless(djpl.save(djplname).get_contents())

        # Check for the saved playslit to be available
        retrievedPls = self.deejaydaemon.get_playlist_list().get_contents()
        self.failUnless(djplname in [p["name"] for p in retrievedPls])

        # Retrieve the saved playlist
        retrievedPl = self.deejaydaemon.get_playlist(djplname)
        for song_nb in range(len(pl)):
            self.assertEqual(pl[song_nb], retrievedPl[song_nb]['path'])

    def testWebradioAddRetrieve(self):
        """Save a webradio and check it is in the list, then delete it."""

        wrList = self.deejaydaemon.get_webradios()

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],
                       ['http://' +\
                        self.testdata.getRandomString(50) + '.pls']]:
            self.assertRaises(DeejaydError, wrList.add_webradio,
                                            self.testdata.getRandomString(),
                                            badURI[0])
            # FIXME : provision for the future where the same webradio may have
            # multiple urls.
            #                                 badURI)


        testWrName = self.testdata.getRandomString()

        # FIXME : provision for the future where the same webradio may have
        # multiple urls.
        # testWrUrls = []
        # for urlCount in range(self.testdata.getRandomInt(10)):
        #     testWrUrls.append('http://' + self.testdata.getRandomString(50))
        testWrUrls = 'http://' + self.testdata.getRandomString(50)

        ans = wrList.add_webradio(testWrName, testWrUrls)
        self.failUnless(ans.get_contents())

        wrList = self.deejaydaemon.get_webradios()

        # FIXME : This should not be, see the future of webradios.
        testWrName += '-1'

        self.failUnless(testWrName in self.deejaydaemon.get_webradios().names())

        retrievedWr1 = wrList.get_webradio(testWrName)
        retrievedWr2 = self.deejaydaemon.get_webradios().\
                                                    get_webradio(testWrName)

        for retrievedWr in [retrievedWr1, retrievedWr2]:
            # FIXME : Same provision for the future.
            # for url in testWrUrls:
            #     self.failUnless(url in retrievedWr['Url'])
            self.assertEqual(testWrUrls, retrievedWr['url'])

        wrList.delete_webradio(testWrName)
        wrList = self.deejaydaemon.get_webradios()
        self.failIf(testWrName in wrList.names())


# vim: ts=4 sw=4 expandtab
