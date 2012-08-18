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
# -*- coding: utf-8 -*-

import os, threading, traceback, base64, hashlib
from twisted.internet import threads, reactor

from deejayd import DeejaydError
from deejayd.component import SignalingComponent, JSONRpcComponent
from deejayd.jsonrpc.interfaces import LibraryModule, jsonrpc_module
from deejayd.mediadb import formats
from deejayd.utils import quote_uri, str_decode, log_traceback
from deejayd import mediafilters
from deejayd.ui import log

class NotFoundException(DeejaydError):pass
class NotSupportedFormat(DeejaydError):pass


##########################################################################
##########################################################################
def inotify_action(func):
    def inotify_action_func(*__args, **__kw):
        self = __args[0]
        try:
            name = self.fs_charset2unicode(__args[1])
            path = self.fs_charset2unicode(__args[2])
        except UnicodeError:
            return

        return func(*__args, **__kw)

    return inotify_action_func


class _Library(SignalingComponent, JSONRpcComponent):
    common_attr = ("filename","uri","type","title","length")
    persistent_attr = ("rating","skipcount","playcount","lastplayed")
    supported_search_type = []
    default_search_sort = None
    type = None

    def __init__(self, db_connection, player, path, fs_charset="utf-8"):
        super(_Library, self).__init__()

        # init Parms
        self.media_attr = []
        for attr_list in [self.__class__.common_attr,\
                           self.__class__.custom_attr,\
                           self.__class__.persistent_attr]:
            self.media_attr.extend(attr_list)
        self._fs_charset = fs_charset
        self._update_id = 0
        self._update_end = True
        self._update_error = None

        self._changes_cb = {}
        self._changes_cb_id = 0

        try: self._path = self.fs_charset2unicode(os.path.abspath(path))
        except UnicodeError:
            raise DeejaydError(_("Root library path has wrong caracters"))
        # test library path
        if not os.path.isdir(self._path):
            msg = _("Unable to find directory %s") \
                    % self.fs_charset2unicode(self._path)
            raise NotFoundException(msg)

        # Connection to the database
        self.db_con = db_connection
        self.mutex = threading.Lock()

        # build supported extension list
        self.ext_dict = formats.get_extensions(player, self.type)

        self.watcher = None

    def fs_charset2unicode(self, path, errors='strict'):
        """
        This function translate file paths from the filesystem encoded form to
        unicode for internal processing.
        """
        return str_decode(path, self._fs_charset, errors)

    def _verify_dir_not_empty(self, root, dirs = None, files = None):
        if len(files) == 0 and len(dirs) == 0 and root != self._path:
            err = _("Unable to find '%s' folder in library") % root
            raise NotFoundException(err)

    def get_dir_content(self, dir = ""):
        abs_dir = os.path.join(self._path, dir).rstrip("/")
        files_rsp = self.db_con.get_dir_content(abs_dir,\
            infos = self.media_attr, type = self.type)
        dirs_rsp = self.db_con.get_dir_list(abs_dir, self.type)
        self._verify_dir_not_empty(abs_dir, dirs_rsp, files_rsp)

        dirs = []
        for dir_id, dir_path in dirs_rsp:
            root, d = os.path.split(dir_path.rstrip("/"))
            if d != "" and root == self.fs_charset2unicode(abs_dir):
                dirs.append(d)
        return {'files': files_rsp, 'directories': dirs, 'root': dir}

    def get_dir_files(self, dir):
        abs_dir = os.path.join(self._path, dir).rstrip("/")
        files_rsp = self.db_con.get_dir_content(abs_dir,\
            infos = self.media_attr, type = self.type)
        self._verify_dir_not_empty(abs_dir, [], files_rsp)
        return files_rsp

    def get_all_files(self,dir):
        abs_dir = os.path.join(self._path, dir).rstrip("/")
        files_rsp = self.db_con.get_alldir_files(abs_dir,\
            infos = self.media_attr, type = self.type)
        self._verify_dir_not_empty(abs_dir, [], files_rsp)
        return files_rsp

    def get_file(self,file):
        file = os.path.join(self._path, file)
        d, f = os.path.split(file)
        files_rsp = self.db_con.get_file(d, f,\
            infos = self.media_attr, type = self.type)
        if len(files_rsp) == 0:
            # this file is not found
            err = _("Unable to find '%s' file in library") % file
            raise NotFoundException(err)
        return files_rsp

    def get_file_withids(self,file_ids):
        files_rsp = self.db_con.get_file_withids(file_ids,\
            infos = self.media_attr, type = self.type)
        if len(files_rsp) != len(file_ids):
            raise NotFoundException
        return files_rsp

    def search_with_filter(self, filter, ords = [], limit = None):
        ft = mediafilters.And()
        ft.combine(mediafilters.Equals("type", self.__class__.search_type))
        if filter is not None:
            ft.combine(filter)

        return self.db_con.search(ft, infos = self.media_attr, orders=ords,\
                limit = limit)

    def search(self, pattern, type = 'all'):
        if pattern is None:
            raise DeejaydError(_("Pattern must be a string"))

        if type not in self.supported_search_type + ["all"]:
            raise DeejaydError(_('Type %s is not supported') % (type,))
        if type == "all":
            filter = mediafilters.Or()
            for tag in self.supported_search_type:
                filter.combine(mediafilters.Contains(tag, pattern))
        else:
            filter = mediafilters.Contains(type, pattern)
        return self.search_with_filter(filter, self.default_search_sort)

    def tag_list(self, tag, filter = None):
        return [x[0] for x in self.db_con.list_tags(tag, filter)]

    def set_file_info(self, file_id, key, value, allow_create = False):
        ans = self.db_con.set_media_infos(file_id, {key: value}, allow_create)
        if not ans:
            raise NotFoundException
        self.dispatch_signame('mediadb.mupdate',\
                attrs = {"type": "update", "id": file_id})
        self.db_con.connection.commit()

    def get_root_path(self):
        return self._path

    def get_root_paths(self):
        root_paths = [self.get_root_path()]
        for id, dirlink_record in self.db_con.get_all_dirlinks('', self.type):
            dirlink = os.path.join(self.get_root_path(), dirlink_record)
            root_paths.append(dirlink)
        return root_paths

    def library_path(self, realpath):
        for root in self.get_root_paths():
            if os.path.islink(root):
                realroot = os.path.realpath(root)
                if realpath.startswith(realroot):
                    return os.path.join(root, realpath[len(realroot)+1:])
        return realpath

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

    def update(self, force = False, sync = False):
        if self._update_end:
            self._update_id += 1
            if sync: # synchrone update
                self._update(force)
                self._update_end = True
            else: # asynchrone update
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
            self.dispatch_signame(self.update_signal_name)

            return dict([(self.type+"_updating_db", self._update_id)])

        raise DeejaydError(_("A library update is already running"))

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

    def _update_dir(self, dir, force = False, dispatch_signal = True):
        dir = self.fs_charset2unicode(dir)

        # dirname/filename : (id, lastmodified)
        library_files = dict([(os.path.join(it[1],it[3]), (it[2],it[4]))\
            for it in self.db_con.get_all_files(dir,self.type)])
        # name : id
        library_dirs = dict([(item[1],item[0]) for item \
                            in self.db_con.get_all_dirs(dir,self.type)])
        # name
        library_dirlinks = [item[1] for item\
                            in self.db_con.get_all_dirlinks(dir, self.type)]

        changes = self.walk_directory(dir or self.get_root_path(),
                library_dirs, library_files, library_dirlinks, force=force,
                dispatch_signal=dispatch_signal)

        # Remove unexistent files and directories from library
        for (id, lastmodified) in library_files.values():
            self.db_con.remove_file(id)
            if dispatch_signal:
                reactor.callFromThread(self.dispatch_signame,\
                        'mediadb.mupdate', attrs = {"type": "remove", "id": id})
            changes.append((id, "remove"))
        for id in library_dirs.values(): self.db_con.remove_dir(id)
        for dirlinkname in library_dirlinks:
            self.db_con.remove_dirlink(dirlinkname, self.type)
            if self.watcher:
                self.watcher.stop_watching_dir(dirlinkname)

        return changes

    def _update(self, force = False):
        self._update_end = False

        try:
            # compare keys recorded in the database with needed key
            # if there is a difference, force update
            keys = self.db_con.get_media_keys(self.search_type)
            # remove cover because it is not used
            try: keys.remove(("cover",))
            except ValueError:
                pass
            if len(keys) > 0 and len(keys) != len(self.media_attr):
                log.msg(\
                    _("%s library has to be updated, this can take a while.")%\
                    (self.type,))
                force = True
            self._update_dir('', force=force)

            self.mutex.acquire()
            self.db_con.erase_empty_dir(self.type)
            self.db_con.update_stats(self.type)
            # commit changes
            self.db_con.connection.commit()
            self.mutex.release()
        finally:
            # close the connection
            self.db_con.close()

    def walk_directory(self, walk_root,
                       library_dirs, library_files, library_dirlinks,
                       force = False, forbidden_roots=None,
                       dispatch_signal=True):
        """Walk a directory for files to update.
        Called recursively to carefully handle symlinks."""
        if not forbidden_roots:
            forbidden_roots = [self.get_root_path()]

        changes = []
        for root, dirs, files in os.walk(walk_root):
            try:
                root = self.fs_charset2unicode(root)
            except UnicodeError: # skip this directory
                log.info("Directory %s skipped because of unhandled characters."\
                         % self.fs_charset2unicode(root, 'replace'))
                continue

            try: dir_id = library_dirs[root]
            except KeyError:
                dir_id = self.db_con.insert_dir(root, self.type)
            else:
                del library_dirs[root]

            # search symlinks
            for dir in dirs:
                try:
                    dir = self.fs_charset2unicode(dir)
                    dir_path = os.path.join(root, dir)
                except UnicodeError: # skip this directory
                    log.info("Directory %s skipped because of unhandled characters."\
                             % self.fs_charset2unicode(dir_path, 'replace'))
                    continue
                # Walk only symlinks that aren't in library root or in one of
                # the additional known root paths which consist in already
                # crawled and out-of-main-root directories
                # (i.e. other symlinks).
                if os.path.islink(dir_path):
                    if not self.is_in_a_root(dir_path, forbidden_roots):
                        forbidden_roots.append(os.path.realpath(dir_path))
                        if dir_path in library_dirlinks:
                            library_dirlinks.remove(dir_path)
                        else:
                            self.db_con.insert_dirlink(dir_path, self.type)
                            if self.watcher:
                                self.watcher.watch_dir(dir_path, self)
                        changes.extend(self.walk_directory(dir_path,
                                 library_dirs, library_files, library_dirlinks,
                                 force, forbidden_roots,
                                 dispatch_signal))

            # else update files
            dir_changes = self.update_files(root, dir_id,
                                            map(self.fs_charset2unicode, files),
                                            library_files,
                                            force, dispatch_signal)
            changes.extend(dir_changes)

        return changes

    def end_update(self, result = True):
        self._update_end = True
        if result: log.msg(_("The %s library has been updated") % self.type)
        else:
            msg = _("Unable to update the %s library. See log.") % self.type
            log.err(msg)
            self._update_error = msg
        return True

    def update_files(self, root, dir_id, files, library_files,
                     force = False, dispatch_signal=True):
        changes = []
        for file in files:
            assert type(file) is unicode

            file_path = os.path.join(root, file)
            try:
                fid, lastmodified = library_files[file_path]
                need_update = force or os.stat(file_path).st_mtime>lastmodified
                changes_type = "update"
            except KeyError:
                need_update, fid = True, None
                changes_type = "add"
            else: del library_files[file_path]
            if need_update:
                file_info = self._get_file_info(file_path)
                if file_info is not None: # file supported
                    fid = self.set_media(dir_id, file_path, file_info, fid)
            if fid: self.set_extra_infos(root, file, fid)
            if need_update and fid:
                if dispatch_signal:
                    reactor.callFromThread(self.dispatch_signame,\
                                'mediadb.mupdate',
                                attrs = {"type": changes_type, "id": fid})
                changes.append((fid, changes_type))

        return changes

    def set_media(self, dir_id, file_path, file_info, file_id):
        if file_info is None: return file_id # not supported
        lastmodified = os.stat(file_path).st_mtime
        if file_id: # do not update persistent attribute
            for attr in self.__class__.persistent_attr: del file_info[attr]
            fid = file_id
            self.db_con.update_file(fid, lastmodified)
        else:
            filename = os.path.basename(file_path)
            fid = self.db_con.insert_file(dir_id, filename, lastmodified)
        self.db_con.set_media_infos(fid, file_info)
        return fid

    def set_extra_infos(self, dir, file, file_id):
        pass

    def _get_file_info(self, file_path):
        (base, ext) = os.path.splitext(file_path)
        # try to get infos from this file
        try: file_info = self.ext_dict[ext.lower()]().parse(file_path)
        except (TypeError, KeyError):
            log.info(_("File %s not supported") % file_path)
            return None
        except Exception:
            log_traceback()
            return None
        return file_info

    #######################################################################
    ## Inotify actions
    #######################################################################
    @inotify_action
    def add_file(self, path, file):
        file_path = os.path.join(path, file)
        file_info = self._get_file_info(file_path)
        if not file_info:
            return self._inotify_add_info(path, file)

        try: dir_id, file_id = self.db_con.is_file_exist(path, file, self.type)
        except TypeError:
            dir_id = self.db_con.is_dir_exist(path, self.type) or\
                     self.db_con.insert_dir(path, self.type)
            file_id = None

        fid = self.set_media(dir_id, file_path, file_info, file_id)
        if fid:
            self.set_extra_infos(path, file, fid)
            self._add_missing_dir(os.path.dirname(path))
            return [(fid, "add")]
        return None

    @inotify_action
    def update_file(self, path, name):
        try: dir_id, file_id = self.db_con.is_file_exist(path, name, self.type)
        except TypeError:
            return self._inotify_update_info(path, name)
        else:
            file_path = os.path.join(path, name)
            file_info = self._get_file_info(file_path)
            if not file_info:
                return self._inotify_update_info(path, name)
            self.set_media(dir_id, file_path, file_info, file_id)
            return [(file_id, "update")]

    @inotify_action
    def remove_file(self, path, name):
        file = self.db_con.is_file_exist(path, name, self.type)
        if file:
            dir_id, file_id = file
            self.db_con.remove_file(file_id)
            self._remove_empty_dir(path)
            return [(file_id, "remove")]
        else:
            return self._inotify_remove_info(path, name)

    @inotify_action
    def add_directory(self, path, name, dirlink=False):
        dir_path = os.path.join(path, name)
        if dirlink:
            self.db_con.insert_dirlink(dir_path, self.type)
        self.watcher.watch_dir(dir_path, self)

        changes = self._update_dir(dir_path.rstrip("/"), dispatch_signal=False)
        self._add_missing_dir(os.path.dirname(dir_path))
        self._remove_empty_dir(path)
        return changes

    @inotify_action
    def remove_directory(self, path, name, dirlink=False):
        dir_path = os.path.join(path, name)
        dir_id = self.db_con.is_dir_exist(dir_path, self.type)
        if not dir_id:
            return None

        if dirlink:
            self.db_con.remove_dirlink(dir_path, self.type)
        self.watcher.stop_watching_dir(dir_path)

        ids = self.db_con.remove_recursive_dir(dir_path)
        self._remove_empty_dir(path)
        return [(id, "remove") for id in ids]

    def inotify_record_changes(self, fids):
        self.mutex.acquire()
        self.db_con.update_stats(self.type)
        self.db_con.connection.commit()
        for fid, signal_type in fids:
            reactor.callFromThread(self.dispatch_signame, 'mediadb.mupdate',\
                    attrs = {"type": signal_type, "id": fid})
        reactor.callFromThread(self.dispatch_signame, self.update_signal_name)
        self.mutex.release()

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


@jsonrpc_module(LibraryModule)
class AudioLibrary(_Library):
    type = "audio"
    search_type = "song"
    update_signal_name = 'mediadb.aupdate'
    custom_attr = ("artist","album","genre","tracknumber","date","bitrate",\
                   "replaygain_track_gain","replaygain_track_peak",\
                   "various_artist","discnumber")
    cover_name = ("cover.jpg", "folder.jpg", ".folder.jpg",\
                  "cover.png", "folder.png", ".folder.png",\
                  "albumart.jpg", "albumart.png")
    supported_search_type = ['title','genre','filename','artist','album']
    default_search_sort = mediafilters.DEFAULT_AUDIO_SORT

    def get_cover(self, file_id):
        try: (cover_id, mime, image) = self.db_con.get_file_cover(file_id)
        except TypeError:
            raise NotFoundException
        return {"mime": mime, "cover": base64.b64decode(image), "id": cover_id}

    def __extract_cover(self, cover_path):
        # import kaa.metadata in the last moment to avoid to launch thread too
        # early
        import kaa.metadata

        if os.path.getsize(cover_path) > 512*1024:
            return None # file too large (> 512k)

        # parse video file with kaa
        cover_infos = kaa.metadata.parse(cover_path)
        if cover_infos is None:
            raise TypeError(_("cover %s not supported by kaa parser") % \
                    cover_path)
        # get mime type of this picture
        mime_type = cover_infos["mime"]
        if unicode(mime_type) not in (u"image/jpeg", u"image/png"):
            log.info(_("cover %s : wrong mime type") % cover_path)
            return None

        try: fd = open(cover_path)
        except Exception:
            log.info(_("Unable to open cover file %s") % cover_path)
            log_traceback()
            return None
        rs = fd.read()
        fd.close()
        return mime_type, base64.b64encode(rs)

    def __find_cover(self, dir):
        cover = None
        for name in self.cover_name:
            cover_path = os.path.join(dir, name)
            if os.path.isfile(cover_path):
                try: (cover, lmod) = self.db_con.is_cover_exist(cover_path)
                except TypeError:
                    try: mime, image = self.__extract_cover(cover_path)
                    except TypeError:
                        return None
                    cover = self.db_con.add_cover(cover_path, mime, image)
                else:
                    if int(lmod)<os.stat(cover_path).st_mtime:
                        try: mime, image = self.__extract_cover(cover_path)
                        except TypeError:
                            return None
                        self.db_con.update_cover(cover, mime, image)
                break
        return cover

    def __update_cover(self, file_id, cover):
        try:
            (recorded_cover, mime, source) = self.db_con.get_file_cover(\
                    file_id,True)
        except TypeError:
            recorded_cover, mime, source = -1, "", ""
        if not source.startswith("hash") and str(recorded_cover) != str(cover):
            self.db_con.set_media_infos(file_id,{"cover": cover})
            return True
        return False

    def __get_digest(self, data):
        return "hash_-_%s" % hashlib.md5(data).hexdigest()

    def _update_dir(self, dir, force=False, dispatch_signal=True):
        changes = super(AudioLibrary, self)._update_dir(dir, force,
                                                        dispatch_signal)
        # remove unused cover
        self.db_con.remove_unused_cover()
        return changes

    def update_files(self, root, dir_id, files, library_files, force=False,
                     dispatch_signal=True):
        changes = []
        if len(files): cover = self.__find_cover(root)
        for file in files:
            assert type(file) is unicode

            file_path = os.path.join(root, file)
            try:
                fid, lastmodified = library_files[file_path]
                need_update = force or os.stat(file_path).st_mtime>lastmodified
                changes_type = "update"
            except KeyError:
                need_update, fid = True, None
                changes_type = "add"
            else: del library_files[file_path]
            if need_update:
                file_info = self._get_file_info(file_path)
                if file_info is not None: # file supported
                    fid = self.set_media(dir_id,file_path,file_info,fid,cover)
            elif fid and cover:
                self.__update_cover(fid, cover)
            if need_update and fid:
                if dispatch_signal:
                    reactor.callFromThread(self.dispatch_signame,
                        'mediadb.mupdate',\
                        attrs = {"type": changes_type, "id": fid})
                changes.append((fid, changes_type))
        return changes

    def set_media(self, dir_id, file_path, file_info, file_id, cover = None):
        if file_info is not None and "cover" in file_info:
            # find a cover in the file
            image = base64.b64encode(file_info["cover"]["data"])
            mime = file_info["cover"]["mime"]
            # use hash to identify cover in the db and avoid duplication
            img_hash = self.__get_digest(image)
            try: (cover, lmod) = self.db_con.is_cover_exist(img_hash)
            except TypeError:
                cover = self.db_con.add_cover(img_hash, mime, image)
            file_info["cover"] = cover
        elif cover: # use the cover available in this directory
            file_info["cover"] = cover
        fid = super(AudioLibrary, self).set_media(dir_id, file_path, \
                file_info, file_id)
        # update compilation tag if necessary
        if fid and "album" in file_info.keys() and file_info["album"] != '':
            self.db_con.set_variousartist_tag(fid, file_info)
        return fid

    #
    # custom inotify actions
    #
    @inotify_action
    def add_file(self, path, file):
        file_path = os.path.join(path, file)
        file_info = self._get_file_info(file_path)
        if not file_info and file in self.cover_name: # it is a cover
            files = self.db_con.get_dircontent_id(path, self.type)
            if len(files) > 0:
                file_path = os.path.join(path, file)
                try: mime, image = self.__extract_cover(file_path)
                except TypeError: # image not supported
                    return False
                if image:
                    cover = self.db_con.add_cover(file_path, mime, image)
                    changes = []
                    for (id,) in files:
                        if self.__update_cover(id, cover):
                            changes.append((id, "update"))
                    return changes
            return None

        try: dir_id, file_id = self.db_con.is_file_exist(path, file, self.type)
        except TypeError:
            dir_id = self.db_con.is_dir_exist(path, self.type) or\
                     self.db_con.insert_dir(path, self.type)
            file_id = None

        fid = self.set_media(dir_id, file_path, file_info, file_id)
        if fid:
            self._add_missing_dir(os.path.dirname(path))
            return [(fid, "add")]
        return None

    def _inotify_remove_info(self, path, file):
        rs = self.db_con.is_cover_exist(os.path.join(path, file))
        try: (cover, lmod) = rs
        except TypeError:
            return None
        ids = self.db_con.search_id("cover", cover)
        for (id,) in ids:
            self.db_con.set_media_infos(id, {"cover": ""})
        self.db_con.remove_cover(cover)
        return [(id, "update") for (id,) in ids]

    def _inotify_update_info(self, path, file):
        file_path = os.path.join(path, file)
        rs = self.db_con.is_cover_exist(file_path)
        try: (cover, lmod) = rs
        except TypeError:
            return None
        image = self.__extract_cover(file_path)
        if image: self.db_con.update_cover(cover, image)
        return []
    ###########################################################


@jsonrpc_module(LibraryModule)
class VideoLibrary(_Library):
    type = "video"
    search_type = "video"
    update_signal_name = 'mediadb.vupdate'
    custom_attr = ("videoheight", "videowidth","external_subtitle",\
            "audio_channels", "subtitle_channels")
    subtitle_ext = (".srt",)
    supported_search_type = ['title']
    default_search_sort = mediafilters.DEFAULT_VIDEO_SORT

    def set_extra_infos(self, dir, file, file_id):
        file_path = os.path.join(dir, file)
        (base_path,ext) = os.path.splitext(file_path)
        sub = ""
        for ext_type in self.subtitle_ext:
            if os.path.isfile(os.path.join(base_path + ext_type)):
                sub = quote_uri(base_path + ext_type)
                break
        try:
            (recorded_sub,) = self.db_con.get_file_info(file_id,\
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
                    uri = quote_uri(os.path.join(path, file))
                    self.db_con.set_media_infos(fid, {"external_subtitle": uri})
                    return [(fid, "update")]
        return None

    def _inotify_remove_info(self, path, file):
        (base_file, ext) = os.path.splitext(file)
        if ext in self.subtitle_ext:
            ids = self.db_con.search_id("external_subtitle",\
                    quote_uri(os.path.join(path, file)))
            for (id,) in ids:
                self.db_con.set_media_infos(id, {"external_subtitle": ""})
            return [(id, "update") for (id,) in ids]
        return None

    def _inotify_update_info(self, path, file):
        return None
    ###########################################################

# vim: ts=4 sw=4 expandtab
