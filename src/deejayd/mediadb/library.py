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
# -*- coding: utf-8 -*-

import os, sys, urllib, threading, traceback
from twisted.internet import threads

from deejayd.component import SignalingComponent
from deejayd.mediadb import formats
from deejayd import database
from deejayd.ui import log

class NotFoundException(Exception):pass
class NotSupportedFormat(Exception):pass


class MediaFile(dict):

    def __init__(self, db, dir_id, dirname, filename, file_id = None):
        self.db = db
        self.replaygain_support = False
        self["media_id"] = file_id or db.insert_file(dir_id, filename)
        # record infos
        self["path"] = os.path.join(dirname, filename)
        self["filename"] = filename
        self["dir_id"] = dir_id

    def destroy(self):
        if not self["media_id"]: raise TypeError
        self.remove_file(self["media_id"])

    def set_uris(self, root_path):
        self["uri"] = os.path.join(root_path, self["path"])
        for k in ("external_subtitle",):
            if k in self.keys() and self[k] != "":
                self[k] = os.path.join(root_path, self[k])

    def set_info(self, key, value, commit = True):
        self.set_infos({key: value}, commit)

    def set_infos(self, infos, commit = True):
        if not self["media_id"]: raise TypeError
        self.db.set_media_infos(self["media_id"], infos)
        if commit: self.db.connection.commit()

    def replay_gain(self):
        """Return the recommended Replay Gain scale factor."""
        try:
            db = float(self.__replaygain["track_gain"].split()[0])
            peak = self.__replaygain["track_peak"] and\
                     float(self.__replaygain["track_peak"]) or 1.0
        except (KeyError, ValueError, IndexError):
            return 1.0
        else:
            scale = 10.**(db / 20)
            if scale * peak > 1:
                scale = 1.0 / peak # don't clip
            return min(15, scale)

##########################################################################
##########################################################################
def inotify_action(func):
    def inotify_action_func(*__args, **__kw):
        self = __args[0]
        try:
            name = self._encode(__args[1])
            path = self._encode(__args[2])
        except UnicodeError:
            return

        self.mutex.acquire()

        rs = func(*__args, **__kw)
        if rs: # commit change
            self.inotify_db.record_mediadb_stats(self.type)
            self.inotify_db.set_update_time(self.type)
            self.inotify_db.connection.commit()
            self.dispatch_signame(self.update_signal_name)

        self.mutex.release()

    return inotify_action_func

class _Library(SignalingComponent):
    common_attr = ("type","title","length")
    type = None

    def __init__(self, db_connection, player, path, fs_charset="utf-8"):
        SignalingComponent.__init__(self)

        # init Parms
        self.media_attr = []
        for i in self.__class__.common_attr: self.media_attr.append(i)
        for j in self.__class__.custom_attr: self.media_attr.append(j)
        self._fs_charset = fs_charset
        self._update_id = 0
        self._update_end = True
        self._update_error = None

        self._path = os.path.abspath(path)
        # test library path
        if not os.path.isdir(self._path):
            msg = _("Unable to find directory %s") % self._path
            raise NotFoundException(msg)

        # Connection to the database
        self.db_con = db_connection

        # init a mutex
        self.mutex = threading.Lock()

        # build supported extension list
        self.ext_dict = formats.get_extensions(player, self.type)

        self.watcher = None

    def _encode(self, data):
        try: rs = data.decode(self._fs_charset, "strict").encode("utf-8")
        except UnicodeError:
            log.err(_("%s has wrong character") %\
                 data.decode(self._fs_charset, "replace").encode("utf-8"))
            raise UnicodeError
        return rs

    def _build_supported_extension(self, player):
        raise NotImplementedError

    def _format_db_answer(self, answer):
        files = []
        for m in answer:
            current = MediaFile(self.db_con, m[0], m[1], m[3], m[2])
            for index, attr in enumerate(self.media_attr):
                current[attr] = m[index+4]
            current.set_uris(self._path)
            files.append(current)

        return files

    def get_dir_content(self, dir):
        files_rsp = self.db_con.get_dir_content(dir, self.media_attr, self.type)
        dirs_rsp = self.db_con.get_dir_list(dir, self.type)
        if len(files_rsp) == 0 and len(dirs_rsp) == 0 and dir != "":
            # nothing found for this directory
            raise NotFoundException

        files = self._format_db_answer(files_rsp)
        dirs = []
        for dir_id, dirname in dirs_rsp:
            root, d = os.path.split(dirname.strip("/"))
            if d != "" and root == self._encode(dir):
                dirs.append(d)
        return {'files': files, 'dirs': dirs}

    def get_dir_files(self,dir):
        files_rsp = self.db_con.get_dir_content(dir, self.media_attr, self.type)
        if len(files_rsp) == 0 and dir != "": raise NotFoundException
        return self._format_db_answer(files_rsp)

    def get_all_files(self,dir):
        files_rsp = self.db_con.get_alldir_files(dir, self.media_attr,\
            self.type)
        if len(files_rsp) == 0 and dir != "": raise NotFoundException
        return self._format_db_answer(files_rsp)

    def get_file(self,file):
        d, f = os.path.split(file)
        files_rsp = self.db_con.get_file(d, f, self.media_attr, self.type)
        if len(files_rsp) == 0:
            # this file is not found
            raise NotFoundException
        return self._format_db_answer(files_rsp)

    def get_root_path(self):
        return self._path

    def get_root_paths(self, db_con=None):
        if not db_con:
            db_con = self.db_con
        root_paths = [self.get_root_path()]
        for id, dirlink_record in db_con.get_all_dirlinks('', self.type):
            dirlink = os.path.join(self.get_root_path(),
                                   dirlink_record[1], dirlink_record[2])
            root_paths.append(dirlink)
        return root_paths

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
            self.dispatch_signame(self.update_signal_name)
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
            # dirname/filename : id
            library_files = dict([(os.path.join(item[1],item[3]), item[2])\
                for item in conn.get_all_files('',self.type)])
            # name : id
            library_dirs = dict([(item[1],item[0]) for item \
                                in conn.get_all_dirs('',self.type)])
            # name
            library_dirlinks = [item[1] for item\
                                in conn.get_all_dirlinks('', self.type)]

            self.walk_directory(conn, self.get_root_path(),
                                library_dirs, library_files, library_dirlinks)

            self.mutex.acquire()
            # Remove unexistent files and directories from library
            for id in library_files.values(): conn.remove_file(id)
            for id in library_dirs.values(): conn.remove_dir(id)
            for dirlinkname in library_dirlinks:
                conn.remove_dirlink(dirlinkname, self.type)
                if self.watcher:
                    self.watcher.stop_watching_dir(os.path.join(root,
                                                                dirlinkname))
            # Remove empty dir
            conn.erase_empty_dir(self.type)
            # update stat values
            conn.record_mediadb_stats(self.type)
            conn.set_update_time(self.type)
            # commit changes
            conn.connection.commit()
            self.mutex.release()
        finally:
            # close the connection
            conn.close()

    def walk_directory(self, db_con, walk_root,
                       library_dirs, library_files, library_dirlinks,
                       forbidden_roots=None):
        """Walk a directory for files to update. Called recursively to carefully handle symlinks."""
        if not forbidden_roots:
            forbidden_roots = [self.get_root_path()]

        for root, dirs, files in os.walk(walk_root):
            try: root = self._encode(root)
            except UnicodeError: # skip this directory
                continue

            strip_root = self.strip_root(root)
            try: dir_id = library_dirs[strip_root]
            except KeyError:
                dir_id = db_con.insert_dir(strip_root, self.type)
            else:
                del library_dirs[strip_root]

            # search symlinks
            for dir in dirs:
                try: dir = self._encode(dir)
                except UnicodeError: # skip this directory
                    continue
                # Walk only symlinks that aren't in library root or in one of
                # the additional known root paths which consist in already
                # crawled and out-of-main-root directories
                # (i.e. other symlinks).
                dir_path = os.path.join(root, dir)
                dirname = os.path.join(strip_root, dir)
                if os.path.islink(dir_path):
                    if not self.is_in_a_root(dir_path, forbidden_roots):
                        forbidden_roots.append(dir_path)
                        if dirname in library_dirlinks:
                            library_dirlinks.remove(dirname)
                        else:
                            db_con.insert_dirlink(dirname, self.type)
                            if self.watcher:
                                self.watcher.watch_dir(dir_path, self)
                        self.walk_directory(db_con, dir_path,
                                 library_dirs, library_files, library_dirlinks,
                                 forbidden_roots)

            # else update files
            for file in files:
                try: file = self._encode(file)
                except UnicodeError: # skip this file
                    continue

                filename = os.path.join(strip_root, file)
                try:
                    fid = library_files[filename]
                    need_update = os.stat(os.path.join(root,file)).st_mtime >= \
                        int(self.last_update_time)
                except KeyError:
                    need_update = True
                    fid = None
                else: del library_files[filename]
                if need_update:
                    fid = self.set_media(db_con,dir_id,strip_root,file,fid)
                if fid: self.set_extra_infos(db_con, strip_root, file, fid)

    def end_update(self, result = True):
        self._update_end = True
        if result: log.msg(_("The %s library has been updated") % self.type)
        else:
            msg = _("Unable to update the %s library. See log.") % self.type
            log.err(msg)
            self._update_error = msg
        return True

    def set_media(self, db_con, dir_id, dirname, filename, file_id):
        file_path = os.path.join(self._path, dirname, filename)
        try: mediainfo_obj = self._get_file_info(filename)
        except NotSupportedFormat:
            log.info(_("File %s not supported") % file_path)
            return
        # try to get infos from this file
        try: file_info = mediainfo_obj.parse(file_path)
        except Exception, ex:
            log.err(_("Unable to get metadata from %s, see traceback\
for more information.") % file_path)
            log.err("------------------Traceback lines--------------------")
            log.err(traceback.format_exc())
            log.err("-----------------------------------------------------")
            return
        media_file = MediaFile(db_con, dir_id, dirname, filename, file_id)
        media_file.set_infos(file_info, commit = False)
        return media_file["media_id"]

    def set_extra_infos(self, db_con, dir, file, file_id):
        raise NotImplementedError

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
    def add_file(self, path, file):
        try: self._get_file_info(file)
        except NotSupportedFormat: return False # file not supported

        strip_path = self.strip_root(path)
        dir_id = self.inotify_db.is_dir_exist(strip_path, self.type) or\
                 self.inotify_db.insert_dir(strip_path, self.type)
        fid = self.set_media(self.inotify_db, dir_id, strip_path, file, None)
        if fid: self.set_extra_infos(self.inotify_db, strip_path, file, fid)
        self._add_missing_dir(os.path.dirname(strip_path))
        return True

    @inotify_action
    def update_file(self, path, name):
        dir = self.strip_root(path)
        file = self.inotify_db.is_file_exist(dir, name, self.type)
        if file:
            dir_id, file_id = file
            self.set_media(self.inotify_db, dir_id, dir, name, file_id)
            return True
        return False

    @inotify_action
    def remove_file(self, path, name):
        dir = self.strip_root(path)
        file = self.inotify_db.is_file_exist(dir, name, self.type)
        if file:
            dir_id, file_id = file
            self.inotify_db.remove_file(file_id)
            self._remove_empty_dir(path)
            return True
        return False

    @inotify_action
    def add_directory(self, path, name, dirlink=False):
        dir_path = os.path.join(path, name)

        if dirlink:
            dirlinkname = os.path.join(self.strip_root(path), name)
            self.inotify_db.insert_dirlink(dirlinkname, self.type)
            self.watcher.watch_dir(dir_path, self)

        self.walk_directory(self.inotify_db, dir_path,
                            {}, {}, self.get_root_paths(self.inotify_db))
        self._add_missing_dir(os.path.dirname(self.strip_root(dir_path)))
        self._remove_empty_dir(path)
        return True

    @inotify_action
    def remove_directory(self, path, name, dirlink=False):
        rel_path = self.strip_root(os.path.join(path,name))
        dir_id = self.inotify_db.is_dir_exist(rel_path, self.type)
        if not dir_id: return False

        if dirlink:
            self.inotify_db.remove_dirlink(rel_path, self.type)
            self.watcher.stop_watching_dir(rel_path)

        self.inotify_db.remove_recursive_dir(rel_path)
        self._remove_empty_dir(path)
        return True

    def _remove_empty_dir(self, path):
        path = self.strip_root(path)
        while path != "":
            if len(self.inotify_db.get_all_files(path, self.type)) > 0:
                break
            dir_id = self.inotify_db.is_dir_exist(path, self.type)
            if dir_id: self.inotify_db.remove_dir(dir_id)
            path = os.path.dirname(path)

    def _add_missing_dir(self, path):
        """ add missing dir in the mediadb """
        while path != "":
            dir_id = self.inotify_db.is_dir_exist(path, self.type)
            if dir_id: break
            self.inotify_db.insert_dir(path, self.type)
            path = os.path.dirname(path)


class AudioLibrary(_Library):
    type = "audio"
    update_signal_name = 'mediadb.aupdate'
    custom_attr = ("artist","album","genre","tracknumber","date","bitrate",\
                   "replaygain_track_gain","replaygain_track_peak")

    def set_extra_infos(self, db_con, dir, file, file_id):
        pass # find cover

    def search(self,type,content):
        accepted_type = ('all','title','genre','filename','artist','album')
        if type not in accepted_type:
            raise NotFoundException

        rs = self.db_con.search(type, content, self.media_attr)
        return self._format_db_answer(rs)


class VideoLibrary(_Library):
    type = "video"
    update_signal_name = 'mediadb.vupdate'
    custom_attr = ("videoheight", "videowidth","external_subtitle")
    subtitle_ext = (".srt",)

    def set_extra_infos(self, db, dir, file, file_id):
        file_path = os.path.join(dir, file)
        (base_path,ext) = os.path.splitext(file_path)
        sub = ""
        for ext_type in self.subtitle_ext:
            if os.path.isfile(os.path.join(self._path, base_path + ext_type)):
                sub = base_path + ext_type
                break
        try: (recorded_sub,) = db.get_file_info(file_id, "external_subtitle")
        except TypeError:
            recorded_sub = None
        if recorded_sub != sub:
            db.set_media_infos(file_id,{"external_subtitle": sub})

    def search(self, content):
        rsp = self.db_con.search("title", content, self.media_attr)
        return self._format_db_answer(rsp)

# vim: ts=4 sw=4 expandtab
