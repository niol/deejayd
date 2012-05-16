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

from deejayd.models import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Enum, Unicode, ForeignKey, Table, Index

##############################################################################
#   MediaList Models
##############################################################################
medialist_filters = Table('medialist_filters', Base.metadata,
     Column('medialist_id', Integer, ForeignKey('medialist.id')),
     Column('filter_id', Integer, ForeignKey('filters.id'))
)

class MediaList(Base):
    __tablename__ = 'medialist'
    __table_args__ = (
        Index('idx_medialist', 'name', 'type', unique = True),
    )
    
    id = Column(Integer, primary_key=True)
    name =  Column(Unicode(512))
    type = Column(Enum("static", "magic"))
    # items -> one-to-many relation
    items = relationship("MediaListLibrayItem", backref="medialist")
    # properties -> one-to-many relation
    properties = relationship("MediaListProperty")
    # sorts -> one-to-many
    sorts = relationship("MediaListSort", order_by="MediaListSort.position")
    # filters -> many-to-many
    filters = relationship('MediaFilter', secondary=medialist_filters)

class MediaListLibrayItem(Base):
    __tablename__ = 'medialist_library_item'
    
    position = Column(Integer, primary_key=True)
    medialist_id = Column(Integer, ForeignKey('medialist.id'))
    libraryfile_id = Column(Integer, ForeignKey('library_file.id'))
    
    # media -> one-to-many
    media = relationship("LibraryFile")

class MediaListProperty(Base):
    __tablename__ = 'medialist_property'
    __table_args__ = (
        Index('idx_medialist_property', 'medialist_id', 'property', unique = True),
    )
    
    id = Column(Integer, primary_key=True)
    property = Column(Unicode(512))
    value = Column(Unicode(512))
    medialist_id = Column(Integer, ForeignKey('medialist.id'))
    
class MediaListSort(Base):
    __tablename__ = 'medialist_sort'
    
    position = Column(Integer, primary_key=True)
    tag = Column(Unicode(512))
    direction = Column(Unicode(512))
    medialist_id = Column(Integer, ForeignKey('medialist.id'))
    
# vim: ts=4 sw=4 expandtab