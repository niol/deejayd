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

def upgrade(cursor):
    sql = [
        "DELETE FROM variables WHERE name = 'currentPos';",
        "INSERT INTO variables VALUES('current','-1');",
        "INSERT INTO variables VALUES('current_source','none');",
        "INSERT INTO variables VALUES('current_pos','0');",
        "INSERT INTO variables VALUES('state','stop');",
        "UPDATE variables SET value = '6' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim: ts=4 sw=4 expandtab
