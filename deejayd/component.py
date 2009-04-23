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


class SignalingComponent(object):
    SUBSCRIPTIONS = {}

    def __init__(self):
        self.__dispatcher = None

    def register_dispatcher(self, dispatcher):
        self.__dispatcher = dispatcher
        # set internal subscription
        for signame in self.SUBSCRIPTIONS.keys():
            self.__dispatcher.subscribe(signame,\
                    getattr(self, self.SUBSCRIPTIONS[signame]))

    def dispatch_signal(self, signal):
        if self.__dispatcher:
            self.__dispatcher._dispatch_signal(signal)

    def dispatch_signame(self, signal_name, attrs = {}):
        if self.__dispatcher:
            self.__dispatcher._dispatch_signame(signal_name, attrs)

# vim: ts=4 sw=4 expandtab