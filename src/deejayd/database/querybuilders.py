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


class _DBQuery(object):

    def __init__(self, table_name):
        self.table_name = table_name

    def get_args(self):
        raise NotImplementedError

    def to_sql(self):
        return str(self)


class SimpleSelect(_DBQuery):

    def __init__(self, table_name):
        super(SimpleSelect, self).__init__(table_name)
        self.selects = []
        self.orders = []
        self.wheres, self.wheres_args = [], []

    def select_column(self, *__args, **__kw):
        for col in __args:
            self.selects.append("%s.%s" % (self.table_name, col))

    def order_by(self, column, desc = False):
        self.orders.append("%s.%s" % (self.table_name, column))

    def append_where(self, where_query, args):
        self.wheres.append(where_query)
        self.wheres_args.extend(args)

    def get_args(self):
        return self.wheres_args

    def __str__(self):
        return "SELECT DISTINCT %s FROM %s WHERE %s"\
               % ( ', '.join(self.selects),
                   self.table_name,
                   ' AND '.join(self.wheres) or 1,
                 )

class MediaSelectQuery(SimpleSelect):

    def __init__(self):
        super(MediaSelectQuery, self).__init__('library')
        self.joins = []
        self.__joined_tags = []
        self.id = False

    def select_id(self):
        self.id = True

    def select_column(self, column_name, table_name=None):
        if not table_name:
            table_name = self.table_name
        self.selects.append("%s.%s" % (table_name, column_name))

    def select_tag(self, tagname):
        self.select_column('value', tagname)
        self.join_on_tag(tagname)

    def order_by_tag(self, tagname, desc = False):
        order = "%s.value" % tagname
        if desc: order = "%s DESC" % order
        self.orders.append(order)
        self.join_on_tag(tagname)

    def join_on_tag(self, tagname):
        if tagname not in self.__joined_tags:
            self.__joined_tags.append(tagname)
            j_st = "JOIN media_info %(tag)s ON %(tag)s.id = library.id\
                                            AND %(tag)s.ikey = '%(tag)s'"\
                   % { 'tag' : tagname }
            self.joins.append(j_st)

    def __str__(self):
        orders = None
        if len(self.orders) >= 1:
            orders = 'ORDER BY ' + ', '.join(self.orders)

        return "SELECT DISTINCT %s %s FROM %s %s WHERE %s %s"\
               % (self.id and 'library.id,' or '',
                  ', '.join(self.selects),
                  self.table_name,
                  ' '.join(self.joins),
                  ' AND '.join(self.wheres) or 1,
                  orders or '')


class EditRecordQuery(_DBQuery):

    def __init__(self, table_name):
        super(EditRecordQuery, self).__init__(table_name)
        self.dbvalues = {}
        self.update_id = None

    def add_value(self, column_name, column_value):
        self.dbvalues[column_name] = column_value

    def set_update_id(self, key, id):
        self.update_key = key
        self.update_id = id

    def get_args(self):
        args = self.dbvalues.values()
        if self.update_id:
            args.append(self.update_id)
        return args

    def __str__(self):
        if self.update_id:
            sets_st = ["%s = %%s" % x for x in self.dbvalues.keys()]
            query = "UPDATE %s SET %s WHERE %s"\
                    % ( self.table_name,
                        ', '.join(sets_st),
                        "%s.%s = %%s" % (self.table_name, self.update_key),
                      )
        else:
            query = "INSERT INTO %s(%s) VALUES(%s)"\
                    % ( self.table_name,
                        ', '.join(self.dbvalues.keys()),
                        ', '.join(["%s" for x in self.get_args()]),
                      )
        return query


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
