# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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


import re
from deejayd import mediafilters
from deejayd.database.querybuilders import EditRecordQuery


class _DBObject(object):

    def __init__(self):
        self.id = None

    def save(self, db):
        raise NotImplementedError


class NoneFilter(_DBObject):

    CLASS_TABLE = 'filters'
    PRIMARY_KEY = 'filter_id'
    TYPE = 'none'

    def __init__(self):
        super(NoneFilter, self).__init__()
        self.id = None

    def restrict(self, query):
        pass

    def save(self, db):
        cursor = db.connection.cursor()

        query = EditRecordQuery(self.CLASS_TABLE)
        query.add_value('type', self.TYPE)
        if self.id:
            query.set_update_id(self.PRIMARY_KEY, self.id)
        cursor.execute(query.to_sql(), query.get_args())
        if not self.id:
            self.id = db.connection.get_last_insert_id(cursor)

        cursor.close()

        return self.id


class _BasicFilter(mediafilters.BasicFilter, NoneFilter):

    TABLE = 'filters_basicfilters'
    TYPE = 'basic'

    def __init__(self, basic_filter):
        NoneFilter.__init__(self)
        mediafilters.BasicFilter.__init__(self, basic_filter.tag,
                                                basic_filter.pattern)

    def restrict(self, query):
        query.join_on_tag(self.tag)
        where_str, arg = self._match_tag()
        query.append_where(where_str, (arg,))

    def _match_tag(self, match_value):
        raise NotImplementedError

    def save(self, db):
        if not self.id:
            new = True
        else:
            new = False

        super(_BasicFilter, self).save(db)

        cursor = db.connection.cursor()

        query = EditRecordQuery(self.TABLE)
        if new:
            query.add_value(self.PRIMARY_KEY, self.id)
        else:
            query.set_update_id(self.PRIMARY_KEY, self.id)
        query.add_value('tag', self.tag)
        query.add_value('operator', self.get_name())
        query.add_value('pattern', self.pattern)
        cursor.execute(query.to_sql(), query.get_args())

        cursor.close()

        return self.id


class Equals(mediafilters.Equals, _BasicFilter):

    def _match_tag(self):
        return "(%s.value = " % (self.tag,) + "%s)", self.pattern


class NotEquals(mediafilters.NotEquals, _BasicFilter):

    def _match_tag(self):
        return "(%s.value != " % (self.tag,) + "%s)", self.pattern


class Contains(mediafilters.Contains, _BasicFilter):

    def _match_tag(self):
        return "(%s.value LIKE " % (self.tag,) + "%s)", "%%"+self.pattern+"%%"


class Regexi(mediafilters.Regexi, _BasicFilter):
    # FIXME : to implement some day
    pass


class _ComplexFilter(mediafilters.ComplexFilter, NoneFilter):

    TABLE = 'filters_complexfilters'
    TYPE = 'complex'

    def __init__(self, complex_filter):
        self.sqlfilterlist = map(SQLizer().translate, complex_filter.filterlist)
        arglist = [self] + self.sqlfilterlist
        mediafilters.ComplexFilter.__init__(*arglist)

    def restrict(self, query):
        if self.filterlist:
            where_str, args = self._build_wheres(query)
            query.append_where(where_str, args)

    def _build_wheres(self, query):
        wheres, wheres_args = [], []
        for filter in self.filterlist:
            if filter.type == "basic":
                query.join_on_tag(filter.tag)
                where_query, arg = filter._match_tag()
                wheres.append(where_query)
                wheres_args.append(arg)
            else: # complex filter
                where_query, args = filter._build_wheres(query)
                wheres.append(where_query)
                wheres_args.extend(args)
        return "(%s)" % (self.combinator.join(wheres),), wheres_args

    def save(self, db):
        if not self.id:
            new = True
        else:
            new = False
        super(_ComplexFilter, self).save(db)

        cursor = db.connection.cursor()

        query = EditRecordQuery(_ComplexFilter.TABLE)
        if new:
            query.add_value(self.PRIMARY_KEY, self.id)
        else:
            query.set_update_id(self.PRIMARY_KEY, self.id)
        query.add_value('combinator', self.get_name())
        cursor.execute(query.to_sql(), query.get_args())

        for subfilter in self.sqlfilterlist:
            subfilter_id = subfilter.save(db)
            query = EditRecordQuery('filters_complexfilters_subfilters')
            query.add_value('complexfilter_id', self.id)
            query.add_value('filter_id', subfilter_id)
            cursor.execute(query.to_sql(), query.get_args())

        cursor.close()

        return self.id


class And(mediafilters.And, _ComplexFilter): combinator = ' AND '
class Or(mediafilters.Or, _ComplexFilter):   combinator = ' OR '


class SQLizer(object):

    translations = {
                     mediafilters.Equals :    Equals,
                     mediafilters.NotEquals : NotEquals,
                     mediafilters.Contains :  Contains,
                     mediafilters.Regexi :    Regexi,
                     mediafilters.And :       And,
                     mediafilters.Or :        Or,
                   }

    def translate(self, object):
        if object == None:
            return NoneFilter(object)
        object_class = SQLizer.translations[object.__class__]
        return object_class(object)

# vim: ts=4 sw=4 expandtab
