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
    webradios = cursor.execute("SELECT * FROM webradio").fetchall()
    # drop old webradio table and create new one
    cursor.execute("DROP TABLE webradio")
    for table in schema.db_schema:
        if table.name in ("webradio", "webradio_entries"):
            for stmt in backend.to_sql(table):
                cursor.execute(stmt)
    # record webradio in new table
    for wid, name, url in webradios:
        wb = cursor.execute("SELECT id from webradio WHERE name=%s",\
                            (name[:-2],))
        try:
            (id,) = wb.fetchone()
        except (TypeError, ValueError):
            cursor.execute("INSERT INTO webradio (name)VALUES(%s)",\
                           (name[:-2],))
            id = cursor.lastrowid
        cursor.execute("INSERT INTO webradio_entries \
            (webradio_id,url)VALUES(%s,%s)", (id, url))

    # remove useless state entries
    query = "DELETE FROM variables WHERE name = %s"
    cursor.executemany(query, [
                ("playlist-playorder",),
                ("video-playorder",),
                ("panel-playorder",),
                ("queue-playorder",),
                ("playlist-repeat",),
                ("video-repeat",),
                ("panel-repeat",),
                ("queueid",),
                ("playlistid",),
                ("panelid",),
                ("webradioid",),
                ("videoid",),
                ("dvdid",),
                ("panel-type",),
                ("panel-value",),
            ])

    # update db version
    sql = [
        "UPDATE variables SET value = '13' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim ts=4 sw=4 expandtab
