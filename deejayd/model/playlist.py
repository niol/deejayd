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

import random
from collections import MutableMapping
from zope.interface import implements

from deejayd import DeejaydError
from deejayd.database.connection import DatabaseConnection
from deejayd.model._model import IObjectModel
from deejayd.model.media_item import AudioItem, VideoItem
from deejayd.model.mediafilters import MediaFilter, And, Or
from deejayd.database.querybuilders import DeleteQuery, EditRecordQuery, \
    ReplaceQuery
from deejayd.database.querybuilders import StaticPlaylistSelectQuery
from deejayd.database.querybuilders import SimpleSelect

__all__ = (
    "PlaylistFactory"
)

class PlaylistEntry(MutableMapping):

    def __init__(self, playlist_manager, id, media):
        self.playlist_manager = playlist_manager
        self.media = media
        self.id = id

    def __len__(self):
        return len(self.media)

    def __iter__(self):
        return self.media.iterkeys()

    def __getitem__(self, key):
        if key == "id":
            return self.id
        elif key == "pos":
            for index, entry in enumerate(self.playlist_manager.get()):
                if entry['id'] == self['id']:
                    return index
            return -1 # entry not in the list anymore
        elif key == "source":
            return self.playlist_manager.get_source()
        return self.media[key]

    def __setitem__(self, key, value):
        if key in ("id", "pos"):
            raise DeejaydError("%s is not mutable" % key)
        self.media[key] = value

    def __delitem__(self, key):
        raise DeejaydError("We can't remove any key from a playlist entry")

    def __getattr__(self, attr):
        if hasattr(self.media, attr):
            return getattr(self.media, attr)
        raise AttributeError

    def get_media(self):
        return self.media

    def set_media(self, media):
        self.media = media

    def get_id(self):
        return self.id


class SimplePlaylist(object):

    def __init__(self, pl_id=0):
        self.source = None
        self.pl_id = pl_id
        self.plmedia_id = 0
        self._playlist = []
        self.repeat = False

    def __len__(self):
        return len(self._playlist)

    def set_source(self, source):
        self.source = source

    def get_source(self):
        return self.source

    def get_id(self):
        return self.pl_id

    def set_id(self, pl_id):
        self.pl_id = pl_id

    def get(self, start=0, length=None):
        if length is not None:
            stop = min(start + int(length), len(self._playlist))
        else:
            stop = len(self._playlist)
        start = min(start, stop)
        return self._playlist[start:stop]

    def get_item(self, id):
        return next((entry for entry in self._playlist\
                      if entry["id"] == id), None)

    def get_item_first(self):
        return self._playlist and self._playlist[0] or None

    def get_item_last(self):
        return self._playlist and self._playlist[-1] or None

    def get_ids(self):
        return [entry["id"] for entry in self._playlist]

    def next(self, pl_entry):
        try:
            idx = self._playlist.index(pl_entry)
            if idx < len(self._playlist) - 1:
                return self._playlist[idx + 1]
        except ValueError:
            pass
        return None

    def previous(self, pl_entry):
        try:
            idx = self._playlist.index(pl_entry)
            if idx > 0:
                return self._playlist[idx - 1]
        except ValueError:
            pass
        return None

    def find(self, media_id):
        for entry in self._playlist:
            if entry["media_id"] == media_id:
                return entry
        raise ValueError

    def set(self, medias):
        self._playlist = map(self._format, medias)
        self.pl_id += 1

    def _format(self, media):
        self.plmedia_id += 1
        return PlaylistEntry(self, int(self.plmedia_id), media)

class _Playlist(SimplePlaylist):
    implements(IObjectModel)
    TABLE = "medialist"
    TYPE = ""

    def __init__(self, library, name, pl_id=0, db_id=None):
        super(_Playlist, self).__init__(pl_id)

        self.db_id = db_id
        self.name = name
        self.library = library
        if library.type == "audio":
            self.ITEM_CLS = AudioItem
        elif library.type == "video":
            self.ITEM_CLS = VideoItem

        self.time_length = 0
        self.repeat = False

    def get_type(self):
        return self.TYPE

    def get_dbid(self):
        return self.db_id

    def save(self):
        if self.db_id is None:
            cursor = DatabaseConnection().cursor()
            query = EditRecordQuery(self.TABLE).add_value("type", self.TYPE)\
                                               .add_value("name", self.name)
            cursor.execute(query.to_sql(), query.get_args())
            self.db_id = DatabaseConnection().get_last_insert_id(cursor)
        return self.db_id

    def erase_from_db(self):
        if self.db_id is not None:
            DeleteQuery(self.TABLE).append_where("id = %s", (self.db_id,))\
                                   .execute()
            self.db_id = None

    def update_media(self, media):
        selected = filter(lambda m: m["media_id"] == media["media_id"], \
                          self._playlist)
        if len(selected) > 0:
            def update(e):
                m = e.get_media()
                m.update(media)
            map(update, selected)
            self.pl_id += 1
            return True
        return False

    def remove_media(self, media_id):
        selected = filter(lambda m: m["media_id"] == media_id, self._playlist)
        if len(selected) > 0:
            map(self._playlist.remove, selected)
            self.pl_id += 1
            return True
        return False

    def _update_time_length(self):
        self.time_length = reduce(lambda t, m: t + int(m["length"]),
                                  self._playlist, 0)


class StaticPlaylist(_Playlist):
    TYPE = "static"
    ITEM_TABLE = "medialist_libraryitem"

    def __init__(self, library, name, pl_id=0, db_id=None):
        super(StaticPlaylist, self).__init__(library, name, pl_id, db_id)
        self.load()

    def load(self):
        if self.db_id is None:
            return

        query = StaticPlaylistSelectQuery(self.ITEM_TABLE, self.db_id)\
                        .select_tags(self.ITEM_CLS.attributes())
        rs = query.execute()
        medias = map(lambda m: self.ITEM_CLS(m), rs)
        self._playlist = map(self._format, medias)
        self._update_time_length()

    def __update(self):
        self._update_time_length()
        self.pl_id += 1

    def set(self, medias):
        self._playlist = map(self._format, medias)
        self.__update()

    def add(self, medias, pos=None):
        if pos is None:
            pos = len(self._playlist)
        self._playlist = self._playlist[:pos] + map(self._format, medias)\
                                              + self._playlist[pos:]
        self.__update()

    def delete(self, ids):
        selected_entry = filter(lambda e: e["id"] in ids, self._playlist)
        if len(selected_entry) != len(ids):
            return False
        map(self._playlist.remove, selected_entry)
        self.__update()
        return True

    def move(self, ids, new_pos):
        selected_items = [item for item in self._playlist if item["id"] in ids]
        if len(selected_items) < len(ids):  # some items are missing
            return False

        if (new_pos != -1):
            s_list = [item for item in self._playlist[:new_pos]\
                       if item["id"] not in ids]
            e_list = [item for item in self._playlist[new_pos:]\
                       if item["id"] not in ids]
            self._playlist = s_list + selected_items + e_list
        else:
            self._playlist = [item for item in self._playlist\
                               if item["id"] not in ids] + selected_items
        self.pl_id += 1
        return True

    def shuffle(self, current=None):
        random.shuffle(self._playlist)
        if current is not None:
            try: self._playlist.remove(current)
            except ValueError: pass
            else:
                self._playlist = [current] + self._playlist
        self.pl_id += 1

    def clear(self):
        self._playlist = []
        self.__update()

    def erase_from_db(self):
        if self.db_id is not None:
            DeleteQuery(self.ITEM_TABLE)\
                    .append_where("medialist_id=%s", (self.db_id,))\
                    .execute()
            super(StaticPlaylist, self).erase_from_db()

    def save(self):
        self.db_id = super(StaticPlaylist, self).save()
        DeleteQuery(self.ITEM_TABLE)\
                .append_where("medialist_id=%s", (self.db_id,))\
                .execute(commit=False)
        for item in self._playlist:
            EditRecordQuery(self.ITEM_TABLE)\
                    .add_value("medialist_id", self.db_id)\
                    .add_value("libraryitem_id", item["media_id"])\
                    .execute(commit=False)
        DatabaseConnection().commit()


class MagicPlaylist(_Playlist):
    FILTER_TABLE = "medialist_filters"
    PROPERTY_TABLE = "medialist_property"
    SORT_TABLE = "medialist_sorts"
    TYPE = "magic"
    default_properties = {
        "use-or-filter": "0",
        "use-limit": "0",
        "limit-value": "50",
        "limit-sort-value": "title",
        "limit-sort-direction": "ascending"
    }

    def __init__(self, library, name, pl_id=0, db_id=None):
        super(MagicPlaylist, self).__init__(library, name, pl_id, db_id)
        self.properties = dict(self.default_properties)
        self.filters, self.sorts = [], []
        if db_id is not None:
            # load filters
            f_ids = SimpleSelect(self.FILTER_TABLE)\
                              .select_column('filter_id')\
                              .append_where("medialist_id = %s", (db_id,))\
                              .execute()
            self.filters = map(lambda i: MediaFilter.load_from_db(i[0]), f_ids)
            # load properties
            self.properties = dict(SimpleSelect(self.PROPERTY_TABLE)\
                                  .select_column('ikey', 'value')\
                                  .append_where("medialist_id = %s", (db_id,))\
                                  .execute()) or dict(self.default_properties)
            # load sorts
            self.sorts = SimpleSelect(self.SORT_TABLE)\
                                  .select_column('tag', 'direction')\
                                  .append_where("medialist_id = %s", (db_id,))\
                                  .execute()

    def load(self):
        filter = self.properties["use-or-filter"] == "1" and Or() or And()
        for f in self.filters:
            filter.combine(f)

        sorts = self.sorts + self.ITEM_CLS.default_sort()
        if self.properties["use-limit"] == "1":
            sorts = [(self.properties["limit-sort-value"], \
                     self.properties["limit-sort-direction"])] + sorts
            limit = int(self.properties["limit-value"])
        else:
            limit = None
        medias = self.library.search_with_filter(filter, sorts, limit)
        self._playlist = map(self._format, medias)
        self._update_time_length()

    def erase_from_db(self):
        if self.db_id is not None:
            for filter in self.filters:
                filter.erase_from_db()
            for table in (self.FILTER_TABLE, self.PROPERTY_TABLE, \
                           self.SORT_TABLE):
                DeleteQuery(table)\
                        .append_where("medialist_id=%s", (self.db_id,))\
                        .execute()
            super(MagicPlaylist, self).erase_from_db()

    def save(self):
        self.db_id = super(MagicPlaylist, self).save()
        # first erase
        for table in (self.FILTER_TABLE, self.SORT_TABLE):
            DeleteQuery(table)\
                    .append_where("medialist_id=%s", (self.db_id,))\
                    .execute(commit=False)

        # save filters
        for filter in self.filters:
            f_id = filter.save()
            EditRecordQuery(self.FILTER_TABLE)\
                .add_value("medialist_id", self.db_id)\
                .add_value("filter_id", f_id)\
                .execute(commit=False)
        # save properties
        for k, v in self.properties.items():
            ReplaceQuery(self.PROPERTY_TABLE)\
                .add_value("medialist_id", self.db_id)\
                .add_value("ikey", k)\
                .add_value("value", v)\
                .execute(commit=False)
        # save sorts
        for tag, direction in self.sorts:
            EditRecordQuery(self.SORT_TABLE)\
                .add_value("medialist_id", self.db_id)\
                .add_value("tag", tag)\
                .add_value("direction", direction)\
                .execute(commit=False)
        DatabaseConnection().commit()

    def __update(self):
        self.load()
        self.pl_id += 1

    def get_properties(self):
        return self.properties

    def set_property(self, k, v):
        self.properties[k] = str(v)
        self.__update()

    def get_main_filter(self):
        filter = self.properties["use-or-filter"] == "1" and Or() or And()
        for f in self.filters:
            filter.combine(f)
        return filter

    def get_filters(self):
        return self.filters

    def add_filter(self, filter):
        self.filters.append(filter)
        self.__update()

    def remove_filter(self, filter):
        self.filters.remove(filter)
        filter.erase_from_db()
        self.__update()

    def clear_filter(self):
        map(lambda f: f.erase_from_db(), self.filters)
        self.filters = []
        self.__update()

    def set_filters(self, filter_list):
        map(lambda f: f.erase_from_db(), self.filters)
        self.filters = list(filter_list)
        self.__update()

    def get_sorts(self):
        return self.sorts

    def sort(self, sorts):
        self.sorts = sorts
        self.__update()


class PlaylistFactory(object):
    PLS_CLS = {
        "magic": MagicPlaylist,
        "static": StaticPlaylist,
    }

    class __impl(object):
        __loaded_instances = {}
        __loaded_simples = {}
        PLS_CLS = {
            "magic": MagicPlaylist,
            "static": StaticPlaylist,
        }

        def load_byid(self, library, pl_id):
            if pl_id not in self.__loaded_instances.keys():
                pls = SimpleSelect(_Playlist.TABLE)\
                            .select_column('name', 'type')\
                            .append_where("id=%s", (pl_id,))\
                            .execute(expected_result="fetchone")
                if pls is None:
                    raise IndexError
                name, type = pls
                pls_instance = self.PLS_CLS[type](library, name, db_id=pl_id)
                self.__loaded_instances[pl_id] = pls_instance
            return self.__loaded_instances[pl_id]

        def __load_by_name(self, library, type, name, create):
            pls = SimpleSelect('medialist').select_column('id')\
                                           .append_where("name=%s", (name,))\
                                           .append_where("type=%s", (type,))\
                                           .execute(expected_result="fetchone")
            pl_id = pls is not None and pls[0] or None
            if pl_id is None:
                if not create: raise IndexError
                pls_instance = self.PLS_CLS[type](library, name, db_id=pl_id)
                pl_id = pls_instance.save()
                self.__loaded_instances[pl_id] = pls_instance
            elif pl_id not in self.__loaded_instances.keys():
                pls_instance = self.PLS_CLS[type](library, name, db_id=pl_id)
                self.__loaded_instances[pl_id] = pls_instance

            return self.__loaded_instances[pl_id]

        def static(self, library, name, create=True):
            return self.__load_by_name(library, "static", name, create)

        def magic(self, library, name, create=True):
            return self.__load_by_name(library, "magic", name, create)

        def simple(self, name):
            if name not in self.__loaded_simples.keys():
                self.__loaded_simples[name] = SimplePlaylist()
            return self.__loaded_simples[name]

        def list(self):
            pls = SimpleSelect(_Playlist.TABLE)\
                        .select_column('id', 'name', 'type')\
                        .order_by('name')\
                        .execute()
                        # .append_where("name NOT LIKE %s", ("__%%",))\
                        # .append_where("name NOT LIKE %s", ("%%__",))\
            pls = filter(lambda p: not p[1].startswith("__")\
                        and not p[1].endswith("__"), pls)
            return map(lambda p: {"pl_id": p[0], "name": p[1], "type": p[2]},
                       pls)

        def erase(self, pl_objects):
            for pl in pl_objects:
                try: del self.__loaded_instances[pl.db_id]
                except IndexError, TypeError:
                    pass
                pl.erase_from_db()

    # storage for the instance reference
    __instance = None

    def __init__(self, *args, **kwargs):
        # Check whether we already have an instance
        if PlaylistFactory.__instance is None:
            # Create and remember instance
            PlaylistFactory.__instance = PlaylistFactory.__impl(*args, **kwargs)

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = PlaylistFactory.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

# vim: ts=4 sw=4 expandtab
