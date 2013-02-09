# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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

from deejayd.jsonrpc import *


def loads_request(string, **kws):
    err = Fault(NOT_WELLFORMED_ERROR, "Bad json-rpc request")

    try: unmarshalled = json.loads(string, **kws)
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

    try: ans = json.loads(string, **kws)
    except ValueError:
        raise err

    for key in ("error", "result", "id"):
        if key not in ans:
            raise err
    return ans

# vim: ts=4 sw=4 expandtab