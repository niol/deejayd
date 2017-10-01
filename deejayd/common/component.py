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

from twisted.python import reflect
from deejayd import DeejaydError
from deejayd.db.connection import Session
from deejayd.db.models import State
from deejayd import jsonrpc as jsonrpclib
from deejayd.server.signals import SIGNALS


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
        return list(self.sub_handlers.keys())

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
    initial_state = {}

    def __init__(self):
        self.state = None

    def load_state(self):
        st_name = "%s_state" % self.state_name
        s = Session.query(State) \
                   .filter(State.name == st_name) \
                   .one_or_none()
        if s is None:
            s = State(name=st_name)
            s.state = self.initial_state
            Session.add(s)
            Session.commit()
        self.state = s.state

    def save_state(self):
        if self.state is None:
            raise DeejaydError(_("You try to save a state "
                                 "which has not been loaded !"))
        st_name = "%s_state" % self.state_name
        s = Session.query(State) \
                   .filter(State.name == st_name) \
                   .one()
        s.state = self.state
