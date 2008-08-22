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

import os, sys, threading, traceback, base64, urllib, locale
from twisted.internet import threads

from deejayd.component import SignalingComponent
from deejayd.mediadb import formats
from deejayd import database, mediafilters
from deejayd.ui import log

class NotFoundException(Exception):pass
class NotSupportedFormat(Exception):pass


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
            self.db_con.update_stats(self.type)
            self.db_con.connection.commit()
            self.dispatch_signame(self.update_signal_name)

        self.mutex.release()

    return inotify_action_func


class _Library(SignalingComponent):
    common_attr = ("filename","uri","type","title","length")
    persistent_attr = ("rating","skipcount","playcount","lastplayed")
    type = None

    def __init__(self, db_connection, player, path, fs_charset="utf-8"):
        SignalingComponent.__init__(self)

        # init Parms
        self.media_attr = []
        for i in self.__class__.common_attr: self.media_attr.append(i)
        for j in self.__class__.custom_attr: self.media_attr.append(j)
        for k in self.__class__.persistent_attr: self.media_attr.append(k)
        self._fs_charset = fs_charset
        self._update_id = 0
        self._update_end = True
        self._update_error = None

        self._changes_cb = {}
        self._changes_cb_id = 0

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
        if type(data) is unicode:
            return data.encode(locale.getpreferredencoding())
        try: rs = data.decode(self._fs_charset, "strict").encode("utf-8")
        except UnicodeError:
            log.err(_("%s has wrong character") %\
              data.decode(self._fs_charset, "ignore").encode("utf-8","ignore"))
            raise UnicodeError
        return rs

    def _build_supported_extension(self, player):
        raise NotImplementedError

    def set_file_info(self, file_id, key, value):
        ans = self.db_con.set_media_infos(file_id, {key: value})
        if not ans:
            raise NotFoundException
        self.emit_changes("update", file_id, threaded = False)
        self.db_con.connection.commit()

    def get_dir_content(self, dir):
        dir = os.path.join(self._path, dir).rstrip("/")
        files_rsp = self.db_con.get_dir_content(dir,\
            infos = self.media_attr, type = self.type)
        dirs_rsp = self.db_con.get_dir_list(dir, self.type)
        if len(files_rsp) == 0 and len(dirs_rsp) == 0 and dir != self._path:
            # nothing found for this directory
            raise NotFoundException

        dirs = []
        for dir_id, dir_path in dirs_rsp:
            root, d = os.path.split(dir_path.rstrip("/"))
            if d != "" and root == self._encode(dir):
                dirs.append(d)
        return {'files': files_rsp, 'dirs': dirs}

    def get_dir_files(self,dir):
        dir = os.path.join(self._path, dir).rstrip("/")
        files_rsp = self.db_con.get_dir_content(dir,\
            infos = self.media_attr, type = self.type)
        if len(files_rsp) == 0 and dir != self._path: raise NotFoundException
        return files_rsp

    def get_all_files(self,dir):
        dir = os.path.join(self._path, dir).rstrip("/")
        files_rsp = self.db_con.get_alldir_files(dir,\
            infos = self.media_attr, type = self.type)
        if len(files_rsp) == 0 and dir != self._path: raise NotFoundException
        return files_rsp

    def get_file(self,file):
        file = os.path.join(self._path, file)
        d, f = os.path.split(file)
        files_rsp = self.db_con.get_file(d, f,\
            infos = self.media_attr, type = self.type)
        if len(files_rsp) == 0:
            # this file is not found
            raise NotFoundException
        return files_rsp

    def get_file_withids(self,file_ids):
        files_rsp = self.db_con.get_file_withids(file_ids,\
            infos = self.media_attr, type = self.type)
        if len(files_rsp) != len(file_ids):
            raise NotFoundException
        return files_rsp

    def search(self, filter):
        type_filter = mediafilters.Equals("type", self.__class__.search_type)
        if not filter: filter = type_filter
        elif filter.get_name() == "and" \
                and not filter.find_filter(type_filter):
            filter.combine(type_filter)
        else:
            filter = mediafilters.And(filter, type_filter)

        rs = self.db_con.search(filter, infos = self.media_attr)
        return rs

    def get_root_path(self):
        return self._path

    def get_root_paths(self):
        root_paths = [self.get_root_path()]
        for id, dirlink_record in self.db_con.get_all_dirlinks('', self.type):
            dirlink = os.path.join(self.get_root_path(), dirlink_record)
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

    def _update_dir(self, dir):
        # dirname/filename : (id, lastmodified)
        library_files = dict([(os.path.join(it[1],it[3]), (it[2],it[4]))\
            for it in self.db_con.get_all_files(dir,self.type)])
        # name : id
        library_dirs = dict([(item[1],item[0]) for item \
                            in self.db_con.get_all_dirs(dir,self.type)])
        # name
        library_dirlinks = [item[1] for item\
                            in self.db_con.get_all_dirlinks(dir, self.type)]

        self.walk_directory(dir or self.get_root_path(),
                            library_dirs, library_files, library_dirlinks)

        # Remove unexistent files and directories from library
        for (id, lastmodified) in library_files.values():
            self.db_con.remove_file(id)
            self.emit_changes("remove", id)
        for id in library_dirs.values(): self.db_con.remove_dir(id)
        for dirlinkname in library_dirlinks:
            self.db_con.remove_dirlink(dirlinkname, self.type)
            if self.watcher:
                self.watcher.stop_watching_dir(os.path.join(root,
                                                            dirlinkname))

    def _update(self):
        self._update_end = False

        try:
            self._update_dir('')

            self.mutex.acquire()
            self.db_con.erase_empty_dir(self.type)
            self.db_con.update_stats(self.type)
            if self.type == "audio": self.db_con.set_compilation_tag()
            # commit changes
            self.db_con.connection.commit()
            self.mutex.release()
        finally:
            # close the connection
            self.db_con.close()

    def walk_directory(self, walk_root,
                       library_dirs, library_files, library_dirlinks,
                       forbidden_roots=None):
        """Walk a directory for files to update.
        Called recursively to carefully handle symlinks."""
        if not forbidden_roots:
            forbidden_roots = [self.get_root_path()]

        for root, dirs, files in os.walk(walk_root):
            try: root = self._encode(root)
            except UnicodeError: # skip this directory
                continue

            try: dir_id = library_dirs[root]
            except KeyError:
                dir_id = self.db_con.insert_dir(root, self.type)
            else:
                del library_dirs[root]

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
                if os.path.islink(dir_path):
                    if not self.is_in_a_root(dir_path, forbidden_roots):
                        forbidden_roots.append(os.path.realpath(dir_path))
                        if dir_path in library_dirlinks:
                            library_dirlinks.remove(dir_path)
                        else:
                            self.db_con.insert_dirlink(dir_path, self.type)
                            if self.watcher:
                                self.watcher.watch_dir(dir_path, self)
                        self.walk_directory(dir_path,
                                 library_dirs, library_files, library_dirlinks,
                                 forbidden_roots)

            # else update files
            for file in files:
                try: file = self._encode(file)
                except UnicodeError: # skip this file
                    continue

                file_path = os.path.join(root, file)
                try:
                    fid, lastmodified = library_files[file_path]
                    need_update = os.stat(file_path).st_mtime > lastmodified
                    changes_type = "update"
                except KeyError:
                    need_update = True
                    fid = None
                    changes_type = "add"
                else: del library_files[file_path]
                if need_update:
                    fid = self.set_media(dir_id,root,file,fid)
                if fid: self.set_extra_infos(root, file, fid)
                if need_update and fid: self.emit_changes(changes_type, fid)

    def end_update(self, result = True):
        self._update_end = True
        if result: log.msg(_("The %s library has been updated") % self.type)
        else:
            msg = _("Unable to update the %s library. See log.") % self.type
            log.err(msg)
            self._update_error = msg
        return True

    def set_media(self, dir_id, dirname, filename, file_id):
        file_path = os.path.join(dirname, filename)
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
        lastmodified = os.stat(file_path).st_mtime
        if file_id: # do not update persistent attribute
            for attr in self.__class__.persistent_attr: del file_info[attr]
            fid = file_id
            self.db_con.update_file(fid, lastmodified)
        else:
            lastmodified = os.stat(file_path).st_mtime
            fid = self.db_con.insert_file(dir_id, filename, lastmodified)
        self.db_con.set_media_infos(fid, file_info)
        return fid

    def set_extra_infos(self, dir, file, file_id):
        raise NotImplementedError

    def _get_file_info(self, filename):
        (base, ext) = os.path.splitext(filename)
        ext = ext.lower()
        if ext in self.ext_dict.keys():
            return self.ext_dict[ext]
        else:
            raise NotSupportedFormat

    def disconnect_to_changes(self, id):
        if id in self._changes_cb.keys():
            del self._changes_cb[id]

    def connect_to_changes(self, cb):
        self._changes_cb_id += 1
        self._changes_cb[self._changes_cb_id] = cb
        return self._changes_cb_id

    def emit_changes(self, type, file_id, threaded = True):
        log.debug(_("library: emit %s change for file %d") % (type, file_id))
        for cb in self._changes_cb.itervalues(): cb(type, file_id, threaded)

    #######################################################################
    ## Inotify actions
    #######################################################################
    @inotify_action
    def add_file(self, path, file):
        try: self._get_file_info(file)
        except NotSupportedFormat: # file not supported
            return self._inotify_add_info(path, file)

        file_record = self.db_con.is_file_exist(path, file, self.type)
        if file_record: # file already exists
            dir_id, file_id = file_record
        else:
            dir_id = self.db_con.is_dir_exist(path, self.type) or\
                     self.db_con.insert_dir(path, self.type)
            file_id = None

        fid = self.set_media(dir_id, path, file, file_id)
        if fid:
            self.set_extra_infos(path, file, fid)
            self._add_missing_dir(path)
            self.emit_changes("add", fid)
        else:
            self._remove_empty_dir(path)
            return self._inotify_add_info(path, file)
        return True

    @inotify_action
    def update_file(self, path, name):
        file = self.db_con.is_file_exist(path, name, self.type)
        if file:
            dir_id, file_id = file
            self.set_media(dir_id, path, name, file_id)
            self.emit_changes("update", file_id)
            return True
        else: return self._inotify_update_info(path, name)

    @inotify_action
    def remove_file(self, path, name):
        file = self.db_con.is_file_exist(path, name, self.type)
        if file:
            dir_id, file_id = file
            self.db_con.remove_file(file_id)
            self._remove_empty_dir(path)
            self.emit_changes("remove", file_id)
            return True
        else: return self._inotify_remove_info(path, name)

    @inotify_action
    def add_directory(self, path, name, dirlink=False):
        dir_path = os.path.join(path, name)

        if dirlink:
            self.db_con.insert_dirlink(dir_path, self.type)
            self.watcher.watch_dir(dir_path, self)

        self._update_dir(dir_path.rstrip("/"))
        self._add_missing_dir(os.path.dirname(dir_path))
        self._remove_empty_dir(path)
        return True

    @inotify_action
    def remove_directory(self, path, name, dirlink=False):
        dir_path = os.path.join(path,name)
        dir_id = self.db_con.is_dir_exist(dir_path, self.type)
        if not dir_id: return False

        if dirlink:
            self.db_con.remove_dirlink(dir_path, self.type)
            self.watcher.stop_watching_dir(dir_path)

        ids = self.db_con.remove_recursive_dir(dir_path)
        for id in ids: self.emit_changes("remove", id)
        self._remove_empty_dir(path)
        return True

    def _remove_empty_dir(self, path):
        while path != "":
            if len(self.db_con.get_all_files(path, self.type)) > 0:
                break
            dir_id = self.db_con.is_dir_exist(path, self.type)
            if dir_id: self.db_con.remove_dir(dir_id)
            path = os.path.dirname(path)

    def _add_missing_dir(self, path):
        """ add missing dir in the mediadb """
        while path != "":
            dir_id = self.db_con.is_dir_exist(path, self.type)
            if dir_id: break
            self.db_con.insert_dir(path, self.type)
            path = os.path.dirname(path)


class AudioLibrary(_Library):
    type = "audio"
    search_type = "song"
    update_signal_name = 'mediadb.aupdate'
    custom_attr = ("artist","album","genre","tracknumber","date","bitrate",\
                   "replaygain_track_gain","replaygain_track_peak",\
                   "compilation")
    cover_name = ("cover.jpg", "folder.jpg", ".folder.jpg")

    def __extract_cover(self, image_path):
        if os.path.getsize(image_path) > 512*1024: return None # file too large
        try: fd = open(image_path)
        except Exception, ex:
            log.info(_("Unable to open cover file"))
            return None
        rs = fd.read()
        fd.close()
        return base64.b64encode(rs)

    def set_extra_infos(self, dir, file, file_id):
        cover = ""
        for name in self.cover_name:
            if os.path.isfile(os.path.join(dir, name)):
                rs = self.db_con.is_cover_exist(os.path.join(dir,name))
                try: (cover, lmod) = rs
                except TypeError:
                    image = self.__extract_cover(os.path.join(dir, name))
                    if image:
                        cover = self.db_con.add_cover(\
                            os.path.join(dir,name), image)
                else:
                    if int(lmod)<os.stat(os.path.join(dir,file)).st_mtime:
                        image = self.__extract_cover(os.path.join(dir, name))
                        if image: self.db_con.update_cover(cover, image)
                break
        try: (recorded_cover,) = self.db_con.get_file_info(file_id, "cover")
        except TypeError: recorded_cover = -1
        if str(recorded_cover) != str(cover):
            self.db_con.set_media_infos(file_id,{"cover": cover})

    #
    # custom inotify actions
    #
    def _inotify_add_info(self, path, file):
        if file in self.cover_name:
            files = self.db_con.get_dircontent_id(path, self.type)
            if len(files) > 0:
                file_path = os.path.join(path, file)
                image = self.__extract_cover(file_path)
                if image:
                    cover = self.db_con.add_cover(file_path, image)
                    for (id,) in files:
                        self.db_con.set_media_infos(id, {"cover":cover})
                        self.emit_changes("update", id)
                    return True
        return False

    def _inotify_remove_info(self, path, file):
        rs = self.db_con.is_cover_exist(os.path.join(path, file))
        try: (cover, lmod) = rs
        except TypeError:
            return False
        ids = self.db_con.search_id("cover", cover)
        for (id,) in ids:
            self.db_con.set_media_infos(id, {"cover": ""})
            self.emit_changes("update", id)
        self.db_con.remove_cover(cover)
        return True

    def _inotify_update_info(self, path, file):
        file_path = os.path.join(path, file)
        rs = self.db_con.is_cover_exist(file_path)
        try: (cover, lmod) = rs
        except TypeError:
            return False
        image = self.__extract_cover(file_path)
        if image: self.db_con.update_cover(cover, image)
        return True
    ###########################################################


class VideoLibrary(_Library):
    type = "video"
    search_type = "video"
    update_signal_name = 'mediadb.vupdate'
    custom_attr = ("videoheight", "videowidth","external_subtitle")
    subtitle_ext = (".srt",)

    def __quote_suburi(self, uri):
        return "file:/%s" % urllib.quote(uri)

    def set_extra_infos(self, dir, file, file_id):
        file_path = os.path.join(dir, file)
        (base_path,ext) = os.path.splitext(file_path)
        sub = ""
        for ext_type in self.subtitle_ext:
            if os.path.isfile(os.path.join(base_path + ext_type)):
                sub = self.__quote_suburi(base_path + ext_type)
                break
        try: (recorded_sub,) = self.db_con.get_file_info(file_id,\
                                                         "external_subtitle")
        except TypeError:
            recorded_sub = None
        if recorded_sub != sub:
            self.db_con.set_media_infos(file_id,{"external_subtitle": sub})

    #
    # custom inotify actions
    #
    def _inotify_add_info(self, path, file):
        (base_file, ext) = os.path.splitext(file)
        if ext in self.subtitle_ext:
            for video_ext in self.ext_dict.keys():
                try: (dir_id,fid,) = self.db_con.is_file_exist(path,\
                                                base_file+video_ext, self.type)
                except TypeError: pass
                else:
                    uri = self.__quote_suburi(os.path.join(path, file))
                    self.db_con.set_media_infos(fid, {"external_subtitle": uri})
                    self.emit_changes("update", fid)
                    return True
        return False

    def _inotify_remove_info(self, path, file):
        (base_file, ext) = os.path.splitext(file)
        if ext in self.subtitle_ext:
            ids = self.db_con.search_id("external_subtitle",\
                    self.__quote_suburi(os.path.join(path, file)))
            for (id,) in ids:
                self.db_con.set_media_infos(id, {"external_subtitle": ""})
                self.emit_changes("update", id)
            return True
        return False

    def _inotify_update_info(self, path, file):
        return False
    ###########################################################

# vim: ts=4 sw=4 expandtab
