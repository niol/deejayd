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

    #  force reload of icecast webradio
    cursor.execute("SELECT id FROM webradio_source WHERE name = 'icecast'")
    rs = cursor.fetchone()
    if rs is not None:
        (s_id,) = rs
        cursor.execute("DELETE FROM webradio_stats WHERE source_id = %s",\
                (s_id,))

    # remove dirlinks records which are useless now
    cursor.execute("DELETE FROM library_dir WHERE type = 'dirlink'")
    cursor.execute("ALTER TABLE library_dir RENAME TO library_dir_dirlinks")
    cursor.execute("CREATE TABLE library_dir (id integer PRIMARY KEY,\
                                              name text,\
                                              lib_type text)")
    cursor.execute("CREATE UNIQUE INDEX library_dir_name_lib_type_idx\
                    ON library_dir (name, lib_type)")
    cursor.execute("INSERT INTO library_dir(id, name, lib_type)\
                           SELECT id, name, lib_type FROM library_dir_dirlinks")
    cursor.execute("DROP TABLE library_dir_dirlinks")

    # update db version
    sql = [
        "UPDATE variables SET value = '15' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim ts=4 sw=4 expandtab
