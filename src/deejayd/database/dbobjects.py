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


class _DBObject(object):
    pass

class NoneFilter(_DBObject):

    def __init__(self, basic_filter):
        pass

    def restrict(self, query):
        pass


class _BasicFilter(mediafilters.BasicFilter, _DBObject):

    def __init__(self, basic_filter):
        mediafilters.BasicFilter.__init__(self, basic_filter.tag,
                                                basic_filter.pattern)

    def restrict(self, query):
        query.join_on_tag(self.tag)
        where_str, arg = self._match_tag()
        query.append_where(where_str, (arg,))

    def _match_tag(self, match_value):
        raise NotImplementedError


class Equals(mediafilters.Equals, _BasicFilter):

    def _match_tag(self):
        return "(%s.value == " % (self.tag,) + "%s)", self.pattern


class NotEquals(mediafilters.NotEquals, _BasicFilter):

    def _match_tag(self):
        return "(%s.value != " % (self.tag,) + "%s)", self.pattern


class Contains(mediafilters.Contains, _BasicFilter):

    def _match_tag(self):
        return "(%s.value LIKE " % (self.tag,) + "%s)", "%%"+self.pattern+"%%"


class Regexi(mediafilters.Regexi, _BasicFilter):
    # FIXME : to implement some day
    pass


class _ComplexFilter(mediafilters.ComplexFilter, _DBObject):

    def __init__(self, complex_filter):
        filterlist = map(SQLizer().translate, complex_filter.filterlist)
        arglist = [self] + filterlist
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
