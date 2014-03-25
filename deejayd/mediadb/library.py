# Deejayd, a media player daemon
# Copyright (C) 2007-2013 Mickael Royer <mickael.royer@gmail.com>
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
# -*- coding: utf-8 -*-

from deejayd import DeejaydError
from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.database.connection import DatabaseConnection
from deejayd.jsonrpc.interfaces import LibraryModule, jsonrpc_module
from deejayd.jsonrpc.interfaces import AudioLibraryModule
from deejayd.mediadb import pathutils
from deejayd.mediadb.parsers import NoParserError, ParseError
from deejayd.mediadb.parsers import AudioParserFactory, VideoParserFactory
from deejayd.model import mediafilters
from deejayd.model.library import LibraryFactory, LibraryDir
from deejayd.model.stats import get_stats
from deejayd.ui import log
from deejayd.utils import quote_uri, str_decode, log_traceback
from twisted.internet import threads, reactor
import os
import threading
import base64
import hashlib
import time
from collections import OrderedDict


class NotFoundException(DeejaydError):pass
class NotSupportedFormat(DeejaydError):pass


class _Library(SignalingComponent, JSONRpcComponent):
    supported_search_type = []
    default_search_sort = None
    type = None
    PARSER = None

    def __init__(self, player, path, fs_charset="utf-8"):
        super(_Library, self).__init__()
        self.lib_obj = getattr(LibraryFactory(), "get_%s_library" % self.type)()
        self.stats = get_stats()

        # init Parms
        self._fs_charset = fs_charset
        self._update_id = 0
        self._update_end = True
        self._update_error = None
        self.watcher = None

        self._changes_cb = {}
        self._changes_cb_id = 0

        try: self._path = self.fs_charset2unicode(os.path.abspath(path))
        except UnicodeError:
            raise DeejaydError(_("Root library path has wrong caracters"))
        # test library path
        if not os.path.isdir(self._path):
            msg = _("Unable to find '%s' folder in library") \
                    % self.fs_charset2unicode(self._path)
            raise NotFoundException(msg)
        self.lib_obj.set_root_path(self._path)

        self.parser = self.PARSER(self)
        self.mutex = threading.Lock()

    def fs_charset2unicode(self, path, errors='strict'):
        """
        This function translate file paths from the filesystem encoded form to
        unicode for internal processing.
        """
        return str_decode(path, self._fs_charset, errors)

    def get_model(self):
        return self.lib_obj

    def _get_dir_obj(self, dir):
        abs_dir = os.path.join(self._path, dir).rstrip("/")
        try: dir_obj = self.lib_obj.get_dir_with_path(abs_dir)
        except DeejaydError:
            err = _("Unable to find '%s' folder in library") % abs_dir
            raise NotFoundException(err)
        return dir_obj

    def get_dir_content(self, dir=""):
        try: rs = self._get_dir_obj(dir).to_json(subdirs=True, files=True)
        except DeejaydError, ex:
            if dir == "":
                return {"root": "", "files": [], "directories": []}
            raise ex
        return rs

    def get_dir_files(self, dir):
        return self._get_dir_obj(dir).get_files()

    def get_file(self, file):
        file = os.path.join(self._path, file)
        d, f = os.path.split(file)

        dir_obj = self._get_dir_obj(d)
        try: file = self.lib_obj.get_file_with_path(dir_obj, f)
        except DeejaydError:
            err = _("Unable to find '%s' file in library") % file
            raise NotFoundException(err)
        return (file,)

    def get_all_files(self, dir_ids):
        try: dirs = self.lib_obj.get_dirs_with_ids(dir_ids)
        except KeyError:
            err = _("Some folder in '%s' has not found in library") \
                  % ",".join(map(str, dir_ids))
            raise NotFoundException(err)
        return reduce(lambda l, d: l+d.get_all_files(), dirs, [])

    def get_file_withids(self, file_ids):
        files_rsp = self.lib_obj.get_files_with_ids(file_ids)
        return files_rsp

    def search(self, f=None, ords=[], limit=None):
        ft = mediafilters.And()
        if f is not None:
            ft.combine(f)

        if not ords:
            ords = self.default_search_sort
        return self.lib_obj.search(ft, orders=ords, limit=limit)

    def tag_list(self, tag, filter=None):
        return [x[-1] for x in self.lib_obj.list_tags(tag, filter)]

    def set_rating(self, mfilter, rating):
        if int(rating) not in range(0, 5):
            raise DeejaydError(_("Bad rating value"))

        medias = self.lib_obj.search(mfilter)
        map(lambda m: m.set_rating(rating), medias)
        # record changes in the filesystem
        DatabaseConnection().commit()

    def get_root_path(self):
        return self._path

    def get_status(self):
        status = []
        if not self._update_end:
            status.append((self.type + "_updating_db", self._update_id))
        if self._update_error:
            status.append((self.type + "_updating_error", self._update_error))
            self._update_error = None

        return dict(status)

    def close(self):
        getattr(LibraryFactory(), "close_%s_library" % self.type)()

    #
    # Update process
    #

    def update(self, force=False, sync=False):
        if self._update_end:
            self._update_id += 1
            if sync:  # synchrone update
                self._update(force=force, sync=sync)
                self._update_end = True
            else:  # asynchrone update
                self.defered = threads.deferToThread(self._update, force)
                self.defered.pause()

                # Add callback functions
                self.defered.addCallback(lambda *x: self.end_update())

                # Add errback functions
                def error_handler(failure, db_class):
                    # Log the exception to debug pb later
                    failure.printTraceback()
                    db_class.end_update(False)
                    return False
                self.defered.addErrback(error_handler, self)

                self.defered.unpause()

            return dict([(self.type + "_updating_db", self._update_id)])

        raise DeejaydError(_("A library update is already running"))

    def _update(self, force=False, sync=False):
        self._update_end = False

        try:
            self.walk_directory('', force=force)

            self.mutex.acquire()
            # TODO make stats works
            self.stats[self.type + "_library_update"] = time.time()
            self.stats.save()
            # commit changes
            DatabaseConnection().commit()
            self.mutex.release()
        finally:
            # close the connection if we are in a specific thread
            if not sync: DatabaseConnection().close()

    def walk_directory(self, walk_root, force=False):
        walk_root = os.path.join(self.get_root_path(),
                                 self.fs_charset2unicode(walk_root))
        walk_root = walk_root.rstrip("/")

        recorded_dirs = OrderedDict()
        recorded_files = []

        for root, subdirs, files in pathutils.walk(walk_root):
            root = root.rstrip("/")
            log.debug('library: update crawling %s' % root)
            try:
                root = self.fs_charset2unicode(root)
            except UnicodeError:  # skip this directory
                log.info("Directory %s skipped because of unhandled characters."\
                         % self.fs_charset2unicode(root, 'replace'))
                continue
            if os.path.basename(root).startswith("."):
                continue  # skip hidden folder

            dir_obj = self.lib_obj.get_dir_with_path(root, create=True)
            parsed_files = self.update_files(dir_obj, files, force)

            def subdir_path(subdir):
                try: subdir = self.fs_charset2unicode(subdir)
                except UnicodeError:
                    return None
                return os.path.join(root, subdir)
            subdir_objs = [recorded_dirs[subdir_path(s)] for s in subdirs \
                            if subdir_path(s) in recorded_dirs]

            if not parsed_files and not subdir_objs:
                dir_obj.erase()
                continue

            map(lambda sd: sd.set_parent(dir_obj), subdir_objs)
            recorded_files += parsed_files
            recorded_dirs[root] = dir_obj

        # save all changes
        for d in reversed(recorded_dirs):
            recorded_dirs[d].save()
        map(lambda f: f.save(), recorded_files)

        # clean library
        self.lib_obj.clean_library(map(lambda d: d.get_id(), recorded_dirs.values()),
                                   map(lambda f: f["media_id"], recorded_files))

    def update_files(self, dir_obj, files, force=False):
        parsed_files = []
        for file in files:
            try: file = self.fs_charset2unicode(file)
            except UnicodeError:  # skip this directory
                log.info("File %s skipped because of unhandled characters."\
                         % self.fs_charset2unicode(file, 'replace'))

            filepath = os.path.join(dir_obj.get_path(), file)

            if os.path.isfile(filepath):
                log.debug('library: updating file %s' % filepath)
            else:
                log.debug('library: skipping broken symlink %s' % filepath)
                continue

            file_obj = self.lib_obj.get_file_with_path(dir_obj, file, create=True)
            need_update = force or os.stat(filepath).st_mtime > file_obj["lastmodified"]
            if need_update:
                file_obj = self._get_file_info(file_obj)
                if file_obj is None:
                    continue
                file_obj["lastmodified"] = int(time.time())
            else:
                self.parser.extra_parse(file_obj)
            parsed_files.append(file_obj)

        return parsed_files

    def _get_file_info(self, file_obj):
        try: file_obj = self.parser.parse(file_obj)
        except NoParserError:
            file_obj.erase()
            log.info(_("File %s not supported") % file_obj.get_path())
            return None
        except Exception:
            file_obj.erase()
            log_traceback(level="info")
            return None
        return file_obj

    def end_update(self, result=True):
        self._update_end = True
        if result:
            log.msg(_("The %s library has been updated") % self.type)
            self.dispatch_signame(self.update_signal_name)
        else:
            msg = _("Unable to update the %s library. See log.") % self.type
            log.err(msg)
            self._update_error = msg
        return True

    #######################################################################
    # # Inotify actions
    #######################################################################
    def update_extrainfo_file(self, file_path):
        self.parser.inotify_extra_parse(file_path)

    def update_file(self, path, file):
        file_path = os.path.join(path, file)

        try:
            file_mtime = os.stat(file_path).st_mtime
        except OSError:
            log.debug("library: file %s is gone, skipping." % file_path)
            return

        dir_obj = self.lib_obj.get_dir_with_path(path, create=True)
        file_obj = self.lib_obj.get_file_with_path(dir_obj, file, create=True)
        need_update = file_mtime > file_obj["lastmodified"]
        if need_update:
            file_obj = self._get_file_info(file_obj)
            if file_obj is None:
                self.update_extrainfo_file(file_path)
                return
            file_obj["lastmodified"] = int(time.time())
            dir_obj.save()
            file_obj.save(commit=True)

    def remove_extrainfo_file(self, file_path):
        self.parser.inotify_extra_remove(file_path)

    def remove_file(self, path, name):
        fn, ext = os.path.splitext(name)
        if ext in self.parser.get_extensions():
            self.remove_media(path, name)
        else:
            self.remove_extrainfo_file(os.path.join(path, name))

    def remove_media(self, path, name):
        log.debug('library: removing file %s from db'\
                % os.path.join(path, name))
        try: dir_obj = self.lib_obj.get_dir_with_path(path)
        except DeejaydError:
            return
        file_obj = self.lib_obj.get_file_with_path(dir_obj, name,
                                                   raise_ex=False)
        if file_obj is not None:
            file_obj.erase()

    def crawl_directory(self, path, name):
        dir_path = os.path.join(path, name)

        # Compute list of paths to avoid in case of symlink loop : paths in db
        # except paths and children crawled or updated here
        indb_dirs = self.lib_obj.get_all_dirs()
        indb_realpaths = []
        for d_id, d in indb_dirs:
            if not pathutils.is_subdir_of(dir_path, d):
                indb_realpaths.append(os.path.realpath(d))

        dcb = lambda dir_path: self.add_directory(*os.path.split(dir_path))
        fcb = lambda file_path: self.update_file(*os.path.split(file_path))
        pathutils.walk_and_do(dir_path, indb_realpaths, dcb, fcb)

    def add_directory(self, path, name):
        dir_path = os.path.join(path, name)
        log.debug('library: adding dir %s in db' % dir_path)
        self.lib_obj.get_dir_with_path(dir_path, create=True)
        self.watcher.watch_dir(dir_path, self)

    def remove_directory(self, path, name):
        dir_path = os.path.join(path, name)
        log.debug('library: removing dir %s in db' % dir_path)
        try:
            dir_obj = self.lib_obj.get_dir_with_path(dir_path)
        except DeejaydError:
            return

        def stop_watchers(d_obj):
            map(stop_watchers, d_obj.get_subdirs())
            self.watcher.stop_watching_dir(d_obj.get_path())
        stop_watchers(dir_obj)

        dir_obj.erase(purge_files=True)

    def dispatch_mupdate(self, fid, signal_type):
        self.dispatch_signame('mediadb.mupdate',
                              attrs={"type": signal_type, "id": fid})
        self.dispatch_signame(self.update_signal_name)


@jsonrpc_module(AudioLibraryModule)
class AudioLibrary(_Library):
    type = "audio"
    PARSER = AudioParserFactory
    search_type = "song"
    update_signal_name = 'mediadb.aupdate'
    supported_search_type = ['title', 'genre', 'filename', 'artist', 'album']
    default_search_sort = mediafilters.DEFAULT_AUDIO_SORT

    def album_list(self, filter=None):
        return self.lib_obj.get_albums_with_filter(filter)

    def get_cover(self, album_id):
        album = self.lib_obj.get_album_with_id(album_id)
        cover_path = os.path.join(self.lib_obj.get_cover_folder(),
                                  album.get_cover_filename())
        if os.path.isfile(cover_path):
            result = ""
            # return base64 encoded cover
            with open(cover_path) as c:
                data = c.read()
                result = base64.b64encode(data)
            return result
        return None


@jsonrpc_module(LibraryModule)
class VideoLibrary(_Library):
    type = "video"
    PARSER = VideoParserFactory
    search_type = "video"
    update_signal_name = 'mediadb.vupdate'
    supported_search_type = ['title']
    default_search_sort = mediafilters.DEFAULT_VIDEO_SORT



# vim: ts=4 sw=4 expandtab
