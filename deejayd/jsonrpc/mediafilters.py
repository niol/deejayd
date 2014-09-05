# Deejayd, a media player daemon
# Copyright (C) 2014 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

from .. import DeejaydError
from . import json


class MediaFilter(object):
    TYPE = 'none'
    db_id = None

    def get_identifier(self):
        return self.__class__.__name__.lower()

    def get_name(self):
        return self.__class__.__name__.lower()

    def __str__(self):
        return NotImplementedError

    def to_json(self):
        raise NotImplementedError

    def to_json_str(self):
        obj = self.to_json()
        return json.dumps(obj)


class BasicFilter(MediaFilter):
    type = 'basic'
    TYPE = 'basic'

    def __init__(self, tag, pattern):
        super(BasicFilter, self).__init__()
        self.tag = tag
        self.pattern = pattern

    def equals(self, filter):
        if filter.type == 'basic' and filter.get_name() == self.get_name():
            return filter.tag == self.tag and filter.pattern == self.pattern
        return False

    def _match_tag(self, table):
        raise NotImplementedError

    def __str__(self):
        return self.repr_str % (self.tag, self.pattern)

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

    def __init__(self, tag, pattern):
        if isinstance(pattern, list):
            pattern = ",".join(map(str, pattern))
        super(In, self).__init__(tag, pattern)

    def _match_tag(self, table):
        keys = self.pattern.split(",")
        q = ",".join(map(lambda k: "%s", keys))
        return "(%s.%s IN (%s))" % (table, self.tag, q), keys


class ComplexFilter(MediaFilter):
    type = 'complex'
    TYPE = 'complex'

    def __init__(self, *__args, **__kwargs):
        super(ComplexFilter, self).__init__()

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


class FilterFactory(object):

    def __init__(self):
        self.load_filters()
        self.NAME2COMPLEX = dict([(x().get_identifier(), x)
                                  for x in self.COMPLEX_FILTERS])
        self.NAME2BASIC = dict([(x(None, None).get_identifier(), x)
                                for x in self.BASIC_FILTERS])


    def load_filters(self):
        self.BASIC_FILTERS = (
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
        self.COMPLEX_FILTERS = (
            And,
            Or,
        )

    def load_from_json(self, json_filter):
        try:
            name = json_filter["id"]
            type = json_filter["type"]
            if type == "basic":
                filter_class = self.NAME2BASIC[name]
                filter = filter_class(json_filter["value"]["tag"], \
                        json_filter["value"]["pattern"])
            elif type == "complex":
                filter = self.NAME2COMPLEX[name]()
                for f in json_filter["value"]:
                    filter.combine(self.load_from_json(f))
            else:
                raise TypeError
            return filter
        except Exception, err:
            raise DeejaydError(_("%s is not a json encoded filter: %s")\
                                % (json_filter, err))


filter_factory = FilterFactory()


# vim: ts=4 sw=4 expandtab
