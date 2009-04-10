# -*- coding: utf-8 -*-
# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Deejayd XML protocol parsing and generation testing"""
import re, unittest, random
from StringIO import StringIO

from testdeejayd import XmlTestCase, TestCaseWithData
import testdeejayd.data

from deejayd.mediafilters import *
from deejayd.net.deejaydProtocol import CommandFactory
from deejayd.interfaces import DeejaydSignal
from deejayd.net.client import _DeejayDaemon,\
                               DeejaydAnswer, DeejaydKeyValue, DeejaydList,\
                               DeejaydFileList, DeejaydMediaList,\
                               DeejaydStaticPlaylist, DeejaydError
from deejayd.net.xmlbuilders import DeejaydXMLAnswerFactory,\
                                    DeejaydXMLCommand, DeejaydXMLSignal


def trim_xml(xml):
    return re.sub('(\s{2,})|(\\n)','', xml)


class TestCommandBuildParse(XmlTestCase):
    """Test the Deejayd client library command building"""

    def testCommandBuilder(self):
        """Client library builds commands according to protocol scheme"""
        cmd = self.xmldata.get_sample_command('command1')

        expectedAnswer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <command name="command1">
        <arg name="argName6" type="filter">
            <and>
                <contains tag="artist">Britney</contains>
                <or>
                    <equals tag="genre">Classical</equals>
                    <equals tag="genre">Disco</equals>
                </or>
            </and>
        </arg>
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

        self.assertEqual(trim_xml(cmd.to_xml()), trim_xml(expectedAnswer))

    def test_command_parser(self):
        """Test a command being parsed correctly by the server."""
        cmd_factory = CommandFactory()

        cmd_name = 'status'
        xml_cmd = self.xmldata.get_sample_command(cmd_name).to_xml()
        xml_tree = cmd_factory.tree_from_line(xml_cmd).findall('command')[0]

        cmd_name, cmd_class, cmd_args = cmd_factory.parseXMLCommand(xml_tree)

        self.assertEqual(cmd_name, cmd_name)
        self.assertEqual(cmd_args['argName1'], 'bou')
        self.assertEqual(cmd_args['argName2'], 'bou2')
        self.assertEqual(cmd_args['argName3'], ['bou2', 'haha', 'aza'])
        self.assertEqual(cmd_args['argName4'], 'bou3')
        self.assertEqual(cmd_args['argName5'], ['bou2', 'hihi', 'aza'])

        retrieved_filter = cmd_args['argName6']
        self.assert_filter_matches_sample(retrieved_filter)


class TestAnswerParser(XmlTestCase):
    """Test the Deejayd client library answer parser"""

    def setUp(self):
        super(TestAnswerParser, self).setUp()
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

    def test_answer_parser_list(self):
        """Test the client library parsing a list answer."""
        originating_command = self.testdata.getRandomString()
        list_answer = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <response name="%s" type="List">""" % originating_command
        how_much = 10
        orig_list = []
        for count in range(how_much):
            item = self.testdata.getRandomString()
            orig_list.append(item)
            list_answer = list_answer + """
        <parm name="item" value="%s" />""" % item
        list_answer = list_answer + """
    </response>
</deejayd>"""

        ans = DeejaydList()
        self.deejayd.expected_answers_queue.put(ans)
        self.parseAnswer(list_answer)
        retrieved_list = ans.get_contents()

        for item in orig_list:
            self.failUnless(item in retrieved_list)

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

    def test_answer_parser_MediaList(self):
        """Test the client library parsing a media list answer"""
        originating_command = 'playlistInfo'

        medialist_answer = self.xmldata.getMediaList(originating_command)

        ans = DeejaydMediaList()
        self.deejayd.expected_answers_queue.put(ans)
        self.parseAnswer(medialist_answer.to_xml())

        self.assertEqual(ans.get_originating_command(), originating_command)

        for media_item in medialist_answer.media_items:
            self.failUnless(media_item in ans.get_medias())

        self.failUnless(ans.is_magic())
        self.assert_filter_matches_sample(ans.get_filter())

    def test_answer_parser_signal(self):
        """Parse a signal message"""
        sig_name = random.sample(DeejaydSignal.SIGNALS, 1).pop()
        raw_sig = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <signal name="%s" />
</deejayd>""" % sig_name

        # We use a list here as a workaround of python nested scopes
        # limitation : 'sig = None' and then in sig_received() 'sig = signal'
        # would not work.
        sig = []
        def sig_received(signal):
            sig.append(signal)
        self.deejayd.subscribe(sig_name, sig_received)

        self.parseAnswer(raw_sig)
        self.assertEqual(sig.pop().get_name(), sig_name)


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

    def test_signal_build(self):
        """Test that signals are built and correctly"""
        sig_name = self.testdata.getRandomString()
        sig = DeejaydXMLSignal()
        sig.set_name(sig_name)

        expected_xml = """<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <signal name="%s"/>
</deejayd>""" % sig_name

        self.assertEqual(trim_xml(sig.to_xml()),
                         trim_xml(expected_xml))


# vim: ts=4 sw=4 expandtab
