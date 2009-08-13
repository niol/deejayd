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

import time
from datetime import datetime
try: import json # python 2.6
except ImportError: # if python < 2.6, require simplejson
    import simplejson as json
from deejayd.rpc import *


class JSONRPCEncoder(json.JSONEncoder):
    """
    Provide custom serializers for JSON-RPC.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y%m%dT%H:%M:%S")
        raise TypeError("%r is not JSON serializable" % (obj,))


class _DeejaydJSON:

    def dump(self):
        return self._build_obj()

    def to_json(self):
        return json.dumps(self._build_obj(), cls=JSONRPCEncoder)

    def to_pretty_json(self):
        s = json.dumps(self._build_obj(), sort_keys=True, indent=4)
        return '\n'.join([l.rstrip() for l in  s.splitlines()])


class JSONRPCRequest(_DeejaydJSON):
    """
    Build JSON-RPC Request
    """
    def __init__(self, method_name, params, notification = False, id = None):
        self.method = method_name
        self.params = params
        # use timestamp as id if no id has been given
        self.id = None
        if not notification:
            self.id = id or int(time.time())

    def _build_obj(self):
        return {"method": self.method, "params": self.params, "id": self.id}

    def get_id(self):
        return self.id


class JSONRPCResponse(_DeejaydJSON):
    """
    Build JSON-RPC Response
    """
    def __init__(self, result, id):
        self.id = id
        self.result = result

    def _build_obj(self):
        result, error = self.result, None
        if isinstance(self.result, Fault):
            error = {"code": self.result.code, "message": str(self.result)}
            result = None

        return {"result": result, "error": error, "id": self.id}

    def to_json(self):
        try:
            return json.dumps(self._build_obj(), cls=JSONRPCEncoder)
        except TypeError, ex:
            error = {"code": NOT_WELLFORMED_ERROR, "message": str(ex)}
            obj = {"result": None, "error": error, "id": self.id}
            return json.dumps(obj)

#
# JSON filter serializer
#
class JSONFilter(_DeejaydJSON):

    def __init__(self, filter):
        self.filter = filter

    def _get_value(self):
        raise NotImplementedError

    def _build_obj(self):
        return {
            "type": self.type,
            "id": self.filter.get_identifier(),
            "value": self._get_value(),
            }

class JSONBasicFilter(JSONFilter):
    type = "basic"
    def _get_value(self):
        return {"tag": self.filter.tag, "pattern": self.filter.pattern}

class JSONComplexFilter(JSONFilter):
    type = "complex"
    def _get_value(self):
        return [Get_json_filter(f).dump() for f in self.filter.filterlist]

def Get_json_filter(filter):
    if filter is None:
        return None
    if filter.type == 'basic':
        json_filter_class = JSONBasicFilter
    elif filter.type == 'complex':
        json_filter_class = JSONComplexFilter
    return json_filter_class(filter)

#
# JSON signal serializer
#
class DeejaydJSONSignal(_DeejaydJSON):

    def __init__(self, signal):
        self.name = signal is not None and signal.get_name() or ""
        self.attrs = signal is not None and signal.get_attrs() or {}

    def set_name(self, name):
        self.name = name

    def _build_obj(self):
        return {"type": "signal",\
                "answer": {"name": self.name, "attrs": self.attrs}}

# vim: ts=4 sw=4 expandtab
