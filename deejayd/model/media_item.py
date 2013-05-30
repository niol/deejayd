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

import time
import os
from collections import MutableMapping

from deejayd.model.mediafilters import DEFAULT_AUDIO_SORT, DEFAULT_VIDEO_SORT
from deejayd.database.querybuilders import DeleteQuery, EditRecordQuery
from deejayd.signals import mediadb_mupdate
from deejayd import DeejaydError

class _MediaItem(MutableMapping):
    TABLE = ""
    TYPE = ""
    # attributes -> key: default_value
    COMMON_ATTRIBUTES = {
        "filename": "",
        "lastmodified": -1,
        "uri": "",
        "title": "",
        "length": 0,
    }
    PERSISTENT_ATTRIBUTES = {
        "rating": 2,
        "skipcount": 0,
        "playcount": 0,
        "lastplayed": -1,
    }
    ATTRIBUTES = {}

    @classmethod
    def attributes(cls):
        return cls.COMMON_ATTRIBUTES.keys()\
               + cls.ATTRIBUTES.keys() + \
               cls.PERSISTENT_ATTRIBUTES.keys()

    def __init__(self, library, dir, name, db_id=None, infos=None):
        self.library = library
        self.dir = dir
        self.name = name
        self.db_id = db_id
        self.dirty_keys = []

        if infos is not None:
            self.data = self._load(infos)
        else: # set default values
            self.data = {}
            for d in (self.COMMON_ATTRIBUTES, self.ATTRIBUTES,
                      self.PERSISTENT_ATTRIBUTES):
                self.data.update(d)
            self.data["filename"] = name

    def _load(self, infos):
        attr = list(self.attributes())
        return dict(map(lambda k, v: (k, v), attr, infos))

    def get_path(self):
        return os.path.join(self.dir.get_path(), self.name)

    def __getitem__(self, key):
        if key == "media_id":
            return self.db_id
        elif key == "type":
            return self.TYPE
        return self.data[key]

    def __setitem__(self, key, value):
        if key == "media_id":
            raise DeejaydError("media id can't be modified")
        if key not in ("cover", "album"):
            self.dirty_keys.append(key)
            self.data[key] = value

    def __delitem__(self, key):
        raise DeejaydError("key can't be removed from media object")

    def __iter__(self):
        return self.data.iterkeys()

    def __len__(self):
        return len(self.data)

    def played(self):
        played = int(self.data["playcount"]) + 1
        timestamp = int(time.time())
        self.data.update({"playcount":str(played), "lastplayed":str(timestamp)})
        self.save(commit=True)

    def skip(self):
        skip = int(self.data["skipcount"]) + 1
        self.data["skipcount"] = str(skip)
        self.save(commit=True)

    def erase(self, commit=False):
        if self.db_id is not None:
            DeleteQuery(self.TABLE).append_where("id = %s", (self.db_id,))\
                              .execute(commit)
            del self.library.loaded_files[self.db_id]
            mediadb_mupdate.send(sender=self, media_id=self.db_id,
                                 type="delete")
            self.db_id = None

    def to_json(self):
        rs = dict(self.data)
        rs.update({
            "media_id": self.db_id,
            "type": self.TYPE,
        })

        return rs

    def save(self, commit=False):
        if self.db_id is None:
            query = EditRecordQuery(self.TABLE) \
                    .add_value("directory", self.dir.get_id())
            for attr in self.attributes():
                query.add_value(attr, self.data[attr])
            self.db_id = query.execute(commit=commit)
            self.library.loaded_files[self.db_id] = self
            mediadb_mupdate.send(sender=self, media_id=self.db_id, type="add")
        elif self.dirty_keys:
            query = EditRecordQuery(self.TABLE)
            query.set_update_id("id", self.db_id)
            for attr in self.dirty_keys:
                query.add_value(attr, self.data[attr])
            query.execute(commit=commit)
            mediadb_mupdate.send(sender=self, media_id=self.db_id,
                                 type="update")

        return self.db_id


class AudioItem(_MediaItem):
    TYPE = "song"
    TABLE = "song"
    ATTRIBUTES = {
        "genre": "",
        "artist": "",
        "tracknumber": "",
        "date": "",
        "replaygain_track_gain": "",
        "replaygain_track_peak": "",
        "discnumber": "",
        "album_id": "-1",
    }

    @classmethod
    def default_sort(cls):
        return DEFAULT_AUDIO_SORT

    def __init__(self, library, dir, name, db_id=None, infos=None):
        self.album = None
        super(AudioItem, self).__init__(library, dir, name, db_id, infos)

    def _load(self, infos):
        data = super(AudioItem, self)._load(infos)
        self.album = self.library.get_album_with_id(data['album_id'])
        return data

    def get_album(self):
        return self.album

    def set_album(self, album):
        self.album = album
        self.data["album_id"] = album["id"]

    def __getitem__(self, key):
        if key == "album" and self.album is not None:
            return self.album["album"]
        return super(AudioItem, self).__getitem__(key)

    def to_json(self):
        rs = super(AudioItem, self).to_json()
        if self.album is not None:
            rs["album"] = self.album["album"]
        return rs

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
    TABLE = "video"
    SUB_TABLE = "external_subtitle"
    ATTRIBUTES = {
        "videoheight": 0,
        "videowidth": 0,
        "audio_channels": 0,
        "subtitle_channels": 0,
        "external_subtitle": "",
    }

    @classmethod
    def default_sort(cls):
        return DEFAULT_VIDEO_SORT

# vim: ts=4 sw=4 expandtab
