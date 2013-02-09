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
import os, re

# Sibling Imports
from twisted.web import resource, server
from twisted.internet import defer

from deejayd import DeejaydError
from deejayd.component import JSONRpcComponent
from deejayd.ui import log
from deejayd.utils import str_decode
from deejayd.model.mediafilters import And
from deejayd.jsonrpc import Fault
from deejayd.jsonrpc.interfaces import jsonrpc_module, WebModule
from deejayd.jsonrpc.jsonparsers import loads_request
from deejayd.jsonrpc.jsonbuilders import JSONRPCResponse


@jsonrpc_module(WebModule)
class WebRpcModule(JSONRpcComponent):

    def __init__(self, core, tmp_dir):
        super(WebRpcModule, self).__init__()
        self.deejayd_core = core
        self._tmp_dir = tmp_dir

    def __find_ids(self, pattern):
        ids = []
        for file in os.listdir(self._tmp_dir):
            if re.compile("^%s-[0-9]+" % pattern).search(file):
                t = file.split("-")[1] # id.ext
                t = t.split(".")
                try : ids.append(int(t[0]))
                except ValueError: pass
        return ids

    def write_cover(self, mid):
        """ Record requested cover in the temp directory """
        try:
            cover = self.deejayd_core.audiolib.get_cover(mid)
        except (TypeError, DeejaydError, KeyError):
            return {"cover": None}

        cover_ids = self.__find_ids("cover")
        ext = cover["mime"] == "image/jpeg" and "jpg" or "png"
        filename = "cover-%s.%s" % (str(cover["id"]), ext)
        if cover["id"] not in cover_ids:
            file_path = os.path.join(self._tmp_dir,filename)
            fd = open(file_path, "w")
            fd.write(cover["cover"])
            fd.close()
            os.chmod(file_path,0644)
            # erase unused cover files
            for id in cover_ids:
                try:
                    os.unlink(os.path.join(self._tmp_dir,\
                            "cover-%s.jpg" % id))
                    os.unlink(os.path.join(self._tmp_dir,\
                            "cover-%s.png" % id))
                except OSError:
                    pass
        return {"cover": os.path.join('tmp', filename), "mime": cover["mime"]}

    def build_panel(self, updated_tag = None):
        """ Build panel list """
        panel = self.deejayd_core.panel
        library = self.deejayd_core.audiolib

        medias, filters, sort = panel.get_content()
        try: filter_list = filters.filterlist
        except (TypeError, AttributeError):
            filter_list = []

        answer = {"panels": {}}
        panel_filter = And()
        # find search filter
        for ft in filter_list:
            if ft.type == "basic" and ft.get_name() == "contains":
                panel_filter.combine(ft)
                answer["search"] = ft.to_json()
                break
            elif ft.type == "complex" and ft.get_name() == "or":
                panel_filter.combine(ft)
                answer["search"] = ft.to_json()
                break

        # find panel filter list
        for ft in filter_list:
            if ft.type == "complex" and ft.get_name() == "and":
                filter_list = ft
                break

        tag_list = panel.get_tags()
        try: idx = tag_list.index(updated_tag)
        except ValueError:
            pass
        else:
            tag_list = tag_list[idx+1:]

        for t in panel.get_tags():
            selected = []

            for ft in filter_list: # OR filter
                try: tag = ft[0].tag
                except (IndexError, TypeError): # bad filter
                    continue
                if tag == t:
                    selected = [t_ft.pattern for t_ft in ft]
                    tag_filter = ft
                    break

            if t in tag_list:
                list = library.tag_list(t, panel_filter)
                items = [{"name": _("All"), "value":"__all__", \
                    "class":"list-all", "sel":str(selected==[]).lower()}]
                if t == "various_artist" and "__various__" in list:
                    items.append({"name": _("Various Artist"),\
                        "value":"__various__",\
                        "class":"list-unknown",\
                        "sel":str("__various__" in selected).lower()})
                items.extend([{"name": l,"value":l,\
                    "sel":str(l in selected).lower(), "class":""}\
                    for l in list if l != "" and l != "__various__"])
                if "" in list:
                    items.append({"name": _("Unknown"), "value":"",\
                        "class":"list-unknown",\
                        "sel":str("" in selected).lower()})
                answer["panels"][t] = items
            # add filter for next panel
            if len(selected) > 0:
                panel_filter.combine(tag_filter)

        return answer


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


class JSONRpcResource(resource.Resource):
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

    def __init__(self, deejayd, tmp_dir):
        resource.Resource.__init__(self)
        self.deejayd_core = deejayd
        self.deejayd_core.put_sub_handler('web', WebRpcModule(deejayd, tmp_dir))

    def render(self, request):
        request.content.seek(0, 0)
        # Unmarshal the JSON-RPC data
        try: content = str_decode(request.content.read())
        except UnicodeError:
            return Fault(self.FAILURE, "Unable to decode JSON-RPC Request")

        log.debug("JSON-RPC Request : %s" % content)

        # By default safari on ios 6 cache all POST resquest / response
        # except if we add cache-control: no-cache in header
        # so do it
        request.setHeader("cache-control", "no-cache")
        try:
            parsed = loads_request(content)
            args, function_path = parsed['params'], parsed["method"]
            function = self.deejayd_core.get_function(function_path)
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
        log.debug("JSON-RPC Request : %s" % ans)
        request.finish()

    def _ebRender(self, failure, id):
        if isinstance(failure.value, Fault):
            return failure.value
        log.err(failure)
        return Fault(self.FAILURE, "error")

__all__ = ["JSONRpcResource", "Handler"]

# vim: ts=4 sw=4 expandtab
