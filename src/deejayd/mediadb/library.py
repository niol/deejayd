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
# -*- coding: utf-8 -*-

import os, sys, threading
from deejayd.mediadb import formats
from deejayd import database
from deejayd.ui import log
from twisted.internet import threads

class NotFoundException(Exception):pass
class NotSupportedFormat(Exception):pass

class _DeejaydFile:
    table = "unknown"

    def __init__(self, db_con, dir, file, root_path, info):
        self.file = os.path.join(root_path, dir, file)
        self.db_con = db_con
        self.dir = dir
        self.filename = file
        self.info = info

    def remove(self):
        self.db_con.remove_file(self.dir, self.file, self.table)

    def insert(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def force_update(self):
        raise NotImplementedError


class DeejaydAudioFile(_DeejaydFile):
    table = "audio_library"

    def insert(self):
        try: file_info = self.info.parse(self.file)
        except:
            log.err(_("Unable to get audio metadata from %s") % self.file)
            return False
        self.db_con.insert_audio_file(self.dir,self.filename,file_info)
        return True

    def update(self):
        try: file_info = self.info.parse(self.file)
        except:
            log.err(_("Unable to get audio metadata from %s") % self.file)
            return False
        self.db_con.update_audio_file(self.dir,self.filename,file_info)
        return True

    def force_update(self):pass


class DeejaydVideoFile(_DeejaydFile):
    table = "video_library"

    def __init__(self, db_con, dir, file, root_path, info):
        _DeejaydFile.__init__(self, db_con, dir, file, root_path, info)

    def insert(self):
        try: file_info = self.info.parse(self.file)
        except:
            log.err(_("Unable to get video metadata from %s") % self.file)
            return False
        self.db_con.insert_video_file(self.dir,self.filename,file_info)
        return True

    def update(self):
        try: file_info = self.info.parse(self.file)
        except:
            log.err(_("Unable to get video metadata from %s") % self.file)
            return False
        self.db_con.update_video_file(self.dir,self.filename,file_info)
        return True

    def force_update(self):
        # Update external subtitle
        file_info = self.info.parse_sub(self.file)
        self.db_con.update_video_subtitle(self.dir,self.filename,file_info)

##########################################################################
##########################################################################
def inotify_action(func):
    def inotify_action_func(self, path, name, **__kw):
        self.mutex.acquire()

        rs = func(self, path, name, **__kw)
        if rs: # commit change
            self.inotify_db.record_mediadb_stats()
            self.inotify_db.set_update_time(self.type)
            self.inotify_db.connection.commit()

        self.mutex.release()

    return inotify_action_func

class _Library:
    ext_dict = {}
    table = None
    type = None
    file_class = None

    def __init__(self, db_connection, player, path):
        # init Parms
        self._update_id = 0
        self._update_end = True
        self._update_error = None

        self._path = os.path.abspath(path)
        # test library path
        if not os.path.isdir(self._path):
            msg = _("Unable to find directory %s") % self._path
            log.err(msg)
            raise NotFoundException(msg)

        # Connection to the database
        self.db_con = db_connection

        # init a mutex
        self.mutex = threading.Lock()

        # build supported extension list
        self._build_supported_extension(player)

    def _build_supported_extension(self, player):
        raise NotImplementedError

    def get_dir_content(self,dir):
        rs = self.db_con.get_dir_info(dir,self.table)
        if len(rs) == 0 and dir != "":
            # nothing found for this directory
            raise NotFoundException

        return self._format_db_rsp(rs)

    def get_dir_files(self,dir):
        rs = self.db_con.get_files(dir,self.table)
        if len(rs) == 0 and dir != "": raise NotFoundException
        return self._format_db_rsp(rs)["files"]

    def get_all_files(self,dir):
        rs = self.db_con.get_all_files(dir)
        if len(rs) == 0 and dir != "": raise NotFoundException
        return self._format_db_rsp(rs)["files"]

    def get_file(self,file):
        rs = self.db_con.get_file_info(file,self.table)
        if len(rs) == 0:
            # this file is not found
            raise NotFoundException
        return self._format_db_rsp(rs)["files"]

    def get_root_path(self):
        return self._path

    def get_status(self):
        status = []
        if not self._update_end:
            status.append((self.type+"_updating_db",self._update_id))
        if self._update_error:
            status.append((self.type+"_updating_error",self._update_error))
            self._update_error = None

        return status

    def close(self):
        pass

    #
    # Update process
    #
    def update(self, sync = False):
        if self._update_end:
            self._update_id += 1
            if sync: # synchrone update
                self._update()
                self._update_end = True
            else: # asynchrone update
                self.defered = threads.deferToThread(self._update)
                self.defered.pause()

                # Add callback functions
                succ = lambda *x: self.end_update()
                self.defered.addCallback(succ)

                # Add errback functions
                def error_handler(failure,db_class):
                    # Log the exception to debug pb later
                    failure.printTraceback()
                    db_class.end_update(False)
                    return False
                self.defered.addErrback(error_handler,self)

                self.defered.unpause()
            return self._update_id

        return 0

    def strip_root(self, path):
        abs_path = os.path.abspath(path)
        rel_path = os.path.normpath(abs_path[len(self.get_root_path()):])

        if rel_path != '.': rel_path = rel_path.strip("/")
        else: rel_path = ''

        return rel_path

    def is_in_root(self, path, root=None):
        """Checks if a directory is physically in the supplied root (the library root by default)."""
        if not root:
            root = self.get_root_path()
        real_root = os.path.realpath(root)
        real_path = os.path.realpath(path)

        head = real_path
        old_head = None
        while head != old_head:
            if head == real_root:
                return True
            old_head = head
            head, tail = os.path.split(head)
        return False

    def is_in_a_root(self, path, roots):
        """Checks if a directory is physically in one of the supplied roots."""
        for root in roots:
            if self.is_in_root(path, root):
                return True
        return False

    def _update(self):
        conn = self.db_con.get_new_connection()
        conn.connect()
        self._update_end = False

        try:
            self.last_update_time = conn.get_update_time(self.type)
            library_files = [(item[0],item[1]) for item \
                                in conn.get_all_files('',self.table)]
            library_dirs = [(item[0],item[1]) for item \
                                in conn.get_all_dirs('',self.table)]

            self.walk_directory(conn, self.get_root_path(), library_dirs,\
                                library_files)

            self.mutex.acquire()
            # Remove unexistent files and directories from library
            for (dir,filename) in library_files:
                conn.remove_file(dir, filename, self.table)
            for (root,dirname) in library_dirs:
                conn.remove_dir(root, dirname, self.table)
            # Remove empty dir
            conn.erase_empty_dir(self.table)
            # update stat values
            conn.record_mediadb_stats()
            conn.set_update_time(self.type)
            # commit changes
            conn.connection.commit()
            self.mutex.release()
        finally:
            # close the connection
            conn.close()

    def walk_directory(self, db_con, walk_root,
                       library_dirs, library_files, forbidden_roots=None):
        """Walk a directory for files to update. Called recursively to carefully handle symlinks."""
        if not forbidden_roots:
            forbidden_roots = [self.get_root_path()]

        for root, dirs, files in os.walk(walk_root):
            # first update directory
            for dir in dirs:
                tuple = (self.strip_root(root), dir)
                if tuple in library_dirs:
                    library_dirs.remove(tuple)
                else:
                    db_con.insert_dir(tuple,self.table)

                # Walk only symlinks that aren't in library root or in one of
                # the forbidden roots which consist in already crawled
                # and out-of-main-root directories (i.e. other symlinks).
                dir_path = os.path.join(root, dir)
                if os.path.islink(dir_path):
                    if not self.is_in_a_root(dir_path, forbidden_roots):
                        forbidden_roots.append(dir_path)
                        self.walk_directory(dir_path,
                                            library_dirs, library_files,
                                            forbidden_roots)

            # else update files
            for file in files:
                try: obj_cls = self._get_file_info(file)
                except NotSupportedFormat:
                    log.info(_("File %s not supported") % file)
                    continue
                file_object = self.file_class(db_con,\
                                self.strip_root(root),\
                                file, self._path, obj_cls)

                tuple = (self.strip_root(root), file)
                if tuple in library_files:
                    library_files.remove(tuple)
                    if os.stat(os.path.join(root,file)).st_mtime >= \
                                                     int(self.last_update_time):
                        file_object.update()
                    # Even if the media has not been modified, we may need
                    # to update some information (like external subtitle)
                    # it is the aim of this function
                    else: file_object.force_update()
                else: file_object.insert()

    def end_update(self, result = True):
        self._update_end = True
        if result: log.msg(_("The %s library has been updated") % self.type)
        else:
            msg = _("Unable to update the %s library. See log.") % self.type
            log.err(msg)
            self._update_error = msg
        return True

    def _get_file_info(self, filename):
        (base, ext) = os.path.splitext(filename)
        ext = ext.lower()
        if ext in self.ext_dict.keys():
            return self.ext_dict[ext]
        else:
            raise NotSupportedFormat

    #######################################################################
    ## Inotify actions
    #######################################################################
    def set_inotify_connection(self, db):
        self.inotify_db = db

    @inotify_action
    def add_file(self, path, name):
        try: obj_cls = self._get_file_info(name)
        except NotSupportedFormat: return False
        file_object = self.file_class(self.inotify_db, self.strip_root(path),\
            name, self._path, obj_cls)
        if not file_object.insert(): return False # insert failed
        self._add_missing_dir(path)
        return True

    @inotify_action
    def update_file(self, path, name):
        try: obj_cls = self._get_file_info(name)
        except NotSupportedFormat: return False
        file_object = self.file_class(self.inotify_db, self.strip_root(path),\
            name, self._path, obj_cls)
        if not file_object.update(): return False# update failed
        return True

    @inotify_action
    def remove_file(self, path, name):
        self.inotify_db.remove_file(self.strip_root(path), name, self.table)
        self._remove_empty_dir(path)
        return True

    @inotify_action
    def add_directory(self, path, name):
        dir_path = os.path.join(path, name)
        self.walk_directory(self.inotify_db, dir_path, [], [])
        self._add_missing_dir(dir_path)
        self._remove_empty_dir(path)
        return True

    @inotify_action
    def remove_directory(self, path, name):
        self.inotify_db.remove_dir(self.strip_root(path), name, self.table)
        self._remove_empty_dir(path)
        return True

    def _remove_empty_dir(self, path):
        path = self.strip_root(path)
        while path != "":
            if len(self.inotify_db.get_all_files(path, self.table)) > 0:
                break
            (path, dirname) = os.path.split(path)
            self.inotify_db.remove_dir(path, dirname, self.table)

    def _add_missing_dir(self, path):
        """ add missing dir in the mediadb """
        path = self.strip_root(path)
        while path != "":
            (path, dirname) = os.path.split(path)
            if self.inotify_db.is_dir_exist(path, dirname, self.table):
                break
            self.inotify_db.insert_dir((path, dirname), self.table)


class AudioLibrary(_Library):
    table = "audio_library"
    type = "audio"
    file_class = DeejaydAudioFile

    def _build_supported_extension(self, player):
        self.ext_dict = formats.get_audio_extensions(player)

    def search(self,type,content):
        accepted_type = ('all','title','genre','filename','artist','album')
        if type not in accepted_type:
            raise NotFoundException

        rs = self.db_con.search_audio_library(type,content)
        return self._format_db_rsp(rs)["files"]

    def find(self,type,content):
        accepted_type = ('title','genre','filename','artist','album')
        if type not in accepted_type:
            raise NotFoundException

        rs = self.db_con.find_audio_library(type,content)
        return self._format_db_rsp(rs)["files"]

    def _format_db_rsp(self,rs):
        # format correctly database result
        files = []
        dirs = []
        for (dir,fn,t,ti,ar,al,gn,tn,dt,lg,bt) in rs:
            if t == 'directory': dirs.append(fn)
            else:
                file_info = {"path":os.path.join(dir,fn),"length":lg,
                             "filename":fn,"dir":dir,
                             "title":ti,"artist":ar,"album":al,"genre":gn,
                             "track":tn,"date":dt,"bitrate":bt,
                             "type":"song"}
                files.append(file_info)
        return {'files':files, 'dirs': dirs}


class VideoLibrary(_Library):
    table = "video_library"
    type = "video"
    file_class = DeejaydVideoFile

    def _build_supported_extension(self, player):
        self.ext_dict = formats.get_video_extensions(player)

    def _format_db_rsp(self,rs):
        # format correctly database result
        files = []
        dirs = []
        for (dir,fn,t,ti,len,videow,videoh,sub) in rs:
            if t == 'directory': dirs.append(fn)
            else:
                file_info = {"path":os.path.join(dir,fn),"length":len,
                             "filename":fn,"dir":dir,
                             "title":ti,
                             "videowidth":videow,"videoheight":videoh,
                             "external_subtitle":sub,"type":"video"}
                files.append(file_info)
        return {'files':files, 'dirs': dirs}

# vim: ts=4 sw=4 expandtab
