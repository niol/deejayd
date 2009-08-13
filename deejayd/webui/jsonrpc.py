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

"""A generic resource for publishing objects via JSON-RPC.
Requires simplejson; can be downloaded from
http://cheeseshop.python.org/pypi/simplejson
"""
from __future__ import nested_scopes

# System Imports
import urlparse

# Sibling Imports
from twisted.web import resource, server
from twisted.internet import defer, protocol, reactor
from twisted.web import http

from deejayd.ui import log
from deejayd.rpc import Fault
from deejayd.rpc.jsonparsers import loads_request
from deejayd.rpc.jsonbuilders import JSONRPCResponse
from deejayd.rpc import protocol as deejayd_protocol


class Handler:
    """Handle a JSON-RPC request and store the state for a request in progress.

    Override the run() method and return result using self.result,
    a Deferred.

    We require this class since we're not using threads, so we can't
    encapsulate state in a running function if we're going  to have
    to wait for results.

    For example, lets say we want to authenticate against twisted.cred,
    run a LDAP query and then pass its result to a database query, all
    as a result of a single JSON-RPC command. We'd use a Handler instance
    to store the state of the running command.
    """

    def __init__(self, resource, *args):
        self.resource = resource # the JSON-RPC resource we are connected to
        self.result = defer.Deferred()
        self.run(*args)

    def run(self, *args):
        # event driven equivalent of 'raise UnimplementedError'
        self.result.errback(NotImplementedError("Implement run() in subclasses"))


class JSONRPC(resource.Resource, deejayd_protocol.DeejaydMainJSONRPC):
    """A resource that implements JSON-RPC.

    Methods published can return JSON-RPC serializable results, Faults,
    Binary, Boolean, DateTime, Deferreds, or Handler instances.

    By default methods beginning with 'jsonrpc_' are published.

    Sub-handlers for prefixed methods (e.g., system.listMethods)
    can be added with putSubHandler. By default, prefixes are
    separated with a '.'. Override self.separator to change this.
    """

    # Error codes for Twisted, if they conflict with yours then
    # modify them at runtime.
    NOT_FOUND = 8001
    FAILURE = 8002

    isLeaf = 1

    def __init__(self, deejayd):
        super(JSONRPC, self).__init__()
        self.subHandlers = {}
        self.deejayd_core = deejayd

    def render(self, request):
        request.content.seek(0, 0)
        # Unmarshal the JSON-RPC data
        content = request.content.read()
        try:
            parsed = loads_request(content)
            args, functionPath = parsed['params'], parsed["method"]
            function = self._getFunction(functionPath)
        except Fault, f:
            try: id = parsed["id"]
            except:
                id = None
            self._cbRender(f, request, id)
        else:
            request.setHeader("content-type", "text/json")
            defer.maybeDeferred(function, *args).addErrback(
                self._ebRender, parsed["id"]
            ).addCallback(
                self._cbRender, request, parsed["id"]
            )
        return server.NOT_DONE_YET

    def _cbRender(self, result, request, id):
        if isinstance(result, Handler):
            result = result.result
        # build json answer
        ans = JSONRPCResponse(result, id).to_json()
        request.setHeader("content-length", str(len(ans)))
        request.write(ans)
        request.finish()

    def _ebRender(self, failure, id):
        if isinstance(failure.value, Fault):
            return failure.value
        log.err(failure)
        return Fault(self.FAILURE, "error")

__all__ = ["JSONRPC", "Handler"]

# vim: ts=4 sw=4 expandtab
