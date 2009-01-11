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

from deejayd.database import schema

def upgrade(cursor, backend, config):
    # create new table medialist_sorts
    for table in schema.db_schema:
        if table.name != "medialist_sorts": continue
        for stmt in backend.to_sql(table):
            cursor.execute(stmt)

    # remove compilation tag and add various_artist tag
    query = "SELECT id FROM media_info WHERE ikey='compilation' and value='1'"
    cursor.execute(query)
    cursor.executemany("INSERT INTO media_info (id,ikey,value)\
            VALUES(%s,%s,%s)", [(id,"various_artist","__various__")\
            for (id,) in cursor.fetchall()])

    query = "SELECT m.id, m.value FROM media_info m\
            JOIN media_info m1 ON m.id = m1.id\
            WHERE m1.ikey='compilation' and m1.value='0' and m.ikey='artist'"
    cursor.execute(query)
    cursor.executemany("INSERT INTO media_info (id,ikey,value)\
            VALUES(%s,%s,%s)", [(id,"various_artist",artist)\
            for (id,artist) in cursor.fetchall()])

    query = "DELETE FROM media_info WHERE ikey='compilation'"
    cursor.execute(query)

    # update db version
    sql = [
        "UPDATE variables SET value = '10' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim ts=4 sw=4 expandtab
