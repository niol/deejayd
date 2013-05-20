#!/usr/bin/env python

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

"""
Use to create documentation of the protocol
"""

# init translation
import gettext, inspect
from deejayd.ui.i18n import DeejaydTranslations
try: t = gettext.translation("deejayd", class_=DeejaydTranslations)
except IOError:
    t = DeejaydTranslations()
t.install()

from deejayd.mediafilters import *
from deejayd.jsonrpc import interfaces
from deejayd.jsonrpc.jsonbuilders import JSONRPCResponse, JSONRPCRequest,\
                                         DeejaydJSONSignal

common_request = [
        {"prefix": "", "desc": "General Commands",\
                       "object": interfaces.CoreModule},
        {"prefix": "introspection.", "desc": "Introspection Commands",\
                       "object": interfaces.IntrospectionModule},
        {"prefix": "player.", "desc": "Player Commands",\
                       "object": interfaces.PlayerModule},
        {"prefix": "audiolib.", "desc": "Audio Library Commands",\
                       "object": interfaces.LibraryModule},
        {"prefix": "videolib.", "desc": "Video Library Commands",\
                       "object": interfaces.LibraryModule},
        {"prefix": "playlist.", "desc": "Playlist Mode Commands",\
                       "object": interfaces.PlaylistSourceModule},
        {"prefix": "panel.", "desc": "Panel Mode Commands",\
                       "object": interfaces.PanelSourceModule},
        {"prefix": "video.", "desc": "Video Mode Commands",\
                       "object": interfaces.VideoSourceModule},
        {"prefix": "webradio.", "desc": "Webradio Mode Commands",\
                       "object": interfaces.WebradioSourceModule},
        {"prefix": "dvd.", "desc": "Dvd Mode Commands",\
                       "object": interfaces.DvdSourceModule},
        {"prefix": "queue.", "desc": "Queue Commands",\
                       "object": interfaces.QueueModule},
        {"prefix": "recpls.", "desc": "Recorded Playlist Commands",\
                       "object": interfaces.RecordedPlaylistModule},
        {"prefix": "signal.", "desc": "Signal commands",
                       "object": interfaces.SignalModule},
    ]

class WikiFormat:

    def commandDoc(self):
        return """
As written in specification, request is like that :
{{{
`%(request)s`
}}}

""" % {
    "request": JSONRPCRequest("method_name",\
                          ["params1", "params2"], id="id").to_pretty_json(),\
    }

    def answerDoc(self):
        return """
As written in specification, response is like that :
{{{
%s
}}}

For deejayd, result parameter has always the same syntax :
{{{
`{
    "type": answer_type,
    "answer": the real answer value
}`
}}}
With response types equals to:
    * ack
    * list
    * dict
    * mediaList
    * dvdInfo
    * fileAndDirList
""" % JSONRPCResponse("deejayd_response", "id").to_pretty_json()

    def formatSectionDoc(self, section):
        cmds = []
        for c_name in dir(section["object"]):
            if not c_name.startswith("__"):
                try: c = getattr(section["object"], c_name)
                except AttributeError:
                    continue
                if inspect.isclass(c): cmds.append(c)
        return """
=== `%(section)s` ===

%(commands)s
""" % {
        "section": section["desc"],
        "commands": "\n\n".join(map(self.formatCommandDoc, cmds,\
                        [section["prefix"] for i in range(len(cmds))])),
    }

    def formatCommandDoc(self, cmd, prefix = ""):
        args = ''

        command_args = getattr(cmd, "args", [])
        for arg in command_args:
            props = []

            # An argument is optional by default
            if 'req' not in arg.keys():
                arg['req'] = False
            if arg['req']:
                props.append('Mandatory')
            else:
                props.append('Optional')

            args += "  * {{{%(name)s}}} (%(props)s) : %(type)s\n"\
                        % { 'name':  arg['name'],
                            'props': ' and '.join(props),
                            'type' : arg['type'] }

        if len(command_args) == 0:
            args = "  * ''This command does not accept any argument.''\n"

        rvalues = None
        try:
            if isinstance(cmd.answer, list):
                rvalues = cmd.answer
            else:
                rvalues = [cmd.answer]
        except AttributeError:
            rvalues = ['ack']

        return """==== `%(name)s` ====

%(desc)s

Arguments :
%(args)s
Expected return value : ''`%(rvalues)s`''

""" % { 'name'    : prefix+cmd.__name__,
        'desc'    : cmd.__doc__.strip('\n'),
        'args'    : args,
        'rvalues' : rvalues }

    def build(self, sections):
        filter = And(Equals("artist", "artist_name"),\
                Or(Contains("genre", "Rock"), Higher("Rating", "4")))
        signal = DeejaydSignal("signal_name", {"attr1": "value1"})
        return """= deejayd - JSON-RPC Protocol =

Deejayd protocol follows JSON-RPC 1.0 specification available
[http://json-rpc.org/wiki/specification here].
All data between the client and server is encoded in UTF-8.

== Commands Format ==

%(cmd_format)s

== Response Format ==

%(answer)s

== Separator ==

Commands and Responses always finish with the separator `ENDJSON\\n`.
So a command is interpreted by deejayd server only if it finish with this
separator.

== Specific Objects ==

=== Mediafilter Objects ===

Mediafilter object has been serialized in a specific way to be passed as
an method argument or receive with an answer. An example is given here.
{{{
`%(filter)s`
}}}

=== Sort Objects ===

Sort object has been serialized in a specific way to be passed as
an method argument or receive with an answer. An example is given here.
{{{
`[["tag1", "ascending"], ["tag2", "descending"]]`
}}}

Possible sort values are : "ascending" and "descending".

=== Signal Objects ===

Signal is available for TCP connection only.
Signal object has been serialized in a specific way to be send to client.
An example is given here.
{{{
`%(signal)s`
}}}

== Common Available Commands ==

%(commands)s

""" % {
        "cmd_format": self.commandDoc(),
        "answer": self.answerDoc(),
        "filter": filter.to_json(),
        "commands": "\n\n".join(map(self.formatSectionDoc, sections)),
        "signal": DeejaydJSONSignal(signal).to_pretty_json(),
    }

if __name__ == "__main__":
    docs = WikiFormat().build(common_request)

    f = open("doc/deejayd_rpc_protocol","w")
    try: f.write(docs)
    finally: f.close()


# vim: ts=4 sw=4 expandtab
