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

import threading
from twisted.internet import reactor

__all__ = ['DeejaydThread', 'switch_to_python_thread']

class _DeejaydThread(object):

    def __init__(self):
        super(_DeejaydThread, self).__init__()
        self.should_stop = threading.Event()

    def start(self):
        reactor.callInThread(self.run)

    def run(self):
        raise NotImplementedError

    def close(self):
        self.should_stop.set()


class _PythonThread(threading.Thread):

    def __init__(self):
        super(_PythonThread, self).__init__()
        self.should_stop = threading.Event()

    def run(self):
        raise NotImplementedError

    def close(self):
        if self.isAlive():
            self.should_stop.set()
            self.join()


DeejaydThread = _DeejaydThread

def switch_to_python_thread():
    global DeejaydThread
    DeejaydThread = _PythonThread

# vim: ts=4 sw=4 expandtab
