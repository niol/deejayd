# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import traceback
from twisted.internet import protocol, reactor
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineReceiver

from deejayd import __version__, DeejaydError
from deejayd.server.signals import SIGNALS
from deejayd.ui import log
from deejayd.common.component import JSONRpcComponent
from deejayd.db.connection import Session
from deejayd.jsonrpc import Fault, DEEJAYD_PROTOCOL_VERSION
from deejayd.jsonrpc.interfaces import jsonrpc_module, SignalModule
from deejayd.jsonrpc.jsonparsers import loads_request
from deejayd.jsonrpc.jsonbuilders import JSONRPCResponse, DeejaydJSONSignal


@jsonrpc_module(SignalModule)
class DeejaydProtocol(LineReceiver, JSONRpcComponent):
    NOT_FOUND = 8001
    FAILURE = 8002
    delimiter = b'ENDJSON\n'

    def __init__(self, deejayd_core):
        super(DeejaydProtocol, self).__init__()
        self.MAX_LENGTH = 40960
        self.subHandlers = {}
        self.deejayd_core = deejayd_core

        self.__need_to_close = False

    def connectionMade(self):
        self.send_buffer("OK DEEJAYD %s protocol %d\n" %
                         (__version__, DEEJAYD_PROTOCOL_VERSION, ))

    def connectionLost(self, reason=ConnectionDone):
        self.factory.close_signals(self)

    def lineReceived(self, line):
        # use str instead of bytes to decode json commands
        # and return answer
        line = line.strip(b"\r").decode("utf-8")
        delimiter = self.delimiter.decode("utf-8")

        try:
            parsed = loads_request(line)
            args, function_path = parsed['params'], parsed["method"]
            if function_path.startswith("signal"):
                # it's a command linked with this connection
                method = function_path.split(self.separator, 1)[1]
                function = self.get_function(method)
            elif function_path == "close":
                function = self.close
            else:
                function = self.deejayd_core.get_function(function_path)
        except Fault as f:
            try:
                r_id = parsed["id"]
            except:
                r_id = None
            ans = JSONRPCResponse(f, r_id)
        else:
            # explicitly init session for this request
            Session()
            try:
                result = function(*args)
                Session.commit()
            except Exception as ex:
                Session.rollback()
                if not isinstance(ex, Fault):
                    log.err(traceback.format_exc())
                    result = Fault(self.FAILURE, _("error, see deejayd log"))
                else:
                    result = ex
            finally:
                Session.remove()
            ans = JSONRPCResponse(result, parsed["id"])

        self.send_buffer(ans.to_json()+delimiter)
        if self.__need_to_close:
            self.transport.loseConnection()
            self.__need_to_close = False

    def send_buffer(self, buf):
        if isinstance(buf, str):
            # twisted expects bytes for the method write
            buf = buf.encode("utf-8")
        self.transport.write(buf)

    def lineLengthExceeded(self, line):
        log.err(_("Request too long, close the connection"))
        self.transport.loseConnection()

    #
    # rpc commands linked with this connection
    #
    def set_subscription(self, signal_name, value):
        if signal_name not in SIGNALS:
            raise DeejaydError(_("Signal %s does not exist") % signal_name)

        if value is False:
            self.factory.set_not_signaled(self, signal_name)
        elif value is True:
            self.factory.set_signaled(self, signal_name)

    def close(self):
        self.__need_to_close = True
        return {"answer": True, "type": "ack"}


class DeejaydFactory(protocol.ServerFactory):
    protocol = DeejaydProtocol
    obj_supplied = False

    def __init__(self, deejayd_core):
        self.deejayd_core = deejayd_core
        self.signaled_clients = dict([(signame, []) for signame in SIGNALS])
        self.core_sub_ids = {}

    def buildProtocol(self, addr):
        p = self.protocol(self.deejayd_core)

        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        for signal_name in SIGNALS:
            self.set_not_signaled(connector, signal_name)

    def set_signaled(self, connector, signal_name):
        client_list =  self.signaled_clients[signal_name]
        if len(client_list) < 1:
            # First subscription for this signal, so subscribe
            receiver = self.sig_bcast_to_clients(signal_name)
            SIGNALS[signal_name].connect(receiver)
            self.core_sub_ids[signal_name] = receiver

        self.signaled_clients[signal_name].append(connector)

    def set_not_signaled(self, connector, signal_name):
        client_list = self.signaled_clients[signal_name]
        if connector in client_list:
            client_list.remove(connector)
        if len(client_list) < 1:
            # No more clients for this signal, we can unsubscribe
            try:
                SIGNALS[signal_name].disconnect(self.core_sub_ids[signal_name])
                del self.core_sub_ids[signal_name]
            except KeyError:
                pass

    def close_signals(self, connector):
        for signal_name in self.signaled_clients:
            if len(self.signaled_clients[signal_name]) > 0:
                self.set_not_signaled(connector, signal_name)

    def sig_bcast_to_clients(self, signal_name):
        def receiver(signal=None, sender=None, **kwargs):
            interested_clients = self.signaled_clients[signal_name]
            if len(interested_clients) > 0:
                j_sig = DeejaydJSONSignal(signal_name, kwargs)
                ans = JSONRPCResponse(j_sig.dump(), None).to_json()
                buf = ans.encode('utf-8') + interested_clients[0].delimiter
                for client in interested_clients:
                    reactor.callFromThread(client.send_buffer, buf)
                    reactor.callFromThread(log.debug, "Send signal ---> "
                                                      "'%s'" % ans)

        return receiver
