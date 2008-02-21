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

class Table(object):
    """Declare a table in a database schema."""

    def __init__(self, name, key=[]):
        self.name = name
        self.columns = []
        self.indices = []
        self.key = key
        if isinstance(key, basestring):
            self.key = [key]

    def __getitem__(self, objs):
        self.columns = [o for o in objs if isinstance(o, Column)]
        self.indices = [o for o in objs if isinstance(o, Index)]
        return self


class Column(object):
    """Declare a table column in a database schema."""

    def __init__(self, name, type='text', size=None, auto_increment=False):
        self.name = name
        self.type = type
        self.size = size
        self.auto_increment = auto_increment


class Index(object):
    """Declare an index for a database schema."""

    def __init__(self, columns):
        self.columns = columns


db_schema_version=5
db_schema = [
    Table('audio_library', key='id')[
        Column('id', auto_increment=True),
        Column('dir'),
        Column('filename'),
        Column('type'),
        Column('title'),
        Column('artist'),
        Column('album'),
        Column('genre'),
        Column('tracknumber'),
        Column('date'),
        Column('length', type='int'),
        Column('bitrate', type='int')],
    Table('video_library', key='id')[
        Column('id', auto_increment=True),
        Column('dir'),
        Column('filename'),
        Column('type'),
        Column('title'),
        Column('videowidth'),
        Column('videoheight'),
        Column('subtitle'),
        Column('length', type='int')],
    Table('webradio', key='wid')[
        Column('wid', type='int'),
        Column('name'),
        Column('url')],
    Table('medialist', key=('name','position'))[
        Column('name'),
        Column('position', type='int'),
        Column('media_id', type='int')],
    Table('stats', key='name')[
        Column('name'),
        Column('value', type='int')],
    Table('variables', key='name')[
        Column('name'),
        Column('value')],
    ]
db_init_cmds = [
    # stats
    "INSERT INTO stats VALUES('video_library_update',0);",
    "INSERT INTO stats VALUES('audio_library_update',0);",
    "INSERT INTO stats VALUES('songs',0);",
    "INSERT INTO stats VALUES('videos',0);",
    "INSERT INTO stats VALUES('artists',0);",
    "INSERT INTO stats VALUES('albums',0);",
    "INSERT INTO stats VALUES('genres',0);",
    # variables
    "INSERT INTO variables VALUES('volume','0');",
    "INSERT INTO variables VALUES('currentPos','0');",
    "INSERT INTO variables VALUES('source','playlist');",
    "INSERT INTO variables VALUES('random','0');",
    "INSERT INTO variables VALUES('repeat','0');",
    "INSERT INTO variables VALUES('queueid','1');",
    "INSERT INTO variables VALUES('playlistid','1');",
    "INSERT INTO variables VALUES('songlistid','1');",
    "INSERT INTO variables VALUES('webradioid','1');",
    "INSERT INTO variables VALUES('dvdid','1');",
    "INSERT INTO variables VALUES('videoid','1');",
    "INSERT INTO variables VALUES('database_version','5');",
    ]

# vim: ts=4 sw=4 expandtab
