# Deejayd, a media player daemon
# Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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
from sqlalchemy import Column, Integer, Unicode, PickleType

##############################################################################
#   State / stats Models
##############################################################################

class Stats(Base):   
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), index = True, unique = True)
    value = Column(Unicode(64))

class State(Base):   
    __tablename__ = 'state'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), index = True, unique = True)
    value = Column(PickleType)
    
# vim: ts=4 sw=4 expandtab