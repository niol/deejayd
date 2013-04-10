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

from deejayd.database import schema

def upgrade(cursor, backend, config):
    # get recorded webradio
    cursor.execute("SELECT * FROM webradio")
    webradios = cursor.fetchall()
    cursor.execute("DROP TABLE webradio")

    for table in schema.DB_SCHEMA["tables"]:
        if table.name in ("webradio", "webradio_categories_relation"):
            for stmt in backend.to_sql(table):
                cursor.execute(stmt)

    # record webradio in new table
    for wid, s_id, c_id, name in webradios:
        cursor.execute("INSERT INTO webradio (id,name,source_id)\
                VALUES(%s,%s,%s)", (wid, name, s_id))
        cursor.execute("INSERT INTO webradio_categories_relation (cat_id,webradio_id)\
                VALUES(%s,%s)", (c_id, wid))

    # remove icecast webradio if it exists

    # update db version
    sql = [
        "UPDATE variables SET value = '15' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim ts=4 sw=4 expandtab