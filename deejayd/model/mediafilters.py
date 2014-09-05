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


import itertools


from deejayd.database.querybuilders import EditRecordQuery, SimpleSelect
from deejayd.database.querybuilders import DeleteQuery, ReplaceQuery
from deejayd.database.connection import DatabaseConnection
from deejayd.model._model import IObjectModel
from zope.interface import implements


class DBMediaFilter(object):
    implements(IObjectModel)
    __loaded_instances = {}

    CLASS_TABLE = 'filters'
    PRIMARY_KEY = 'filter_id'

    @classmethod
    def get_filter_type(cls, filter_id):
        query = SimpleSelect(cls.CLASS_TABLE)
        record = query.select_column('type')\
                      .append_where("filter_id = %s", (filter_id,))\
                      .execute(expected_result="fetchone")

        if not record: raise ValueError
        return record[0]

    @classmethod
    def load_from_db(cls, filter_id):
        if filter_id in cls.__loaded_instances:
            return cls.__loaded_instances[filter_id]

        try: type = cls.get_filter_type(filter_id)
        except ValueError:
            return None
        if type == "basic":
            filter = DBBasicFilter.load_from_db(filter_id)
        elif type == "complex":
            filter = DBComplexFilter.load_from_db(filter_id)

        if filter is not None:
            cls.__loaded_instances[filter_id] = filter
        return filter

    @classmethod
    def new(cls, mf):
        if mf.type == 'complex':
            return DBComplexFilter(mf)
        elif mf.type == 'basic':
            return DBBasicFilter(mf)
        else:
            raise RuntimeError('Unknown filter type')

    @classmethod
    def load_from_json(cls, json_filter):
        mf = mediafilters.filter_factory.load_from_json(json_filter)
        return cls.new(mf)

    def __init__(self, media_filter):
        self.media_filter = media_filter

    def get_identifier(self):
        return self.media_filter.get_identifier()

    def get_name(self):
        return self.media_filter.get_name()

    def __str__(self):
        return self.media_filter.__str__()

    def get_id(self):
        return self.media_filter.db_id

    def save(self):
        cursor = DatabaseConnection().cursor()

        query = EditRecordQuery(self.CLASS_TABLE)
        query.add_value('type', self.media_filter.TYPE)
        if self.media_filter.db_id is not None:
            query.set_update_id(self.PRIMARY_KEY, self.media_filter.db_id)
        cursor.execute(query.to_sql(), query.get_args())
        if self.media_filter.db_id is None:
            self.media_filter.db_id = DatabaseConnection().get_last_insert_id(cursor)

        cursor.close()
        return self.media_filter.db_id

    def erase_from_db(self):
        if self.media_filter.db_id is not None:
            DeleteQuery(self.CLASS_TABLE)\
                        .append_where("filter_id = %s", (self.media_filter.db_id,))\
                        .execute()
            self.media_filter.db_id = None

    def to_json(self):
        return self.media_filter.to_json()

    def to_json_str(self):
        return self.media_filter.to_json_str()

    def _get_table(self, tag, query):
        return tag == "album" and "album" or query.table_name


class DBBasicFilter(DBMediaFilter):
    TABLE = 'filters_basicfilters'

    @classmethod
    def load_from_db(cls, filter_id):
        record = SimpleSelect(cls.TABLE)\
                              .select_column('tag', 'operator', 'pattern')\
                              .append_where("filter_id = %s", (filter_id,))\
                              .execute(expected_result="fetchone")

        if record:
            bfilter_class = mediafilters.filter_factory.NAME2BASIC[record[1]]
            f = bfilter_class(record[0], record[2])
            f.db_id = filter_id
            return DBBasicFilter(f)
        return None

    def equals(self, filter):
        return self.media_filter.equals(filter.media_filter)

    def restrict(self, query):
        query.join_on_tag(self.media_filter.tag)
        where_str, arg = self.media_filter._match_tag(self._get_table(self.media_filter.tag, query))
        if not isinstance(arg, list):
            arg = (arg,)
        query.append_where(where_str, arg)

    def __str__(self):
        return self.media_filter.__str__()

    def save(self):
        new = self.media_filter.db_id is None
        super(DBBasicFilter, self).save()

        query = EditRecordQuery(self.TABLE)
        if new:
            query.add_value(self.PRIMARY_KEY, self.media_filter.db_id)
        else:
            query.set_update_id(self.PRIMARY_KEY, self.media_filter.db_id)
        query.add_value('tag', self.media_filter.tag)\
             .add_value('operator', self.get_name())\
             .add_value('pattern', self.media_filter.pattern)\
             .execute()
        return self.media_filter.db_id

    def erase_from_db(self):
        if self.media_filter.db_id is not None:
            DeleteQuery(self.TABLE)\
                        .append_where("filter_id = %s", (self.media_filter.db_id,))\
                        .execute()
            super(DBBasicFilter, self).erase_from_db()


class DBComplexFilter(DBMediaFilter):
    TABLE = 'filters_complexfilters'
    SUBFILTERS_TABLE = 'filters_complexfilters_subfilters'

    @classmethod
    def load_from_db(cls, filter_id):
        record = SimpleSelect(cls.TABLE)\
                              .select_column('combinator')\
                              .append_where("filter_id = %s", (filter_id,))\
                              .execute(expected_result="fetchone")

        if record:
            cfilter = mediafilters.filter_factory.NAME2COMPLEX[record[0]]
            cfilter.db_id = filter_id
            dbcfilter = DBComplexFilter(cfilter)

            sf_records = SimpleSelect(cls.SUBFILTERS_TABLE)\
                        .select_column('filter_id')\
                        .append_where("complexfilter_id = %s", (filter_id,))\
                        .execute()
            for sf_record in sf_records:
                sf_id = sf_record[0]
                dbcfilter.combine(DBMediaFilter.load_from_db(sf_id))
            return dbcfilter
        return None

    def combine(self, filter):
        self.media_filter.combine(filter.media_filter)

    def equals(self, filter):
        return self.media_filter.equals(filter.media_filter)

    def find_filter_by_tag(self, tag):
        return self.media_filter.find_filter_by_tag(tag)

    def find_filter_by_name(self, name):
        return self.media_filter.find_filter_by_name(name)

    def find_filter(self, filter):
        return self.media_filter.find_filter(filter.media_filter)

    def remove_filter(self, filter):
        self.media_filter.remove(filter.media_filter)

    def __iter__(self):
        return itertools.imap(DBMediaFilter.new,
                              iter(self.media_filter.filterlist))

    def __getitem__(self, idx):
        return self.media_filter[idx]

    def __len__(self):
        return len(self.media_filter)

    def restrict(self, query):
        if self.media_filter.filterlist:
            where_str, args = self._build_wheres(query)
            query.append_where(where_str, args)

    def _build_wheres(self, query):
        if not self.media_filter.filterlist: return "(1)", []
        wheres, wheres_args = [], []
        for f in self.media_filter.filterlist:
            if f.type == "basic":
                query.join_on_tag(f.tag)
                where_query, arg = f._match_tag(\
                        self._get_table(f.tag, query))
                wheres.append(where_query)
                wheres_args.append(arg)
            else:  # complex filter
                where_query, args = self.new(f)._build_wheres(query)
                wheres.append(where_query)
                wheres_args.extend(args)
        return "(%s)" % (self.media_filter.combinator.join(wheres),), wheres_args

    def save(self):
        new = self.media_filter.db_id is None
        super(ComplexFilter, self).save()

        query = EditRecordQuery(ComplexFilter.TABLE)
        if new:
            query.add_value(self.PRIMARY_KEY, self.filter_id.db_id)
        else:
            query.set_update_id(self.PRIMARY_KEY, self.media_filter.db_id)
        query.add_value('combinator', self.get_name())\
             .execute()

        for subfilter in self.media_filter.filterlist:
            subfilter_id = subfilter.save()
            query = ReplaceQuery(self.SUBFILTERS_TABLE)\
                              .add_value('complexfilter_id', self.media_filter.db_id)\
                              .add_value('filter_id', subfilter_id)\
                              .execute()

        return self.media_filter.db_id

    def erase_from_db(self):
        if self.media_filter.db_id is not None:
            subfilters = SimpleSelect(self.SUBFILTERS_TABLE)\
                        .select_column('filter_id')\
                        .append_where("complexfilter_id = %s", (self.media_filter.db_id,))\
                        .execute()
            for (id,) in subfilters:
                f = MediaFilter.load_from_db(id)
                if f is not None: f.erase_from_db()

            DeleteQuery(self.SUBFILTERS_TABLE)\
                        .append_where("complexfilter_id = %s", (self.media_filter.db_id,))\
                        .execute()
            DeleteQuery(self.TABLE)\
                        .append_where("filter_id = %s", (self.media_filter.db_id,))\
                        .execute()
            super(ComplexFilter, self).erase_from_db()


# vim: ts=4 sw=4 expandtab
