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

import time
import os.path
from sqlalchemy.orm import util
from twisted.internet import threads
from deejayd import DeejaydError
from deejayd.db.connection import Session, DatabaseLock
from deejayd.db.models import LibraryFolder, Media, Library
from deejayd.common.component import SignalingComponent, JSONRpcComponent
from deejayd.common.component import PersistentStateComponent
from deejayd.server.utils import log_traceback
from deejayd.db.models import And
from deejayd.ui import log
from deejayd.library import pathutils


class BaseLibrary(SignalingComponent, JSONRpcComponent,
                  PersistentStateComponent):
    OBJECT_CLASS = None
    TYPE = ""
    PARSER = None
    DEFAULT_SORT = None
    UPDATE_SIGNAL_NAME = ""
    state_name = ""
    initial_state = {
        "last_update": -1
    }

    def __init__(self, path):
        super(BaseLibrary, self).__init__()

        # get root path for this library
        path = os.path.abspath(path).rstrip("/")
        self.root_path = path
        # test library path
        if not os.path.isdir(self.root_path):
            msg = _("Unable to find '%s' folder in library") % self.root_path
            raise DeejaydError(msg)

        library = Session.query(Library) \
                         .filter(Library.name == self.TYPE) \
                         .one_or_none()
        if library is None:
            library = Library(name=self.TYPE, path=self.root_path)
            Session.add(library)
            Session.commit()
        self.library_id = library.id
        self.updating_state = {
            "id": 0,
            "running": False,
            "error": None
        }
        self.parser = self.PARSER(self)
        self.watcher = None
        self.load_state()

    #
    # RPC interfaces
    #
    def get_dir_content(self, f_name=""):
        f_path = os.path.join(self.root_path, f_name).rstrip("/")
        folder = self._get_folder(f_path)
        if folder is not None:
            return folder.to_json(subfolders=True, medias=True)
        elif f_name == "":
            return {"path": "", "files": [], "directories": []}
        else:
            err = _("Unable to find '%s' folder in library") % f_name
            raise DeejaydError(err)

    def search(self, f=None, ords=[], limit=None):
        ft = And()
        if f is not None:
            ft.combine(f)

        try:
            db_filter = ft.get_filter(self.OBJECT_CLASS)
        except AttributeError as ex:
            raise DeejaydError(str(ex))
        ords = ords or self.DEFAULT_SORT
        medias = Session.query(self.OBJECT_CLASS) \
                        .filter(db_filter) \
                        .order_by(ords) \
                        .all()
        return [m.to_json() for m in medias]

    def tag_list(self, tag_name, ft=None):
        q = Session.query(getattr(self.OBJECT_CLASS, tag_name))
        if ft is not None:
            q = q.filter(ft.get_filter(self.OBJECT_CLASS))
        return [t for (t,) in q.all()]

    def set_rating(self, ft, rating):
        if int(rating) not in list(range(0, 5)):
            raise DeejaydError(_("Bad rating value"))

        q = Session.query(self.OBJECT_CLASS)
        if ft is not None:
            q = q.filter(ft.get_filter(self.OBJECT_CLASS))
        for m in q.all():
            m.rating = rating
        Session.commit()

    def get_status(self):
        return {"updating_state": self.updating_state}

    def get_stats(self):
        raise NotImplementedError

    def update(self, force=False, sync=False):
        if self.updating_state["running"]:
            log.err(_("A library update is already running"))
            return

        self.updating_state["id"] += 1
        if sync:  # synchrone update
            self.walk_directory('', force=force)
            self.state["last_update"] = time.time()
        else:  # asynchrone update
            self.updating_state["running"] = True
            defered = threads.deferToThread(self.update_in_thread, '', force)
            defered.pause()

            # Add callback functions
            defered.addCallback(lambda *x: self.end_update())

            # Add errback functions
            def error_handler(failure, db_class):
                # Log the exception to debug pb later
                failure.printTraceback()
                db_class.end_update(False)
                return False
            defered.addErrback(error_handler, self)

            defered.unpause()
        return dict([(self.TYPE + "_updating_db", 
                      self.updating_state["id"])])

    #
    # functions used by other modules of deejayd
    #
    def get_file(self, file_path):
        abs_path = os.path.join(self.root_path, file_path)
        media = self._get_file_with_path(abs_path)
        if media is None:
            raise DeejaydError(_("file %s is not found in the db") % file_path)
        return media

    def get_all_files(self, dir_ids):
        medias = []
        folders = Session.query(LibraryFolder)\
                         .filter(LibraryFolder.id.in_(dir_ids)) \
                         .all()
        for f in folders:
            medias.extend(Session.query(self.OBJECT_CLASS)
                                 .join(LibraryFolder)
                                 .filter(LibraryFolder.path.startswith(f.path))
                                 .all())
        return medias

    def get_file_withids(self, file_ids):
        if not file_ids:
            return []
        return Session.query(self.OBJECT_CLASS) \
                      .filter(Media.m_id.in_(file_ids)) \
                      .order_by(Media.m_id) \
                      .all()

    def get_root_path(self):
        return self.root_path

    def close(self):
        self.save_state()

    #
    # functions related to library update process
    #
    def update_in_thread(self, walk_root, force=False):
        # init session for this thread
        DatabaseLock.acquire()
        Session()
        self.walk_directory(walk_root, force)
        # close session to avoid problems
        Session.remove()
        DatabaseLock.release()

    def end_update(self, result=True):
        self.updating_state["running"] = False
        if result:
            log.msg(_("The %s library has been updated") % self.TYPE)
            self.dispatch_signame(self.UPDATE_SIGNAL_NAME)
            self.state["last_update"] = time.time()
        else:
            msg = _("Unable to update the %s library. See log.") % self.TYPE
            log.err(msg)
            self.updating_state["error"] = msg
        return True

    def walk_directory(self, walk_root, force=False):
        walk_root = os.path.join(self.root_path, walk_root)
        walk_root = walk_root.rstrip("/")
        walked_folders = []
        # cache all medias recorded in database
        media_dict = {}
        for m in Session.query(self.OBJECT_CLASS).all():
            media_dict[m.get_path()] = m

        for root, subdirs, files in pathutils.walk(walk_root):
            root = root.rstrip("/")
            log.debug('library: update crawling %s' % root)
            if os.path.basename(root).startswith("."):
                continue  # skip hidden folder

            folder = self._get_folder(root)
            if folder is None:
                folder = LibraryFolder(library_id=self.library_id,
                                       path=root,
                                       name=os.path.basename(root))
                Session.add(folder)
            self.parse_files(folder, files, media_dict, force)

            subdirs_obj = self.get_subdirs(folder, subdirs)
            for sd in subdirs_obj:
                sd.parent_folder = folder
            walked_folders.append(root)

        # clean library
        Session.query(LibraryFolder) \
               .filter(LibraryFolder.library_id == self.library_id) \
               .filter(LibraryFolder.path.notin_(walked_folders)) \
               .delete(synchronize_session='fetch')
        if len(media_dict) > 0:
            db_media_ids = [media_dict[k].m_id for k in media_dict]
            erased_files = Session.query(self.OBJECT_CLASS) \
                            .filter(self.OBJECT_CLASS.m_id.in_(db_media_ids)) \
                            .all()
            for f in erased_files:
                Session.delete(f)
        Session.commit()

    def get_subdirs(self, parent, subdirs):
        def subdir_path(subdir):
            return os.path.join(parent.path, subdir)
        subdirs = [subdir_path(sd) for sd in subdirs
                   if subdir_path(sd) is not None]

        return subdirs and Session.query(LibraryFolder) \
                                  .filter(LibraryFolder.library_id
                                          == self.library_id,
                                          LibraryFolder.path.in_(subdirs)) \
                                  .all()

    def parse_files(self, folder, files, media_dict, force):
        for f in files:
            filepath = os.path.join(folder.path, f)
            if os.path.isfile(filepath):
                log.debug('library: updating file %s' % filepath)
            else:
                log.debug('library: skipping broken symlink %s' % filepath)
                continue

            need_update = True
            if filepath in media_dict:
                file_obj = media_dict[filepath]
                need_update = force or os.stat(
                    filepath).st_mtime > file_obj.last_modified
            elif self.parser.is_supported(filepath):
                file_obj = self.OBJECT_CLASS(filename=f, folder=folder)
            else:
                continue

            if need_update:
                file_obj = self._get_file_info(file_obj)
                if file_obj is None:
                    continue
                file_obj.last_modified = int(time.time())
            else:
                self.parser.extra_parse(file_obj)

            if filepath in media_dict:
                del media_dict[filepath]

    #
    # internal functions
    #
    def _get_folder(self, f_path):
        return Session.query(LibraryFolder) \
                      .filter(LibraryFolder.path == f_path,
                              LibraryFolder.library_id == self.library_id) \
                      .one_or_none()

    def _get_file(self, folder, filename):
        return Session.query(Media).join(LibraryFolder) \
                      .filter(LibraryFolder.path == folder.path,
                              Media.filename == filename) \
                      .one_or_none()

    def _get_file_with_path(self, file_path):
        folder, filename = os.path.split(file_path)
        return Session.query(self.OBJECT_CLASS) \
                      .join(LibraryFolder) \
                      .filter(LibraryFolder.path == folder) \
                      .filter(self.OBJECT_CLASS.filename == filename) \
                      .one_or_none()

    def _get_file_info(self, file_obj):
        try:
            file_obj = self.parser.parse(file_obj, Session)
        except Exception:
            if util.has_identity(file_obj):
                Session.delete(file_obj)
            else:
                Session.expunge(file_obj)
            log_traceback(level="info")
            return None
        return file_obj

    #######################################################################
    # # Inotify actions
    #######################################################################
    def update_extrainfo_file(self, file_path):
        self.parser.inotify_extra_parse(file_path)

    def update_file(self, path, filename):
        file_path = os.path.join(path, filename)
        try:
            file_mtime = os.stat(file_path).st_mtime
        except OSError:
            log.debug("library: file %s is gone, skipping." % file_path)
            return

        folder = self._get_folder(path)
        if folder is not None:
            file_obj = self._get_file(folder, filename)
            if file_obj is None:
                file_obj = self.OBJECT_CLASS(filename=filename, folder=folder,
                                             last_modified=-1)
            if file_mtime > file_obj.last_modified:
                file_obj = self._get_file_info(file_obj)
                if file_obj is None:
                    self.update_extrainfo_file(file_path)
                    return
            Session.add(file_obj)
        else:
            log.info("Inotify: a media has been updated in an unknown folder")

    def remove_extrainfo_file(self, file_path):
        self.parser.inotify_extra_remove(file_path)

    def remove_file(self, path, name):
        fn, ext = os.path.splitext(name)
        if ext in self.parser.get_extensions():
            self.remove_media(path, name)
        else:
            self.remove_extrainfo_file(os.path.join(path, name))

    def remove_media(self, path, name):
        file_obj = self._get_file_with_path(os.path.join(path, name))
        if file_obj is not None:
            Session.delete(file_obj)

    def crawl_directory(self, path, name):
        dir_path = os.path.join(path, name)

        # Compute list of paths to avoid in case of symlink loop : paths in db
        # except paths and children crawled or updated here
        indb_dirs = Session.query(LibraryFolder.id, LibraryFolder.path).all()
        indb_realpaths = []
        for d_id, d in indb_dirs:
            if not pathutils.is_subdir_of(dir_path, d):
                indb_realpaths.append(os.path.realpath(d))

        def dcb(dir_path):
            dirname, filename = os.path.split(dir_path)
            self.add_directory(dirname, filename)

        def fcb(dir_path):
            dirname, filename = os.path.split(dir_path)
            self.update_file(dirname, filename)
        pathutils.walk_and_do(dir_path, indb_realpaths, dcb, fcb,
                              topdown=True)

    def add_directory(self, path, name):
        parent = self._get_folder(path)
        if parent is not None:
            dir_path = os.path.join(path, name)
            folder = LibraryFolder(name=name, parent_folder=parent,
                                   path=dir_path, library_id=self.library_id)
            Session.add(folder)
            self.watcher.watch_dir(dir_path, self)

    def remove_directory(self, path, name):
        dir_path = os.path.join(path, name)
        folder = self._get_folder(dir_path)

        if folder is not None:
            def stop_watchers(d_obj):
                for ch_obj in d_obj.child_folders:
                    stop_watchers(ch_obj)
                self.watcher.stop_watching_dir(d_obj.path)
            stop_watchers(folder)
            Session.delete(folder)
