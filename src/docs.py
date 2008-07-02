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
from deejayd.net.xmlbuilders import *

def headerXMLCommands():
    return """= deejayd - XML Protocol =

All data between the client and server is encoded in UTF-8.

== Commands Format ==

{{{
<?xml version="1.0" encoding="utf-8"?>
<deejayd>
    <command name="cmdName1">
        <arg name="argName1" type="simple">value</arg>
        <arg name="argName2" type="multiple">
            <value>value1</value>
            <value>value2</value>
        </arg>
    </command>
    <command name="cmdName2">
        <arg name="argName1" type="simple">value</arg>
        <arg name="argName2" type="multiple">
            <value>value1</value>
            <value>value2</value>
        </arg>
        <arg name="argName6" type="filter">
            <and>
                <contains tag="artist">Britney</contains>
                <or>
                    <equals tag="genre">Classical</equals>
                    <equals tag="genre">Disco</equals>
                </or>
            </and>
        </arg>
    </command>
</deejayd>
ENDXML
}}}

{{{ENDXML}}} is used as command delimiter.

For certain commands, you may need to pass several values as an argument. If
so, you have to set the argument type to {{{multiple}}} instead of {{{single}}}.

== Response Format ==

{{{ENDXML}}} is also used as an answer delimiter.
"""

commandsOrders  = ("close", "ping", "status", "stats", "setMode", "getMode",
                   "audioUpdate", "videoUpdate", "getdir", "search",
                   "getvideodir", "playToggle", "goto", "stop", "next",
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
                   "setSubscription", "setMediaRating")

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


class DeejaydXMLDocFactory(DeejaydXMLAnswerFactory):

    def getSampleParmDict(self, howMuch = 2):
        parmDict = {}
        for i in range(howMuch):
            parmDict['parmName' + str(i)] = 'parmValue' + str(i)
        return parmDict

    def getError(self):
        error = self.get_deejayd_xml_answer('error', 'cmdName')
        error.set_error_text('error text')
        return error

    def getAck(self):
        ack = self.get_deejayd_xml_answer('Ack', 'cmdName')
        return ack

    def getKeyValue(self):
        kv = self.get_deejayd_xml_answer('KeyValue', 'cmdName')
        kv.set_pairs(self.getSampleParmDict())
        return kv

    def getList(self):
        l = self.get_deejayd_xml_answer('List', 'cmdName')
        for i in range(2):
            l.contents.append("item%d" % i)
        return l

    def getFileAndDirList(self):
        fl = self.get_deejayd_xml_answer('FileAndDirList', 'cmdName')
        fl.set_directory('optionnal_described_dirname')
        fl.add_directory('dirName')
        fl.set_filetype('song or video')

        fl.add_file(self.getSampleParmDict())

        return fl

    def getMediaList(self):
        ml = self.get_deejayd_xml_answer('MediaList', 'cmdName')
        ml.set_mediatype("song or video or webradio or playlist")
        ml.add_media(self.getSampleParmDict())
        ml.add_media({"parmName1": "parmValue1", \
            "audio": [{"idx": "0", "lang": "lang1"}, \
                      {"idx": "1", "lang": "lang2"}],\
            "subtitle": [{"idx": "0", "lang": "lang1"}]})
        return ml

    def getDvdInfo(self):
        dvd = self.get_deejayd_xml_answer('DvdInfo', 'cmdName')
        dvd_info = {'title': "DVD Title", "longest_track": 1,\
                    'track':
                      [ {"ix": 1,\
                         "length":"track length",\
                         "audio":[\
                            { 'ix': 0,\
                              'lang': 'lang code'\
                            }],\
                         "subp":[\
                            { 'ix': 0,\
                              'lang': 'lang code'\
                            },\
                            { 'ix': 1,\
                              'lang': 'lang code'\
                            }],\
                         "chapter":[
                            {'ix': 1,\
                             'length': 'chapter length'\
                            }]\
                        },\
                      ],\
                   }
        dvd.set_info(dvd_info)
        return dvd

    responseTypeExBuilders = {
                               DeejaydXMLError: getError,
                               DeejaydXMLAck: getAck,
                               DeejaydXMLKeyValue: getKeyValue,
                               DeejaydXMLList : getList,
                               DeejaydXMLFileDirList: getFileAndDirList,
                               DeejaydXMLDvdInfo: getDvdInfo,
                               DeejaydXMLMediaList: getMediaList,
                             }

    def getExample(self, responseClass):
        builder = self.responseTypeExBuilders[responseClass]
        if builder == None:
            return 'No example available.'
        else:
            return builder(self)

    def formatResponseDoc(self, response):
        info = {}
        info['type'] = response.response_type
        info['desc'] = response.__doc__
        info['example'] = self.getExample(response).to_pretty_xml()

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

if __name__ == "__main__":
    # XML Doc
    docs = headerXMLCommands()

    docs += """
There are 6 response types :"""

    respDocBuilder = DeejaydXMLDocFactory()
    for response in respDocBuilder.response_types:
        docs += respDocBuilder.formatResponseDoc(response)

    docs += """
Responses may be combined in the same physical message :
{{{
%s
}}}""" % respDocBuilder.formatCombinedResponse()

    docs += """

== Available Commands ==

"""
    for cmd in commandsOrders:
        docs += formatCommandDoc(commandsXML.commands[cmd])

    f = open("doc/deejayd_xml_protocol","w")
    try: f.write(docs)
    finally: f.close()

# vim: ts=4 sw=4 expandtab
