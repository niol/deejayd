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

from collections import MutableMapping

from deejayd.model._model import IObjectModel
from deejayd.database.querybuilders import SimpleSelect, ReplaceQuery, \
    EditRecordQuery, DeleteQuery, WebradioSelectQuery
from deejayd import DeejaydError
from zope.interface import implements


class Webradio(MutableMapping):

    def __init__(self, wb_infos):
        # wb_infos : id, name, urls (separated by ,)
        self.wb_data = {
            "wb_id": wb_infos[0],
            "title": wb_infos[1],
            "type": "webradio",
            "uri": "",
            "url-type": "urls",
            "url-index": 0,
            "urls": (wb_infos[2]).split(","),
        }

    def __len__(self):
        return len(self.wb_data)

    def __iter__(self):
        return self.wb_data.iterkeys()

    def __getitem__(self, key):
        return self.wb_data[key]

    def __setitem__(self, key, value):
        self.wb_data[key] = value

    def __delitem__(self, key):
        raise DeejaydError("We can't remove any key from a playlist entry")

    def to_json(self):
        return dict(self.wb_data)

class WebradioSource(object):
    implements(IObjectModel)
    CAT_TABLE = "webradio_categories"
    CAT_REL_TABLE = "webradio_categories_relation"
    WEB_TABLE = "webradio"
    URL_TABLE = "webradio_entries"
    STAT_TABLE = "webradio_stats"

    def __init__(self, source_name, db_id):
        self.source_name = source_name
        self.db_id = db_id

    def get_categories(self):
        cats = SimpleSelect(self.CAT_TABLE)\
                    .select_column("name", "id")\
                    .append_where("source_id = %s", (self.db_id,))\
                    .execute()
        return dict(cats)

    def add_categorie(self, name, commit=True):
        if name in self.get_categories().keys():
            raise DeejaydError(_("category %s already exists") % name)
        cat_id = EditRecordQuery(self.CAT_TABLE)\
                        .add_value("source_id", self.db_id)\
                        .add_value("name", name)\
                        .execute(commit=commit)
        return {"id": cat_id, "name": name}

    def delete_categories(self, cat_ids, commit=True):
        for key, table in [("id", self.CAT_TABLE),
                           ("cat_id", self.CAT_REL_TABLE)]:
            DeleteQuery(table)\
                    .append_where(key + " IN (%s)", (",".join(map(str, cat_ids)),))\
                    .execute(commit=commit)

    def clear_categories(self, commit=True):
        where_select = "SELECT id FROM %s WHERE source_id = %d" \
                % (self.CAT_TABLE, self.db_id)
        DeleteQuery(self.CAT_REL_TABLE)\
              .append_where("cat_id IN (%s)" % where_select, ())\
              .execute(commit=commit)
        DeleteQuery(self.CAT_TABLE)\
              .append_where("source_id = %s", (self.db_id,))\
              .execute(commit=commit)

    def get_webradios(self, cat_id=None):
        query = WebradioSelectQuery(self.WEB_TABLE, self.URL_TABLE,
                                    self.CAT_REL_TABLE)\
                .append_where(self.WEB_TABLE + ".source_id = %s", (self.db_id,))
        if cat_id is not None:
            query.select_category(cat_id)
        return map(lambda w_infos: Webradio(w_infos), query.execute())

    def add_webradio(self, name, cat_ids, urls, commit=True):
        wb_id = EditRecordQuery(self.WEB_TABLE)\
                    .add_value("name", name)\
                    .add_value("source_id", self.db_id)\
                    .execute(commit=commit)
        for cat_id in cat_ids:
            ReplaceQuery(self.CAT_REL_TABLE)\
                    .add_value("webradio_id", wb_id)\
                    .add_value("cat_id", cat_id)\
                    .execute(commit=commit)
        for url in urls:
            EditRecordQuery(self.URL_TABLE)\
                        .add_value("url", url)\
                        .add_value("webradio_id", wb_id)\
                        .execute(commit=commit)

    def delete_webradios(self, wb_ids, commit=True):
        for table, key in [(self.WEB_TABLE, "id"),
                           (self.URL_TABLE, 'webradio_id'),
                           (self.CAT_REL_TABLE, 'webradio_id')]:
            DeleteQuery(table)\
                .append_where(key + " IN (%s)", (",".join(map(str, wb_ids)),))\
                .execute(commit=commit)

    def clear_webradios(self, commit=True):
        where_select = SimpleSelect(self.WEB_TABLE)\
                    .select_column("id")\
                    .append_where("source_id = %d" % self.db_id, ())\
                    .to_sql()
        DeleteQuery(self.CAT_REL_TABLE)\
              .append_where("webradio_id IN (%s)" % where_select, ())\
              .execute(commit=commit)
        DeleteQuery(self.URL_TABLE)\
              .append_where("webradio_id IN (%s)" % where_select, ())\
              .execute(commit=commit)
        DeleteQuery(self.WEB_TABLE)\
              .append_where("source_id = %s", (self.db_id,))\
              .execute(commit=commit)

    def get_stats(self):
        return dict(SimpleSelect(self.STAT_TABLE)\
                        .select_column("key", "value")\
                        .append_where("source_id = %s", (self.db_id,))\
                        .execute())

    def set_stats(self, stats, commit=True):
        for k, v in stats.items():
            ReplaceQuery(self.STAT_TABLE)\
                .add_value("source_id", self.db_id)\
                .add_value("key", k)\
                .add_value("value", v)\
                .execute(commit=commit)

class WebradioFactory(object):

    class __impl(object):
        __loaded_sources = {}
        TABLE = "webradio_source"

        def get_source(self, name):
            if name not in self.__loaded_sources:
                wb = SimpleSelect(self.TABLE)\
                            .select_column("id")\
                            .append_where("name=%s", (name,))\
                            .execute(expected_result="fetchone")
                if wb is None:
                    wb_id = EditRecordQuery(self.TABLE)\
                                .add_value("name", name)\
                                .execute()
                else:
                    wb_id = wb[0]
                self.__loaded_sources[name] = WebradioSource(name, wb_id)
            return self.__loaded_sources[name]

    # storage for the instance reference
    __instance = None

    def __init__(self, *args, **kwargs):
        # Check whether we already have an instance
        if WebradioFactory.__instance is None:
            # Create and remember instance
            WebradioFactory.__instance = WebradioFactory.__impl(*args, **kwargs)

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = WebradioFactory.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

# vim: ts=4 sw=4 expandtab