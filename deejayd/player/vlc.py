# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import os
import threading
from twisted.internet import reactor, task
from deejayd.player import _vlc
from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from pytyx11 import x11
from deejayd.player._base import _BasePlayer, PLAYER_PAUSE, \
                                 PLAYER_PLAY, PLAYER_STOP


LIBVLC_VERSIONS = ('2.2', )


@jsonrpc_module(PlayerModule)
class VlcPlayer(_BasePlayer):
    class PlayingEventHandler(object):

        def __init__(self, evt_mg):
            self.__lock = threading.Lock()
            self.__event = threading.Event()
            self.__playing = False
            evt_mg.event_attach(_vlc.EventType.MediaPlayerPlaying,
                                self.on_playing_event)
            evt_mg.event_attach(_vlc.EventType.MediaPlayerEncounteredError,
                                self.on_error_event)

        def on_error_event(self, instance):
            self.__event.set()

        def on_playing_event(self, instance):
            self.__lock.acquire()
            self.__playing = True
            self.__lock.release()
            self.__event.set()

        def get_playing(self):
            self.__lock.acquire()
            result = bool(self.__playing)
            self.__lock.release()
            return result

        def wait(self, timeout=None):
            self.__event.wait(timeout)

        def release(self, evt_mg):
            evt_mg.event_detach(_vlc.EventType.MediaPlayerPlaying)
            evt_mg.event_detach(_vlc.EventType.MediaPlayerEncounteredError)

    NAME = "vlc"
    supported_options = (
        "current-audio",
        "av-offset",
        "sub-offset",
        "current-sub",
        'aspect-ratio',
    )

    def __init__(self, config):
        super(VlcPlayer, self).__init__(config)
        # test version, this backend only works with specific versions of vlc
        version = _vlc.libvlc_get_version()
        good_version = False
        for v in LIBVLC_VERSIONS:
            if version.startswith(v):
                good_version = True
        if not good_version:
            raise PlayerError(_("Vlc backend only works with versions %s of "
                             "libvlc") % ', '.join([v + 'X'
                                                    for v in LIBVLC_VERSIONS]))

        # init main instance
        options = "--audio-replay-gain-mode none"
        if not self.video_enable:
            options += " --no-video"
        try:
            self.__vlc = _vlc.Instance(options)
        except _vlc.VLCException, ex:
            raise PlayerError(_("Unable to init vlc player: %s") % ex)

        # init vlc player and event manager
        self.__player = self.__vlc.media_player_new()
        self.__evt_manager = self.__player.event_manager()
        self.__evt_manager.event_attach(_vlc.EventType.MediaPlayerEndReached,
                                        self.__on_eof)
        # set audio output
        wanted_aout = config.get("vlc", "audio_output")
        if wanted_aout != "auto":
            try:
                self.__player.audio_output_set(wanted_aout)
            except Exception:
                raise PlayerError(_("VLC does not support audio "
                                    "output %s") % wanted_aout)

        # other variables
        self.__osd_call_id = None
        self.__display = None
        self.__window = None
        self.__playing_handler = None
        # task to update metadata, useful for webradio
        # because no event is fired when the playing song changes
        self.__metadata_task = task.LoopingCall(self.__check_metadata)

    def play(self):
        if self._playing_media is None:
            return

        playing = False
        uris = iter(self._playing_media.get_uris())
        try:
            while not playing:
                uri = uris.next()
                media = self.__vlc.media_new(uri)
                self.__player.set_media(media)
                needs_video = self.video_enable and self._playing_media.has_video()
                if needs_video and self.__window is None:
                    self.__prepare_x_window()
                    self.__player.set_xwindow(self.__window.window_p())

                self.__playing_handler = VlcPlayer.PlayingEventHandler(self.__evt_manager)
                self.__player.play()
                self.__playing_handler.wait(3)
                playing = self.__playing_handler.get_playing()
                self.__playing_handler.release(self.__evt_manager)
        except StopIteration:
            raise PlayerError(_("unable to play file "
                                "%s") % self._playing_media['title'])
        else:
            # check metadata periodically if necessary
            if self._playing_media.need_metadata_refresh():
                self.__metadata_task.start(2)
            
            # restore video state for this media
            if self._playing_media.has_video():
                p_state = self._playing_media["playing_state"]
                self._player_set_zoom(p_state["zoom"])
                self._player_set_aspectratio(p_state["aspect-ratio"])

    def pause(self):
        self.__player.pause()
        self.dispatch_signame('player.status')

    def get_position(self):
        if self.get_state() != PLAYER_STOP:
            return int(self.__player.get_time() / 1000)
        return 0

    def _set_position(self, pos):
        if self.get_state() != PLAYER_STOP and self.__player.is_seekable():
            self.__player.set_time(pos * 1000)

    def get_state(self):
        vlc_state = self.__player.get_state()
        if vlc_state == _vlc.State.Playing:
            return PLAYER_PLAY
        elif vlc_state == _vlc.State.Paused:
            return PLAYER_PAUSE
        return PLAYER_STOP

    def is_supported_uri(self, uri_type):
        # TODO : find a way to know list of available module to implement this
        return True

    def _change_file(self, new_file):
        def needs_video(m):
            return self.video_enable and m is not None and m.has_video()

        self.__player.stop()
        try:
            self.__metadata_task.stop()
        except:
            pass
        if needs_video(self._playing_media) and not needs_video(new_file):
            # destroy window since it does not useful anymore
            self.__destroy_x_window()
        self._playing_media = new_file
        # replaygain reset
        self.set_volume(self.get_volume(), sig=False)
        self.play()

        self.dispatch_signame('player.status')
        self.dispatch_signame('player.current')

    def _set_volume(self, vol, sig=True):
        self.__player.audio_set_volume(int(vol))

    def _player_set_zoom(self, zoom):
        if zoom == 100:
            value = 0
        else:
            value = float(zoom) / float(100)
        self.__player.video_set_scale(value)

    def _player_set_aspectratio(self, aspect_ratio):
        if aspect_ratio == 'auto':
            aspect_ratio = None
        self.__player.video_set_aspect_ratio(aspect_ratio)

    def _player_set_avoffset(self, offset):
        if self.__player.audio_set_delay(offset * 1000) == -1:  # error
            raise PlayerError(_("Unable to update audio/video delay"))

    def _player_set_suboffset(self, offset):
        if self.__player.video_set_spu_delay(offset * 1000) == -1:  # error
            raise PlayerError(_("Unable to update spu delay"))

    def _player_set_alang(self, lang_idx):
        self.__player.audio_set_track(lang_idx)

    def _player_set_slang(self, lang_idx):
        self.__player.video_set_spu(lang_idx)

    def _player_get_alang(self):
        return self.__player.audio_get_track()

    def _player_get_slang(self):
        return self.__player.video_get_spu()

    def _osd_set(self, text):
        if self.__osd_call_id is not None:
            self.__osd_call_id.cancel()
        self.__player.video_set_marquee_string(_vlc.VideoMarqueeOption.Text,
                                               text)
        self.__player.video_set_marquee_int(_vlc.VideoMarqueeOption.Size,
                                            self._video_options['osd_size'])
        self.__player.video_set_marquee_int(_vlc.VideoMarqueeOption.Enable, 1)
        self.__osd_call_id = reactor.callLater(2, self._osd_hide)

    def _osd_hide(self):
        self.__player.video_set_marquee_int(_vlc.VideoMarqueeOption.Enable, 0)
        self.__osd_call_id = None

    def __on_eof(self, instance):
        def eof_cb():
            self._playing_media.played()
            self._playing_media['last_position'] = 0
            self._change_file(self._source.next(explicit=False))
        reactor.callFromThread(eof_cb)

    def __check_metadata(self):
        m = self.__player.get_media()
        if m is not None:
            desc = m.get_meta(_vlc.Meta.NowPlaying)
            # TODO update title if necessary
            self.dispatch_signame('player.current')

    def __prepare_x_window(self):
        d_list = [self._video_options["display"]]
        if "DISPLAY" in os.environ:
            d_list.append(os.environ["DISPLAY"])
        display_ids = iter(d_list)
        try:
            while self.__display is None:
                display_id = display_ids.next()
                try:
                    self.__display = x11.X11Display(id=display_id)
                except (x11.X11Error, KeyError):
                    self.__display = None
        except StopIteration:
            raise PlayerError(_("Unable to open video display"))

        self.__display.set_dpms(False)
        if self._video_options["fullscreen"]:
            self.__window = x11.X11Window(self.__display,
                                          fullscreen=True)
        else:
            self.__window = x11.X11Window(self.__display,
                                          width=400, height=200)

    def __destroy_x_window(self):
        if self.__window is not None:
            self.__player.set_xwindow(-1)
            self.__window.close()
            self.__display.destroy()
            self.__window = None
            self.__display = None
