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


__all__ = (
            'BASIC_FILTERS', 'NAME2BASIC',
            'Equals', 'NotEquals', 'Contains', 'NotContains', 'Regexi',
            'Higher', 'Lower',
            'COMPLEX_FILTERS', 'NAME2COMPLEX',
            'And', 'Or',
          )


class MediaFilter(object):

    def get_identifier(self):
        return self.__class__.__name__.lower()

    def get_name(self):
        return self.__class__.__name__.lower()

    def __str__(self):
        return NotImplementedError


class BasicFilter(MediaFilter):
    type = 'basic'

    def __init__(self, tag, pattern):
        super(BasicFilter, self).__init__()
        self.tag = tag
        self.pattern = pattern

    def equals(self, filter):
        if filter.type == 'basic' and filter.get_name() == self.get_name():
            return filter.tag == self.tag and filter.pattern == self.pattern
        return False

    def __str__(self):
        return self.repr_str % (self.tag, self.pattern)


class Equals(BasicFilter):    repr_str = "(%s == '%s')"
class NotEquals(BasicFilter): repr_str = "(%s != '%s')"
class Contains(BasicFilter):  repr_str = "(%s == '%%%s%%')"
class NotContains(BasicFilter):  repr_str = "(%s != '%%%s%%')"
class Regexi(BasicFilter):    repr_str = "(%s ~ /%s/)"
class Higher(BasicFilter):    repr_str = "(%s >= %s)"
class Lower(BasicFilter):    repr_str = "(%s <= %s)"


BASIC_FILTERS = (
                  Equals,
                  NotEquals,
                  Contains,
                  NotContains,
                  Regexi,
                  Higher,
                  Lower,
                )

NAME2BASIC = dict([(x(None, None).get_identifier(), x) for x in BASIC_FILTERS])


class ComplexFilter(MediaFilter):
    type = 'complex'

    def __init__(*__args, **__kwargs):
        self = __args[0]
        super(ComplexFilter, self).__init__()

        self.filterlist = []
        for filter in __args[1:]:
            self.combine(filter)

    def combine(self, filter):
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


class And(ComplexFilter): repr_joiner = " && "
class Or(ComplexFilter):  repr_joiner = " || "


COMPLEX_FILTERS = (
                    And,
                    Or,
                  )

NAME2COMPLEX = dict([(x().get_identifier(), x) for x in COMPLEX_FILTERS])


# vim: ts=4 sw=4 expandtab
