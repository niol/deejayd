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

from deejayd.database.connection import DatabaseConnection
from deejayd.database.querybuilders import SimpleSelect, ReplaceQuery

class Stats(IterableUserDict):
    table_name = "stats"

    def __init__(self):
        IterableUserDict.__init__(self)
        stats = SimpleSelect(self.table_name) \
                    .select_column("name", "value") \
                    .execute()
        self.data = dict(stats)

    def save(self):
        for key in self.data:
            ReplaceQuery(self.table_name) \
                    .add_value("name", key) \
                    .add_value("value", self.data[key]) \
                    .execute(commit=False)
        DatabaseConnection().commit()

stats = None
def get_stats():
    global stats

    if stats is None:
        stats = Stats()
    return stats

# vim: ts=4 sw=4 expandtab