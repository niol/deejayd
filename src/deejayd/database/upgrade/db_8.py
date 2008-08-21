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

import os, urllib
from deejayd.database import schema

def upgrade(cursor, backend, config):
    # get audio/video library
    cursor.execute("SELECT * FROM audio_library;")
    audio_library = cursor.fetchall()
    cursor.execute("SELECT * FROM video_library;")
    video_library = cursor.fetchall()

    # get medialist
    cursor.execute("SELECT DISTINCT name FROM medialist ORDER BY name")
    medialist = {}
    for (name,) in cursor.fetchall():
        if name == "__videocurrent__":
            query = "SELECT l.dir, l.filename\
              FROM medialist p JOIN video_library l \
              ON p.media_id = l.id WHERE p.name = %s ORDER BY p.position"
        else:
            query = "SELECT l.dir, l.filename\
              FROM medialist p JOIN audio_library l\
              ON p.media_id = l.id WHERE p.name = %s ORDER BY p.position"
        cursor.execute(query, (name,))
        medialist[name] = cursor.fetchall()

    # erase old table
    cursor.execute("DROP TABLE audio_library")
    cursor.execute("DROP TABLE video_library")
    cursor.execute("DROP TABLE medialist")

    # create new table/indexes
    for table in schema.db_schema:
        if table.name in ("webradio", "stats", "variables"):
            continue
        for stmt in backend.to_sql(table):
            cursor.execute(stmt)
    for query in backend.custom_queries:
        cursor.execute(query)

    # set library directory
    audio_dirs, video_dirs = {}, {}
    query = "INSERT INTO library_dir (name,lib_type,type)VALUES(%s,%s,%s)"

    path = config.get("mediadb","music_directory")
    cursor.execute(query, (path.rstrip("/"), "audio", "directory")) # root
    audio_dirs[path.rstrip("/")] = cursor.lastrowid
    for id,dir,fn,type,tit,art,alb,gn,tk,date,len,bt,rpg,rpp in audio_library:
        if type != "file":
            cursor.execute(query, (os.path.join(path,dir,fn), "audio", type))
            audio_dirs[os.path.join(path,dir,fn).rstrip("/")] = cursor.lastrowid

    path = config.get("mediadb","video_directory")
    cursor.execute(query, (path.rstrip("/"), "video", "directory")) # root
    video_dirs[path.rstrip("/")] = cursor.lastrowid
    for id,dir,fn,type,tit,width,height,sub,len in video_library:
        if type != "file":
            cursor.execute(query, (os.path.join(path,dir,fn), "video", type))
            video_dirs[os.path.join(path,dir,fn).rstrip("/")] = cursor.lastrowid

    # set library files
    library_files = {}
    query = "INSERT INTO library (directory,name)VALUES(%s, %s)"
    for id,dir,fn,type,tit,art,alb,gn,tk,date,len,bt,rpg,rpp in audio_library:
        path = config.get("mediadb","music_directory")
        if type == "file":
            try: dir_id = audio_dirs[os.path.join(path,dir).rstrip("/")]
            except KeyError:
                continue
            cursor.execute(query, (dir_id,fn))
            file_id = cursor.lastrowid
            infos = {
                "type": "song",
                "filename": fn,
                "uri": "file:/%s" % urllib.quote(os.path.join(path,dir,fn)),
                "rating": "2",
                "lastplayed": "0",
                "skipcount": "0",
                "playcount": "0",
                "compilation": "0",
                "tracknumber": tk,
                "title": tit,
                "genre": gn,
                "artist": art,
                "album": alb,
                "date": date,
                "replaygain_track_gain":rpg,
                "replaygain_track_peak":rpp,
                "bitrate": bt,
                "length": len,
                "cover": "",
                }
            entries = [(file_id, k, v) for k, v in infos.items()]
            cursor.executemany("INSERT INTO media_info\
                (id,ikey,value)VALUES(%s,%s,%s)", entries)
            library_files[os.path.join(path,dir,fn)] = file_id

    for id,dir,fn,type,tit,width,height,sub,len in video_library:
        path = config.get("mediadb","video_directory")
        if type == "file":
            try: dir_id = video_dirs[os.path.join(path,dir).rstrip("/")]
            except KeyError:
                continue
            cursor.execute(query, (dir_id,fn))
            file_id = cursor.lastrowid
            infos = {
                "type": "video",
                "filename": fn,
                "uri": "file:/%s" % urllib.quote(os.path.join(path,dir,fn)),
                "rating": "2",
                "lastplayed": "0",
                "skipcount": "0",
                "playcount": "0",
                "title": tit,
                "length": len,
                "videowidth": width,
                "videoheight": height,
                "external_subtitle": sub,
                }
            entries = [(file_id, k, v) for k, v in infos.items()]
            cursor.executemany("INSERT INTO media_info\
                (id,ikey,value)VALUES(%s,%s,%s)", entries)
            library_files[os.path.join(path,dir,fn)] = file_id

    # set medialist
    for pl_name, items in medialist.items():
        cursor.execute("INSERT INTO medialist (name,type)VALUES(%s,%s)",\
                            (pl_name, "static"))
        pl_id = cursor.lastrowid
        path = config.get("mediadb","music_directory")
        if pl_name == "__videocurrent__":
            path = config.get("mediadb","video_directory")
        for item in items:
            try: file_id = library_files[os.path.join(path,item[0],item[1])]
            except KeyError:
                continue
            cursor.execute("INSERT INTO medialist_libraryitem\
                (medialist_id,libraryitem_id)VALUES(%s,%s)", (pl_id, file_id))

    # other updates
    sql = [
        "DELETE FROM variables WHERE name='songlistid'",
        "DELETE FROM variables WHERE name='repeat'",
        "DELETE FROM variables WHERE name='random'",
        "DELETE FROM variables WHERE name='qrandom'",
        "INSERT INTO variables VALUES('playlist-playorder','inorder');",
        "INSERT INTO variables VALUES('panel-playorder','inorder');",
        "INSERT INTO variables VALUES('video-playorder','inorder');",
        "INSERT INTO variables VALUES('queue-playorder','inorder');",
        "INSERT INTO variables VALUES('playlist-repeat','0');",
        "INSERT INTO variables VALUES('panel-repeat','0');",
        "INSERT INTO variables VALUES('video-repeat','0');",
        "INSERT INTO variables VALUES('panelid','1');",
        "INSERT INTO variables VALUES('panel-type','panel');",
        "INSERT INTO variables VALUES('panel-value','');",

        "UPDATE variables SET value = '8' WHERE name = 'database_version';",
        ]
    for s in sql:
        cursor.execute(s)

# vim: ts=4 sw=4 expandtab
