# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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

from UserDict import IterableUserDict
import cPickle as pickle

from deejayd.model._model import IObjectModel
from deejayd.database.connection import DatabaseConnection
from deejayd.database.querybuilders import SimpleSelect, ReplaceQuery
from zope.interface import implements

class PersistentState(IterableUserDict):
    implements(IObjectModel)
    table_name = "variables"

    @classmethod
    def load_from_db(cls, name, default_state):
        db_cursor = DatabaseConnection.Instance().cursor()
        query = SimpleSelect(cls.table_name).select_column("value")\
                                            .append_where("name = %s" , (name,))
        db_cursor.execute(query.to_sql(), query.get_args())
        try:
            (rs,) =  db_cursor.fetchone()
            rs = cls(name, pickle.loads(str(rs)))
        except (ValueError, TypeError):
            rs = cls(name, default_state)
        db_cursor.close()
        return rs

    def __init__(self, name, data):
        IterableUserDict.__init__(self, data)
        self.name = name

    def save(self):
        db_cursor = DatabaseConnection.Instance().cursor()
        query = ReplaceQuery(self.table_name).add_value("name", self.name) \
                                 .add_value("value", pickle.dumps(self.data))
        db_cursor.execute(query.to_sql(), query.get_args())
        DatabaseConnection.Instance().commit()
        db_cursor.close()

    @classmethod
    def load_from_json(cls, json_object):
        raise NotImplementedError # not used

    def to_json(self):
        raise NotImplementedError # not used

# vim: ts=4 sw=4 expandtab
