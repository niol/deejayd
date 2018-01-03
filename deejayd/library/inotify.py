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


import os
import functools
import twisted.internet.inotify
import twisted.python.filepath
import twisted.python._inotify
from deejayd.ui import log
from deejayd.library import pathutils
from deejayd.db.connection import Session


class DeejaydInotify(twisted.internet.inotify.INotify):
    IN_WATCH_MASK = twisted.internet.inotify.IN_DELETE | \
                    twisted.internet.inotify.IN_CREATE | \
                    twisted.internet.inotify.IN_MOVED_FROM | \
                    twisted.internet.inotify.IN_MOVED_TO | \
                    twisted.internet.inotify.IN_CLOSE_WRITE

    def __init__(self, audio_library, video_library, encoding="utf-8"):
        super(DeejaydInotify, self).__init__()

        self.__audio_library = audio_library
        self.__video_library = video_library

        for library in (self.__audio_library, self.__video_library):
            if library:
                library.watcher = self
                dcb = lambda dir_path: self.watch_dir(dir_path, library)
                pathutils.walk_and_do(library.root_path, dcb=dcb)

    def start(self):
        self.startReading()

    def close(self):
        # stop watching all
        for library in (self.__audio_library, self.__video_library):
            if library:
                library.watcher = self
                dcb = lambda dir_path: self.stop_watching_dir(dir_path)
                pathutils.walk_and_do(library.root_path, dcb=dcb)

        self.stopReading()

    def __occured_on_dirlink(self, library, file_path):
        return os.path.islink(file_path) and os.path.isdir(file_path)

    def __isdir_event(self, mask):
        return twisted.internet.inotify.IN_ISDIR & mask

    def process_event(self, ignore, filepath, mask, library, dir_path):
        # Raised events use real paths, and in the libraries, paths follow
        # symlinks on directories. Therefore, paths must be fixed to use
        # symlinks before being passed on to the library. This is why
        # the library dir_path is passed and used here.
        session = Session()
        filename = filepath.basename().decode("utf-8")
        fpath = os.path.join(dir_path, filename)

        log.debug("inotify: %s event on '%s'"
                  % (twisted.internet.inotify.humanReadableMask(mask), fpath))

        path, name = os.path.split(fpath)

        if mask & twisted.internet.inotify.IN_CREATE:
            if self.__isdir_event(mask)\
                    or self.__occured_on_dirlink(library, fpath):
                library.crawl_directory(path, name)
        elif mask & twisted.internet.inotify.IN_DELETE:
            if self.__isdir_event(mask)\
                    or self.__occured_on_dirlink(library, fpath):
                library.remove_directory(path, name)
            elif not self.__isdir_event(mask):
                library.remove_file(path, name)
        elif mask & twisted.internet.inotify.IN_MOVED_FROM:
            if not self.__isdir_event(mask):
                library.remove_file(path, name)
            else:
                library.remove_directory(path, name)
        elif mask & twisted.internet.inotify.IN_MOVED_TO:
            if not self.__isdir_event(mask):
                library.update_file(path, name)
            else:
                library.crawl_directory(path, name)
        elif mask & twisted.internet.inotify.IN_CLOSE_WRITE:
            library.update_file(path, name)

        session.commit()
        session.close()

    def watch_dir(self, dir_path, library):
        event_processor = functools.partial(self.process_event,
                                            library=library, dir_path=dir_path)
        try:
            self.watch(twisted.python.filepath.FilePath(dir_path),
                       self.IN_WATCH_MASK,
                       callbacks=[event_processor])
        except twisted.python._inotify.INotifyError:
            log.debug("inotify: dir to watch gone '%s'" % dir_path)
        else:
            log.debug("inotify: watching directory '%s'" % dir_path)

    def stop_watching_dir(self, dir_path):
        try:
            self.ignore(twisted.python.filepath.FilePath(dir_path))
        except KeyError:
            log.info("inotify: failed to stop watching directory '%s' "
                     "(not watched?)" % dir_path)
        else:
            log.debug("inotify: stopped watching directory '%s'" % dir_path)
