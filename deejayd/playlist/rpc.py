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

from sqlalchemy.orm import with_polymorphic, subqueryload
from deejayd import DeejaydError
from deejayd.common.component import SignalingComponent, JSONRpcComponent
from deejayd.jsonrpc.interfaces import jsonrpc_module, RecordedPlaylistModule
from deejayd.db.connection import Session
from deejayd.db.models import MediaList, StaticMediaList, Filter
from deejayd.db.models import MagicMediaList, StaticMediaListItem


def load_playlist(pls_type):
    def load_playlist_decorator(func):
        def load_playlist_func(self, pl_id, *__args, **__kw):
            if pls_type == "static":
                pls = Session.query(StaticMediaList).get(pl_id)
            elif pls_type == "magic":
                all_ft = with_polymorphic(Filter, "*", flat=True)
                pls = Session.query(MagicMediaList)\
                             .options(subqueryload(
                                 MagicMediaList.filters.of_type(all_ft))
                                )\
                             .filter(MagicMediaList.id == pl_id)\
                             .one()
            if pls is None:
                raise DeejaydError(_("Playlist %s not found") % str(pl_id))
            rs = func(self, pls, *__args, **__kw)

            if rs is True:
                Session.commit()
                self.dispatch_signame('recpls.update', pl_id=pl_id)
                return None
            return rs

        return load_playlist_func

    return load_playlist_decorator


@jsonrpc_module(RecordedPlaylistModule)
class DeejaydRecordedPlaylist(SignalingComponent, JSONRpcComponent):

    def __init__(self, audio_library):
        super(DeejaydRecordedPlaylist, self).__init__()
        self.library = audio_library

    def get_list(self):
        playlists = Session.query(MediaList).all()
        return [p.to_json() for p in playlists if not p.name.startswith("__")]

    def get_content(self, pl_id, first=0, length=None):
        magic_or_static = with_polymorphic(MediaList, "*")

        pls = Session.query(magic_or_static)\
                     .filter(MediaList.id == pl_id)\
                     .one_or_none()
        if pls is None:
            raise DeejaydError(_("Playlist with id %s does not exist"))
        return {
            "medias": [m.to_json() 
                       for m in pls.get_medias(Session, first, length)],
            "sort": pls.get_sorts(),
            "filter": pls.get_filter()
        }

    def create(self, name, p_type):
        if name == "":
            raise DeejaydError(_("Set a playlist name"))
        if p_type not in ("static", "magic"):
            raise DeejaydError(_("playlist type has to be 'static' or 'magic'"))

        pls = Session.query(MediaList)\
                     .filter(MediaList.name == name)\
                     .one_or_none()
        if pls is not None:
            raise DeejaydError(_("This playlist already exists"))

        pl_cls = p_type == "static" and StaticMediaList or MagicMediaList
        pls = pl_cls(name=name)
        Session.add(pls)
        Session.commit()
        self.dispatch_signame('recpls.listupdate')
        return {"pl_id": pls.id, "name": name, "type": p_type}

    def erase(self, pl_ids):
        if len(pl_ids) > 0:
            magic_or_static = with_polymorphic(MediaList, "*")
            pls = Session.query(magic_or_static)\
                         .filter(MediaList.id.in_(pl_ids))\
                         .all()
            for pl in pls:
                Session.delete(pl)
            Session.commit()
            self.dispatch_signame('recpls.listupdate')

    @load_playlist("static")
    def static_load_folders(self, pls, dir_ids):
        medias = self.library.get_all_files(dir_ids)
        for m in medias:
            pls.items.append(StaticMediaListItem(media=m))
        return True

    @load_playlist("static")
    def static_load_medias(self, pls, m_ids):
        medias = self.library.get_file_withids(m_ids)
        for m in medias:
            pls.items.append(StaticMediaListItem(media=m))
        return True

    @load_playlist("static")
    def static_remove_medias(self, pls, m_ids):
        if len(m_ids) > 0:
            Session.query(StaticMediaListItem)\
                .filter(StaticMediaListItem.id.in_(m_ids))\
                .delete(synchronize_session='fetch')
        return True

    @load_playlist("static")
    def static_clear(self, pls):
        Session.query(StaticMediaListItem)\
               .filter(StaticMediaListItem.medialist == pls)\
               .delete(synchronize_session='fetch')
        return True

    @load_playlist("magic")
    def magic_add_filter(self, pls, ft):
        pls.filters.append(ft)
        return True

    @load_playlist("magic")
    def magic_remove_filter(self, pls, ft):
        for db_ft in pls.filters:
            if db_ft.equals(ft):
                pls.filters.remove(db_ft)
        return True

    @load_playlist("magic")
    def magic_clear_filter(self, pls):
        for ft in pls.filters:
            pls.filters.remove(ft)
        return True

    @load_playlist("magic")
    def magic_get_properties(self, pls):
        return pls.get_properties()

    @load_playlist("magic")
    def magic_set_property(self, pls, k, v):
        p_list = [
            "use-or-filter",
            "use-limit",
            "limit-value",
            "limit-sort-value",
            "limit-sort-direction"
        ]
        if k not in p_list:
            raise DeejaydError(_("Property %s does not exist "
                                 "for magic playlist") % k)
        setattr(pls, k.replace("-", "_"), v)
        return True
