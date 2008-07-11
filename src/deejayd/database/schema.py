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

    def __init__(self, columns, unique = True):
        self.unique = unique
        self.columns = columns


db_schema_version=8
db_schema = [
    Table('library_dir', key='id')[
        Column('id', auto_increment=True),
        Column('name'),
        Column('lib_type'), # audio or video
        Column('type'), # directory or dirlink
        Index(('name', 'lib_type'))],
    Table('library', key='id')[
        Column('id', auto_increment=True),
        Column('directory', type='int'),
        Column('name'),
        Index(('name', 'directory')),
        Index(('directory',), unique = False)],
    Table('media_info', key=('id','ikey'))[
        Column('id', type="int"),
        Column('ikey'),
        Column('value')],
    Table('cover', key='id')[
        Column('id', auto_increment=True),
        Column('source'), # path to the cover file or audio file (internal)
        Column('lmod', type="int"), # last modified
        Column('image', type="blob"),
        Index(('source',))],
    Table('medialist', key='id')[
        Column('id', auto_increment=True),
        Column('name'),
        Column('type'), # magic or static
        Index(('name','type'))],
    Table('medialist_libraryitem', key=('position'))[
        Column('position', auto_increment=True),
        Column('medialist_id', type='int'),
        Column('libraryitem_id', type='int')],
    Table('medialist_filters', key=('filter_id'))[
        Column('filter_id', type='int'),
        Column('medialist_id', type='int'), # optional
        Column('type')], # complex or basic
    Table('medialist_basicfilters', key=('basicfilter_id'))[
        Column('basicfilter_id', type='int'),
        Column('tag'), # criterion
        Column('operator'), # equal, not equal, regex, regexi, etc.
        Column('pattern')], # matched value
    Table('medialist_complexfilters', key=('complexfilter_id'))[
        Column('complexfilter_id', type='int'),
        Column('lfilter', type='int'), # filter_id
        Column('combinator'), # AND, OR, XOR
        Column('rfilter', type='int')], # filter_id
    Table('webradio', key='wid')[
        Column('wid', type='int'),
        Column('name'),
        Column('url')],
    Table('stats', key='name')[
        Column('name'),
        Column('value', type='int')],
    Table('variables', key='name')[
        Column('name'),
        Column('value')],

    # for future use
    # Table('webradio', key='id')[
    #     Column('id', auto_increment=True),
    #     Column('name'),
    #     Index(('name',))],
    # Table('webradio_entries', key='pos')[
    #     Column('pos', auto_increment=True),
    #     Column('url'),
    #     Column('webradio_id', type='int'),
    #     Index(('url', 'webradio_id'))],
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
    "INSERT INTO variables VALUES('current','-1');",
    "INSERT INTO variables VALUES('current_source','none');",
    "INSERT INTO variables VALUES('current_pos','0');",
    "INSERT INTO variables VALUES('state','stop');",
    "INSERT INTO variables VALUES('source','playlist');",
    "INSERT INTO variables VALUES('playlist-playorder','inorder');",
    "INSERT INTO variables VALUES('video-playorder','inorder');",
    "INSERT INTO variables VALUES('panel-playorder','inorder');",
    "INSERT INTO variables VALUES('queue-playorder','inorder');",
    "INSERT INTO variables VALUES('playlist-repeat','0');",
    "INSERT INTO variables VALUES('panel-repeat','0');",
    "INSERT INTO variables VALUES('video-repeat','0');",
    "INSERT INTO variables VALUES('queueid','1');",
    "INSERT INTO variables VALUES('playlistid','1');",
    "INSERT INTO variables VALUES('panelid','1');",
    "INSERT INTO variables VALUES('webradioid','1');",
    "INSERT INTO variables VALUES('dvdid','1');",
    "INSERT INTO variables VALUES('videoid','1');",
    "INSERT INTO variables VALUES('panel-type','panel');",
    "INSERT INTO variables VALUES('panel-value','');",
    "INSERT INTO variables VALUES('database_version','8');",
    ]

# vim: ts=4 sw=4 expandtab
