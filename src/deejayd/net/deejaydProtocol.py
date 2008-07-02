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

import sys
from twisted.application import service, internet
from twisted.internet import protocol, reactor
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET

from deejayd.interfaces import DeejaydSignal
from deejayd.mediafilters import *
from deejayd.ui import log
from deejayd.net import commandsXML, xmlbuilders

class DeejaydProtocol(LineReceiver):

    def __init__(self, deejayd_core, protocol_manager):
        self.delimiter = "ENDXML\n"
        self.MAX_LENGTH = 40960
        self.deejayd_core = deejayd_core
        self.manager = protocol_manager

    def connectionMade(self):
        from deejayd import __version__
        self.cmdFactory = CommandFactory(self.deejayd_core)
        self.send_buffer("OK DEEJAYD %s\n" % (__version__,), xml=False)

    def connectionLost(self, reason=ConnectionDone):
        self.manager.close_signals(self)

    def lineReceived(self, line):
        line = line.strip("\r")
        # DEBUG Informations
        log.debug(line)

        remoteCmd = self.cmdFactory.createCmdFromXML(line)
        remoteCmd.register_connector(self)
        rsp = remoteCmd.execute()
        self.send_buffer(rsp)

        if 'close' in remoteCmd.commands:
            self.transport.loseConnection()

    def send_buffer(self, buf, xml=True):
        if isinstance(buf, unicode):
            buf = buf.encode("utf-8")
        self.transport.write(buf)
        if xml:
            self.transport.write(self.delimiter)
        log.debug(buf)

    def lineLengthExceeded(self, line):
        log.err(_("Request too long, close the connection"))
        self.transport.loseConnection()

    def set_signaled(self, signal_name):
        self.manager.set_signaled(self, signal_name)

    def set_not_signaled(self, signal_name):
        self.manager.set_not_signaled(self, signal_name)


class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol
    obj_supplied = False

    def __init__(self, deejayd_core):
        self.deejayd_core = deejayd_core
        self.signaled_clients = dict([(signame, []) for signame\
                                                    in DeejaydSignal.SIGNALS])
        self.core_sub_ids = {}

    def startFactory(self):
        log.info(_("Net Protocol activated"))

    def buildProtocol(self, addr):
        p = self.protocol(self.deejayd_core, self)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        for signal_name in DeejaydSignal.SIGNALS:
            self.set_not_signaled(connector, signal_name)

    def set_signaled(self, connector, signal_name):
        client_list =  self.signaled_clients[signal_name]
        if len(client_list) < 1:
            # First subscription for this signal, so subscribe
            sub_id = self.deejayd_core.subscribe(signal_name,
                                                 self.sig_bcast_to_clients)
            self.core_sub_ids[signal_name] = sub_id

        self.signaled_clients[signal_name].append(connector)

    def set_not_signaled(self, connector, signal_name):
        client_list =  self.signaled_clients[signal_name]
        if connector in client_list:
            client_list.remove(connector)
        if len(client_list) < 1:
            # No more clients for this signal, we can unsubscribe
            self.deejayd_core.unsubscribe(self.core_sub_ids[signal_name])

    def close_signals(self, connector):
        for signal_name in self.signaled_clients.keys():
            if len(self.signaled_clients[signal_name]) > 0:
                self.set_not_signaled(connector, signal_name)

    def sig_bcast_to_clients(self, signal):
        interested_clients = self.signaled_clients[signal.get_name()]
        if len(interested_clients) > 0:
            xml_sig = xmlbuilders.DeejaydXMLSignal(signal.get_name())
            for client in interested_clients:
                # http://twistedmatrix.com/pipermail/twisted-python/2007-August/015905.html
                # says : "Don't call reactor methods from any thread except the
                # one which is running the reactor.  This will have
                # unpredictable results and generally be broken."
                # This is the "why" of this weird call instead of a simple
                # client.send_buffer(xml_sig.to_xml()).
                reactor.callFromThread(client.send_buffer, xml_sig.to_xml())


class CommandFactory:

    TAG2BASIC   = dict([(x(None, None).get_xml_identifier(), x)\
                        for x in BASIC_FILTERS])
    TAG2COMPLEX = dict([(x().get_xml_identifier(), x) for x in COMPLEX_FILTERS])

    def __init__(self, deejayd_core=None):
        self.deejayd_core = deejayd_core

    def tree_from_line(self, line):
        return ET.fromstring(line)

    def createCmdFromXML(self,line):
        queueCmd = commandsXML.queueCommands(self.deejayd_core)

        try: xml_tree = self.__tree_from_line(line)
        except:
            queueCmd.addCommand('parsing error', commandsXML.UnknownCommand, [])
        else:
            cmds = xml_tree.findall("command")
            for cmd in cmds:
                (cmdName,cmdClass,args) = self.parseXMLCommand(cmd)
                queueCmd.addCommand(cmdName,cmdClass,args)

        return queueCmd

    def __parse_filter(self, xml_filter):
        filter_xml_name = xml_filter.tag
        if filter_xml_name in CommandFactory.TAG2BASIC.keys():
            filter_class = CommandFactory.TAG2BASIC[filter_xml_name]
            return filter_class(xml_filter.attrib['tag'], xml_filter.text)
        elif filter_xml_name in CommandFactory.TAG2COMPLEX.keys():
            filter_class = CommandFactory.TAG2COMPLEX[filter_xml_name]
            filter_list = [self.__parse_filter(f) for f in xml_filter]
            return filter_class(*filter_list)
        else:
            raise ValueError('Unknwown filter type %s' % filter_xml_name)

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
            elif type == "filter":
                try:
                    if len(arg) != 1:
                        raise ValueError('Only one filter allowed in arg')
                    value = self.__parse_filter(arg[0])
                except ValueError, ex:
                    return (str(ex), commandsXML.UnknownCommand, {})
            args[name] = value

        if cmdName in commandsXML.commands.keys():
            return (cmdName, commandsXML.commands[cmdName], args)
        else: return (cmdName,commandsXML.UnknownCommand,{})


# vim: ts=4 sw=4 expandtab
