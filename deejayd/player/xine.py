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

from twisted.internet import reactor
from pytyxi import xine

from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from deejayd.player._base import _BasePlayer, PLAYER_PAUSE, \
                                 PLAYER_PLAY, PLAYER_STOP
from deejayd.ui import log


@jsonrpc_module(PlayerModule)
class XinePlayer(_BasePlayer):
    NAME = "xine"
    supported_options = (\
            "audio_lang",
            "sub_lang",
            "av_offset",
            "sub_offset",
            "zoom",
            "aspect_ratio"\
        )
    default_channels = [{"lang": "none", "ix":-2}, {"lang": "auto", "ix":-1}]

    supported_extensions = None
    xine_plugins = None

    def __init__(self, plugin_manager, config):
        # init main instance
        try:
            self.__xine = xine.XinePlayer()
        except xine.XineError:
            raise PlayerError(_("Unable to init a xine instance"))
        self.__supports_gapless = self.__xine.has_gapless()

        super(XinePlayer, self).__init__(plugin_manager, config)
        self.__xine_options = {
            "video": self.config.get("xine", "video_output"),
            "audio": self.config.get("xine", "audio_output"),
            "software_mixer": self.config.getboolean("xine", "software_mixer"),
            }
        self.__video_aspects = {
                "auto": xine.Stream.XINE_VO_ASPECT_AUTO,
                "1:1": xine.Stream.XINE_VO_ASPECT_SQUARE,
                "4:3": xine.Stream.XINE_VO_ASPECT_4_3,
                "16:9": xine.Stream.XINE_VO_ASPECT_ANAMORPHIC,
            }

        # init vars
        self.__window = None
        self.__stream = None
        self.__osd = None

    def play(self):
        super(XinePlayer, self).play()
        if not self._media_file: return

        # format correctly the uri
        uri = self._media_file["uri"].encode("utf-8")
        # For dvd chapter
        if "chapter" in self._media_file.keys() and \
                    self._media_file["chapter"] != -1:
            uri += ".%d" % self._media_file["chapter"]
        # load external subtitle
        if self._has_external_subtitle():
            # external subtitle
            uri += "#subtitle:%s" \
                    % self._media_file["external_subtitle"].encode("utf-8")

        needs_video = self._media_file["type"] == "video"
        stream_should_change = True
        if self.__stream:
            stream_should_change = (needs_video and\
                                    not self.__stream.has_video())\
                                or (not needs_video and
                                    self.__stream.has_video())
        if stream_should_change:
            self._create_stream(needs_video)

        def open_uri(uri):
            try:
                self.__stream.open(uri)
                self.__stream.play(0, 0)
            except xine.XineError:
                msg = _("Unable to play file %s") % uri
                log.err(msg)
                raise PlayerError(msg)

        if self._media_file["type"] == "webradio":
            while True:
                try: open_uri(self._media_file["uri"])
                except PlayerError, ex:
                    if self._media_file["url-index"] < \
                                            len(self._media_file["urls"]) - 1:
                        self._media_file["url-index"] += 1
                        self._media_file["uri"] = \
                                self._media_file["urls"]\
                                [self._media_file["url-index"]].encode("utf-8")
                    else:
                        raise ex
                else:
                    break
        else:
            try: open_uri(uri)
            except PlayerError, ex:
                self._destroy_stream()
                raise ex

        if self.__window:
            self.__window.show(needs_video)
        self._init_video_information()

    def _change_file(self, new_file, gapless=False):
        sig = self.get_state() == PLAYER_STOP and True or False
        if self._media_file == None\
                or new_file == None\
                or self._media_file["type"] != new_file["type"]:
            self._destroy_stream()
            gapless = False

        self._media_file = new_file
        if gapless and self.__supports_gapless:
            self.__stream.set_param(xine.Stream.XINE_PARAM_GAPLESS_SWITCH, 1)
        self.play()
        if gapless and self.__supports_gapless:
            self.__stream.set_param(xine.Stream.XINE_PARAM_GAPLESS_SWITCH, 0)

        # replaygain reset
        self.set_volume(self.get_volume(), sig=False)

        if sig: self.dispatch_signame('player.status')
        self.dispatch_signame('player.current')

    def pause(self):
        if self.get_state() == PLAYER_PAUSE:
            self.__stream.set_param(xine.Stream.XINE_PARAM_SPEED,
                                    xine.Stream.XINE_SPEED_NORMAL)
        elif self.get_state() == PLAYER_PLAY:
            self.__stream.set_param(xine.Stream.XINE_PARAM_SPEED,
                                    xine.Stream.XINE_SPEED_PAUSE)
        else: return
        self.dispatch_signame('player.status')

    def set_zoom(self, zoom):
        if zoom > xine.Stream.XINE_VO_ZOOM_MAX\
        or zoom < xine.Stream.XINE_VO_ZOOM_MIN:
            raise PlayerError(_("Zoom value not accepted"))
        self.__stream.set_param(xine.Stream.XINE_PARAM_VO_ZOOM_X, zoom)
        self.__stream.set_param(xine.Stream.XINE_PARAM_VO_ZOOM_Y, zoom)
        self._media_file["zoom"] = zoom
        self.osd(_("Zoom: %d percent") % zoom)

    def _player_set_aspectratio(self, aspect_ratio):
        asp = self.__video_aspects[aspect_ratio]
        if self.__stream.has_video():
            self.__stream.set_param(xine.Stream.XINE_PARAM_VO_ASPECT_RATIO, asp)

    def _player_set_avoffset(self, offset):
        self.__stream.set_param(xine.Stream.XINE_PARAM_AV_OFFSET, offset * 90)

    def _player_set_suboffset(self, offset):
        self.__stream.set_param(xine.Stream.XINE_PARAM_SPU_OFFSET, offset * 90)

    def _player_set_alang(self, lang_idx):
        self.__stream.set_param(xine.Stream.XINE_PARAM_AUDIO_CHANNEL_LOGICAL,
                                lang_idx)

    def _player_set_slang(self, lang_idx):
        self.__stream.set_param(xine.Stream.XINE_PARAM_SPU_CHANNEL, lang_idx)

    def _player_get_alang(self):
        return self.__stream.get_param(xine.Stream.\
                XINE_PARAM_AUDIO_CHANNEL_LOGICAL)

    def _player_get_slang(self):
        return self.__stream.get_param(xine.Stream.XINE_PARAM_SPU_CHANNEL)

    def _set_volume(self, vol, sig=True):
        if self.__stream: self.__stream.set_volume(vol)

    def get_position(self):
        if not self.__stream: return 0
        return self.__stream.get_pos()

    def _set_position(self, pos):
        pos = int(pos * 1000)
        state = self.get_state()
        if state == PLAYER_PAUSE:
            self.__stream.play(0, pos)
            self.__stream.set_param(xine.Stream.XINE_PARAM_SPEED,
                                    xine.Stream.XINE_SPEED_PAUSE)
        elif state == PLAYER_PLAY:
            self.__stream.play(0, pos)

    def get_state(self):
        if not self.__stream: return PLAYER_STOP

        status = self.__stream.get_status()
        if status == xine.Stream.XINE_STATUS_PLAY:
            if self.__stream.get_param(xine.Stream.XINE_PARAM_SPEED)\
               == xine.Stream.XINE_SPEED_NORMAL:
                return PLAYER_PLAY
            return PLAYER_PAUSE
        return PLAYER_STOP

    def is_supported_uri(self, uri_type):
        if self.xine_plugins == None:
            self.xine_plugins = self.__xine.list_input_plugins()

        return uri_type in self.xine_plugins

    def is_supported_format(self, format):
        if self.supported_extensions == None:
            self.supported_extensions = self.__xine.get_supported_extensions()
        return format.strip(".") in self.supported_extensions

    def close(self):
        super(XinePlayer, self).close()
        self.__xine.destroy()

    def _create_stream(self, has_video=True):
        if self.__stream != None:
            self._destroy_stream()

        # open audio driver
        driver_name = self.__xine_options["audio"]
        try:
            audio_port = xine.AudioDriver(self.__xine, driver_name)
        except xine.XineError:
            raise PlayerError(_("Unable to open audio driver"))

        # open video driver
        if has_video and self.__xine_options["video"] != "none":
            try:
                video_port = xine.VideoDriver(self.__xine,
                                          self.__xine_options["video"],
                                          self._video_options["display"],
                                          self._video_options["fullscreen"])
            except xine.XineError:
                msg = _("Unable to open video driver")
                log.err(msg)
                raise PlayerError(msg)
            else:
                self.__window = video_port.window
        else:
            video_port = None

        # create stream
        self.__stream = self.__xine.stream_new(audio_port, video_port)
        self.__stream.set_software_mixer(self.__xine_options["software_mixer"])

        if video_port and self._video_options["osd"]:
            self.__osd = self.__stream.osd_new(self._video_options["osd_size"])

        # add event listener
        self.__stream.add_event_callback(self._event_callback)

        # restore volume
        self.__stream.set_volume(self.get_volume())

    def _destroy_stream(self):
        if self.__stream:
            self.__stream.destroy()
            self.__stream = None
            self.__window = None
            self.__osd = None

    def _osd_set(self, text):
        if not self.__osd: return
        self.__osd.clear()
        self.__osd.draw_text(60, 20, text.encode("utf-8"))
        self.__osd.show()

        reactor.callLater(2, self._osd_hide, text)

    def _osd_hide(self, text):
        if self.__osd:
            self.__osd.hide(text)

    #
    # callbacks
    #
    def _eof(self):
        if self._media_file:
            if self._media_file["type"] == "webradio":
                # an error happened, try the next url
                if self._media_file["url-index"] \
                        < len(self._media_file["urls"]) - 1:
                    self._media_file["url-index"] += 1
                    self._media_file["uri"] = \
                            self._media_file["urls"]\
                                [self._media_file["url-index"]].encode("utf-8")
                    try:
                        self.play()
                    except PlayerError:
                        # This stream is really dead, all its mirrors
                        pass
                return False
            else:
                try: self._media_file.played()
                except AttributeError: pass
                for plugin in self.plugins:
                    plugin.on_media_played(self._media_file)
        new_file = self._source.next(explicit=False)
        try: self._change_file(new_file, gapless=True)
        except PlayerError:
            pass
        return False

    def _update_metadata(self):
        if not self._media_file or self._media_file["type"] != "webradio":
            return False

        # update webradio song info
        meta = [
            (xine.Stream.XINE_META_INFO_TITLE, 'song-title'),
            (xine.Stream.XINE_META_INFO_ARTIST, 'song-artist'),
            (xine.Stream.XINE_META_INFO_ALBUM, 'song-album'),
        ]
        for info, name in meta:
            text = self.__stream.get_meta_info(info)
            if not text:
                continue
            text = text.decode('UTF-8', 'replace')
            if name not in self._media_file.keys() or\
                           self._media_file[name] != text:
                self._media_file[name] = text
        self.dispatch_signame('player.current')
        return False

    # this callback is not called in the main reactor thread
    # so we have to use callFromThread function instead of callLater
    # see |http://twistedmatrix.com/documents/current/api/
    #     |twisted.internet.interfaces.IReactorThreads.callFromThread.html
    def _event_callback(self, user_data, event):
        if event.type == xine.Event.XINE_EVENT_UI_PLAYBACK_FINISHED:
            log.info("Xine event : playback finished")
            reactor.callFromThread(self._eof)
        elif event.type == xine.Event.XINE_EVENT_UI_SET_TITLE:
            log.info("Xine event : set title")
            reactor.callFromThread(self._update_metadata)
        elif event.type == xine.Event.XINE_EVENT_UI_MESSAGE:
            log.info("Xine event : message")
            try:
                message = event.message()
            except xine.XineError, errornum:
                message = _("Xine error %s") % errornum
            if message is not None:
                reactor.callFromThread(log.err, message)
        return True

# vim: ts=4 sw=4 expandtab