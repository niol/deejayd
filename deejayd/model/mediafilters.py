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

from deejayd import DeejaydError
from deejayd.jsonrpc import json
from deejayd.database.querybuilders import EditRecordQuery, SimpleSelect
from deejayd.database.querybuilders import DeleteQuery, ReplaceQuery
from deejayd.database.connection import DatabaseConnection
from deejayd.model._model import IObjectModel
from zope.interface import implements

__all__ = (
            'BASIC_FILTERS', 'NAME2BASIC',
            'Equals', 'NotEquals', 'Contains', 'NotContains', 'Regexi',
            'Higher', 'Lower', 'In',
            'COMPLEX_FILTERS', 'NAME2COMPLEX',
            'And', 'Or',
          )


class MediaFilter(object):
    implements(IObjectModel)
    __loaded_instances = {}

    CLASS_TABLE = 'filters'
    PRIMARY_KEY = 'filter_id'
    TYPE = 'none'

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
            filter = BasicFilter.load_from_db(filter_id)
        elif type == "complex":
            filter = ComplexFilter.load_from_db(filter_id)

        if filter is not None:
            cls.__loaded_instances[filter_id] = filter
        return filter

    @classmethod
    def load_from_json(cls, json_filter):
        try:
            name = json_filter["id"]
            type = json_filter["type"]
            if type == "basic":
                filter_class = NAME2BASIC[name]
                filter = filter_class(json_filter["value"]["tag"], \
                        json_filter["value"]["pattern"])
            elif type == "complex":
                filter = NAME2COMPLEX[name]()
                for f in json_filter["value"]:
                    filter.combine(MediaFilter.load_from_json(f))
            else:
                raise TypeError
            return filter
        except Exception, err:
            raise DeejaydError(_("%s is not a json encoded filter: %s")\
                                % (json_filter, err))

    def __init__(self, db_id=None):
        self.db_id = db_id

    def get_identifier(self):
        return self.__class__.__name__.lower()

    def get_name(self):
        return self.__class__.__name__.lower()

    def __str__(self):
        return NotImplementedError

    def get_id(self):
        return self.db_id

    def save(self):
        cursor = DatabaseConnection().cursor()

        query = EditRecordQuery(self.CLASS_TABLE)
        query.add_value('type', self.TYPE)
        if self.db_id is not None:
            query.set_update_id(self.PRIMARY_KEY, self.db_id)
        cursor.execute(query.to_sql(), query.get_args())
        if self.db_id is None:
            self.db_id = DatabaseConnection().get_last_insert_id(cursor)

        cursor.close()
        return self.db_id

    def erase_from_db(self):
        if self.db_id is not None:
            DeleteQuery(self.CLASS_TABLE)\
                        .append_where("filter_id = %s", (self.db_id,))\
                        .execute()
            self.db_id = None

    def to_json(self):
        raise NotImplementedError

    def to_json_str(self):
        obj = self.to_json()
        return json.dumps(obj)

    def _get_table(self, tag, query):
        return tag == "album" and "album" or query.table_name


class BasicFilter(MediaFilter):
    type = 'basic'
    TABLE = 'filters_basicfilters'
    TYPE = 'basic'

    @classmethod
    def load_from_db(cls, filter_id):
        record = SimpleSelect(cls.TABLE)\
                              .select_column('tag', 'operator', 'pattern')\
                              .append_where("filter_id = %s", (filter_id,))\
                              .execute(expected_result="fetchone")

        if record:
            bfilter_class = NAME2BASIC[record[1]]
            f = bfilter_class(record[0], record[2], db_id=filter_id)
            return f
        return None

    def __init__(self, tag, pattern, db_id=None):
        super(BasicFilter, self).__init__(db_id=db_id)
        self.tag = tag
        self.pattern = pattern

    def equals(self, filter):
        if filter.type == 'basic' and filter.get_name() == self.get_name():
            return filter.tag == self.tag and filter.pattern == self.pattern
        return False

    def restrict(self, query):
        query.join_on_tag(self.tag)
        where_str, arg = self._match_tag(self._get_table(self.tag, query))
        if not isinstance(arg, list):
            arg = (arg,)
        query.append_where(where_str, arg)

    def _match_tag(self, table):
        raise NotImplementedError

    def __str__(self):
        return self.repr_str % (self.tag, self.pattern)

    def save(self):
        new = self.db_id is None
        super(BasicFilter, self).save()

        query = EditRecordQuery(self.TABLE)
        if new:
            query.add_value(self.PRIMARY_KEY, self.db_id)
        else:
            query.set_update_id(self.PRIMARY_KEY, self.db_id)
        query.add_value('tag', self.tag)\
             .add_value('operator', self.get_name())\
             .add_value('pattern', self.pattern)\
             .execute()
        return self.db_id

    def erase_from_db(self):
        if self.db_id is not None:
            DeleteQuery(self.TABLE)\
                        .append_where("filter_id = %s", (self.db_id,))\
                        .execute()
            super(BasicFilter, self).erase_from_db()

    def to_json(self):
        return {
            "type": self.type,
            "id": self.get_identifier(),
            "value": {"tag": self.tag, "pattern": self.pattern},
            }


class Equals(BasicFilter):
    repr_str = "(%s == '%s')"
    def _match_tag(self, table):
        return "(%s.%s = " % (table, self.tag) + "%s)", self.pattern

class NotEquals(BasicFilter):
    repr_str = "(%s != '%s')"
    def _match_tag(self, table):
        return "(%s.%s != " % (table, self.tag) + "%s)", self.pattern

class StartsWith(BasicFilter):
    repr_str = "(%s == '%s%%')"
    def _match_tag(self, table):
        return "(%s.%s LIKE " % (table, self.tag) + "%s)", self.pattern + "%%"

class Contains(BasicFilter):
    repr_str = "(%s == '%%%s%%')"
    def _match_tag(self, table):
        return "(%s.%s LIKE " % (table, self.tag) + "%s)", "%%" + self.pattern + "%%"

class NotContains(BasicFilter):
    repr_str = "(%s != '%%%s%%')"
    def _match_tag(self, table):
        return "(%s.%s NOT LIKE " % (table, self.tag) + "%s)", "%%" + self.pattern + "%%"

class Regexi(BasicFilter):
    repr_str = "(%s ~ /%s/)"

class Higher(BasicFilter):
    repr_str = "(%s >= %s)"
    def _match_tag(self, table):
        return "(%s.%s >= " % (table, self.tag) + "%s)", self.pattern

class Lower(BasicFilter):
    repr_str = "(%s <= %s)"
    def _match_tag(self, table):
        return "(%s.%s <= " % (table, self.tag) + "%s)", self.pattern

class In(BasicFilter):
    repr_str = "(%s in (%s))"

    def __init__(self, tag, pattern, db_id=None):
        if isinstance(pattern, list):
            pattern = ",".join(map(str, pattern))
        super(In, self).__init__(tag, pattern, db_id=db_id)

    def _match_tag(self, table):
        keys = self.pattern.split(",")
        q = ",".join(map(lambda k: "%s", keys))
        return "(%s.%s IN (%s))" % (table, self.tag, q), keys

BASIC_FILTERS = (
                  Equals,
                  NotEquals,
                  StartsWith,
                  Contains,
                  NotContains,
                  Regexi,
                  Higher,
                  Lower,
                  In,
                )

NAME2BASIC = dict([(x(None, None).get_identifier(), x) for x in BASIC_FILTERS])


class ComplexFilter(MediaFilter):
    type = 'complex'
    TABLE = 'filters_complexfilters'
    SUBFILTERS_TABLE = 'filters_complexfilters_subfilters'
    TYPE = 'complex'

    @classmethod
    def load_from_db(cls, filter_id):
        record = SimpleSelect(cls.TABLE)\
                              .select_column('combinator')\
                              .append_where("filter_id = %s", (filter_id,))\
                              .execute(expected_result="fetchone")

        if record:
            cfilter = NAME2COMPLEX[record[0]](db_id=filter_id)

            sf_records = SimpleSelect(cls.SUBFILTERS_TABLE)\
                        .select_column('filter_id')\
                        .append_where("complexfilter_id = %s", (filter_id,))\
                        .execute()
            for sf_record in sf_records:
                sf_id = sf_record[0]
                cfilter.combine(MediaFilter.load_from_db(sf_id))
            return cfilter
        return None

    def __init__(self, *__args, **__kwargs):
        db_id = "db_id" in __kwargs and __kwargs["db_id"] or None
        super(ComplexFilter, self).__init__(db_id=db_id)

        self.filterlist = []
        for filter in __args:
            self.combine(filter)

    def combine(self, filter):
        if filter is not None:
            self.filterlist.append(filter)

    def equals(self, filter):
        if filter.type == 'complex' and len(filter) == len(self.filterlist):
            for ft in self.filterlist:
                if not filter.find_filter(ft): return False
            return True
        return False

    def find_filter_by_tag(self, tag):
        return [ft for ft in self.filterlist\
            if ft.type == 'basic' and ft.tag == tag]

    def find_filter_by_name(self, name):
        return [ft for ft in self.filterlist if ft.get_name() == name]

    def find_filter(self, filter):
        return [ft for ft in self.filterlist if ft.equals(filter)]

    def remove_filter(self, filter):
        filters = self.find_filter(filter)
        if not filters:
            raise ValueError
        for ft in filters: self.filterlist.remove(ft)

    def __iter__(self):
        return iter(self.filterlist)

    def __getitem__(self, idx):
        return self.filterlist[idx]

    def __len__(self):
        return len(self.filterlist)

    def __str__(self):
        filters_str = map(str, self.filterlist)
        return "(%s)" % self.repr_joiner.join(filters_str)

    def restrict(self, query):
        if self.filterlist:
            where_str, args = self._build_wheres(query)
            query.append_where(where_str, args)

    def _build_wheres(self, query):
        if not self.filterlist: return "(1)", []
        wheres, wheres_args = [], []
        for f in self.filterlist:
            if f.type == "basic":
                query.join_on_tag(f.tag)
                where_query, arg = f._match_tag(\
                        self._get_table(f.tag, query))
                wheres.append(where_query)
                wheres_args.append(arg)
            else:  # complex filter
                where_query, args = f._build_wheres(query)
                wheres.append(where_query)
                wheres_args.extend(args)
        return "(%s)" % (self.combinator.join(wheres),), wheres_args

    def save(self):
        new = self.db_id is None
        super(ComplexFilter, self).save()

        query = EditRecordQuery(ComplexFilter.TABLE)
        if new:
            query.add_value(self.PRIMARY_KEY, self.db_id)
        else:
            query.set_update_id(self.PRIMARY_KEY, self.db_id)
        query.add_value('combinator', self.get_name())\
             .execute()

        for subfilter in self.filterlist:
            subfilter_id = subfilter.save()
            query = ReplaceQuery(self.SUBFILTERS_TABLE)\
                              .add_value('complexfilter_id', self.db_id)\
                              .add_value('filter_id', subfilter_id)\
                              .execute()

        return self.db_id

    def erase_from_db(self):
        if self.db_id is not None:
            subfilters = SimpleSelect(self.SUBFILTERS_TABLE)\
                        .select_column('filter_id')\
                        .append_where("complexfilter_id = %s", (self.db_id,))\
                        .execute()
            for (id,) in subfilters:
                f = MediaFilter.load_from_db(id)
                if f is not None: f.erase_from_db()

            DeleteQuery(self.SUBFILTERS_TABLE)\
                        .append_where("complexfilter_id = %s", (self.db_id,))\
                        .execute()
            DeleteQuery(self.TABLE)\
                        .append_where("filter_id = %s", (self.db_id,))\
                        .execute()
            super(ComplexFilter, self).erase_from_db()

    def to_json(self):
        return {
            "type": self.type,
            "id": self.get_identifier(),
            "value": [f.to_json() for f in self.filterlist]
            }


class And(ComplexFilter):
    repr_joiner = " && "
    combinator = ' AND '

class Or(ComplexFilter):
    repr_joiner = " || "
    combinator = ' OR '


COMPLEX_FILTERS = (
                    And,
                    Or,
                  )

NAME2COMPLEX = dict([(x().get_identifier(), x) for x in COMPLEX_FILTERS])

# vim: ts=4 sw=4 expandtab
