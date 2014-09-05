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
from testdeejayd import TestCaseWithData
from deejayd.jsonrpc.mediafilters import *
from deejayd.jsonrpc.jsonbuilders import JSONRPCRequest, JSONRPCResponse,\
                                        DeejaydJSONSignal

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
        self.assertEqual(trim_json(filter.to_json_str()), \
                         trim_json(expected_answer))

    def test_signal_builder(self):
        """ test JSON-RPC Signal building """
        expected_answer = """{"answer":
            {"name": "signal_name",
             "attrs": {"attr2": 22, "attr1": "value1"}},
            "type": "signal"}"""
        s = DeejaydJSONSignal("signal_name", {"attr1": "value1", "attr2": 22})
        self.assertEqual(trim_json(s.to_json()), trim_json(expected_answer))

# vim: ts=4 sw=4 expandtab
