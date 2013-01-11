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

import threading, os
from twisted.internet import reactor
from deejayd.player import _vlc
from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from pytyx11 import x11
from deejayd.player._base import _BasePlayer, PLAYER_PAUSE,\
                                 PLAYER_PLAY, PLAYER_STOP
from deejayd.ui import log


@jsonrpc_module(PlayerModule)
class VlcPlayer(_BasePlayer):
    class PlayingEventHandler(object):
        
        def __init__(self, evt_mg):
            self.__lock = threading.Lock()
            self.__event = threading.Event()
            self.__playing = False
            evt_mg.event_attach(_vlc.EventType.MediaPlayerPlaying, self.on_playing_event)
            evt_mg.event_attach(_vlc.EventType.MediaPlayerEncounteredError, self.on_error_event)
        
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
        
        def wait(self, timeout = None):
            self.__event.wait(timeout)
        
        def release(self, evt_mg):
            evt_mg.event_detach(_vlc.EventType.MediaPlayerPlaying)
            evt_mg.event_detach(_vlc.EventType.MediaPlayerEncounteredError)
    
    NAME = "vlc"
    supported_options = (\
            "audio_lang",
            "av_offset",
            "sub_offset",
            "sub_lang",
       )

    def __init__(self, db, plugin_manager, config):
        # test version, this backend only works with version 2.0.X of libvlc
        version = _vlc.libvlc_get_version()
        if not version.startswith("2.0."):
            raise PlayerError(_("Vlc backend only works with version 2.0.X of libvlc"))
        
        # init main instance
        try: self.__vlc = _vlc.Instance()
        except _vlc.VLCException, ex:
            raise PlayerError(_("Unable to init vlc player: %s") % ex)
        super(VlcPlayer, self).__init__(db, plugin_manager, config)

        # init vlc player and event manager
        self.__player = self.__vlc.media_player_new()
        self.__evt_manager = self.__player.event_manager()
        self.__evt_manager.event_attach(_vlc.EventType.MediaPlayerEndReached, self.__on_eof)
        # set audio output
        wanted_aout = config.get("vlc", "audio_output")
        if wanted_aout != "auto":
            audio_outputs = self.__vlc.audio_output_enumerate_devices()
            find = False
            for aout in audio_outputs:
                if aout['name'] == wanted_aout:
                    self.__player.audio_output_set(aout['name'])
                    find = True
                    break
            if not find:
                raise PlayerError(_("VLC does not support audio output %s") \
                        % wanted_aout)

        # other varaibles
        self.__osd_call_id = None
        self.__display = None
        self.__window = None
        self.__playing_handler = None

    def play(self):
        super(VlcPlayer, self).play()
        if self._media_file is None: return

        # format correctly the uri
        uri = self._media_file["uri"].encode("utf-8")
        media = self.__vlc.media_new(unicode(uri))
        self.__player.set_media(media)
        needs_video = self._media_file["type"] == "video"
        if needs_video and self.__window is None:
            self.__prepare_x_window()
            self.__player.set_xwindow(self.__window.window_p())

        self.__playing_handler = VlcPlayer.PlayingEventHandler(self.__evt_manager)
        self.__player.play()
        self.__playing_handler.wait(3)
        playing = self.__playing_handler.get_playing()
        self.__playing_handler.release(self.__evt_manager)
        if not playing:
            raise PlayerError(_("unable to play file %s") \
                              % self._media_file['title'])
        if needs_video: self.__init_video_information()

    def pause(self):
        self.__player.pause()
        self.dispatch_signame('player.status')

    def stop(self):
        if self.get_state() != PLAYER_STOP:
            self._source.queue_reset()
            self._change_file(None)
            self.dispatch_signame('player.status')

    def get_position(self):
        if self.get_state() != PLAYER_STOP:
            return int(self.__player.get_position() *\
                    float(self.__media_length()))
        return 0

    def _set_position(self,pos):
        if self.get_state() != PLAYER_STOP and self.__player.is_seekable():
            self.__player.set_position(pos / float(self.__media_length()))

    def get_state(self):
        vlc_state = self.__player.get_state()
        if vlc_state == _vlc.State.Playing:
            return PLAYER_PLAY
        elif vlc_state == _vlc.State.Paused:
            return PLAYER_PAUSE
        return PLAYER_STOP

    def is_supported_uri(self,uri_type):
        # TODO : find a way to know list of available module to implement this
        return True

    def is_supported_format(self,format):
        # TODO : find a way to know list of available module to implement this
        return True

    def set_zoom(self, zoom):
        if zoom == 100:
            value = 0
        else:
            value = float(zoom) / float(100)
        self.__player.video_set_scale(value)
        self._media_file["zoom"] = zoom

    def _change_file(self,new_file):
        def needs_video(media):
            if media is not None and media['type'] == 'video':
                return True
            return False

        self.__player.stop()
        if needs_video(self._media_file) and not needs_video(new_file):
            # destroy window since it does not useful anymore
            self.__destroy_x_window()
        self._media_file = new_file
        self.play()

        if self._media_file is not None:
            self.dispatch_signame('player.status')

    def _set_volume(self, vol, sig=True):
        self.__player.audio_set_volume(vol)

    def _player_set_aspectratio(self, aspect_ratio):
        # NOT SUPPORTED
        pass

    def _player_set_avoffset(self, offset):
        if self.__player.audio_set_delay(offset * 1000) == -1: # error
            raise PlayerError(_("Unable to update audio/video delay"))

    def _player_set_suboffset(self, offset):
        if self.__player.video_set_spu_delay(offset * 1000) == -1: # error
            raise PlayerError(_("Unable to update spu delay"))

    def _player_set_alang(self,lang_idx):
        self.__player.audio_set_track(lang_idx)

    def _player_set_slang(self,lang_idx):
        self.__player.video_set_spu(lang_idx)

    def _player_get_alang(self):
        return self.__player.audio_get_track()

    def _player_get_slang(self):
        return self.__player.video_get_spu()

    def _osd_set(self, text):
        if self.__osd_call_id is not None:
            self.__osd_call_id.cancel()
        self.__player.video_set_marquee_string(_vlc.VideoMarqueeOption.Text, text)
        self.__player.video_set_marquee_int(_vlc.VideoMarqueeOption.Size, 
                                            self._video_options['osd_size'])
        self.__player.video_set_marquee_int(_vlc.VideoMarqueeOption.Enable, 1)
        self.__osd_call_id = reactor.callLater(2, self._osd_hide)

    def _osd_hide(self):
        self.__player.video_set_marquee_int(_vlc.VideoMarqueeOption.Enable, 0)
        self.__osd_call_id = None

    def __on_eof(self, instance):
        def eof_cb():
            try: self._media_file.played()
            except AttributeError:
                pass
            else:
                for plugin in self.plugins:
                    plugin.on_media_played(self._media_file)

            self._change_file(self._source.next(explicit = False))
        reactor.callFromThread(eof_cb)

    def __media_length(self):
        if self._media_file is not None and "length" in self._media_file:
            return int(self._media_file['length'])
        return 0

    def __prepare_x_window(self):
        # open display
        def open_display(d):
            try: self.__display = x11.X11Display(id=d)
            except x11.X11Error:
                raise PlayerError(_("Unable to open video display"))

        try: open_display(self._video_options["display"])
        except PlayerError, ex: # try to get display with env var
            try: open_display(os.environ["DISPLAY"])
            except (PlayerError,KeyError):
                raise ex

        if self._video_options["fullscreen"]:
            self.__window = x11.X11Window(self.__display,\
                    fullscreen = True)
        else:
            self.__window = x11.X11Window(self.__display,\
                    width=400, height=200)
            
    def __destroy_x_window(self):
        if self.__window is not None:
            self.__player.set_xwindow(-1)
            self.__window.close()
            self.__display.destroy()
            self.__window = None
            self.__display = None
                
    def __init_video_information(self):
        if self._current_is_video():
            # subtitles
            sub_channels = [{"lang": "none", "ix": 0}]
            if "subtitle_channels" in self._media_file.keys():
                for i in range(int(self._media_file["subtitle_channels"])):
                    sub_channels.append(\
                        {"lang": _("Sub channel %d") % (i+1,), "ix": i+1})
            if self._has_external_subtitle():
                sub_channels.append({"lang": "external", \
                                     "ix": len(sub_channels)})
            if len(sub_channels) > 1:
                self._media_file['subtitle'] = sub_channels
                self._media_file["sub_offset"] = 0
                self._media_file["subtitle_idx"] = self._player_get_slang()
                
            # audio channels
            audio_channels = [{"lang": "none", "ix": -1}]
            if "audio_channels" in self._media_file.keys():
                for i in range(int(self._media_file["audio_channels"])):
                    audio_channels.append(\
                            {"lang": _("Audio channel %d") % (i+1,), "ix": i+1})
            if len(audio_channels) > 0:        
                self._media_file["audio"] = audio_channels
                self._media_file["av_offset"] = 0
                self._media_file["audio_idx"] = self._player_get_alang()

# vim: ts=4 sw=4 expandtab
