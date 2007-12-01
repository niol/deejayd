import deejayd.interfaces
from deejayd.interfaces import DeejaydError,\
                               DeejaydAnswer, DeejaydKeyValue, DeejaydFileList,\
                               DeejaydMediaList, DeejaydDvdInfo
from deejayd.ui.config import DeejaydConfig
from deejayd import player, sources, mediadb, database

# Exception imports
import deejayd.sources.webradio
import deejayd.sources._base
import deejayd.sources.playlist
import deejayd.mediadb.library


# FIXME : This file is still a big mess. All commands that are flagged not
# implemented (raising NotImplementedError) should be rewritten as directly
# calling appropriate methods on deejayd internal objects. See commandXML for
# implementation. See testdeejayd/test_core.py to known what should already
# work.


class DeejaydWebradioList(deejayd.interfaces.DeejaydWebradioList):

    def __init__(self, deejaydcore):
        self.deejaydcore = deejaydcore
        self.source = self.__get_wr_source()

    def __get_wr_source(self):
        try:
            return self.deejaydcore.sources.get_source('webradio')
        except sources.sources.UnknownSourceException:
            raise DeejaydError('Webradio support not available.')

    def get(self):
        return self.source.get_content()

    def names(self):
        all_wr = self.get()
        names = []
        for wr in all_wr:
            names.append(wr['title'])
        return names

    def get_webradio(self, name):
        all_wr = self.get()
        for wr in all_wr:
            if wr['title'] == name:
                return wr
        raise DeejaydError('Webradio %s not found' % name)

    def add_webradio(self, name, urls):
        try:
            self.source.add(urls, name)
        except sources.webradio.UnsupportedFormatException:
            raise DeejaydError('Webradio URI not supported')
        except deejayd.mediadb.library.NotFoundException:
            raise DeejaydError('Webradio info could not be retrieved')

    def delete_webradios(self, wr_ids):
        for id in wr_ids:
            try:
                self.source.delete(int(id))
            except sources._base.ItemNotFoundException:
                raise DeejaydError('Webradio with id %d not found' % id)

    def clear(self):
        self.source.clear()


class DeejaydQueue(deejayd.interfaces.DeejaydQueue):

    def __init__(self, deejaydcore):
        self.deejaydcore = deejaydcore
        self.source = self.deejaydcore.sources.get_source('queue')

    def get(self, first = 0, length = None):
        return self.source.get_content()

    def add_songs(self, paths, position = None):
        position = position and int(position) or None
        try:
            self.source.add_path(paths, position)
        except sources._base.ItemNotFoundException:
            raise DeejaydError('%s not found' % (paths,))

    def loads(self, names, pos=None):
        pos = pos and int(pos) or None
        try:
            self.source.load_playlist(self.name, pos)
        except sources.playlist.PlaylistNotFoundException:
            raise DeejaydError('Playlist %s does not exist.' % name)

    def clear(self):
        self.source.clear()

    def del_songs(self, ids):
        for id in ids:
            try:
                self.source.delete(int(id))
            except sources._base.ItemNotFoundException:
                raise DeejaydError('Song with id %d not found', id)


class DeejaydPlaylist(deejayd.interfaces.DeejaydPlaylist):

    def __init__(self, deejaydcore, name=None):
        self.deejaydcore = deejaydcore
        self.source = self.deejaydcore.sources.get_source("playlist")
        self.name = name

    def get(self, first=0, length=-1):
        try:
            songs = self.source.get_content(self.name)
        except sources.playlist.PlaylistNotFoundException:
            raise DeejaydError('Playlist %s not found' % self.name)
        else:
            ml = DeejaydMediaList()
            last = length == -1 and len(songs) or int(first) + int(length) - 1
            ml.set_medias(songs[int(first):last])
            return ml

    def save(self, name):
        try:
            self.source.save(name)
        except sources.playlist.PlaylistNotFoundException:
            raise DeejaydError('Playlist %s does not exist.' % name)

    def add_songs(self, paths, position=None):
        pos = position and int(position) or None
        try:
            self.source.add_path(paths, self.name, pos)
        except sources._base.ItemNotFoundException:
            raise DeejaydError('%s not found' % (paths,))

    def loads(self, names, pos=None):
        pos = pos and int(pos) or None
        try:
            self.source.load_playlist(self.name, pos)
        except sources.playlist.PlaylistNotFoundException:
            raise DeejaydError('Playlist %s does not exist.' % name)

    def shuffle(self, name=None):
        try:
            self.source.shuffle(name)
        except sources.playlist.PlaylistNotFoundException:
            raise DeejaydError('Playlist %s does not exist.' % name)

    def clear(self, name=None):
        try:
            self.source.clear(name)
        except sources.playlist.PlaylistNotFoundException:
            raise DeejaydError('Playlist %s does not exist.' % name)

    def del_songs(self, ids, name=None):
        if not name:
            name = self.name

        for nb in ids:
            try:
                self.source.delete(int(nb), "id", name)
            except sources._base.ItemNotFoundException:
                raise DeejaydError('Playlist %s does not have a song of id %d'
                                   % (name, nb))
            except sources.playlist.PlaylistNotFoundException:
                raise DeejaydError('Playlist %s does not exist.' % name)


class DeejayDaemonCore(deejayd.interfaces.DeejaydCore):

    def __init__(self, config=None):
        if not config:
            config = DeejaydConfig()

        db = database.init(config).get_db()
        db.connect()

        self.player = player.init(db, config)

        self.audio_library,self.video_library = mediadb.init(db,\
                                            self.player,config)

        self.sources = sources.init(self.player, db, self.audio_library,
                                             self.video_library, config)

    def play_toggle(self):
        # play
        raise NotImplementedError

    def stop(self):
        # stop
        raise NotImplementedError

    def previous(self):
        # previous
        raise NotImplementedError

    def next(self):
        # next
        raise NotImplementedError

    def seek(self, pos):
        # seek
        raise NotImplementedError

    def get_current(self):
        # current
        raise NotImplementedError

    def get_playlist(self, name=None):
        pls = DeejaydPlaylist(self, name)
        pls.get()
        return pls

    def get_webradios(self):
        return DeejaydWebradioList(self)

    def get_queue(self):
        return DeejaydQueue(self)

    def go_to(self, id, id_type = None, source = None):
        # play
        raise NotImplementedError

    def set_volume(self, volume_value):
        # setVolume
        raise NotImplementedError

    def set_option(self, option_name, option_value):
        # setOption
        raise NotImplementedError

    def set_mode(self, mode_name):
        try:
            self.sources.set_source(mode_name)
        except sources.UnknownSourceException:
            raise DeejaydError('Unknown mode: %s' % mode_name)

    def get_modes(self):
        # getMode
        raise NotImplementedError

    def set_alang(self, lang_idx):
        # setAland
        raise NotImplementedError

    def set_slang(self, lang_idx):
        # setSlang
        raise NotImplementedError

    def get_status(self):
        status = self.player.get_status()
        status.extend(self.sources.get_status())
        status.extend(self.audio_library.get_status())
        if self.video_library:
            status.extend(self.video_library.get_status())
        return dict(status)

    def get_stats(self):
        # stats
        raise NotImplementedError

    def update_audio_library(self):
        return self.audio_library.update()

    def update_video_library(self):
        return self.video_library.update()

    def erase_playlist(self, name):
        # playlistErase
        raise NotImplementedError

    def get_playlist_list(self):
        return self.sources.get_source('playlist').get_list()

    def get_audio_dir(self,dir = None):
        # getDir
        raise NotImplementedError

    def audio_search(self, search_txt, type):
        raise NotImplementedError

    def get_video_dir(self,dir = None):
        # getvideodir
        raise NotImplementedError

    def set_video_dir(self, dir):
        # setvideodir
        raise NotImplementedError

    def dvd_reload(self):
        # dvdLoad
        raise NotImplementedError

    def get_dvd_content(self):
        # dvdInfo
        raise NotImplementedError


# vim: ts=4 sw=4 expandtab
