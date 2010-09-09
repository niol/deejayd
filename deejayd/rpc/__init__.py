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

from deejayd.interfaces import DeejaydError

# Deejayd protocol version number
DEEJAYD_PROTOCOL_VERSION = 4

# from specification
# http://groups.google.com/group/json-rpc/web/json-rpc-1-2-proposal
NOT_WELLFORMED_ERROR  = -32700
INVALID_JSONRPC       = -32600
METHOD_NOT_FOUND      = -32601
INVALID_METHOD_PARAMS = -32602
INTERNAL_ERROR        = -32603
METHOD_NOT_CALLABLE   = -32604


class Fault(DeejaydError):
    """Indicates an JSON-RPC fault package."""
    def __init__(self, code, message):
        super(Fault, self).__init__()
        self.code = code
        self._message = message

# vim: ts=4 sw=4 expandtab
