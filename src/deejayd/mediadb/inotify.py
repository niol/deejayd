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

import os, threading
from deejayd.ui import log
# pynotify support
inotify_support = True
try: from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent
except ImportError:
    inotify_support = False

#############################################################################
##### Events Watcher
#############################################################################
if inotify_support:

    def log_event(func):
        def log_event_func(self, event):
            log.info(_("Inotify event %s: %s") % \
                (event.event_name,os.path.join(event.path, event.name)))
            func(self,event)

        return log_event_func

    class LibraryWatcher(ProcessEvent):

        def __init__(self,library):
            self.__library = library
            self.__created_files = []

        @log_event
        def process_IN_CREATE(self, event):
            if not event.is_dir:
                self.__created_files.append((event.path, event.name))

        @log_event
        def process_IN_DELETE(self, event):
            if not event.is_dir:
                self.__library.remove_file(event.path, event.name)

        @log_event
        def process_IN_MOVED_FROM(self, event):
            if not event.is_dir:
                self.__library.remove_file(event.path, event.name)
            else:
                self.__library.remove_directory(event.path, event.name)

        @log_event
        def process_IN_MOVED_TO(self, event):
            if not event.is_dir:
                self.__library.add_file(event.path, event.name)
            else:
                self.__library.add_directory(event.path, event.name)

        @log_event
        def process_IN_CLOSE_WRITE(self, event):
            if (event.path, event.name) in self.__created_files:
                self.__library.add_file(event.path, event.name)
                del self.__created_files[\
                        self.__created_files.index((event.path, event.name))]
            else:
                self.__library.update_file(event.path, event.name)

        def process_IN_IGNORED(self, event):
            # This is said to be useless in the documentation, and is
            # effectively useless for us except for adding extreme verbosity
            # to the tests. Farewell, IN_IGNORED!
            pass


#############################################################################

class DeejaydInotify(threading.Thread):

    def __init__(self, db, audio_library, video_library):
        threading.Thread.__init__(self)
        self.should_stop = threading.Event()

        self.__audio_library = audio_library
        self.__video_library = video_library
        self.__db = db

    def run(self):
        # open a new database connection for this thread
        threaded_db = self.__db.get_new_connection()
        threaded_db.connect()

        wm = WatchManager()
        # watched events
        mask = EventsCodes.IN_DELETE | EventsCodes.IN_CREATE |\
               EventsCodes.IN_MOVED_FROM | EventsCodes.IN_MOVED_TO |\
               EventsCodes.IN_CLOSE_WRITE
        notifier = Notifier(wm)

        for library in (self.__audio_library, self.__video_library):
            if library:
                library.set_inotify_connection(threaded_db)
                for dir_path in library.get_root_paths():
                    wm.add_watch(dir_path, mask,
                                 proc_fun=LibraryWatcher(library), rec=True,
                                 auto_add=True)

        while not self.should_stop.isSet():
            # process the queue of events as explained above
            notifier.process_events()
            if notifier.check_events():
                # read notified events and enqeue them
                notifier.read_events()

        notifier.stop()
        # close database connection
        threaded_db.close()

    def close(self):
        self.should_stop.set()
        threading.Thread.join(self)

# vim: ts=4 sw=4 expandtab
