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
from deejayd.models.library import LibraryFile, LibraryFileInfo
from sqlalchemy.orm import relationship
from sqlalchemy import or_, and_
from sqlalchemy import Column, Integer, Unicode, ForeignKey, Table, String

##############################################################################
#   MediaFilter Models
##############################################################################
class MediaFilter(Base):
    __tablename__ = 'filters'
    
    id = Column(Integer, primary_key=True)
    type = Column('type', String(50))
    __mapper_args__ = {
            'polymorphic_on': type,
            'with_polymorphic':'*',
    }
    
    def filter(self, q):
        if self.type == "basic":
            pass

subfilters = Table('filters_complexfilters_subfilters', Base.metadata,
     Column('complexfilter_id', Integer, ForeignKey('filters_complexfilters.filter_id')),
     Column('filter_id', Integer, ForeignKey('filters.id'))
)

class MediaBasicFilter(MediaFilter):
    __tablename__ = 'filters_basicfilters'
    
    id = Column(Integer, ForeignKey('filters.id'), primary_key=True)
    tag =  Column(Unicode(512))
    operator =  Column(Unicode(64))
    pattern =  Column(Unicode(512))
    __mapper_args__ = {
                       'polymorphic_identity': 'basic',
                       'polymorphic_on': operator,
                       'with_polymorphic':'*',
                       }
    
    def filter(self, query): # query on LibraryFile
        return query.join("metas").filter(self._match_tag())
    
    def _match_tag(self):
        raise NotImplementedError

class Equal(MediaBasicFilter):
    __mapper_args__ = {'polymorphic_identity': u'equal'}
    
    def _match_tag(self):
        return and_(LibraryFileInfo.keyword == self.tag, 
                    LibraryFileInfo.value == self.pattern)
    
class NotEqual(MediaBasicFilter):
    __mapper_args__ = {'polymorphic_identity': u'not_equal'}
    
    def _match_tag(self):
        return and_(LibraryFileInfo.keyword == self.tag, 
                    LibraryFileInfo.value != self.pattern)

class Contains(MediaBasicFilter):
    __mapper_args__ = {'polymorphic_identity': u'contains'}

    def _match_tag(self, query):
        return and_(LibraryFileInfo.keyword == self.tag, 
                    LibraryFileInfo.value.like("%"+self.pattern+"%"))


class MediaComplexFilter(MediaFilter):
    __tablename__ = 'filters_complexfilters'
    
    id = Column(Integer, ForeignKey('filters.id'), primary_key=True)
    combinator =  Column(Unicode(64))
    filters = relationship('MediaFilter', secondary=subfilters)
    __mapper_args__ = {
                'polymorphic_identity': 'complex',
                'polymorphic_on': combinator,
                'with_polymorphic':'*',
    }
    
    def filter(self, query):
        args = []
        for f in self.filters:
            if f.type == 'basic':
                args.append(f._match_tag())
            

class And(MediaComplexFilter):
    __mapper_args__ = {'polymorphic_identity': u'and'}

class Or(MediaComplexFilter):
    __mapper_args__ = {'polymorphic_identity': u'or'}

if __name__ == "__main__":
    from deejayd.database.connection import DatabaseConnection
    DatabaseConnection.debug = True
    inst = DatabaseConnection.Instance()
    ses = inst.get_session()
    
    
# vim: ts=4 sw=4 expandtab