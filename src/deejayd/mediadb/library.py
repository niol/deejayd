# -*- coding: utf-8 -*-

import tag
import os, sys
from deejayd import database
from deejayd.ui import log
from twisted.internet import threads

class NotFoundException(Exception):pass

class DeejaydAudioFile:

    def __init__(self,db_con,player,dir,root_path):
        self.dir = dir
        self.player = player
        self.root_path = root_path
        self.update_function = db_con.update_audio_file
        self.insert_function = db_con.insert_audio_file
        self.file_type = "audio"

    def insert(self,f):
        file_info = self._get_file_info(f)
        if file_info:
            self.insert_function(self.dir,file_info)

    def update(self,f):
        file_info = self._get_file_info(f)
        if file_info:
            self.update_function(self.dir,file_info)

    def force_update(self,f):pass

    def _get_file_info(self,f):
        real_dir = os.path.join(self.root_path, self.dir)
        real_file = os.path.join(real_dir,f)

        try: file_info = tag.FileTagFactory(self.player).\
                                get_file_tag_object(real_file,self.file_type)
        except tag.NotSupportedFormat:
            # Not an supported file
            log.info("%s : %s format not supported" % (f,self.file_type))
            return None

        try: file_info.load_file_info()
        except tag.UnknownException:
            log.info(\
                "%s : unable to obtain metadata from this %s file, skipped"\
                % (f,self.file_type))
            return None
        else: return file_info


class DeejaydVideoFile(DeejaydAudioFile):

    def __init__(self,db_con,player,dir,root_path = None):
        DeejaydAudioFile.__init__(self,db_con,player,dir,root_path)
        self.db_con = db_con

        self.update_function = self.db_con.update_video_file
        self.insert_function = self.db_con.insert_video_file
        self.__id = self.db_con.get_last_video_id() or 0
        self.file_type = "video"

    def insert(self,f):
        file_info = self._get_file_info(f)
        if file_info:
            file_info["id"] = self.__get_next_id()
            self.insert_function(self.dir,file_info)

    def force_update(self,f):
        real_dir = os.path.join(self.root_path, self.dir)
        real_file = os.path.join(real_dir,f)

        # Update external subtitle
        file_info = tag.FileTagFactory(self.player).\
                                get_file_tag_object(real_file,self.file_type)
        file_info.load_subtitle()
        self.db_con.update_video_subtitle(self.dir,file_info)

    def __get_next_id(self):
        self.__id += 1
        return self.__id


class Library:

    def __init__(self, db_connection, player, path):
        # init Parms
        self._update_id = 0
        self._update_end = True
        self._update_error = None
        self._db_con_update = None

        self._player = player
        self._path = os.path.abspath(path)
        # test library path
        if not os.path.isdir(self._path):
            msg = "Unable to find directory %s" % (self._path,)
            log.err(msg)
            raise NotFoundException(msg)

        # Connection to the database
        self.db_con = db_connection

    def get_dir_content(self,dir):
        rs = self.db_con.get_dir_info(dir,self._table)
        if len(rs) == 0 and dir != "":
            # nothing found for this directory
            raise NotFoundException

        return self._format_db_rsp(rs)

    def get_dir_files(self,dir):
        rs = self.db_con.get_files(dir,self._table)
        if len(rs) == 0 and dir != "": raise NotFoundException
        return self._format_db_rsp(rs)["files"]

    def get_all_files(self,dir):
        rs = self.db_con.get_all_files(dir)
        if len(rs) == 0 and dir != "": raise NotFoundException
        return self._format_db_rsp(rs)["files"]

    def get_file(self,file):
        rs = self.db_con.get_file_info(file,self._table)
        if len(rs) == 0:
            # this file is not found
            raise NotFoundException
        return self._format_db_rsp(rs)["files"]

    def get_root_path(self):
        return self._path

    def get_status(self):
        status = []
        if not self._update_end:
            status.append((self._type+"_updating_db",self._update_id))
        if self._update_error:
            status.append((self._type+"_updating_error",self._update_error))
            self._update_error = None

        return status

    def close(self):
        pass

    #
    # Update process
    #
    def update(self):
        if self._update_end:
            self._update_id += 1
            self.defered = threads.deferToThread(self._update)
            self.defered.pause()

            # Add callback functions
            succ = lambda *x: self.end_update()
            self.defered.addCallback(succ)

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
        in_a_root = False
        for root in roots:
            if self.is_in_root(path, root):
                in_a_root = True
        return in_a_root

    def _update(self):
        self._db_con_update = self.db_con.get_new_connection()
        self._db_con_update.connect()
        self._update_end = False
        self.last_update_time = self._db_con_update.get_update_time(self._type)

        library_files = [(item[0],item[1]) for item \
                        in self._db_con_update.get_all_files('',self._table)]
        library_dirs = [(item[0],item[1]) for item in \
                            self._db_con_update.get_all_dirs('',self._table)]

        self.walk_directory(self.get_root_path(), library_dirs, library_files)

        # Remove unexistent files and directories from library
        for (dir,filename) in library_files:
            self._db_con_update.remove_file(dir,filename,self._table)
        for (root,dirname) in library_dirs:
            self._db_con_update.remove_dir(root,dirname,self._table)

        # Remove empty dir
        self._db_con_update.erase_empty_dir(self._table)

        # update stat values
        self._db_con_update.record_mediadb_stats()
        self._db_con_update.set_update_time(self._type)

        # commit changes and close the connection
        self._db_con_update.connection.commit()
        self._db_con_update.close()
        self._db_con_update = None

    def walk_directory(self, walk_root,
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
                    self._db_con_update.insert_dir(tuple,self._table)

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
            file_object = self._file_class(self._db_con_update,
                                           self._player,
                                           self.strip_root(root),
                                           self._path)
            for file in files:
                tuple = (self.strip_root(root), file)
                if tuple in library_files:
                    library_files.remove(tuple)
                    if os.stat(os.path.join(root,file)).st_mtime >= \
                                                     int(self.last_update_time):
                        file_object.update(file)
                    # Even if the media has not been modified, we may need
                    # to update some information (like external subtitle)
                    # it is the aim of this function
                    else: file_object.force_update(file)
                else: file_object.insert(file)

    def end_update(self, result = True):
        self._update_end = True
        if result: log.msg("The %s library has been updated" % self._type)
        else:
            msg = "Unable to update the %s library. See log." % self._type
            log.err(msg)
            self._update_error = msg
            # close opened connection if necessary
            if self._db_con_update != None:
                self._db_con_update.close()
                self._db_con_update = None
        return True


class AudioLibrary(Library):

    def __init__(self, db_connection, player, path):
        self._table = "audio_library"
        self._type = "audio"
        self._file_class = DeejaydAudioFile
        Library.__init__(self, db_connection, player, path)

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


class VideoLibrary(Library):

    def __init__(self, db_connection, player, path):
        self._table = "video_library"
        self._type = "video"
        self._file_class = DeejaydVideoFile
        Library.__init__(self, db_connection, player, path)

    def _format_db_rsp(self,rs):
        # format correctly database result
        files = []
        dirs = []
        for (dir,fn,t,id,ti,len,videow,videoh,sub) in rs:
            if t == 'directory': dirs.append(fn)
            else:
                file_info = {"path":os.path.join(dir,fn),"length":len,
                             "filename":fn,"dir":dir,
                             "title":ti,"id":id,
                             "videowidth":videow,"videoheight":videoh,
                             "external_subtitle":sub,"type":"video"}
                files.append(file_info)
        return {'files':files, 'dirs': dirs}

# vim: ts=4 sw=4 expandtab
