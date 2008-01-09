# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

import sys
from twisted.application import service, internet
from twisted.internet import protocol
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET

from deejayd.ui import log
from deejayd.net import commandsXML

class DeejaydProtocol(LineReceiver):

    def __init__(self, deejayd_core):
        self.delimiter = "ENDXML\n"
        self.MAX_LENGTH = 40960
        self.deejayd_core = deejayd_core

    def connectionMade(self):
        from deejayd import __version__
        self.cmdFactory = CommandFactory(self.deejayd_core)
        self.transport.write("OK DEEJAYD %s\n" % (__version__,))

    def connectionLost(self, reason=ConnectionDone):
        pass

    def lineReceived(self, line):
        line = line.strip("\r")
        # DEBUG Informations
        log.debug(line)

        remoteCmd = self.cmdFactory.createCmdFromXML(line)
        rsp = remoteCmd.execute()
        if isinstance(rsp, unicode):
            rsp = rsp.encode("utf-8")
        # DEBUG Informations
        log.debug(rsp)

        self.transport.write(rsp + self.delimiter)
        if 'close' in remoteCmd.commands:
            self.transport.loseConnection()

    def lineLengthExceeded(self, line):
        log.err(_("Request too long, close the connection"))
        self.transport.loseConnection()


class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol
    obj_supplied = False

    def __init__(self, deejayd_core):
        self.deejayd_core = deejayd_core

    def startFactory(self):
        log.info(_("Net Protocol activated"))

    def buildProtocol(self, addr):
        p = self.protocol(self.deejayd_core)
        p.factory = self
        return p


class CommandFactory:

    def __init__(self, deejayd_core=None):
        self.deejayd_core = deejayd_core

    def createCmdFromXML(self,line):
        queueCmd = commandsXML.queueCommands(self.deejayd_core)

        try: xml_tree = ET.fromstring(line)
        except:
            queueCmd.addCommand('parsing error', commandsXML.UnknownCommand, [])
        else:
            cmds = xml_tree.findall("command")
            for cmd in cmds:
                (cmdName,cmdClass,args) = self.parseXMLCommand(cmd)
                queueCmd.addCommand(cmdName,cmdClass,args)

        return queueCmd

    def parseXMLCommand(self,cmd):
        cmdName = cmd.attrib["name"]
        args = {}
        for arg in cmd.findall("arg"):
            name = arg.attrib["name"]
            type = arg.attrib["type"]
            if type == "simple":
                value = arg.text
            elif type == "multiple":
                value = []
                for val in arg.findall("value"):
                    value.append(val.text)
            args[name] = value

        if cmdName in commandsXML.commands.keys():
            return (cmdName, commandsXML.commands[cmdName], args)
        else: return (cmdName,commandsXML.UnknownCommand,{})

# vim: ts=4 sw=4 expandtab
