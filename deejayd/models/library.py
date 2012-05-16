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
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import Column, Integer, Enum, Unicode, ForeignKey, LargeBinary,\
                       Boolean

##############################################################################
#   Library Models
##############################################################################
class Cover(Base):
    __tablename__ = 'cover'

    id = Column(Integer, primary_key=True)
    source =  Column(Unicode(512))
    mime_type = Column(Unicode(512))
    lmod = Column(Integer)
    image = Column(LargeBinary)

class Library(Base):
    __tablename__ = 'library'

    id = Column(Integer, primary_key=True)
    name =  Column(Unicode(64))
    # one-to-many relationship
    directories = relationship("LibraryDir",
                               lazy="dynamic",
                               cascade="all, delete-orphan",
                               order_by="LibraryDir.name",
                               backref="library")


class LibraryDir(Base):
    __tablename__ = 'library_dir'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128))
    path =  Column(Unicode(512))
    islink = Column(Boolean)
    # library many-to-one relation
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    # parent folder
    parent_id = Column(Integer, ForeignKey('library_dir.id'))
    subdirs = relationship("LibraryDir",
                           cascade="all",
                           lazy='joined', join_depth=1)
    # files one-to-many
    files = relationship("LibraryFile",
                         cascade="all, delete-orphan",
                         order_by="LibraryFile.name", backref='directory')

class LibraryFile(Base):
    __tablename__ = 'library_file'

    id = Column(Integer, primary_key=True)
    name =  Column(Unicode(512))
    last_modified = Column(Integer)

    # directory many-to-one relation
    directory_id = Column(Integer, ForeignKey('library_dir.id'), nullable=False)

    # metas one-to-many
    metas = relationship("LibraryFileInfo", backref="file",
                         lazy='subquery', # load all meta by default
                         collection_class=attribute_mapped_collection('keyword'),
                         cascade="all, delete-orphan")

class LibraryFileInfo(Base):
    __tablename__ = 'library_file_info'

    id = Column(Integer, primary_key=True)
    keyword =  Column(Unicode(512))
    value =  Column(Unicode(512))

    # ForeignKey -> LibraryFile
    file_id = Column(Integer, ForeignKey('library_file.id'), nullable=False)

    def __str__(self):
        return str(self.value)

    def __unicaode__(self):
        return self.value


# vim: ts=4 sw=4 expandtab
