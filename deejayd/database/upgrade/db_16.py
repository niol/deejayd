# Deejayd, a media player daemon
# Copyright (C) 2014 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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


import os
from deejayd.database import schema


def upgrade(cursor, backend, config):
    # Create new tables and columns
    cursor.executescript("""
        ALTER TABLE library_dir ADD COLUMN parent_id INTEGER;

        CREATE TABLE song (
            id INTEGER PRIMARY KEY,
            directory INTEGER,
            filename TEXT,
            lastmodified INTEGER,
            uri TEXT,
            title TEXT,
            length INTEGER,
            skipcount INTEGER,
            playcount INTEGER,
            lastplayed INTEGER,
            rating INTEGER,
            album_id INTEGER,
            artist TEXT,
            genre TEXT,
            tracknumber TEXT,
            date TEXT,
            replaygain_track_gain TEXT,
            replaygain_track_peak TEXT,
            replaygain_album_gain TEXT,
            replaygain_album_peak TEXT,
            discnumber TEXT
        );
        CREATE UNIQUE INDEX song_filename_directory_idx ON library_dir (name, lib_type);
        CREATE INDEX song_directory_idx ON song (directory);

        CREATE TABLE album (
            id INTEGER PRIMARY KEY,
            album TEXT,
            compilation INTEGER,
            cover_type TEXT,
            cover_lmod INTEGER
        );
        CREATE UNIQUE INDEX album_album_idx ON album (album);

        CREATE TABLE artist (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE UNIQUE INDEX artist_name_idx ON artist (name);

        CREATE TABLE artist_album (
            artist_id INTEGER PRIMARY KEY,
            album_id TEXT
        );

        CREATE TABLE video (
            id INTEGER PRIMARY KEY,
            directory INTEGER,
            filename TEXT,
            uri TEXT,
            title TEXT,
            length INTEGER,
            skipcount INTEGER,
            playcount INTEGER,
            lastplayed INTEGER,
            lastpos INTEGER,
            rating INTEGER,
            lastmodified INTEGER,
            videoheight INTEGER,
            videowidth INTEGER,
            audio_channels INTEGER,
            subtitle_channels INTEGER,
            external_subtitle TEXT
        );
        CREATE UNIQUE INDEX video_filename_directory_idx ON video (filename, directory);
        CREATE INDEX video_directory_idx ON video (directory);
    """)

    # Migrate song table for songs used in playlists (id need not to change).
    # (set lastmodified to 0 to force reload of files on mediadb update).
    albums = {}
    for id, name in cursor.execute("SELECT id, name FROM medialist WHERE type='static' AND name NOT LIKE '\\_\\_%%\\_\\_' ESCAPE '\\'").fetchall():
        for song_id, directory, filename, album in cursor.execute(\
            "SELECT library.id, library.directory, library.name,\
                    media_info.value\
             FROM library, medialist_libraryitem, media_info\
             WHERE medialist_libraryitem.libraryitem_id = library.id\
             AND medialist_libraryitem.libraryitem_id\
             AND library.id = media_info.id\
             AND media_info.ikey = 'album'").fetchall():
            if album not in albums:
                cursor.execute("INSERT INTO\
                    album(album, cover_lmod) VALUES(%s, 0)", (album, ))
                albums[album] = cursor.lastrowid
            cursor.execute("INSERT INTO\
                song(id, directory, filename, lastmodified, album_id)\
                VALUES(%s, %s, %s, 0, %s)",
                (song_id, directory, filename, albums[album]))

    # Fill out parent_id
    for id, name in cursor.execute("SELECT id, name FROM library_dir").fetchall():
        parent_name = os.path.dirname(name)
        parent_id = cursor.execute("SELECT id FROM library_dir WHERE name=%s", (parent_name, )).fetchone()
        if parent_id is None:
            cursor.execute("UPDATE library_dir SET parent_id=NULL WHERE id=%s",
                           (id, ))
        else:
            cursor.execute("UPDATE library_dir SET parent_id=%s WHERE id=%s",
                           (parent_id[0], id))

    # Cleanup useless fields
    for id, name in cursor.execute("SELECT id, name FROM medialist").fetchall():
        if name in ('__djcurrent__', '__panelcurrent__', '__videocurrent__'):
            cursor.execute("DELETE FROM medialist_libraryitem WHERE medialist_id=%s", (id, ))
            cursor.execute("DELETE FROM medialist WHERE id=%s", (id, ))
    cursor.executescript("""
        DELETE FROM medialist WHERE name = '__djcurrent__';
        DELETE FROM medialist WHERE name = '__panelcurrent__';
        DELETE FROM medialist WHERE name = '__videocurrent__';

        DROP INDEX cover_source_idx;
        DROP INDEX id_key_value_1x;
        DROP INDEX id_key_value_2x;
        DROP INDEX key_value_1x;
        DROP INDEX key_value_2x;
        DROP INDEX library_directory_idx;
        DROP INDEX library_name_directory_idx;
        DROP INDEX webradio_stats_key_source_id_idx;

        DROP TABLE library;
        DROP TABLE media_info;
        DROP TABLE cover;
        DROP TABLE webradio_stats;
    """)

    cursor.execute("UPDATE variables SET value = '16' WHERE name = 'database_version';")


# vim ts=4 sw=4 expandtab
