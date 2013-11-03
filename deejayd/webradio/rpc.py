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

from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.jsonrpc.interfaces import WebradioModule, jsonrpc_module
from deejayd.webradio.IWebradioSource import IEditWebradioSource
from deejayd.webradio.local import WebradioLocalSource
from deejayd.webradio.icecast import IceCastSource
from deejayd import DeejaydError
from deejayd.ui.config import DeejaydConfig


def require_source(editable = False):
    def require_editable_source(func):
        def impl(self, source_name, *args, **kwargs):
            if source_name not in self.wb_sources.keys():
                raise DeejaydError(_("Webradio source %s not supported") %
                             source_name)
            source = self.wb_sources[source_name]
            if editable and not IEditWebradioSource.providedBy(source):
                raise DeejaydError(_("You can not edit this webradio source"))

            res = func(self, source, *args, **kwargs)
            return res

        impl.__name__ = func.__name__
        return impl

    return require_editable_source


@jsonrpc_module(WebradioModule)
class DeejaydWebradio(SignalingComponent, JSONRpcComponent):

    def __init__(self):
        super(DeejaydWebradio, self).__init__()

        self.wb_sources = { "local": WebradioLocalSource() }
        if DeejaydConfig().getboolean("webradio", "icecast"):
            self.wb_sources["icecast"] = IceCastSource()

    def get_available_sources(self):
        return [{
            "name": s.NAME,
            "editable": IEditWebradioSource.providedBy(s)} \
        for s in self.wb_sources.values()]

    @require_source(editable=False)
    def get_source_content(self, source, category=None, start=0, length=None):
        return source.get_webradios(category)

    @require_source(editable=False)
    def get_source_categories(self, source):
        return source.get_categories()

    @require_source(editable=False)
    def get_source_status(self, source):
        return source.get_status()

    @require_source(editable=True)
    def source_add_category(self, source, cat):
        self.dispatch_signame('webradio.listupdate')
        return source.add_categorie(cat)

    @require_source(editable=True)
    def source_delete_categories(self, source, cat_ids):
        source.remove_categories(cat_ids)

    @require_source(editable=True)
    def source_add_webradio(self, source, name, urls, cat=None):
        source.add_webradio(name, urls, cat)

    @require_source(editable=True)
    def source_delete_webradios(self, source, wb_ids):
        source.remove_webradios(wb_ids)

    @require_source(editable=True)
    def source_clear_webradios(self, source):
        source.clear_webradios()

# vim: ts=4 sw=4 expandtab
