# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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

from deejayd.database.connection import DatabaseConnection

class _DBQuery(object):

    def __init__(self, table_name):
        self.table_name = table_name

    def get_args(self):
        raise NotImplementedError

    def to_sql(self):
        return str(self)

    def execute(self):
        raise NotImplementedError

class SimpleSelect(_DBQuery):

    def __init__(self, table_name):
        super(SimpleSelect, self).__init__(table_name)
        self.selects = []
        self.orders = []
        self.wheres, self.wheres_args = [], []

    def select_column(self, *__args, **__kw):
        for col in __args:
            self.selects.append("%s.%s" % (self.table_name, col))
        return self

    def order_by(self, column):
        self.orders.append("%s.%s" % (self.table_name, column))
        return self

    def append_where(self, where_query, args=[]):
        self.wheres.append(where_query)
        if type(args) not in (list, tuple):
            args = [args]
        self.wheres_args.extend(args)
        return self

    def get_args(self):
        return self.wheres_args

    def __str__(self):
        return "SELECT DISTINCT %s FROM %s WHERE %s"\
               % (', '.join(self.selects),
                   self.table_name,
                   ' AND '.join(self.wheres) or 1,
                 )

    def execute(self, expected_result="fetchall"):
        cursor = DatabaseConnection().cursor()
        cursor.execute(self.to_sql(), self.get_args())
        result = getattr(cursor, expected_result)()

        cursor.close()
        return result


class ComplexSelect(SimpleSelect):

    def __init__(self, table_name):
        super(ComplexSelect, self).__init__(table_name)
        self.joins = []

    def join(self, table_name, condition):
        j_sql = "JOIN %s %s ON %s" % (table_name, table_name, condition)
        self.joins.append(j_sql)
        return self

    def order_by(self, column, table_name=None, descending=False):
        if not table_name:
            table_name = self.table_name
        self.orders.append("%s.%s %s" % (table_name, column,
                                         descending and "DESC" or ""))
        return self

    def select_column(self, column_name, table_name=None):
        if not table_name:
            table_name = self.table_name
        self.selects.append("%s.%s" % (table_name, column_name))
        return self

    def __str__(self):
        orders = None
        if len(self.orders) >= 1:
            orders = 'ORDER BY ' + ', '.join(self.orders)

        return "SELECT DISTINCT %s FROM %s %s WHERE %s %s"\
               % (', '.join(self.selects),
                   self.table_name,
                  ' '.join(self.joins),
                   ' AND '.join(self.wheres) or 1,
                   orders or '',
                 )


class WebradioSelectQuery(SimpleSelect):

    def __init__(self, wb_table, url_table, cat_rel_table):
        super(WebradioSelectQuery, self).__init__(wb_table)
        self.cat_rel_table = cat_rel_table
        self.selects = [
             "%s.id" % wb_table,
             "%s.name" % wb_table,
             "GROUP_CONCAT(%s.url)" % url_table
        ]
        self.joins = [
            "JOIN %(url)s ON %(url)s.webradio_id = %(wb)s.id"\
                   % { 'url' : url_table, 'wb': self.table_name }
        ]
        self.group_by = ["%s.id" % wb_table]

    def select_category(self, cat_id):
        cat_join = "JOIN %(cat_rel)s ON %(cat_rel)s.webradio_id = %(wb)s.id"\
                   % { 'cat_rel' : self.cat_rel_table, 'wb': self.table_name }
        self.joins.append(cat_join)
        self.append_where(self.cat_rel_table + ".cat_id = %s", (cat_id,))

    def __str__(self):
        group_by = 'GROUP BY ' + ', '.join(self.group_by)
        return "SELECT DISTINCT %s FROM %s %s WHERE %s %s"\
               % (', '.join(self.selects),
                  self.table_name,
                  ' '.join(self.joins),
                  ' AND '.join(self.wheres) or 1,
                  group_by,)

class LibrarySelectQuery(ComplexSelect):
    dedicated_table = ('album',)

    def __init__(self, media_table, libdir_table):
        super(LibrarySelectQuery, self).__init__(media_table)
        self.limit = None
        self.__joined_tags = []
        self.libdir_table = libdir_table

    def set_limit(self, limit):
        self.limit = limit
        return self

    def select_dir(self):
        join_d = "JOIN %(d)s %(d)s ON %(d)s.id = %(m)s.directory" \
                 % {"d": self.libdir_table, "m": self.table_name}
        self.joins.append(join_d)
        self.selects = map(lambda a: "%s.%s" % (self.libdir_table, a),
                           ("id", "name", "parent_id"))

    def select_tag(self, tag):
        self.join_on_tag(tag)
        table = tag in self.dedicated_table and tag or self.table_name
        self.select_column(tag, table_name=table)

    def join_on_tag(self, tagname):
        if tagname in self.dedicated_table and tagname not in self.__joined_tags:
            self.__joined_tags.append(tagname)
            j_st = "JOIN %(tag)s %(tag)s ON %(tag)s.id = %(table)s.%(tag)s_id" \
                   % { 'tag' : tagname, "table": self.table_name }
            self.joins.append(j_st)
        return self

    def order_by_tag(self, tag, descending=False):
        self.join_on_tag(tag)
        table = tag in self.dedicated_table and tag or self.table_name
        return self.order_by(tag, table_name=table, descending=descending)

    def __str__(self):
        if not self.orders:
            self.orders = [self.libdir_table + ".name",
                           self.table_name + ".filename"]
        orders = 'ORDER BY ' + ', '.join(self.orders)

        limit = None
        if self.limit is not None:
            limit = "LIMIT %s" % str(self.limit)

        return "SELECT DISTINCT %s FROM %s %s WHERE %s %s %s"\
               % (', '.join(self.selects),
                  self.table_name,
                  ' '.join(self.joins),
                  ' AND '.join(self.wheres) or 1,
                  orders or '',
                  limit or '')


class _DBActionQuery(_DBQuery):

    def execute(self, commit=True, expected_result="lastid"):
        cursor = DatabaseConnection().cursor()
        cursor.execute(self.to_sql(), self.get_args())
        rs = None
        if expected_result == "lastid":
            rs = DatabaseConnection().get_last_insert_id(cursor)
        elif expected_result == "rowcount":
            rs = cursor.rowcount
        cursor.close()
        if commit:
            DatabaseConnection().commit()

        return rs

class EditRecordQuery(_DBActionQuery):

    def __init__(self, table_name):
        super(EditRecordQuery, self).__init__(table_name)
        self.dbvalues = {}
        self.update_id = None

    def add_value(self, column_name, column_value):
        self.dbvalues[column_name] = column_value
        return self

    def set_update_id(self, key, id):
        self.update_key = key
        self.update_id = id
        return self

    def get_args(self):
        args = self.dbvalues.values()
        if self.update_id:
            args.append(self.update_id)
        return args

    def __str__(self):
        if self.update_id:
            sets_st = ["%s = %%s" % x for x in self.dbvalues.keys()]
            query = "UPDATE %s SET %s WHERE %s"\
                    % (self.table_name,
                        ', '.join(sets_st),
                        "%s.%s = %%s" % (self.table_name, self.update_key),
                      )
        else:
            query = "INSERT INTO %s(%s) VALUES(%s)"\
                    % (self.table_name,
                        ', '.join(self.dbvalues.keys()),
                        ', '.join(["%s" for x in self.get_args()]),
                      )
        return query


class ReplaceQuery(EditRecordQuery):

    def __str__(self):
        return "REPLACE INTO %s(%s) VALUES(%s)"\
                % (self.table_name,
                    ', '.join(self.dbvalues.keys()),
                    ', '.join(["%s" for x in self.get_args()]),
                  )

class DeleteQuery(_DBActionQuery):

    def __init__(self, table_name):
        super(DeleteQuery, self).__init__(table_name)
        self.wheres, self.wheres_args = [], []

    def append_where(self, where_query, args):
        self.wheres.append(where_query)
        self.wheres_args.extend(args)
        return self

    def get_args(self):
        return self.wheres_args

    def __str__(self):
        return "DELETE FROM %s WHERE %s"\
               % (self.table_name,
                  ' AND '.join(self.wheres) or 1,)

# vim: ts=4 sw=4 expandtab
