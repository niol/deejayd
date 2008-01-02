# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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
            log.info("inotify event %s: %s" % \
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
                self.__created_files.append((event.path, event.name))
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
        if self.__audio_library != None:# watch audio library
            self.__audio_library.set_inotify_connection(threaded_db)
            wm.add_watch(self.__audio_library.get_root_path(), mask, \
                proc_fun=LibraryWatcher(self.__audio_library), rec=True,\
                auto_add=True)
        if self.__video_library != None: # watch video library
            self.__video_library.set_inotify_connection(threaded_db)
            wm.add_watch(self.__video_library.get_root_path(), mask, \
                proc_fun=LibraryWatcher(self.__video_library), rec=True,\
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
