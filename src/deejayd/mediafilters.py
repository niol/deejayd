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


__all__ = ('Equals', 'NotEquals', 'Contains', 'Regexi',
           'And', 'Or',
          )


class MediaFilter(object):
    pass


class BasicFilter(MediaFilter):

    def __init__(self, tag, pattern):
        super(BasicFilter, self).__init__()
        self.tag = tag
        self.pattern = pattern


class Equals(BasicFilter):

    operator = 'EQUAL'


class NotEquals(BasicFilter):

    operator = 'NOT_EQUAL'


class Contains(BasicFilter):

    operator = 'CONTAINS'


class Regexi(BasicFilter):

    operator = 'REGEXI'


class ComplexFilter(MediaFilter):

    def __init__(*__args, **__kwargs):
        self = __args[0]
        super(ComplexFilter, self).__init__()

        self.filterlist = []
        for filter in __args[1:]:
            self.filterlist.append(filter)


class And(ComplexFilter):

    operator = 'AND'


class Or(ComplexFilter):

    operator = 'OR'


# vim: ts=4 sw=4 expandtab
