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

from twisted.python import reflect
from deejayd.model.state import PersistentState
from deejayd import jsonrpc as jsonrpclib
from deejayd.signals import SIGNALS

class JSONRpcComponent(object):
    separator = '.'

    def __init__(self):
        super(JSONRpcComponent, self).__init__()
        self.sub_handlers = {}

    def put_sub_handler(self, prefix, handler):
        self.sub_handlers[prefix] = handler

    def get_sub_handler(self, prefix):
        return self.sub_handlers.get(prefix, None)

    def get_sub_handler_prefixes(self):
        return self.sub_handlers.keys()

    def get_function(self, function_path):
        """Given a string, return a function, or raise jsonrpclib.Fault.

        This returned function will be called, and should return the result
        of the call, a Deferred, or a Fault instance.

        Override in subclasses if you want your own policy. The default
        policy is that given functionPath 'foo', return the method at
        self.jsonrpc_foo, i.e. getattr(self, "jsonrpc_" + functionPath).
        If functionPath contains self.separator, the sub-handler for
        the initial prefix is used to search for the remaining path.
        """
        if function_path.find(self.separator) != -1:
            prefix, function_path = function_path.split(self.separator, 1)
            handler = self.get_sub_handler(prefix)
            if handler is None:
                raise jsonrpclib.Fault(jsonrpclib.METHOD_NOT_FOUND,
                    "no such sub-handler %s" % prefix)
            return handler.get_function(function_path)

        f = getattr(self, "jsonrpc_%s" % function_path, None)
        if not f:
            raise jsonrpclib.Fault(jsonrpclib.METHOD_NOT_FOUND,
                "function %s not found" % function_path)
        elif not callable(f):
            raise jsonrpclib.Fault(jsonrpclib.METHOD_NOT_CALLABLE,
                "function %s not callable" % function_path)
        else:
            return f

    def list_functions(self):
        """Return a list of the names of all jsonrpc methods."""
        return reflect.prefixedMethodNames(self.__class__, 'jsonrpc_')

class SignalingComponent(object):

    def dispatch_signame(self, signal_name, **kwargs):
        signal = SIGNALS[signal_name]
        signal.send(sender=self, **kwargs)

class PersistentStateComponent(object):
    state_name = ""
    initial_state = {}

    def load_state(self):
        st_name = self.state_name == "" and "%s_state" % self.name \
                or self.state_name
        self.state = PersistentState.load_from_db(st_name, self.initial_state)

    def close(self):
        self.state.save()

# vim: ts=4 sw=4 expandtab
