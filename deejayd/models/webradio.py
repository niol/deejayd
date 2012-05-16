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
from sqlalchemy import Column, Integer, UniqueConstraint, Unicode, ForeignKey

##############################################################################
#   Webradio Models
##############################################################################
class WebradioSource(Base):
    __tablename__ = 'webradio_source'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(512), index = True, unique = True)
    # categories -> one-to-many
    categories = relationship("WebradioCategories", order_by="WebradioCategories.name")
    # stats -> one-to-many
    stats = relationship("WebradioStats", order_by="WebradioStats.key")

class WebradioCategories(Base):
    __tablename__ = 'webradio_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(512), index = True, unique = True)
    source_id = Column(Integer, ForeignKey('webradio_source.id'))
    # webradios -> one-to-many
    webradios = relationship("Webradio", order_by="Webradio.name")
    
class Webradio(Base):
    __tablename__ = 'webradio'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(512), index = True)
    cat_id = Column(Integer, ForeignKey('webradio_categories.id'))
    # entries -> one-to-many
    entries = relationship("WebradioEntries")

class WebradioEntries(Base):
    __tablename__ = 'webradio_entries'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(1024))
    webradio_id = Column(Integer, ForeignKey('webradio.id'))

class WebradioStats(Base):
    __tablename__ = 'webradio_stats'
    __table_args__ = (
        UniqueConstraint('key', 'source_id'),
    )
    
    id = Column(Integer, primary_key=True)
    key = Column(Unicode(512))
    value = Column(Unicode(512))
    source_id = Column(Integer, ForeignKey('webradio_source.id'))

# vim: ts=4 sw=4 expandtab