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

import sys, traceback
from twisted.application import service, internet
from twisted.internet import protocol, reactor
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver

from deejayd import __version__
from deejayd import DeejaydSignal
from deejayd.ui import log
from deejayd.utils import str_decode
from deejayd.component import JSONRpcComponent
from deejayd.jsonrpc import Fault, DEEJAYD_PROTOCOL_VERSION
from deejayd.jsonrpc.interfaces import jsonrpc_module, TcpModule
from deejayd.jsonrpc.jsonparsers import loads_request
from deejayd.jsonrpc.jsonbuilders import JSONRPCResponse, DeejaydJSONSignal


@jsonrpc_module(TcpModule)
class DeejaydProtocol(LineReceiver, JSONRpcComponent):
    NOT_FOUND = 8001
    FAILURE = 8002
    delimiter = 'ENDJSON\n'

    def __init__(self, deejayd_core, protocol_manager):
        super(DeejaydProtocol, self).__init__()
        self.MAX_LENGTH = 40960
        self.subHandlers = {}
        self.deejayd_core = deejayd_core
        self.manager = protocol_manager

        self.__need_to_close = False

    def connectionMade(self):
        self.send_buffer("OK DEEJAYD %s protocol %d\n" %
                         (__version__, DEEJAYD_PROTOCOL_VERSION, ))

    def connectionLost(self, reason=ConnectionDone):
        self.manager.close_signals(self)

    def lineReceived(self, line):
        line = line.strip("\r")
        # DEBUG Informations
        log.debug(line)

        try:
            parsed = loads_request(line)
            args, function_path = parsed['params'], parsed["method"]
            if function_path.startswith("tcp"):
                # it's a command linked with this tcp connection
                method = function_path.split(self.separator, 1)[1]
                function = self.get_function(method)
            else:
                function = self.deejayd_core.get_function(function_path)
        except Fault, f:
            try: id = parsed["id"]
            except:
                id = None
            ans = JSONRPCResponse(f, id)
        else:
            try: result = function(*args)
            except Exception, ex:
                if not isinstance(ex, Fault):
                    log.err(str_decode(traceback.format_exc()))
                    result = Fault(self.FAILURE, _("error, see deejayd log"))
                else:
                    result = ex
            ans = JSONRPCResponse(result, parsed["id"])

        self.send_buffer(ans.to_json()+self.delimiter)
        if self.__need_to_close:
            self.transport.loseConnection()

    def send_buffer(self, buf):
        if isinstance(buf, unicode):
            buf = buf.encode("utf-8")
        self.transport.write(buf)
        log.debug(buf)

    def lineLengthExceeded(self, line):
        log.err(_("Request too long, close the connection"))
        self.transport.loseConnection()

    #
    # rpc commands linked with a TCP connection
    #
    def set_subscription(self, signal, value):
        if value is False:
            self.manager.set_not_signaled(self, signal)
        elif value is True:
            self.manager.set_signaled(self, signal)

    def close(self):
        self.__need_to_close = True

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
            j_sig = DeejaydJSONSignal(signal)
            ans = JSONRPCResponse(j_sig.dump(), None).to_json()
            for client in interested_clients:
                reactor.callFromThread(client.send_buffer, ans+client.delimiter)

# vim: ts=4 sw=4 expandtab
