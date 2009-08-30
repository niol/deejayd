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

"""Deejayd JSON-RPC protocol testing"""

import re
from testdeejayd import TestCaseWithAudioAndVideoData, TestCaseWithData
from deejayd.mediafilters import *
from deejayd.interfaces import DeejaydSignal
from deejayd.net.client import _DeejayDaemon,\
        DeejaydAnswer, DeejaydKeyValue, DeejaydList,\
        DeejaydFileList, DeejaydMediaList,\
        DeejaydStaticPlaylist, DeejaydError
from deejayd.rpc.jsonbuilders import JSONRPCRequest, JSONRPCResponse,\
                                     Get_json_filter, DeejaydJSONSignal

def trim_json(json):
    return re.sub('(\s{2,})|(\\n)',' ', json)

class TestJSONRPCBuilders(TestCaseWithData):

    def test_request_builder(self):
        """ test JSON-RPC request building """
        cmd = JSONRPCRequest("m_name", ["args1", 2])
        expected_answer = """{"params": ["args1", 2],
                "method": "m_name",
                "id": %d}""" % cmd.get_id()
        self.assertEqual(trim_json(cmd.to_json()), trim_json(expected_answer))

    def test_response_builder(self):
        """ test JSON-RPC response building """
        expected_answer = """{"id": 22,
                "result": {"answer": ["r1", "r2"],
                "type": "type1"}, "error": null}"""
        ans = JSONRPCResponse({"type": "type1", "answer": ["r1", "r2"]}, 22)
        self.assertEqual(trim_json(ans.to_json()), trim_json(expected_answer))

    def test_filter_builder(self):
        """ test JSON-RPC mediafilter building """
        filter = And(Equals("artist", "artist_name"),\
                Or(Contains("genre", "Rock"), Higher("Rating", "4")))
        expected_answer = """{"type": "complex",
            "id": "and",
            "value": [{"type": "basic",
                       "id": "equals",
                       "value": {"pattern": "artist_name", "tag": "artist"}},
                      {"type": "complex",
                       "id": "or",
                       "value": [{"type": "basic",
                                  "id": "contains",
                                  "value": {"pattern": "Rock",
                                            "tag": "genre"}},
                                           {"type": "basic",
                                            "id": "higher",
                                            "value": {"pattern": "4",
                                                      "tag": "Rating"}}]}]}"""
        f = Get_json_filter(filter)
        self.assertEqual(trim_json(f.to_json()), trim_json(expected_answer))

    def test_signal_builder(self):
        """ test JSON-RPC Signal building """
        signal = DeejaydSignal("signal_name", {"attr1": "value1", "attr2": 22})
        expected_answer = """{"answer":
            {"name": "signal_name",
             "attrs": {"attr2": 22, "attr1": "value1"}},
            "type": "signal"}"""
        s = DeejaydJSONSignal(signal)
        self.assertEqual(trim_json(s.to_json()), trim_json(expected_answer))


class TestAnswerParser(TestCaseWithData):
    """Test the Deejayd client library answer parser"""

    def setUp(self):
        super(TestAnswerParser, self).setUp()
        self.deejayd = _DeejayDaemon()

    def parse_answer(self, str):
        self.deejayd._build_answer(str)

    def test_answer_parser_wrongformat(self):
        """Test the client library parsing a wrong format answer"""
        wrong_answer = """{"id": 1,
                "result": {"answer": true,
                "type": "ack"}}"""
        ans = DeejaydAnswer()
        ans.set_id(1)
        self.deejayd.expected_answers_queue.put(ans)
        self.assertRaises(DeejaydError, self.parse_answer, wrong_answer)

    def test_answer_parser_wrongid(self):
        """Test the client library parsing an answer with wrong id"""
        wrongid_answer = """{"id": 1,
                "error": null,
                "result": {"answer": true,
                "type": "ack"}}"""
        ans = DeejaydAnswer()
        ans.set_id(2)
        self.deejayd.expected_answers_queue.put(ans)
        self.assertRaises(DeejaydError, self.parse_answer, wrongid_answer)

    def test_answer_parser_ack(self):
        """Test the client library parsing an ack answer"""
        ack_answer = """{"id": 1,
                "result": {"answer": true,
                "type": "ack"}, "error": null}"""
        ans = DeejaydAnswer()
        ans.set_id(1)
        self.deejayd.expected_answers_queue.put(ans)
        self.parse_answer(ack_answer)

        self.failUnless(ans.get_contents())

    def test_answer_parser_keyvalue(self):
        """Test the client library parsing a key value answer"""
        how_much = 10
        orig_key_value = {}
        for count in range(how_much):
            key = self.testdata.getRandomString()
            value =  self.testdata.getRandomString()
            orig_key_value[key] = value
        key_value_answer = """{"id": 1,
                "error": null,
                "result": {"type": "dict",
                           "answer": {%s}}}""" \
            % ",".join([""" "%s": "%s" """ % (k,v) \
                            for k,v in orig_key_value.items()])

        ans = DeejaydKeyValue()
        ans.set_id(1)
        self.deejayd.expected_answers_queue.put(ans)
        self.parse_answer(key_value_answer)

        retrieved_key_values = ans.get_contents()
        for key in orig_key_value.keys():
            self.assertEqual(orig_key_value[key], retrieved_key_values[key])

    def test_answer_parser_list(self):
        """Test the client library parsing a list answer."""
        how_much = 10
        orig_list = []
        for count in range(how_much):
            item = self.testdata.getRandomString()
            orig_list.append(item)
        list_answer = """{"id": 1,
                "error": null,
                "result": {"type": "list",
                           "answer": [%s]}}""" \
            % ",".join([""" "%s" """ % v for v in orig_list])

        ans = DeejaydList()
        ans.set_id(1)
        self.deejayd.expected_answers_queue.put(ans)
        self.parse_answer(list_answer)
        retrieved_list = ans.get_contents()

        for item in orig_list:
            self.failUnless(item in retrieved_list)

    def test_answer_parser_fileanddir_list(self):
        """Test the client library parsing a file/dir list answer"""
        def dict_to_json(input):
            return """{%s}""" % ",".join([""" "%s": "%s" """ % (k,v)\
                    for k,v in input.items()])

        how_much = self.testdata.getRandomInt(50)
        orig_files, orig_dirs = [], []
        for count in range(how_much):
            if self.testdata.getRandomElement(['file','directory']) == 'file':
                file = {}
                file['id'] = count
                how_much_parms = self.testdata.getRandomInt()
                for parm_count in range(how_much_parms):
                    name = self.testdata.getRandomString()
                    value =  self.testdata.getRandomString()
                    file[name] = value

                orig_files.append(file)
            else:
                dirname = self.testdata.getRandomString()
                orig_dirs.append(dirname)
        fandd_list_answer = """{"id": 1,
                "error": null,
                "result": {"type": "fileAndDirList",
                           "answer": {"type": "song",
                                      "directories": [%(dirs)s],
                                      "files": [%(files)s],
                                      "root": ""}}}""" \
            % {
                "dirs": ",".join([""" "%s" """ % v for v in orig_dirs]),
                "files": ",".join([""" %s """ % dict_to_json(v)\
                                              for v in orig_files]),
            }

        ans = DeejaydFileList()
        ans.set_id(1)
        self.deejayd.expected_answers_queue.put(ans)
        self.parse_answer(fandd_list_answer)

        for file in orig_files:
            # Find corresponding file in retrieved files
            found = False
            for retrieved_file in ans.get_files():
                if file['id'] == int(retrieved_file['id']):
                    found = True
                    break

            for key in file.keys():
                self.failUnless(key in retrieved_file.keys())
                self.assertEqual(unicode(file[key]), retrieved_file[key])

        for dir in orig_dirs:
            self.failUnless(unicode(dir) in ans.get_directories())

    def test_answer_parser_medialist(self):
        """Test the client library parsing a medialist answer"""
        def dict_to_json(input):
            return """{%s}""" % ",".join([""" "%s": "%s" """ % (k,v)\
                    for k,v in input.items()])

        how_much = self.testdata.getRandomInt(50)
        orig_medias = []
        for count in range(how_much):
            media = {}
            media['id'] = count
            how_much_parms = self.testdata.getRandomInt()
            for parm_count in range(how_much_parms):
                name = self.testdata.getRandomString()
                value =  self.testdata.getRandomString()
                media[name] = value
            orig_medias.append(media)

        filter = And(Equals("artist", "artist_name"),\
                Or(Contains("genre", "Rock"), Higher("Rating", "4")))
        json_filter = Get_json_filter(filter)

        medialist_answer = """{"id": 1,
                "error": null,
                "result": {"type": "mediaList",
                           "answer": {"media_type": "song",
                                      "medias": [%(medias)s],
                                      "filter": %(filter)s}}}""" \
            % {
                "filter": json_filter.to_json(),
                "medias": ",".join([""" %s """ % dict_to_json(v)\
                                              for v in orig_medias]),
            }

        ans = DeejaydMediaList()
        ans.set_id(1)
        self.deejayd.expected_answers_queue.put(ans)
        self.parse_answer(medialist_answer)

        for media in orig_medias:
            # Find corresponding media
            found = False
            for retrieved_media in ans.get_medias():
                if media['id'] == int(retrieved_media['id']):
                    found = True
                    break

            for key in media.keys():
                self.failUnless(key in retrieved_media.keys())
                self.assertEqual(unicode(media[key]), retrieved_media[key])

        self.failUnless(ans.is_magic())
        self.failUnless(filter.equals(ans.get_filter()))

    def test_answer_parser_signal(self):
        """Parse a signal message"""
        sig_name = self.testdata.getRandomElement(DeejaydSignal.SIGNALS)
        raw_sig = """{"answer":
            {"name": "%s",
             "attrs": {"attr2": 22, "attr1": "value1"}},
            "type": "signal"}""" % sig_name
        signal_answer = """{"id": null,
                "error": null,
                "result": %s}""" % trim_json(raw_sig)

        # We use a list here as a workaround of python nested scopes
        # limitation : 'sig = None' and then in sig_received() 'sig = signal'
        # would not work.
        sig = []
        def sig_received(signal):
            sig.append(signal)
        self.deejayd.subscribe(sig_name, sig_received)

        self.parse_answer(signal_answer)
        self.assertEqual(sig.pop().get_name(), sig_name)

# vim: ts=4 sw=4 expandtab
