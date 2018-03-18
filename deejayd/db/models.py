# cc-stat-server, server to catch curentcost message and produce stat
# Copyright (C) 2013 Mickael Royer <mickael.royer@gmail.com>
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

import os.path
import base64
import time
from sqlalchemy.orm import with_polymorphic
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import or_, and_
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Unicode
from sqlalchemy import Float, LargeBinary
from sqlalchemy import Boolean, PickleType
from sqlalchemy import UniqueConstraint
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


class Library(Base):
    __tablename__ = 'library'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64))
    path = Column(Unicode(1024))


class LibraryFolder(Base):
    __tablename__ = 'library_folder'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("library_folder.id"), nullable=True)
    library_id = Column(Integer, ForeignKey("library.id"))
    name = Column(Unicode(128))
    path = Column(Unicode(1024))

    library = relationship("Library", backref="folders")
    child_folders = relationship(
        "LibraryFolder", backref=backref('parent_folder', remote_side=[id]),
        order_by="LibraryFolder.name")
    medias = relationship("Media",
                          backref="folder",
                          order_by="Media.filename",
                          cascade="save-update, delete, delete-orphan")

    def __strip_path(self):
        rel_path = self.path.replace(self.library.path, "")
        return rel_path.lstrip("/")

    def to_json(self, subfolders=False, medias=False):
        result = {
            "id": self.id,
            "name": self.name,
            "path": self.__strip_path()
        }
        if subfolders:
            result["directories"] = [f.to_json() for f in self.child_folders]
        if medias:
            result["files"] = [m.to_json() for m in self.medias]
        return result


class Media(Base):
    __tablename__ = 'media'

    m_id = Column(Integer, primary_key=True)
    folder_id = Column(Integer, ForeignKey('library_folder.id'))
    m_type = Column(Unicode(32))
    filename = Column(Unicode(128))
    length = Column(Float)
    last_modified = Column(Integer, default=-1)
    last_played = Column(Integer, nullable=True, default=None)
    last_position = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    skip_count = Column(Integer, default=0)
    rating = Column(Integer, default=2)
    uri = Column(Unicode(512))
    title = Column(Unicode(512))

    __mapper_args__ = {
        'polymorphic_on': m_type
    }

    def to_json(self):
        return {
            "m_id": self.m_id,
            "type": self.m_type,
            "filename": self.filename,
            "title": self.title,
            "play_count": self.play_count,
            "skip_count": self.skip_count,
            "rating": self.rating,
            "length": self.length,
            "uri": self.uri
        }

    def get_path(self):
        return os.path.join(self.folder.path, self.filename)


class Album(Base):
    __tablename__ = 'album'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(512))
    cover = Column(LargeBinary, nullable=True)
    cover_type = Column(Unicode(64), nullable=True)  # 'jpeg' or 'png'
    cover_lmod = Column(Integer)

    songs = relationship("Song",
                         lazy="dynamic",
                         order_by="Song.discnumber",
                         backref="album")

    def erase_cover(self):
        self.cover = None
        self.cover_type = None
        self.cover_lmod = -1

    def update_cover(self, cover, mimetype):
        self.cover = base64.b64encode(cover)
        self.cover_type = mimetype
        self.cover_lmod = int(time.time())

    def to_json(self, cover=False, songs=False):
        infos = {
            "id": self.id,
            "name": self.name,
        }
        if cover:
            infos["cover"] = {
                "data": base64.b64decode(self.cover),
                "mimetype": self.cover_type
            }
        if songs:
            infos["songs"] = [s.to_json() for s in self.songs]
            infos["length"] = sum([s["length"] for s in self.songs])
        return infos


class Song(Media):
    __tablename__ = 'song'

    m_id = Column(Integer, ForeignKey('media.m_id', ondelete='CASCADE'),
                  primary_key=True)
    album_id = Column(Integer, ForeignKey('album.id'))
    artist = Column(Unicode(128))
    genre = Column(Unicode(128))
    tracknumber = Column(Unicode(32))
    discnumber = Column(Unicode(32))
    date = Column(Unicode(16))
    replaygain_track_gain = Column(String(512))
    replaygain_track_peak = Column(String(512))
    replaygain_album_gain = Column(String(512))
    replaygain_album_peak = Column(String(512))

    __mapper_args__ = {
        'polymorphic_identity': 'song',
    }

    def to_json(self):
        result = super(Song, self).to_json()
        result.update({
            "album": self.album.name,
            "album_id": self.album.id,
            "artist": self.artist,
            "genre": self.genre,
            "date": self.date,
            "tracknumber": self.tracknumber,
            "discnumber": self.discnumber,
        })
        return result


class Video(Media):
    __tablename__ = 'video'

    m_id = Column(Integer, ForeignKey('media.m_id', ondelete='CASCADE'),
                  primary_key=True)
    width = Column(Integer)
    height = Column(Integer)
    external_subtitle = Column(Unicode(1024))
    playing_state = Column(PickleType())

    audio_channels = relationship("AudioChannel",
                                  lazy="dynamic",
                                  cascade="all, delete-orphan",
                                  order_by="AudioChannel.c_idx",
                                  backref="video")
    sub_channels = relationship("SubtitleChannel",
                                lazy="dynamic",
                                cascade="all, delete-orphan",
                                order_by="SubtitleChannel.c_idx",
                                backref="video")

    __mapper_args__ = {
        'polymorphic_identity': 'video',
    }

    def to_json(self):
        result = super(Video, self).to_json()
        result.update({
            "width": self.width,
            "height": self.height,
            "external_subtitle": self.external_subtitle,
            "audio_channels": [
                {"is_external": False, "idx": 0, "lang": "Auto"},
                {"is_external": False, "idx": -1, "lang": _("Disabled")},
            ] + [c.to_json() for c in self.audio_channels],
            "sub_channels": [
                {"is_external": False, "idx": 0, "lang": "Auto"},
                {"is_external": False, "idx": -1, "lang": _("Disabled")},
            ] + [c.to_json() for c in self.sub_channels],
            "playing_state": self.playing_state
        })
        if self.external_subtitle != "":
            result["sub_channels"].append({
                "is_external": True,
                "idx": self.sub_channels.count()+1,
                "lang": "external"
            })
        return result


class AudioChannel(Base):
    __tablename__ = 'audio_channel'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('video.m_id'))
    lang = Column(Unicode(32))
    c_idx = Column(Integer)

    def to_json(self):
        return {
            "lang": self.lang,
            "idx": self.c_idx
        }


class SubtitleChannel(Base):
    __tablename__ = 'subtitle_channel'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('video.m_id'))
    lang = Column(Unicode(32))
    c_idx = Column(Integer)
    is_external = Column(Boolean, default=False)

    def to_json(self):
        return {
            "lang": self.lang,
            "idx": self.c_idx,
            "is_external": self.is_external
        }


#
# media list related tab
#
class MediaList(Base):
    __tablename__ = "medialist"

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), unique=True)
    p_type = Column(Unicode(32))

    __mapper_args__ = {
        'polymorphic_on': p_type
    }

    def to_json(self):
        return {
            "pl_id": self.id,
            "name": self.name,
            "type": self.p_type
        }


class StaticMediaList(MediaList):
    __tablename__ = "st_medialist"

    id = Column(Integer, ForeignKey('medialist.id', ondelete='CASCADE'),
                primary_key=True)
    items = relationship("StaticMediaListItem", 
                         backref="medialist",
                         cascade="all, delete-orphan")
    __mapper_args__ = {
        'polymorphic_identity': 'static',
    }

    def get_medias(self, session, start=0, length=None):
        media_type = with_polymorphic(Media, "*")
        query = session.query(StaticMediaListItem)\
                       .filter(StaticMediaListItem.media.of_type(media_type))\
                       .filter(StaticMediaListItem.medialist == self)\
                       .offset(start)
        if length is not None:
            query = query.limit(length)
        return [it for it in query.all()]


class StaticMediaListItem(Base):
    __tablename__ = "st_medialist_item"

    id = Column(Integer, primary_key=True)
    medialist_id = Column(Integer, ForeignKey("st_medialist.id"))
    media_id = Column(Integer, ForeignKey("media.m_id"))

    media = relationship("Media")

    def to_json(self):
        result = {"id": self.id}
        result.update(self.media.to_json())
        return result


magic_pls_filters = Table('magic_pls_filter', Base.metadata,
                          Column('left_id', Integer,
                                 ForeignKey('mg_medialist.id')),
                          Column('right_id', Integer,
                                 ForeignKey('filter.id'))
                          )


class MagicMediaList(MediaList):
    __tablename__ = "mg_medialist"

    id = Column(Integer, ForeignKey('medialist.id', ondelete='CASCADE'),
                primary_key=True)
    filters = relationship("Filter", secondary=magic_pls_filters)
    use_or_filter = Column(Boolean, default=False)
    use_limit = Column(Boolean, default=False)
    limit_value = Column(Integer, default=-1)
    limit_sort_value = Column(String(512), default="Song.title")
    limit_sort_direction = Column(String(64), default="asc")
    __mapper_args__ = {
        'polymorphic_identity': 'magic',
    }

    def get_medias(self, session, start=0, length=None):
        c_ft = self.get_filter()
        db_filter = c_ft.get_filter(Song)
        medias = session.query(Song) \
                        .filter(db_filter) \
                        .all()
        return medias

    def get_filter(self):
        c_ft = self.use_or_filter and Or() or And()
        for ft in self.filters:
            c_ft.combine(ft)
        return c_ft

    def get_properties(self):
        return {
            "use-or-filter": self.use_or_filter,
            "use-limit": self.use_limit,
            "limit-value": self.limit_value,
            "limit-sort-value": self.limit_sort_value,
            "limit-sort-direction": self.limit_sort_direction
        }


#
# filter related tab
#
class Filter(Base):
    __tablename__ = "filter"

    id = Column(Integer, primary_key=True)
    f_type = Column(String(64))

    __mapper_args__ = {
        'polymorphic_on': f_type
    }


class BasicFilter(Filter):
    __tablename__ = "basic_filter"

    id = Column(Integer, ForeignKey('filter.id'), primary_key=True)
    tag = Column(String(32))
    operator = Column(String(32))
    pattern = Column(Unicode(128))

    __mapper_args__ = {
        'polymorphic_identity': 'basic',
    }

    def equals(self, ft):
        if ft.f_type == 'basic' and ft.operator == self.operator:
            return ft.tag == self.tag and ft.pattern == self.pattern
        return False

    def to_json(self):
        return {
            "type": self.f_type,
            "id": self.operator,
            "value": {"tag": self.tag, "pattern": self.pattern}

        }

    def get_filter(self, base_cls):
        if self.operator == "equals":
            return getattr(base_cls, self.tag) == self.pattern
        elif self.operator == "not_equals":
            return getattr(base_cls, self.tag) != self.pattern
        elif self.operator == "contains":
            return getattr(base_cls, self.tag).contains(self.pattern)
        elif self.operator == "startswith":
            return getattr(base_cls, self.tag).like(self.pattern+"%")
        elif self.operator == "in":
            return getattr(base_cls, self.tag).in_(self.pattern)
        return None


class Equals(object):

    def __new__(cls, tag, pattern):
        return BasicFilter(operator="equals", tag=tag, pattern=pattern)


class NotEquals(object):

    def __new__(cls, tag, pattern):
        return BasicFilter(operator="not_equals", tag=tag, pattern=pattern)


class Contains(object):

    def __new__(cls, tag, pattern):
        return BasicFilter(operator="contains", tag=tag, pattern=pattern)


class StartsWith(BasicFilter):

    def __new__(cls, tag, pattern):
        return BasicFilter(operator="startswith", tag=tag, pattern=pattern)


class In(BasicFilter):

    def __new__(cls, tag, pattern):
        return BasicFilter(operator="in", tag=tag, pattern=pattern)


filter_association_table = Table('filter_association', Base.metadata,
                                 Column('left_id', Integer,
                                        ForeignKey('complex_filter.id')),
                                 Column('right_id', Integer,
                                        ForeignKey('filter.id'))
                                 )


class ComplexFilter(Filter):
    __tablename__ = "complex_filter"

    id = Column(Integer, ForeignKey('filter.id'), primary_key=True)
    combinator = Column(String(32))
    subfilters = relationship("Filter", secondary=filter_association_table)

    __mapper_args__ = {
        'polymorphic_identity': 'complex',
    }

    def __init__(self, combinator, *ft_list):
        super(ComplexFilter, self).__init__()
        self.combinator = combinator
        self.combine(*ft_list)

    def __len__(self):
        return len(self.subfilters)

    def combine(self, *ft_list):
        for ft in ft_list:
            if ft is not None:
                self.subfilters.append(ft)

    def equals(self, t_ft):
        if t_ft.type == 'complex' and len(t_ft) == len(self.subfilters):
            for f in self.filterlist:
                if not t_ft.find_filter(f):
                    return False
            return True
        return False

    def find_filter(self, t_filter):
        return [ft for ft in self.subfilters if ft.equals(t_filter)]

    def remove_filter(self, t_filter):
        filters = self.find_filter(t_filter)
        if not filters:
            raise ValueError
        for ft in filters:
            self.subfilters.remove(ft)

    def to_json(self):
        return {
            "type": self.f_type,
            "id": self.combinator,
            "value": [f.to_json() for f in self.subfilters]
            }

    def get_filter(self, base_cls):
        filters = [f.get_filter(base_cls) for f in self.subfilters]
        if self.combinator == "and":
            return and_(*filters)
        elif self.combinator == "or":
            return or_(*filters)
        return None


class And(object):

    def __new__(cls, *ft_list):
        return ComplexFilter("and", *ft_list)


class Or(object):

    def __new__(cls, *ft_list):
        return ComplexFilter("or", *ft_list)


#
# webradio related tab
#
class WebradioSource(Base):
    __tablename__ = "webradio_source"

    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True)

    categories = relationship("WebradioCategory",
                              backref="source",
                              order_by="WebradioCategory.name",
                              cascade="delete, delete-orphan")
    webradios = relationship("Webradio",
                             backref="source",
                             order_by="Webradio.name",
                             cascade="delete, delete-orphan")


wb_association_table = Table('webradio_category_association', Base.metadata,
                             Column('left_id', Integer,
                                    ForeignKey('webradio_category.id')),
                             Column('right_id', Integer,
                                    ForeignKey('webradio.id'))
                             )


class WebradioCategory(Base):
    __tablename__ = "webradio_category"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('webradio_source.id'))
    name = Column(Unicode(128))

    UniqueConstraint('source_id', 'name', name='sname_idx')
    webradios = relationship("Webradio",
                             secondary=wb_association_table,
                             backref="categories")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name
        }


class Webradio(Base):
    __tablename__ = "webradio"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('webradio_source.id'))
    name = Column(Unicode(256))

    UniqueConstraint('source_id', 'name', name='sname_idx')
    entries = relationship("WebradioEntry",
                           backref="webradio",
                           cascade="save-update, delete, delete-orphan")

    def to_json(self):
        return {
            "w_id": self.id,
            "title": self.name,
            "urls": [e.url for e in self.entries]
        }


class WebradioEntry(Base):
    __tablename__ = "webradio_entry"

    id = Column(Integer, primary_key=True)
    webradio_id = Column(Integer, ForeignKey('webradio.id'))
    url = Column(Unicode(512))


#
# State related table
#
class State(Base):
    __tablename__ = "state"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    state = Column(PickleType)
