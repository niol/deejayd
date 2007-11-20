"""Deejayd XML protocol parsing and generation testing"""
# -*- coding: utf-8 -*-

from testdeejayd import TestCaseWithData
import testdeejayd.data

from deejayd.net.client import DeejaydXMLCommand, _DeejayDaemon,\
                               DeejaydAnswer, DeejaydKeyValue,\
                               DeejaydFileList, DeejaydMediaList,\
                               DeejaydPlaylist, DeejaydError
from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory

# FIXME : We should not need those here, this is some code duplication from the
# client code.
from StringIO import StringIO

import re, unittest

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

        self.assertEqual(self.trimXML(cmd.to_xml()),\
            self.trimXML(expectedAnswer))


class TestAnswerParser(TestCaseWithData):
    """Test the Deejayd client library answer parser"""

    def setUp(self):
        TestCaseWithData.setUp(self)
        self.deejayd = _DeejayDaemon()

    def parseAnswer(self, str):
        self.deejayd._build_answer(StringIO(str))

    def testAnswerParserAck(self):
        """Test the client library parsing an ack answer"""

        originatingCommand = 'ping'
        ackAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="Ack"/>
</deejayd>""" % originatingCommand

        ans = DeejaydAnswer()
        self.deejayd.expected_answers_queue.put(ans)
        self.parseAnswer(ackAnswer)

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
        self.deejayd.expected_answers_queue.put(ans)
        self.parseAnswer(errorAnswer)

        self.assertEqual(ans.get_originating_command(), originatingCommand)
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
        self.deejayd.expected_answers_queue.put(ans)
        self.parseAnswer(keyValueAnswer)

        self.assertEqual(ans.get_originating_command(), originatingCommand)
        retrievedKeyValues = ans.get_contents()

        for key in origKeyValue.keys():
            self.assertEqual(origKeyValue[key], retrievedKeyValues[key])

    def testAnswerFileAndDirList(self):
        """Test the client library parsing a file/dir list answer"""
        originatingCommand = self.testdata.getRandomString()

        fileListAnswer_noroot = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="FileAndDirList">""" % originatingCommand

        fileListAnswer_root = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response directory="%s" name="%s" type="FileAndDirList">"""\
            % (self.testdata.getRandomString(), originatingCommand)

        for fileListAnswer in [fileListAnswer_noroot, fileListAnswer_root]:
            howMuch = self.testdata.getRandomInt(50)
            origFiles = []
            origDirs = []

            for count in range(howMuch):

                if self.testdata.getRandomElement(['file',
                                                   'directory']) == 'file':
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
            self.deejayd.expected_answers_queue.put(ans)
            self.parseAnswer(fileListAnswer)

            self.assertEqual(ans.get_originating_command(), originatingCommand)

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

        ans = DeejaydMediaList()
        self.deejayd.expected_answers_queue.put(ans)
        self.parseAnswer(webradioListAnswer)

        self.assertEqual(ans.get_originating_command(), originatingCommand)

        for webradio in origWebradios:
            self.failUnless(webradio in ans.get_medias())


class TestAnswerBuilder(TestCaseWithData):
    """Test answer building"""

    def setUp(self):
        TestCaseWithData.setUp(self)
        self.ans_factory = DeejaydXMLAnswerFactory()

    def test_answer_parser_unicode(self):
        """Test that answers may be loaded with unicode"""
        ml = self.ans_factory.get_deejayd_xml_answer('MediaList',
                                     self.testdata.getRandomString())
        ml.set_mediatype(self.testdata.getRandomString())
        ml.set_medias(self.testdata.sampleLibrary)
        self.failUnless(ml.to_xml())


# vim: ts=4 sw=4 expandtab
