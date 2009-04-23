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

import os, threading, traceback, Queue
from deejayd.ui import log
from deejayd.utils import str_encode
import pyinotify

#############################################################################
##### Events Watcher
#############################################################################

def log_event(func):
    def log_event_func(self, event):
        path = os.path.join(event.path.decode("utf-8"),\
                event.name.decode("utf-8"))
        try:
            event.maskname
        except AttributeError:
            event.maskname = event.event_name
        log.info(_("Inotify event %s: %s") % (event.maskname, path))
        func(self,event)

    return log_event_func

class InotifyWatcher(pyinotify.ProcessEvent):

    def __init__(self, library, queue):
        self.__library = library
        self.__queue = queue

    @log_event
    def process_IN_CREATE(self, event):
        self.__queue.put(("create", self.__library, event))

    @log_event
    def process_IN_DELETE(self, event):
        self.__queue.put(("delete", self.__library, event))

    @log_event
    def process_IN_MOVED_FROM(self, event):
        self.__queue.put(("move_from", self.__library, event))

    @log_event
    def process_IN_MOVED_TO(self, event):
        self.__queue.put(("move_to", self.__library, event))

    @log_event
    def process_IN_CLOSE_WRITE(self, event):
        self.__queue.put(("close_write", self.__library, event))

    def process_IN_IGNORED(self, event):
        # This is said to be useless in the documentation, and is
        # effectively useless for us except for adding extreme verbosity
        # to the tests. Farewell, IN_IGNORED!
        pass


class _LibraryWatcher(threading.Thread):

    def __init__(self, db, queue):
        threading.Thread.__init__(self)
        self.should_stop = threading.Event()
        self.__db = db
        self.__queue = queue
        self.__created_files = []
        self.__record = False

    def run(self):
        while not self.should_stop.isSet():
            try: type, library, event = self.__queue.get(True, 0.1)
            except Queue.Empty:
                continue
            try: self.__record = self.__execute(type,library,event)\
                    or self.__record
            except Exception, ex:
                path = str_encode(os.path.join(event.path, event.name))
                log.err(_("Inotify problem for '%s', see traceback") % path)
                log.err("------------------Traceback lines--------------------")
                log.err(traceback.format_exc())
                log.err("-----------------------------------------------------")
            if self.__record and self.__queue.empty(): # record changes
                library.inotify_record_changes()
        self.__db.close()

    def __occured_on_dirlink(self, library, event):
        if not event.name:
            return False
        file_path = os.path.join(event.path, event.name)
        if os.path.exists(file_path):
            return os.path.islink(file_path) and os.path.isdir(file_path)
        else:
            # File seems to have been deleted, so we lookup for a dirlink
            # in the library.
            return file_path in library.get_root_paths()

    def __execute(self, type, library, event):
        # first be sure that path are correct
        try:
            path = library._encode(event.path)
            name = library._encode(event.name)
        except UnicodeError: # skip this event
            return False

        if type == "create":
            if self.__occured_on_dirlink(library, event):
                return library.add_directory(path, name, True)
            elif not self.is_on_dir(event):
                self.__created_files.append((path, name))
        elif type == "delete":
            if self.__occured_on_dirlink(library, event):
                return library.remove_directory(path, name, True)
            elif not self.is_on_dir(event):
                return library.remove_file(path, name)
        elif type == "move_from":
            if not self.is_on_dir(event):
                return library.remove_file(path, name)
            else:
                return library.remove_directory(path, name)
        elif type == "move_to":
            if not self.is_on_dir(event):
                return library.add_file(path, name)
            else:
                return library.add_directory(path, name)
        elif type == "close_write":
            if (path, name) in self.__created_files:
                del self.__created_files[\
                        self.__created_files.index((path, name))]
                return library.add_file(path, name)
            else:
                return library.update_file(path, name)

        return False

    def close(self):
        self.should_stop.set()
        threading.Thread.join(self)


class LibraryWatcher(_LibraryWatcher):

    def is_on_dir(self, event):
        return event.dir


class LibraryWatcherOLD(_LibraryWatcher):

    def is_on_dir(self, event):
        return event.is_dir


#############################################################################

class _DeejaydInotify(threading.Thread):

    def __init__(self, db, audio_library, video_library):
        threading.Thread.__init__(self)
        self.should_stop = threading.Event()

        self.__audio_library = audio_library
        self.__video_library = video_library
        self.__db = db
        self.__queue = Queue.Queue(1000)

        self.__wm = pyinotify.WatchManager()
        self.__watched_dirs = {}
        self.EVENT_MASK = self.watched_events_mask()

    def is_watched (self, dir_path):
        return dir_path in self.__watched_dirs.keys()

    def watch_dir(self, dir_path, library):
        if self.is_watched(dir_path):
            raise ValueError('dir %s is already watched' % dir_path)
        wdd = self.__wm.add_watch(dir_path, self.EVENT_MASK,
                      proc_fun=InotifyWatcher(library,self.__queue), rec=True,
                      auto_add=True)
        self.__watched_dirs[dir_path] = wdd

    def stop_watching_dir(self, dir_path):
        if self.is_watched(dir_path):
            wdd = self.__watched_dirs[dir_path]
            del self.__watched_dirs[dir_path]
            self.__wm.rm_watch(wdd[dir_path], rec=True)

    def run(self):
        notifier = self.notifier(self.__wm)

        for library in (self.__audio_library, self.__video_library):
            if library:
                library.watcher = self
                for dir_path in library.get_root_paths():
                    self.watch_dir(dir_path, library)

        # start library watcher thread
        lib_watcher = self.watcher(self.__db, self.__queue)
        lib_watcher.start()
        while not self.should_stop.isSet():
            # process the queue of events as explained above
            notifier.process_events()
            if notifier.check_events():
                # read notified events and enqeue them
                notifier.read_events()
        lib_watcher.close()
        notifier.stop()

    def close(self):
        self.should_stop.set()
        threading.Thread.join(self)


class DeejaydInotify(_DeejaydInotify):

    def watched_events_mask(self):
        return pyinotify.IN_DELETE |\
               pyinotify.IN_CREATE |\
               pyinotify.IN_MOVED_FROM |\
               pyinotify.IN_MOVED_TO |\
               pyinotify.IN_CLOSE_WRITE

    def watcher(self, db, queue):
        return LibraryWatcher(db, queue)

    def notifier(self, watch_manager):
        return pyinotify.Notifier(watch_manager, timeout=1000)


class DeejaydInotifyOLD(_DeejaydInotify):

    def watched_events_mask(self):
        return pyinotify.EventsCodes.IN_DELETE |\
               pyinotify.EventsCodes.IN_CREATE |\
               pyinotify.EventsCodes.IN_MOVED_FROM |\
               pyinotify.EventsCodes.IN_MOVED_TO |\
               pyinotify.EventsCodes.IN_CLOSE_WRITE

    def watcher(self, db, queue):
        return LibraryWatcherOLD(db, queue)

    def notifier(self, watch_manager):
        return pyinotify.Notifier(watch_manager)


def get_watcher(db, audio_library, video_library):
    try:
        pyinotify_version = map(int, pyinotify.__version__.split('.'))
    except AttributeError:
        pyinotify_version = [0, 7]

    if pyinotify_version >= [0, 8]:
        return DeejaydInotify(db, audio_library, video_library)
    else:
        return DeejaydInotifyOLD(db, audio_library, video_library)


# vim: ts=4 sw=4 expandtab