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

__version__ = "0.14.0"


class DeejaydError(Exception):
    """General purpose error structure."""


def Singleton(singleton_cls):
    class SingletonClass(object):
        # storage for the instance reference
        __instance = None

        @classmethod
        def destroy(cls):
            if cls.__instance is not None:
                cls.__instance = None

        def __init__(self, *args, **kwargs):
            """ Create DatabaseConnection instance """
            # Check whether we already have an instance
            if self.__instance is None:
                # Create and remember instance
                self.__class__.__instance = singleton_cls(*args, **kwargs)

            # Store instance reference as the only member in the handle
            self.__dict__['_Singleton__instance'] = self.__class__.__instance

        def __getattr__(self, attr):
            """ Delegate access to implementation """
            return getattr(self.__instance, attr)

        def __setattr__(self, attr, value):
            """ Delegate access to implementation """
            return setattr(self.__instance, attr, value)

    SingletonClass.__name__ = singleton_cls.__name__
    return SingletonClass
