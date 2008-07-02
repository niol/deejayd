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
            'BASIC_FILTERS', 'Equals', 'NotEquals', 'Contains', 'Regexi',
            'COMPLEX_FILTERS', 'And', 'Or',
          )


class MediaFilter(object):

    def get_xml_identifier(self):
        return self.__class__.__name__.lower()


class BasicFilter(MediaFilter):
    type = 'basic'

    def __init__(self, tag, pattern):
        super(BasicFilter, self).__init__()
        self.tag = tag
        self.pattern = pattern


class Equals(BasicFilter):    pass
class NotEquals(BasicFilter): pass
class Contains(BasicFilter):  pass
class Regexi(BasicFilter):    pass


BASIC_FILTERS = (
                  Equals,
                  NotEquals,
                  Contains,
                  Regexi,
                )


class ComplexFilter(MediaFilter):
    type = 'complex'

    def __init__(*__args, **__kwargs):
        self = __args[0]
        super(ComplexFilter, self).__init__()

        self.filterlist = []
        for filter in __args[1:]:
            self.filterlist.append(filter)



class And(ComplexFilter): pass
class Or(ComplexFilter):  pass


COMPLEX_FILTERS = (
                    And,
                    Or,
                  )


# vim: ts=4 sw=4 expandtab
