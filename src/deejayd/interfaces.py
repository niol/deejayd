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


import locale


class DeejaydError(Exception):
    """General purpose error structure."""

    # Handle unicode messages, what Exceptions cannot. See Python issue at
    # http://bugs.python.org/issue2517
    def __str__(self):
        if type(self.message) is unicode:
            return str(self.message.encode(locale.getpreferredencoding()))
        else:
            return str(self.message)


class DeejaydAnswer(object):
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
        self.get_contents()
        return self.contents[name]

    def keys(self):
        self.get_contents()
        return self.contents.keys()

    def items(self):
        self.get_contents()
        return self.contents.items()


class DeejaydList(DeejaydAnswer):
    """List answer."""

    def __len__(self):
        self.get_contents()
        return len(self.contents)

    def __iter__(self):
        self.get_contents()
        return self.contents.__iter__()


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
        self.get_contents()
        return self.files

    def get_directories(self):
        self.get_contents()
        return self.directories


class DeejaydMediaList(DeejaydAnswer):
    """Media list answer."""

    def __init__(self):
        DeejaydAnswer.__init__(self)
        self.medias = []
        self.total_length = None
        self.filter = None
        self.order = None

    def set_total_length(self, length):
        self.total_length = length

    def get_total_length(self):
        return self.total_length

    def add_media(self, media):
        self.medias.append(media)

    def get_medias(self):
        self.get_contents()
        return self.medias

    def set_medias(self, medias):
        self.medias = medias

    def is_magic(self):
        return self.filter != None

    def set_filter(self, filter):
        self.filter = filter

    def get_filter(self):
        return self.filter

    def set_order(self, order):
        self.order = order

    def get_order(self):
        return self.order


class DeejaydDvdInfo(DeejaydAnswer):
    """Dvd information answer."""

    def __init__(self):
        DeejaydAnswer.__init__(self)
        self.dvd_content = {}

    def set_dvd_content(self, infos):
        for (k, v) in infos.items():
            self.dvd_content[k] = v

    def add_track(self, track):
        if "track" not in self.dvd_content.keys():
            self.dvd_content['track'] = []
        self.dvd_content['track'].append(track)

    def get_dvd_contents(self):
        self.get_contents()
        if "track" not in self.dvd_content.keys():
            self.dvd_content['track'] = []
        return self.dvd_content


class DeejaydStaticPlaylist(object):
    """ Static playlist object """

    def get(self, first=0, length=-1):
        raise NotImplementedError

    def add_path(self, path):
        return self.add_paths([path])

    def add_paths(self, paths):
        raise NotImplementedError

    def add_song(self, song_id):
        return self.add_songs([song_id])

    def add_songs(self, song_ids):
        raise NotImplementedError


class DeejaydWebradioList(object):
    """Webradio list management."""

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def add_webradio(self, name, urls):
        raise NotImplementedError

    def delete_webradio(self, wr_id):
        return self.delete_webradios([wr_id])

    def delete_webradios(self, wr_ids):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class DeejaydQueue(object):
    """Queue management."""

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def add_path(self, path, pos = None):
        return self.add_paths([path], pos)

    def add_paths(self, paths, pos = None):
        raise NotImplementedError

    def add_song(self, song_id, pos = None):
        return self.add_songs([song_id], pos)

    def add_songs(self, song_ids, pos = None):
        raise NotImplementedError

    def load_playlist(self, pl_id, pos = None):
        return self.load_playlists([pl_id], pos)

    def load_playlists(self, pl_ids, pos = None):
        raise NotImplementedError

    def move(self, ids, new_pos):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def del_song(self, id):
        return self.del_songs([id])

    def del_songs(self, ids):
        raise NotImplementedError


class DeejaydPanel(object):

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def get_active_list(self):
        raise NotImplementedError

    def set_active_list(self, type, pl_id=""):
        raise NotImplementedError

    def set_panel_filters(self, tag, values):
        raise NotImplementedError

    def remove_panel_filters(self, tag):
        raise NotImplementedError

    def clear_panel_filters(self):
        raise NotImplementedError

    def set_search_filter(self):
        raise NotImplementedError

    def clear_search_filter(self):
        raise NotImplementedError

    def set_orders(self):
        raise NotImplementedError


class DeejaydPlaylistMode(object):

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def save(self, name):
        raise NotImplementedError

    def add_path(self, path, pos = None):
        return self.add_paths([path], pos)

    def add_paths(self, paths, pos = None):
        raise NotImplementedError

    def add_song(self, song_id, pos = None):
        return self.add_songs([song_id], pos)

    def add_songs(self, song_ids, pos = None):
        raise NotImplementedError

    def load(self, pl_id, pos = None):
        return self.loads([pl_id], pos)

    def loads(self, pl_ids, pos = None):
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


class DeejaydVideo(object):
    """Video management."""

    def get(self, first = 0, length = None):
        raise NotImplementedError

    def set(self, value, type = "directory"):
        raise NotImplementedError


class DeejaydSignal(object):

    SIGNALS = ('player.status',       # Player status change (play/pause/stop/
                                      # random/repeat/volume/manseek)
               'player.current',      # Currently played song
               'player.plupdate',     # The current playlist has changed
               'playlist.update',     # The stored playlist list has changed
                                      # (either a saved playlist has been saved
                                      # or deleted).
               'webradio.listupdate',
               'panel.update',
               'queue.update',
               'video.update',
               'dvd.update',
               'mode',                # Mode change
               'mediadb.aupdate',     # Media library audio update
               'mediadb.vupdate',     # Media library video update
              )

    def __init__(self, name=None):
        self.name = name

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name


class DeejaydCore(object):
    """Abstract class for a deejayd core."""

    def __init__(self):
        self._clear_subscriptions()

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

    def set_option(self, source, option_name, option_value):
        raise NotImplementedError

    def set_mode(self, mode_name):
        raise NotImplementedError

    def get_mode(self):
        raise NotImplementedError

    def set_player_option(self, option_name, option_value):
        raise NotImplementedError

    def get_status(self):
        raise NotImplementedError

    def get_stats(self):
        raise NotImplementedError

    def update_audio_library(self):
        raise NotImplementedError

    def update_video_library(self):
        raise NotImplementedError

    def create_recorded_playlist(self, name, type):
        raise NotImplementedError

    def get_recorded_playlist(self, pl_id):
        raise NotImplementedError

    def erase_playlist(self, pl_ids):
        raise NotImplementedError

    def get_playlist_list(self):
        raise NotImplementedError

    def get_playlist(self):
        raise NotImplementedError

    def get_webradios(self):
        raise NotImplementedError

    def get_queue(self):
        raise NotImplementedError

    def get_panel(self):
        raise NotImplementedError

    def get_video(self):
        raise NotImplementedError

    def set_media_rating(self, media_ids, rating, type = "audio"):
        raise NotImplementedError

    def get_audio_dir(self, dir=None):
        raise NotImplementedError

    def get_audio_cover(self, media_id):
        raise NotImplementedError

    def audio_search(self, search_txt, type = 'all'):
        raise NotImplementedError

    def get_video_dir(self, dir=None):
        raise NotImplementedError

    def dvd_reload(self):
        raise NotImplementedError

    def mediadb_list(self, taglist, filter):
        raise NotImplementedError

    def get_dvd_content(self):
        raise NotImplementedError

    def __get_next_sub_id(self):
        sub_id = self.__sub_id_counter
        self.__sub_id_counter = self.__sub_id_counter + 1
        return sub_id

    def subscribe(self, signal_name, callback):
        """Subscribe to a signal with a callback. Returns an id."""
        if signal_name not in DeejaydSignal.SIGNALS:
            return DeejaydError('Unknown signal provided for subscription.')

        sub_id = self.__get_next_sub_id()
        self.__sig_subscriptions[sub_id] = (signal_name, callback)
        return sub_id

    def unsubscribe(self, sub_id):
        """Unsubscribe using the provied id."""
        try:
            del self.__sig_subscriptions[sub_id]
        except IndexError:
            raise DeejaydError('Unknown subscription id')

    def get_subscriptions(self):
        """Get the list of currently subcribed signals for this instance."""
        return dict([(sub_id, sub[0]) for (sub_id, sub)\
                                      in self.__sig_subscriptions.items()])

    def _clear_subscriptions(self):
        self.__sig_subscriptions = {}
        self.__sub_id_counter = 0

    def _dispatch_signal(self, signal):
        for cb in [sub[1] for sub in self.__sig_subscriptions.values()\
                                  if sub[0] == signal.get_name()]:
            cb(signal)

    def _dispatch_signame(self, signal_name):
        self._dispatch_signal(DeejaydSignal(signal_name))


# vim: ts=4 sw=4 expandtab
