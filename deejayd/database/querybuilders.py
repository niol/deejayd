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

    def select_column(self, column_name, table_name=None):
        if not table_name:
            table_name = self.table_name
        self.selects.append("%s.%s" % (table_name, column_name))
        return self

    def __str__(self):
        return "SELECT DISTINCT %s FROM %s %s WHERE %s"\
               % (', '.join(self.selects),
                   self.table_name,
                  ' '.join(self.joins),
                   ' AND '.join(self.wheres) or 1,
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


class MediaSelectQuery(SimpleSelect):

    def __init__(self):
        super(MediaSelectQuery, self).__init__('library')
        self.joins = []
        self.limit = None
        self.__joined_tags = []
        self.id = False

    def select_id(self):
        self.id = True
        return self

    def select_column(self, column_name, table_name=None):
        if not table_name:
            table_name = self.table_name
        self.selects.append("%s.%s" % (table_name, column_name))
        return self

    def select_tag(self, tagname):
        self.select_column('value', tagname)
        self.join_on_tag(tagname)
        return self

    def select_tags(self, tags):
        for tagname in tags:
            self.select_tag(tagname)
        return self

    def order_by_tag(self, tagname, desc=False):
        order = "%s.value" % tagname
        if desc: order = "%s DESC" % order
        self.orders.append(order)
        self.join_on_tag(tagname)
        return self

    def join_on_tag(self, tagname):
        if tagname not in self.__joined_tags:
            self.__joined_tags.append(tagname)
            j_st = "JOIN media_info %(tag)s ON %(tag)s.id = library.id\
                                            AND %(tag)s.ikey = '%(tag)s'"\
                   % { 'tag' : tagname }
            self.joins.append(j_st)
        return self

    def set_limit(self, limit):
        self.limit = limit
        return self

    def __str__(self):
        orders, limit = None, None
        if len(self.orders) >= 1:
            orders = 'ORDER BY ' + ', '.join(self.orders)
        if self.limit is not None:
            limit = "LIMIT %s" % str(self.limit)


        return "SELECT DISTINCT %s %s FROM %s %s WHERE %s %s %s"\
               % (self.id and 'library.id,' or '',
                  ', '.join(self.selects),
                  self.table_name,
                  ' '.join(self.joins),
                  ' AND '.join(self.wheres) or 1,
                  orders or '',
                  limit or '')


class StaticPlaylistSelectQuery(MediaSelectQuery):

    def __init__(self, item_table, pl_id):
        super(StaticPlaylistSelectQuery, self).__init__()
        self.select_id()
        join_ml = "JOIN %s ml ON ml.libraryitem_id = library.id" % item_table
        self.joins.append(join_ml)
        self.orders.append("ml.position")
        self.append_where("ml.medialist_id = %s", (pl_id,))

    def order_by_tag(self, tagname, desc=False):
        raise NotImplementedError  # static playlist are ordered by position


class LibrarySelectQuery(MediaSelectQuery):

    def __init__(self, libdir_table):
        super(LibrarySelectQuery, self).__init__()
        join_d = "JOIN %(d)s %(d)s ON %(d)s.id = library.directory" % {"d": libdir_table}
        self.joins.append(join_d)
        self.orders += [libdir_table + ".name", self.table_name + ".name"]

    def order_by_tag(self, tagname, desc=False):
        raise NotImplementedError  # this query are ordered by folder/file name


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
