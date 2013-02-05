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


import os
import sys
import functools
import twisted.internet.inotify
import twisted.python.filepath
import twisted.python._inotify
from deejayd.ui import log
import deejayd.mediadb.library
from deejayd.mediadb import pathutils


class DeejaydInotify(twisted.internet.inotify.INotify):

    IN_WATCH_MASK = twisted.internet.inotify.IN_DELETE |\
                    twisted.internet.inotify.IN_CREATE |\
                    twisted.internet.inotify.IN_MOVED_FROM |\
                    twisted.internet.inotify.IN_MOVED_TO |\
                    twisted.internet.inotify.IN_CLOSE_WRITE

    def __init__(self, db, audio_library, video_library):
        super(DeejaydInotify, self).__init__()

        self.__audio_library = audio_library
        self.__video_library = video_library
        self.__db = db

        for library in (self.__audio_library, self.__video_library):
            if library:
                library.watcher = self
                dcb = lambda dir_path: self.watch_dir(dir_path, library)
                pathutils.walk_and_do(library._path, dcb=dcb)

    def start(self):
        self.startReading()

    def close(self):
        map(self.ignore, self._watchpaths.copy()) # stop watching all
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
        filename = library.fs_charset2unicode(filepath.basename())
        fpath = library.fs_charset2unicode(os.path.join(dir_path, filename))

        log.debug("inotify: %s event on '%s'"\
                  % (twisted.internet.inotify.humanReadableMask(mask), fpath))

        path, name = os.path.split(fpath)

        library.mutex.acquire()
        if mask & twisted.internet.inotify.IN_CREATE:
            if self.__isdir_event(mask)\
            or self.__occured_on_dirlink(library, fpath):
                library.add_directory(path, name)
        elif mask & twisted.internet.inotify.IN_DELETE:
            if self.__occured_on_dirlink(library, fpath):
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
                library.add_file(path, name)
            else:
                library.add_directory(path, name)
        elif mask & twisted.internet.inotify.IN_CLOSE_WRITE:
            try:
                library.update_file(path, name)
            except deejayd.mediadb.library.NotFoundException:
                library.add_file(path, name)

        library.db_con.update_stats(library.type)
        library.db_con.connection.commit()
        library.db_con.close()
        library.mutex.release()

    def watch_dir(self, dir_path, library):
        # inotify bindings need encoded strings
        e_path = dir_path.encode(sys.getfilesystemencoding())

        event_processor = functools.partial(self.process_event,
                                            library=library, dir_path=dir_path)
        try:
            self.watch(twisted.python.filepath.FilePath(e_path),
                       self.IN_WATCH_MASK,
                       callbacks=[event_processor])
        except twisted.python._inotify.INotifyError:
            log.debug("inotify: dir to watch gone '%s'" % dir_path)
        else:
            log.debug("inotify: watching directory '%s'" % dir_path)

    def stop_watching_dir(self, dir_path):
        # inotify bindings need encoded strings
        e_path = dir_path.encode(sys.getfilesystemencoding())

        self.ignore(twisted.python.filepath.FilePath(e_path))
        log.debug("inotify: stopped watching directory '%s'" % dir_path)


# vim: ts=4 sw=4 expandtab
