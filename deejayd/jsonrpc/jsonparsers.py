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

import json
from deejayd import DeejaydError
from deejayd.jsonrpc import Fault, NOT_WELLFORMED_ERROR
from deejayd.db.models import And, Or, Equals, NotEquals, Contains, In
from deejayd.db.models import StartsWith


BASIC_FILTERS = {
    "equals": Equals,
    "in": In,
    "notequals": NotEquals,
    "contains": Contains,
    "startswith": StartsWith
}

COMPLEX_FILTERS = {
    "and": And,
    "or": Or
}


def loads_request(string, **kws):
    err = Fault(NOT_WELLFORMED_ERROR, "Bad json-rpc request")

    try:
        unmarshalled = json.loads(string, **kws)
    except ValueError:
        raise err

    if (isinstance(unmarshalled, dict)):
        for key in ("method", "params", "id"):
            if key not in unmarshalled:
                raise err
        return unmarshalled
    raise err


def loads_response(string, **kws):
    err = Fault(NOT_WELLFORMED_ERROR, "Bad json-rpc response")

    try:
        ans = json.loads(string, **kws)
    except ValueError:
        raise err

    for key in ("error", "result", "id"):
        if key not in ans:
            raise err
    return ans


def load_mediafilter(json_filter):
    try:
        name = json_filter["id"]
        f_type = json_filter["type"]
        if f_type == "basic":
            filter_class = BASIC_FILTERS[name]
            ft = filter_class(json_filter["value"]["tag"],
                              json_filter["value"]["pattern"])
        elif f_type == "complex":
            ft = COMPLEX_FILTERS[name]()
            for f in json_filter["value"]:
                ft.combine(load_mediafilter(f))
        else:
            raise TypeError
        return ft
    except Exception as err:
        raise DeejaydError(_("%s is not a json encoded "
                             "filter: %s") % (json_filter, err))
