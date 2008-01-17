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

class DeejaydError(Exception):
    """General purpose error structure."""
    pass


class DeejaydAnswer:
    """General purpose core answer container."""

    def __init__(self):
        self.contents = None
        self.error = False

    def set_error(self, msg):
        self.contents = msg
        self.error = True

    def get_contents(self):
        if self.error:
            raise DeejaydError(self.contents)
        return self.contents


class DeejaydKeyValue(DeejaydAnswer):
    """Dictionnary answer."""

    def __getitem__(self, name):
        return self.contents[name]

    def keys(self):
        return self.contents.keys()

    def items(self):
        return self.contents.items()


class DeejaydFileList(DeejaydAnswer):
    """File list answer."""

    def __init__(self):
        DeejaydAnswer.__init__(self)
        self.root_dir = ""
        self.files = []
        self.directories = []

    def set_rootdir(self, dir):
        self.root_dir = dir

    def add_file(self, file):
        self.files.append(file)

    def add_dir(self, dir):
        self.directories.append(dir)

    def set_files(self, files):
        self.files = files

    def set_directories(self, dirs):
        self.directories = dirs

    def get_files(self):
        return self.files

    def get_directories(self):
        return self.directories


class DeejaydMediaList(DeejaydAnswer):
    """Media list answer."""

    def __init__(self):
        DeejaydAnswer.__init__(self)
        self.medias = []

    def add_media(self, media):
        self.medias.append(media)

    def get_medias(self):
        return self.medias

    def set_medias(self, medias):
        self.medias = medias

class DeejaydDvdInfo(DeejaydAnswer):
    """Dvd information answer."""

    def __init__(self):
        DeejaydAnswer.__init__(self)
        self.dvd_content = {}

    def set_dvd_content(self, infos):
        self.dvd_content = infos

    def add_track(self, track):
        if "track" not in self.dvd_content.keys():
            self.dvd_content['track'] = []
        self.dvd_content['track'].append(track)

    def get_dvd_contents(self):
        if "track" not in self.dvd_content.keys():
            self.dvd_content['track'] = []
        return self.dvd_content


class DeejaydWebradioList:
    """Webradio list management."""

    def get(self):
        raise NotImplementedError

    def add_webradio(self, name, urls):
        raise NotImplementedError

    def delete_webradio(self, wr_id):
        return self.delete_webradios([wr_id])

    def delete_webradios(self, wr_ids):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class DeejaydQueue:
    """Queue management."""

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def add_media(self, path, position=None):
        return self.add_medias([path], position)

    def add_medias(self, paths, type = "audio", pos = None):
        raise NotImplementedError

    def load_playlist(self, name, pos = None):
        return self.load_playlists([name], pos)

    def load_playlists(self, names, pos = None):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def del_song(self, id):
        return self.del_songs([id])

    def del_songs(self, ids):
        raise NotImplementedError


class DeejaydPlaylist:
    """Playlist management."""

    def __init__(self, pl_name = None):
        self.__pl_name = pl_name

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def save(self, name):
        raise NotImplementedError

    def add_song(self, path, position = None):
        return self.add_songs([path], position)

    def add_songs(self, paths, position = None):
        raise NotImplementedError

    def load(self, name, pos = None):
        return self.loads([name], pos)

    def loads(self, names, pos = None):
        raise NotImplementedError

    def move(self, ids, new_pos):
        raise NotImplementedError

    def shuffle(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def del_song(self, id):
        return self.del_songs([id])

    def del_songs(self, ids):
        raise NotImplementedError


class DeejaydCore:
    """Abstract class for a deejayd core."""

    def ping(self):
        raise NotImplementedError

    def play_toggle(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def previous(self):
        raise NotImplementedError

    def next(self):
        raise NotImplementedError

    def seek(self, pos):
        raise NotImplementedError

    def get_current(self):
        raise NotImplementedError

    def go_to(self, id, id_type = None, source = None):
        raise NotImplementedError

    def set_volume(self, volume_value):
        raise NotImplementedError

    def set_option(self, option_name, option_value):
        raise NotImplementedError

    def set_mode(self, mode_name):
        raise NotImplementedError

    def get_mode(self):
        raise NotImplementedError

    def set_alang(self, lang_idx):
        raise NotImplementedError

    def set_slang(self, lang_idx):
        raise NotImplementedError

    def get_status(self):
        raise NotImplementedError

    def get_stats(self):
        raise NotImplementedError

    def update_audio_library(self):
        raise NotImplementedError

    def update_video_library(self):
        raise NotImplementedError

    def erase_playlist(self, names):
        raise NotImplementedError

    def get_playlist_list(self):
        raise NotImplementedError

    def get_playlist(self, name=None):
        raise NotImplementedError

    def get_webradios(self):
        raise NotImplementedError

    def get_queue(self):
        raise NotImplementedError

    def get_audio_dir(self, dir=None):
        raise NotImplementedError

    def audio_search(self, search_txt, type = 'all'):
        raise NotImplementedError

    def get_video_dir(self, dir=None):
        raise NotImplementedError

    def get_videolist(self):
        raise NotImplementedError

    def set_video(self, value, type):
        raise NotImplementedError

    def dvd_reload(self):
        raise NotImplementedError

    def get_dvd_content(self):
        raise NotImplementedError


# vim: ts=4 sw=4 expandtab
