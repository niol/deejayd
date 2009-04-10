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
    # get covers
    cursor.execute("SELECT * FROM cover;")
    covers = cursor.fetchall()

    # drop old table
    cursor.execute("DROP TABLE cover")
    # create new table
    for table in schema.db_schema:
        if table.name != "cover": continue
        for stmt in backend.to_sql(table):
            cursor.execute(stmt)

    query = "INSERT INTO cover (id,source,mime_type,lmod,image)\
            VALUES(%s,%s,%s,%s,%s)"
    for (id, source, lmod, img) in covers:
        mime = "image/jpeg"
        cursor.execute(query, (id, source, mime, lmod, img))

    sql = [
        "UPDATE variables SET value = '9' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim: ts=4 sw=4 expandtab
