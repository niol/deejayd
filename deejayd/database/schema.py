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

    def __init__(self, columns, unique=True):
        self.unique = unique
        self.columns = columns


DB_SCHEMA = {
    "version": 15,
    "tables": [
        Table('library_dir', key='id')[
            Column('id', auto_increment=True),
            Column('parent_id', type='int'),
            Column('name'),
            Column('lib_type'),  # audio or video
            Index(('name', 'lib_type'))],

        # audio related tables
        Table('song', key='id')[
            Column('id', auto_increment=True),
            Column('directory', type='int'),  # foreign key to library_dir
            Column('filename'),
            Column('lastmodified', type='int'),
            Column('uri'),
            Column('title'),
            Column('length', type='int'),
            Column('skipcount', type='int'),
            Column('playcount', type='int'),
            Column('lastplayed', type='int'),
            Column('rating', type='int'),
            Column('album_id', type='int'),  # foreign key to album
            Column('artist'),
            Column('genre'),
            Column('tracknumber'),
            Column('date'),
            Column('replaygain_track_gain'),
            Column('replaygain_track_peak'),
            Column('discnumber'),
            Index(('filename', 'directory')),
            Index(('directory',), unique=False)],
        Table('album', key='id')[
            Column('id', auto_increment=True),
            Column('album'),  # foreign key to library_dir
            Column('compilation', type='int'),
            Column('cover_type'), # "image/jpeg" "image/png"
            Column('cover_lmod', type='int'),
            Index(('album',), unique=True)],
        Table('artist', key='id')[
            Column('id', auto_increment=True),
            Column('name'),  # foreign key to library_dir
            Index(('name',), unique=True)],
        Table('artist_album', key='id')[
            Column('artist_id', auto_increment=True),
            Column('album_id')],  # foreign key to library_dir

        # video related tables
        Table('video', key='id')[
            Column('id', auto_increment=True),
            Column('directory', type='int'),  # foreign key to library_dir
            Column('filename'),
            Column('uri'),
            Column('title'),
            Column('length', type='int'),
            Column('skipcount', type='int'),
            Column('playcount', type='int'),
            Column('lastplayed', type='int'),
            Column('rating', type='int'),
            Column('lastmodified', type='int'),
            Column('videoheight', type='int'),
            Column('videowidth', type='int'),
            Column('audio_channels', type='int'),
            Column('subtitle_channels', type='int'),
            Column('external_subtitle'),
            Index(('filename', 'directory')),
            Index(('directory',), unique=False)],

        # medialist related tables
        Table('medialist', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('type'),  # magic or static
            Index(('name', 'type'))],
        Table('medialist_libraryitem', key=('position'))[
            Column('position', auto_increment=True),
            Column('medialist_id', type='int'),
            Column('libraryitem_id', type='int')],
        Table('medialist_property', key=('medialist_id', 'ikey'))[
            Column('medialist_id', type='int'),
            Column('ikey'),
            Column('value')],
        Table('medialist_sorts', key=('position'))[
            Column('position', auto_increment=True),
            Column('medialist_id', type='int'),
            Column('tag'),
            Column('direction')],
        Table('medialist_filters', key=('medialist_id', 'filter_id'))[
            Column('medialist_id', type='int'),
            Column('filter_id', type='int')],

        # filter related tables
        Table('filters', key=('filter_id'))[
            Column('filter_id', auto_increment=True),
            Column('type')],  # complex or basic
        Table('filters_basicfilters', key=('filter_id'))[
            Column('filter_id', type='int'),
            Column('tag'),  # criterion
            Column('operator'),  # equal, not equal, regex, regexi, etc.
            Column('pattern')],  # matched value
        Table('filters_complexfilters', key=('filter_id'))[
            Column('filter_id', type='int'),
            Column('combinator')],  # AND, OR, XOR
        Table('filters_complexfilters_subfilters',
              key=('complexfilter_id', 'filter_id'))[
            Column('complexfilter_id', type='int'),
            Column('filter_id', type='int')],

        # webradio related tables
        Table('webradio_source', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Index(('name',), unique=True)],
        Table('webradio_categories', key='id')[
            Column('id', auto_increment=True),
            Column('source_id', type='int'),
            Column('name'),
            Index(('name', 'source_id'), unique=True)],
        Table('webradio_categories_relation', key=('cat_id', 'webradio_id'))[
            Column('cat_id', type='int'),
            Column('webradio_id', type='int'), ],
        Table('webradio', key='id')[
            Column('id', auto_increment=True),
            Column('source_id', type='int'),
            Column('name'),
            Index(('name',), unique=False)],
        Table('webradio_entries', key='id')[
            Column('id', auto_increment=True),
            Column('url'),
            Column('webradio_id', type='int'),
            Index(('url', 'webradio_id'))],
        Table('webradio_stats', key='id')[
            Column('id', auto_increment=True),
            Column('source_id', type='int'),
            Column('key'),
            Column('value'),
            Index(('key', 'source_id'), unique=True)],
        Table('stats', key='name')[
            Column('name'),
            Column('value', type='int')],
        Table('variables', key='name')[
            Column('name'),
            Column('value')],
        ],
    "initial_sql": [
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
        "INSERT INTO variables VALUES('database_version','15');",
    ],
}

# vim: ts=4 sw=4 expandtab
