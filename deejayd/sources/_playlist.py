# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import random
import time
from collections import MutableMapping
from sqlalchemy.orm import with_polymorphic
from deejayd import DeejaydError
from deejayd.db.connection import Session
from deejayd.db.models import StaticMediaList, StaticMediaListItem
from deejayd.db.models import Media, Video, Song
from functools import reduce


def update_action(func):
    def new_func(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.pl_id += 1
        self.time_length = reduce(lambda t, m: t + m["length"], self.medialist, 0)

    return new_func


class PlaylistEntry(MutableMapping):

    def __init__(self, playlist, p_id, media, source):
        self.playlist = playlist
        self.id = p_id
        self.media = media.to_json()
        self.source = source
        self.desc = ""

    def __len__(self):
        return len(self.media) + 2

    def __iter__(self):
        return iter(self.media)

    def __delitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        if key in ["last_position"]:
            self.__update_media(dict([(key, value)]))

    def __getitem__(self, key):
        if key == "id":
            return self.id
        elif key == "pos":
            for index, entry in enumerate(self.playlist.medialist):
                if entry.id == self.id:
                    return index
            return -1  # entry not in the list anymore
        elif key == "source":
            return self.source
        elif key == "desc":
            return self.desc
        return self.media[key]

    def __update_media(self, attrs):
        session = Session()
        video_or_song = with_polymorphic(Media, [Song, Video])
        m_obj = Session.query(video_or_song)\
                       .filter(Media.m_id == self.media["m_id"])\
                       .one_or_none()
        if m_obj is None:
            raise DeejaydError("Weird error: media with id %d "
                               "disappear" % self.media["m_id"])
        for key in attrs:
            setattr(m_obj, key, attrs[key])
            self.media[key] = attrs[key]
        session.commit()
        Session.remove()

    def played(self):
        self.__update_media({
            "play_count": self.media["play_count"] + 1,
            "last_played": int(time.time())
        })

    def stopped(self, position):
        u_attrs = {"last_position": position}
        if position > 90 * self.media["length"] / 100:
            # If stopped after most of the track, consider played
            u_attrs.update({
                "play_count": self.media["play_count"] + 1,
                "last_played": int(time.time())
            })
        self.__update_media(u_attrs)

    def skip(self):
        self.__update_media({
            "skip_count": self.media["skip_count"] + 1
        })

    def set_description(self, desc):
        self.desc = desc

    def is_seekable(self):
        return True

    def get_uris(self):
        return [self.media["uri"]]

    def has_video(self):
        return self.media["type"] == "video"

    def need_metadata_refresh(self):
        return False

    def has_subtitle(self):
        return self.media["sub_channels"] \
                or self.media["external_subtitle"] != ""

    def replay_gain(self, profiles, pre_amp_gain=0, fallback_gain=0):
        """Return the computed Replay Gain scale factor.

        profiles is a list of Replay Gain profile names ('album',
        'track') to try before giving up. The special profile name
        'none' will cause no scaling to occur. pre_amp_gain will be
        applied before checking for clipping. fallback_gain will be
        used when the song does not have replaygain information.
        """
        if self.media["type"] == "video":
            return 1.0

        for profile in profiles:
            if profile == "none":
                return 1.0
            try:
                db = self.media.get("replaygain_%s_gain" % profile).split()[0]
                db = float(db)
                peak = self.media.get("replaygain_%s_peak" % profile, None)
                if peak is None:
                    peak = 1.0
                else:
                    peak = float(peak)
            except (AttributeError, TypeError):
                continue
            else:
                db += pre_amp_gain
                scale = 10. ** (db / 20)
                if scale * peak > 1:
                    scale = 1.0 / peak  # don't clip
                return min(15, scale)
        else:
            return min(15, 10. ** ((fallback_gain + pre_amp_gain) / 20))

    def to_json(self):
        result = {
            "id": self.id,
            "pos": self["pos"]
        }
        result.update(self.media)
        return result


class Playlist(object):

    def __init__(self, source, pl_id):
        self.source = source
        self.repeat = False
        self.plmedia_id = 0
        self.pl_id = pl_id
        self.time_length = 0

        # load recorded playlist if exist
        db_list = Session.query(StaticMediaList)\
                         .filter(StaticMediaList.name == "__"+source)\
                         .one_or_none()
        if db_list is None:
            db_list = StaticMediaList(name="__"+source)
            Session.add(db_list)
            Session.commit()
        self.medialist = [PlaylistEntry(self,
                                        self.__get_next_id(),
                                        i.media,
                                        self.source
                                        ) for i in db_list.items]
        self.time_length = reduce(lambda t, m: t + m["length"], self.medialist, 0)

    def save(self):
        db_list = Session.query(StaticMediaList)\
                         .filter(StaticMediaList.name == "__"+self.source)\
                         .one()
        db_list.items = []
        for entry in self.medialist:
            db_list.items.append(StaticMediaListItem(media_id=entry["m_id"]))
        Session.commit()

    def __get_next_id(self):
        self.plmedia_id += 1
        return self.plmedia_id

    def __len__(self):
        return len(self.medialist)

    def get_plid(self):
        return self.pl_id

    def get(self, start=0, length=None):
        if length is not None:
            stop = min(start + int(length), len(self.medialist))
        else:
            stop = len(self.medialist)
        start = min(start, stop)
        return self.medialist[start:stop]

    def get_item(self, item_id):
        return next((entry for entry in self.medialist
                     if entry["id"] == item_id), None)

    def get_item_with_pos(self, item_pos):
        return self.medialist[item_pos]

    def get_item_first(self):
        return self.medialist and self.medialist[0] or None

    def get_item_last(self):
        return self.medialist and self.medialist[-1] or None

    def get_ids(self):
        return [entry["id"] for entry in self.medialist]

    def get_time_length(self):
        return self.time_length

    def next(self, pl_entry):
        try:
            idx = self.medialist.index(pl_entry)
            if idx < len(self.medialist) - 1:
                return self.medialist[idx + 1]
        except ValueError:
            pass
        return None

    def previous(self, pl_entry):
        try:
            idx = self.medialist.index(pl_entry)
            if idx > 0:
                return self.medialist[idx - 1]
        except ValueError:
            pass
        return None

    def find(self, media_id):
        for entry in self.medialist:
            if entry["m_id"] == media_id:
                return entry
        raise ValueError

    @update_action
    def load(self, medias, queue=True):
        if not queue:
            self.medialist = []
        self.medialist += [PlaylistEntry(self, self.__get_next_id(),
                                         media, self.source
                                         ) for media in medias]

    @update_action
    def move(self, ids, new_pos):
        selected_items = [item for item in self.medialist if item["id"] in ids]
        if new_pos == -1:
            new_pos = len(self.medialist)
        s_list = [it for it in self.medialist[:new_pos] if it["id"] not in ids]
        e_list = [it for it in self.medialist[new_pos:] if it["id"] not in ids]
        self.medialist = s_list + selected_items + e_list
    
    @update_action
    def shuffle(self, current=None):
        random.shuffle(self.medialist)
        if current is not None:
            try:
                self.medialist.remove(current)
            except ValueError:
                pass
            else:
                self.medialist = [current] + self.medialist

    @update_action
    def clear(self):
        self.medialist = []

    @update_action
    def remove(self, plitem_ids):
        self.medialist = [i for i in self.medialist if i.id not in plitem_ids]
