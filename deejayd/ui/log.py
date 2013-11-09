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


import signal, sys, locale

from twisted.python import log
from deejayd.ui.config import DeejaydConfig

ERROR = 0
INFO = 1
DEBUG = 2

level = DeejaydConfig().get("general","log")
log_level = {"error": ERROR, "info": INFO, \
             "debug": DEBUG}[level]


class LogFile:

    def __init__(self, path):
        self.path = path
        self.open()

    def open(self):
        try:
            self.fd = open(self.path, 'a')
        except IOError:
            sys.exit("Unable to open the log file %s" % self.path)

    def reopen(self):
        self.fd.close()
        self.open()


class SignaledFileLogObserver(log.FileLogObserver):

    def __init__(self, path):
        self.log_file = LogFile(path, False)
        self.log_file.open()
        self.__observe_log_file()

    def __observe_log_file(self):
        log.FileLogObserver.__init__(self, self.log_file.fd)

    def reopen_cb(self):
        self.stop()
        self.log_file.reopen()
        self.__observe_log_file()
        self.start()


def __log(log_msg):
    try: log.msg(log_msg.encode(locale.getpreferredencoding()))
    except UnicodeError:
        # perharps prefered encoding not correctly set, force to UTF-8
        log.msg(log_msg.encode('utf-8'))
    
def err(err, fatal = False):
    msg = _("ERROR - %s") % err
    __log(msg)
    if fatal: sys.exit(err)

def msg(msg):
    __log(msg)

def info(msg):
    if log_level >= INFO:
        msg = _("INFO - %s") % msg
        __log(msg)

def debug(msg):
    if log_level >= DEBUG:
        msg = _("DEBUG - %s") % msg
        __log(msg)


# vim: ts=4 sw=4 expandtab
