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


class MediaSelectQuery(object):

    def __init__(self):
        self.selects = []
        self.joins = []
        self.__joined_tags = []
        self.wheres, self.wheres_args = [], []
        self.orders = []
        self.id = False

    def append_where(self, where_query, args):
        self.wheres.append(where_query)
        self.wheres_args.extend(args)

    def select_id(self):
        self.id = True

    def select_tag(self, tagname):
        self.selects.append("%s.value" % tagname)
        self.join_on_tag(tagname)

    def order_by_tag(self, tagname):
        self.orders.append("%s.value" % tagname)
        self.join_on_tag(tagname)

    def join_on_tag(self, tagname):
        if tagname not in self.__joined_tags:
            self.__joined_tags.append(tagname)
            j_st = "JOIN media_info %(tag)s ON %(tag)s.id == library.id\
                                            AND %(tag)s.ikey == '%(tag)s'"\
                   % { 'tag' : tagname }
            self.joins.append(j_st)

    def __str__(self):
        orders = None
        if len(self.orders) >= 1:
            orders = 'ORDER BY ' + ', '.join(self.orders)

        return "SELECT DISTINCT %s %s FROM library %s WHERE %s %s"\
               % (self.id and 'library.id,' or '',
                  ', '.join(self.selects),
                  ' '.join(self.joins),
                  ' AND '.join(self.wheres) or 1,
                  orders or '')

    def get_args(self):
        return self.wheres_args

    def to_sql(self):
        return str(self)


def query_decorator(answer_type):
    def query_decorator_instance(func):

        def query_func(self, *__args, **__kw):
            cursor = self.connection.cursor()
            rs = func(self, cursor, *__args, **__kw)
            if answer_type == "lastid":
                rs = self.connection.get_last_insert_id(cursor)
            elif answer_type == "rowcount":
                rs = cursor.rowcount
            elif answer_type == "fetchall":
                rs = cursor.fetchall()
            elif answer_type == "fetchone":
                rs = cursor.fetchone()
            elif answer_type == "medialist":
                rs = self._medialist_answer(cursor.fetchall(),__kw['infos'])

            cursor.close()
            return rs

        return query_func

    return query_decorator_instance


# vim: ts=4 sw=4 expandtab
