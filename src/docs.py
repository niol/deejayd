#!/usr/bin/env python

# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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

from deejayd.net import commandsXML
from testdeejayd.xmldatabuilder import DeejaydXMLSampleFactory


class DeejaydXMLDocFactory(DeejaydXMLSampleFactory):

    def formatResponseDoc(self, response):
        info = {}
        info['type'] = response.response_type
        info['desc'] = response.__doc__
        info['example'] = self.get_sample_answer(response).to_pretty_xml()

        responseDoc = """
  * '''`%(type)s`''' : %(desc)s
{{{
%(example)sENDXML
}}}""" % info

        return responseDoc

    def formatCombinedResponse(self):
        combi = self.getAck()
        self.set_mother(combi)
        combiFact = DeejaydXMLDocFactory()
        combiFact.set_mother(combi)
        vl = combiFact.getMediaList()
        return combi.to_pretty_xml()


def headerXMLCommands(xml_doc_builder):
    return """= deejayd - XML Protocol =

All data between the client and server is encoded in UTF-8.

== Commands Format ==

{{{
%s
ENDXML
}}}

{{{ENDXML}}} is used as command delimiter.

For certain commands, you may need to pass several values as an argument. If
so, you have to set the argument type to {{{multiple}}} instead of {{{single}}}.

== Response Format ==

{{{ENDXML}}} is also used as an answer delimiter.
""" % xml_doc_builder.get_sample_command('cmdName1').to_pretty_xml()

commandsOrders  = ("close", "ping", "status", "stats", "setMode", "getMode",
                   "audioUpdate", "videoUpdate", "getAudioDir", "audioSearch",
                   "getVideoDir", "playToggle", "goto", "stop", "next",
                   "previous", "setVolume", "seek", "setOption", "current",
                   "setPlayerOption", "staticPlaylistInfo",
                   "staticPlaylistAdd", "playlistInfo", "playlistList",
                   "playlistAdd", "playlistRemove", "playlistClear",
                   "playlistMove", "playlistShuffle", "playlistErase",
                   "playlistLoad", "playlistSave", "webradioList",
                   "webradioAdd", "webradioRemove", "webradioClear",
                   "queueInfo", "queueAdd", "queueMove", "queueLoadPlaylist",
                   "queueRemove", "queueClear", "setvideo","videoInfo",
                   "dvdLoad","dvdInfo",
                   "setSubscription", "setMediaRating", "mediadbList")

# Check for missing commands in commandsOrder
missingCmdsInOrderredList = []
for cmdName in commandsXML.commands.keys():
    if cmdName not in commandsOrders:
        missingCmdsInOrderredList.append(cmdName)
if len(missingCmdsInOrderredList) > 0:
    import sys
    sys.exit("Please order the documentation of the following commands : %s."
             % ', '.join(missingCmdsInOrderredList))


def formatCommandDoc(cmd):
    args = ''

    command_args = None
    try:
        command_args = cmd.command_args
    except AttributeError:
        command_args = []

    for arg in command_args:
        props = []

        # An argument is simple by default
        if 'mult' not in arg.keys():
            arg['mult'] = False
        if arg['mult']:
            props.append('Multiple')
        else:
            props.append('Simple')

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
        if isinstance(cmd.command_rvalue, list):
            rvalues = cmd.command_rvalue
        else:
            rvalues = [cmd.command_rvalue]
    except AttributeError:
        rvalues = ['Ack']

    return """=== `%(name)s` ===

%(desc)s

Arguments :
%(args)s
Expected return value : ''`%(rvalues)s`''

""" % { 'name'    : cmd.command_name,
        'desc'    : cmd.__doc__.strip('\n'),
        'args'    : args,
        'rvalues' : ' or '.join(rvalues) }


def formatCmdDoc(name, cmdObj):
    infos = cmdObj("", None, []).docInfos()
    # Args
    argsText = ""
    if "args" in infos:
        for arg in infos["args"]:
            req = arg["req"] and "true" or "false"
            mult = "false"
            if "mult" in arg: mult = arg["mult"]

            argsText += "%s : type->%s, required->%s\n" %\
                    (arg["name"],arg["type"],req)

    return """
-----------------
%(name)s
-----------------
arguments :
%(args)s
description :
%(descr)s
    """ % {"name":name,
           "args":argsText,
           "descr":infos["description"].strip("\n")
    }


if __name__ == "__main__":
    xml_doc_builder = DeejaydXMLDocFactory()

    # XML Doc
    docs = headerXMLCommands(xml_doc_builder)

    docs += """
There are 6 response types :"""

    for response in xml_doc_builder.response_types:
        docs += xml_doc_builder.formatResponseDoc(response)

    docs += """
Responses may be combined in the same physical message :
{{{
%s
}}}""" % xml_doc_builder.formatCombinedResponse()

    docs += """

== Available Commands ==

"""
    for cmd in commandsOrders:
        docs += formatCommandDoc(commandsXML.commands[cmd])

    f = open("doc/deejayd_xml_protocol","w")
    try: f.write(docs)
    finally: f.close()


# vim: ts=4 sw=4 expandtab
