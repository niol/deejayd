# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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


import signal

from twisted.python import log
from deejayd.ui.config import DeejaydConfig

ERROR = 0
INFO = 1
DEBUG = 2

level = DeejaydConfig().get("general","log")
log_level = {"error": ERROR, "info": INFO, \
             "debug": DEBUG}[level]


class LogFile:

    def __init__(self, path, autosignal=True):
        self.path = path
        self.open()
        if autosignal:
            self.set_reopen_signal()

    def open(self):
        try:
            self.fd = open(self.path, 'a')
        except IOError:
            sys.exit("Unable to open the log file %s" % self.path)

    def reopen(self):
        self.fd.close()
        self.open()

    def __reopen_cb(self, signal, frame):
        self.reopen()

    def set_reopen_signal(self, sig=signal.SIGHUP, callback=None):
        if not callback:
            callback = self.__reopen_cb
        signal.signal(sig, callback)


class SignaledFileLogObserver(log.FileLogObserver):

    def __init__(self, path):
        self.log_file = LogFile(path, False)
        self.log_file.open()
        self.__observe_log_file()
        self.log_file.set_reopen_signal(callback=self.__reopen_cb)

    def __observe_log_file(self):
        log.FileLogObserver.__init__(self, self.log_file.fd)

    def __reopen_cb(self, signal, frame):
        self.stop()
        self.log_file.reopen()
        self.__observe_log_file()
        self.start()


def err(err):
    log.msg(_("ERROR - %s") % err)

def msg(msg):
    log.msg(msg)

def info(msg):
    if log_level >= INFO:
        log.msg(_("INFO - %s") % msg)

def debug(msg):
    if log_level >= DEBUG:
        log.msg(_("DEBUG - %s") % msg)


# vim: ts=4 sw=4 expandtab
