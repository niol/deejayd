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

import time, base64
from zope.interface import implements
from UserDict import IterableUserDict

from deejayd.model._model import IObjectModel
from deejayd.model.mediafilters import DEFAULT_AUDIO_SORT, DEFAULT_VIDEO_SORT
from deejayd.database.connection import DatabaseConnection
from deejayd.database.querybuilders import ReplaceQuery
from deejayd.database.querybuilders import DeleteQuery, EditRecordQuery

class _MediaItem(IterableUserDict):
    implements(IObjectModel)
    TABLE = "library"
    TYPE = ""
    INFO_TABLE = "media_info"
    COMMON_ATTRIBUTES = (
        "filename",
        "uri",
        "type",
        "title",
        "length"
    )
    PERSISTENT_ATTRIBUTES = (
        "rating",
        "skipcount",
        "playcount",
        "lastplayed"
    )
    ATTRIBUTES = []

    @classmethod
    def attributes(cls):
        return cls.COMMON_ATTRIBUTES + cls.ATTRIBUTES + \
             cls.PERSISTENT_ATTRIBUTES

    def __init__(self, infos, db_id=None):
        attr = ["media_id"] + list(self.attributes())
        self.data = dict(map(lambda k, v: (k, v), attr, infos))

    def played(self):
        played = int(self.data["playcount"]) + 1
        timestamp = int(time.time())
        self.data.update({"playcount":str(played), "lastplayed":str(timestamp)})
        self.save(commit=True)

    def skip(self):
        skip = int(self.data["skipcount"]) + 1
        self.data["skipcount"] = str(skip)
        self.save(commit=True)

    def erase_from_db(self, commit=False):
        if self.db_id is not None:
            for table in (self.TABLE, self.INFO_TABLE):
                DeleteQuery(table).append_where("id = %s", (self.db_id,))\
                                  .execute(commit)
            self.db_id = None

    def to_json(self):
        return dict(self.data)

    def save(self, commit=False):
        cursor = DatabaseConnection().cursor()

        query = EditRecordQuery(self.TABLE)
        for k in ('directory', 'name', 'lastmodified'):
            query.add_value(k, self.attr[k])
        if self.db_id is not None:
            query.set_update_id(self.PRIMARY_KEY, self.db_id)
        cursor.execute(query.to_sql(), query.get_args())
        if self.db_id is None:
            self.db_id = DatabaseConnection().get_last_insert_id(cursor)

        # update meta - informations
        for k, v in self.data.items():
            ReplaceQuery(self.INFO_TABLE).add_value("ikey", k)\
                                         .add_value("value", v)\
                                         .add_value("id", self.db_id)\
                                         .execute(commit)

        cursor.close()
        if commit:
            DatabaseConnection().commit()
        return self.db_id


class AudioItem(_MediaItem):
    TYPE = "song"
    ATTRIBUTES = (
        "artist",
        "album",
        "genre",
        "tracknumber",
        "date",
        "bitrate",
        "replaygain_track_gain",
        "replaygain_track_peak",
        "various_artist",
        "discnumber"
    )

    @classmethod
    def default_sort(cls):
        return DEFAULT_AUDIO_SORT

    def get_cover(self):
        try: (id, mime, cover) = self.db.get_file_cover(self["media_id"])
        except TypeError:
            raise AttributeError
        return {"cover": base64.b64decode(cover), "id":id, "mime": mime}

    def replay_gain(self):
        """Return the recommended Replay Gain scale factor."""
        try:
            db = float(self["replaygain_track_gain"].split()[0])
            peak = self["replaygain_track_peak"] and\
                     float(self["replaygain_track_peak"]) or 1.0
        except (KeyError, ValueError, IndexError):
            return 1.0
        else:
            scale = 10.**(db / 20)
            if scale * peak > 1:
                scale = 1.0 / peak  # don't clip
            return min(15, scale)


class VideoItem(_MediaItem):
    TYPE = "video"
    ATTRIBUTES = (
        "videoheight",
        "videowidth",
        "external_subtitle",
        "audio_channels",
        "subtitle_channels"
    )

    @classmethod
    def default_sort(cls):
        return DEFAULT_VIDEO_SORT

# vim: ts=4 sw=4 expandtab