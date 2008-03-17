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

import deejayd.interfaces
from deejayd.interfaces import DeejaydError,\
                               DeejaydAnswer, DeejaydKeyValue, DeejaydFileList,\
                               DeejaydMediaList, DeejaydDvdInfo
from deejayd.ui.config import DeejaydConfig
from deejayd import player, sources, mediadb, database

# Exception imports
import deejayd.sources.webradio
import deejayd.mediadb.library


def require_mode(mode_name):
    def require_mode_instance(func):

        def require_mode_func(self, *__args, **__kw):
            if self.sources.is_available(mode_name):
                return func(self, *__args, **__kw)
            else:
                raise DeejaydError(_("mode %s is not activated.") % mode_name)

        require_mode_func.__name__ = func.__name__
        return require_mode_func

    return require_mode_instance

# This decorator is used for the core interface to provide :
# - A simple way of converting python types to deejayd answers as required by
#   the defined network interface. This is to ensure that the core API stays
#   the same as the client library API. This way, code written as a deejayd
#   client can become a full media player for free by swaping
#   deejayd.net.DeejaydClient and deejayd.core.DeejaydCore .
# - A simple way to make this optionnal using an optionnal objanswer argument.
#   Please don't use objanswer=False if you think that what you write may one
#   day be used as a deejayd network client. This was originally provided for
#   use in the deejayd.net.commandsXML module.
def returns_deejaydanswer(answer_class):
    def returns_deejaydanswer_instance(func):

        def interface_clean_func(*__args, **__kw):
            if __kw.has_key('objanswer'):
                objanswer = __kw['objanswer']
                del __kw['objanswer']
            else:
               objanswer = True
            if objanswer:
                ans = answer_class()
                try:
                    res = func(*__args, **__kw)
                except DeejaydError, txt:
                    ans.set_error(txt)
                else:
                    if res == None:
                        ans.contents = True
                    elif answer_class == DeejaydMediaList:
                        ans.set_medias(res)
                    elif answer_class == DeejaydFileList:
                        root_dir, dirs, files = res
                        if root_dir != None:
                            ans.set_rootdir(root_dir)
                        ans.set_files(files)
                        ans.set_directories(dirs)
                    elif answer_class == DeejaydDvdInfo:
                        ans.set_dvd_content(res)
                    else:
                        ans.contents = res
                return ans
            else:
                return func(*__args, **__kw)

        interface_clean_func.__name__ = func.__name__
        return interface_clean_func

    return returns_deejaydanswer_instance


class DeejaydWebradioList(deejayd.interfaces.DeejaydWebradioList):

    def __init__(self, deejaydcore):
        self.deejaydcore = deejaydcore
        self.source = self.__get_wr_source()

    def __get_wr_source(self):
        try:
            return self.deejaydcore.sources.get_source('webradio')
        except sources.sources.UnknownSourceException:
            raise DeejaydError(_('Webradio support not available.'))

    @returns_deejaydanswer(DeejaydMediaList)
    def get(self):
        return self.source.get_content()

    @returns_deejaydanswer(DeejaydAnswer)
    def add_webradio(self, name, urls):
        try:
            self.source.add(urls, name)
        except sources.webradio.UnsupportedFormatException:
            raise DeejaydError(_('Webradio URI not supported'))
        except sources.webradio.UrlNotFoundException:
            raise DeejaydError(_('Webradio info could not be retrieved'))

    @returns_deejaydanswer(DeejaydAnswer)
    def delete_webradios(self, wr_ids):
        for id in wr_ids:
            try:
                self.source.delete(int(id))
            except sources._base.MediaNotFoundError:
                raise DeejaydError(_('Webradio with id %d not found') % int(id))

    @returns_deejaydanswer(DeejaydAnswer)
    def clear(self):
        self.source.clear()


class DeejaydQueue(deejayd.interfaces.DeejaydQueue):

    def __init__(self, deejaydcore):
        self.deejaydcore = deejaydcore
        self.source = self.deejaydcore.sources.get_source('queue')

    @returns_deejaydanswer(DeejaydMediaList)
    def get(self, first = 0, length = None):
        return self.source.get_content()

    @returns_deejaydanswer(DeejaydAnswer)
    def add_medias(self, paths, pos = None):
        position = pos and int(pos) or None
        try:
            self.source.add_path(paths, position)
        except sources._base.MediaNotFoundError:
            raise DeejaydError(_('%s not found') % (paths,))

    @returns_deejaydanswer(DeejaydAnswer)
    def load_playlists(self, names, pos=None):
        pos = pos and int(pos) or None
        try:
            self.source.load_playlist(names, pos)
        except sources._base.PlaylistNotFoundError:
            raise DeejaydError(_('Playlist %s does not exist.') % str(names))

    @returns_deejaydanswer(DeejaydAnswer)
    def clear(self):
        self.source.clear()

    @returns_deejaydanswer(DeejaydAnswer)
    def del_songs(self, ids):
        for id in ids:
            try:
                self.source.delete(int(id))
            except sources._base.MediaNotFoundError:
                raise DeejaydError(_('Song with id %d not found') % int(id))


class DeejaydPlaylist(deejayd.interfaces.DeejaydPlaylist):

    def __init__(self, deejaydcore, name=None):
        self.deejaydcore = deejaydcore
        self.source = self.deejaydcore.sources.get_source("playlist")
        self.name = name

    @returns_deejaydanswer(DeejaydMediaList)
    def get(self, first=0, length=-1):
        try:
            songs = self.source.get_content(playlist = self.name)
        except sources._base.PlaylistNotFoundError:
            raise DeejaydError(_('Playlist %s not found') % self.name)
        else:
            last = length == -1 and len(songs) or int(first) + int(length) - 1
            return songs[int(first):last]

    @returns_deejaydanswer(DeejaydAnswer)
    def save(self, name):
        self.source.save(name)

    @returns_deejaydanswer(DeejaydAnswer)
    def add_songs(self, paths, position=None):
        p = position and int(position) or None
        try:
            self.source.add_path(paths, playlist = self.name, pos = p)
        except sources._base.MediaNotFoundError:
            raise DeejaydError(_('%s not found') % (paths,))
        except sources._base.PlaylistNotFoundError:
            raise DeejaydError(_('Playlist %s not found') % self.name)

    @returns_deejaydanswer(DeejaydAnswer)
    def loads(self, names, pos=None):
        if self.name != None:
            raise DeejaydError(_('Unable to load pls in a saved pls.'))
        pos = pos and int(pos) or None
        try:
            self.source.load_playlist(names, pos)
        except sources._base.PlaylistNotFoundError:
            raise DeejaydError(_('Playlist %s does not exist.') % str(names))

    @returns_deejaydanswer(DeejaydAnswer)
    def move(self, ids, new_pos):
        if self.name != None:
            raise DeejaydError(_('Unable to load pls in a saved pls.'))
        ids = [int(id) for id in ids]
        try:
            self.source.move(ids, int(new_pos))
        except sources._base.MediaNotFoundError:
            raise DeejaydError(_('song with ids %s not found') % (str(ids),))

    @returns_deejaydanswer(DeejaydAnswer)
    def shuffle(self):
        try:
            self.source.shuffle(playlist = self.name)
        except sources._base.PlaylistNotFoundError:
            raise DeejaydError(_('Playlist %s does not exist.') % self.name)

    @returns_deejaydanswer(DeejaydAnswer)
    def clear(self):
        try:
            self.source.clear(playlist = self.name)
        except sources._base.PlaylistNotFoundError:
            raise DeejaydError(_('Playlist %s does not exist.') % self.name)

    @returns_deejaydanswer(DeejaydAnswer)
    def del_songs(self, ids):
        name = self.name
        for nb in ids:
            try:
                self.source.delete(int(nb), "id", playlist = name)
            except sources._base.MediaNotFoundError:
                raise DeejaydError(\
                  _('Playlist %s does not have a song of id %d') % (name, nb))
            except sources._base.PlaylistNotFoundError:
                raise DeejaydError(_('Playlist %s does not exist.') % name)


class DeejayDaemonCore(deejayd.interfaces.DeejaydCore):

    def __init__(self, config=None):
        deejayd.interfaces.DeejaydCore.__init__(self)

        if not config:
            config = DeejaydConfig()

        self.db = database.init(config)
        self.db.connect()

        self.player = player.init(self.db, config)
        self.player.register_dispatcher(self)

        self.audio_library,self.video_library, self.watcher = \
            mediadb.init(self.db, self.player,config)
        self.audio_library.register_dispatcher(self)
        if self.video_library:
            self.video_library.register_dispatcher(self)

        self.sources = sources.init(self.player, self.db, self.audio_library,
                                             self.video_library, config)
        self.sources.register_dispatcher(self)
        for source in self.sources.sources_obj.values():
            source.register_dispatcher(self)

        # start inotify thread when we are sure that all init stuff are ok
        if self.watcher:
            self.watcher.start()

    def close(self):
        for obj in (self.watcher,self.player,self.sources,self.audio_library,\
                    self.video_library,self.db):
            if obj != None: obj.close()

    @returns_deejaydanswer(DeejaydAnswer)
    def play_toggle(self):
        if self.player.get_state() == player._base.PLAYER_PLAY:
            self.player.pause()
        else:
            try: self.player.play()
            except player.PlayerError, err:
                raise DeejaydError(str(err))

    @returns_deejaydanswer(DeejaydAnswer)
    def stop(self):
        self.player.stop()

    @returns_deejaydanswer(DeejaydAnswer)
    def previous(self):
        try: self.player.previous()
        except player.PlayerError, err:
            raise DeejaydError(str(err))

    @returns_deejaydanswer(DeejaydAnswer)
    def next(self):
        try: self.player.next()
        except player.PlayerError, err:
            raise DeejaydError(str(err))

    @returns_deejaydanswer(DeejaydAnswer)
    def seek(self, pos):
        self.player.set_position(int(pos))

    @returns_deejaydanswer(DeejaydMediaList)
    def get_current(self):
        medias = []
        current = self.player.get_playing()
        if current != None:
            medias.append(current)
        return medias

    @require_mode("playlist")
    def get_playlist(self, name=None):
        pls = DeejaydPlaylist(self, name)
        pls.get()
        return pls

    @require_mode("webradio")
    def get_webradios(self):
        return DeejaydWebradioList(self)

    def get_queue(self):
        return DeejaydQueue(self)

    @returns_deejaydanswer(DeejaydAnswer)
    def go_to(self, id, id_type = "id", source = None):
        if id_type != "dvd_id":
            try: id = int(id)
            except ValueError:
                raise DeejaydError(_("Bad value for id parm"))

        try: self.player.go_to(id, id_type, source)
        except player.PlayerError, err:
            raise DeejaydError(str(err))

    @returns_deejaydanswer(DeejaydAnswer)
    def set_volume(self, volume_value):
        self.player.set_volume(int(volume_value))

    @returns_deejaydanswer(DeejaydAnswer)
    def set_option(self, option_name, option_value):
        try: self.sources.set_option(option_name, int(option_value))
        except KeyError:
            raise DeejaydError(_('Option %s does not exist') % option_name)

    @returns_deejaydanswer(DeejaydAnswer)
    def set_mode(self, mode_name):
        try:
            self.sources.set_source(mode_name)
        except sources.UnknownSourceException:
            raise DeejaydError(_('Unknown mode: %s') % mode_name)

    @returns_deejaydanswer(DeejaydKeyValue)
    def get_mode(self):
        av_sources = self.sources.get_available_sources()
        modes = {}
        for s in self.sources.sources_list:
            modes[s] = s in av_sources or 1 and 0
        return modes

    @returns_deejaydanswer(DeejaydAnswer)
    def set_player_option(self, name, value):
        try: self.player.set_option(name, int(value))
        except KeyError:
            raise DeejaydError(_("Option %s does not exist") % name)
        except NotImplementedError:
            raise DeejaydError(_("Option %s is not supported for this backend")\
                                % name)
        except player.PlayerError, err:
            raise DeejaydError(err)

    @returns_deejaydanswer(DeejaydKeyValue)
    def get_status(self):
        status = self.player.get_status()
        status.extend(self.sources.get_status())
        status.extend(self.audio_library.get_status())
        if self.video_library:
            status.extend(self.video_library.get_status())
        return dict(status)

    @returns_deejaydanswer(DeejaydKeyValue)
    def get_stats(self):
        ans = self.db.get_stats()
        return dict(ans)

    @returns_deejaydanswer(DeejaydKeyValue)
    def update_audio_library(self, sync = False):
        return {'audio_updating_db': self.audio_library.update(sync)}

    @require_mode("video")
    @returns_deejaydanswer(DeejaydKeyValue)
    def update_video_library(self, sync = False):
        if not self.video_library:
            raise DeejaydError(_("Video mode disabled"))
        return {'video_updating_db': self.video_library.update(sync)}

    @require_mode("playlist")
    @returns_deejaydanswer(DeejaydAnswer)
    def erase_playlist(self, names):
        for name in names:
            self.sources.get_source("playlist").rm(name)

    @require_mode("playlist")
    @returns_deejaydanswer(DeejaydMediaList)
    def get_playlist_list(self):
        plname_list = []
        for plname in self.sources.get_source('playlist').get_list():
            plname_list.append({'name': plname})
        return plname_list

    @returns_deejaydanswer(DeejaydFileList)
    def get_audio_dir(self,dir = None):
        if dir == None: dir = ""
        try: contents = self.audio_library.get_dir_content(dir)
        except deejayd.mediadb.library.NotFoundException:
            raise DeejaydError(_('Directory %s not found in database') % dir)

        return dir, contents['dirs'], contents['files']

    @returns_deejaydanswer(DeejaydFileList)
    def audio_search(self, search_txt, type = 'all'):
        try: list = self.audio_library.search(type, search_txt)
        except deejayd.mediadb.library.NotFoundException:
            raise DeejaydError(_('Type %s is not supported') % (type,))

        return None, [], list

    @require_mode("video")
    @returns_deejaydanswer(DeejaydFileList)
    def get_video_dir(self,dir = None):
        if not self.video_library:
            raise DeejaydError(_("Video mode disabled"))

        if dir == None: dir = ""
        try: contents = self.video_library.get_dir_content(dir)
        except deejayd.mediadb.library.NotFoundException:
            raise DeejaydError(_('Directory %s not found in database') % dir)

        return dir, contents['dirs'], contents['files']

    @require_mode("video")
    @returns_deejaydanswer(DeejaydMediaList)
    def get_videolist(self):
        return self.sources.get_source("video").get_content()

    @require_mode("video")
    @returns_deejaydanswer(DeejaydAnswer)
    def set_video(self, value, type = "directory"):
        try: self.sources.get_source("video").set(type, value)
        except deejayd.sources._base.MediaNotFoundError:
            raise DeejaydError(_('Directory %s not found in database') % value)

    @require_mode("dvd")
    @returns_deejaydanswer(DeejaydAnswer)
    def dvd_reload(self):
        try: self.sources.get_source("dvd").load()
        except sources.dvd.DvdError, msg:
            raise DeejaydError('%s' % msg)

    @require_mode("dvd")
    @returns_deejaydanswer(DeejaydDvdInfo)
    def get_dvd_content(self):
        return self.sources.get_source("dvd").get_content()


# vim: ts=4 sw=4 expandtab
