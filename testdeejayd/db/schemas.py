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

from deejayd.database.schema import Table, Column, Index

SCHEMAS = {
    14: {
        "tables": [
            Table('library_dir', key='id')[
                Column('id', auto_increment=True),
                Column('name'),
                Column('lib_type'),  # audio or video
                Column('type'),  # directory or dirlink
                Index(('name', 'lib_type', 'type'))],
            Table('library', key='id')[
                Column('id', auto_increment=True),
                Column('directory', type='int'),
                Column('name'),
                Column('lastmodified', type='int'),
                Index(('name', 'directory')),
                Index(('directory',), unique=False)],
            Table('media_info', key=('id', 'ikey'))[
                Column('id', type="int"),
                Column('ikey'),
                Column('value')],
            Table('cover', key='id')[
                Column('id', auto_increment=True),
                # path to the cover file or
                # hash of the picture for cover inside audio file
                Column('source'),
                Column('mime_type'),  # mime type of the cover, ex image/jpeg
                Column('lmod', type="int"),  # last modified
                Column('image', type="blob"),
                Index(('source',))],
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
            Table('webradio_source', key='id')[
                Column('id', auto_increment=True),
                Column('name'),
                Index(('name',), unique=True)],
            Table('webradio_categories', key='id')[
                Column('id', auto_increment=True),
                Column('source_id', type='int'),
                Column('name'),
                Index(('name', 'source_id'), unique=True)],
            Table('webradio', key='id')[
                Column('id', auto_increment=True),
                Column('source_id', type='int'),
                Column('cat_id', type='int'),
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
        "INSERT INTO variables VALUES('database_version','14');",
        ],
    }
}

# vim: ts=4 sw=4 expandtab