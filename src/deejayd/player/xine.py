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

from os import path
from ctypes import *
from twisted.internet import reactor
from deejayd.player import PlayerError
from deejayd.player._base import *
from deejayd.player._xine import *
from deejayd.player.display import x11
from deejayd.ui import log


class XinePlayer(UnknownPlayer):
    name = "xine"
    supported_extensions = None
    plugins = None

    def __init__(self,db,config):
        UnknownPlayer.__init__(self,db,config)
        self.__xine_options = {
            "video": self.config.get("xine", "video_output"),
            "display" : self.config.get("xine", "video_display"),
            "osd_support" : self.config.getboolean("xine", "osd_support"),
            "osd_font_size" : self.config.getint("xine", "osd_font_size"),
            }

        # init main instance
        self.__xine = xine_new()
        if not self.__xine:
            raise PlayerError(_("Unable to init a xine instance"))
        xine_config_load(self.__xine, xine_get_homedir() + "/.xine/config")
        xine_init(self.__xine)

        # init vars
        self.__supports_gapless = xine_check_version(1, 1, 1) == 1
        self.__volume = 100
        self.__audio_port = None
        self.__video_port = None
        self.__stream = None
        self.__event_queue = None
        self.__mine_stream = None
        self.__osd = None

    def init_video_support(self):
        UnknownPlayer.init_video_support(self)
        # init display
        try: self.__display = x11.X11Display(self.__xine_options,\
                                             self._fullscreen)
        except x11.X11Error, err:
            log.err(str(err))
            raise PlayerError(str(err))
        # init instance to get video and dvd informations
        self.__mine_stream = xine_stream_new(self.__xine, None, None)

    def start_play(self):
        if not self._media_file: return

        # format correctly the uri
        uri = self._media_file["uri"]
        # For dvd chapter
        if "chapter" in self._media_file.keys() and \
                    self._media_file["chapter"] != -1:
            uri += ".%d" % self._media_file["chapter"]
        # load external subtitle
        if "external_subtitle" in self._media_file and \
                self._media_file["external_subtitle"].startswith("file://"):
            uri += "#subtitle:%s" % self._media_file["external_subtitle"]
            self._media_file["subtitle"] = [{"lang": "none", "ix": -2},\
                                            {"lang": "auto", "ix": -1},\
                                            {"lang": "external", "ix":0}]

        if not self.__stream:
            has_video = self._media_file["type"] == "video"
            self._create_stream(has_video)
        if not xine_open(self.__stream, uri) or \
           not xine_play(self.__stream, 0, 0):
            self._destroy_stream()
            msg = _("Unable to play file %s") % uri
            log.err(msg)
            raise PlayerError(msg)
        isvideo = self._media_file["type"] == "video"
        if self.__video_port:
            self.__display.show(isvideo)

        # init video information
        if self._media_file["type"] == "video":
            self._media_file["av_offset"] = 0
            if "audio" in self._media_file:
                self._media_file["audio_idx"] = \
                    self.__do_get_property(XINE_PARAM_AUDIO_CHANNEL_LOGICAL)
            if "subtitle" in self._media_file:
                self._media_file["sub_offset"] = 0
                self._media_file["subtitle_idx"] = \
                    self.__do_get_property(XINE_PARAM_SPU_CHANNEL)

    def _change_file(self, new_file, gapless = False):
        sig = self.get_state() == PLAYER_STOP and True or False
        if self._media_file == None\
                or new_file == None\
                or self._media_file["type"] != new_file["type"]:
            self._destroy_stream()
            gapless = False

        self._media_file = new_file
        if gapless and self.__supports_gapless:
            xine_set_param(self.__stream, XINE_PARAM_GAPLESS_SWITCH, 1)
        self.start_play()
        if gapless and self.__supports_gapless:
            xine_set_param(self.__stream, XINE_PARAM_GAPLESS_SWITCH, 0)

        # replaygain reset
        self.set_volume(self.__volume, sig=False)

        if sig: self.dispatch_signame('player.status')
        self.dispatch_signame('player.current')

    def pause(self):
        if self.get_state() == PLAYER_PAUSE:
            self.__do_set_property(XINE_PARAM_SPEED, XINE_SPEED_NORMAL)
        elif self.get_state() == PLAYER_PLAY:
            self.__do_set_property(XINE_PARAM_SPEED, XINE_SPEED_PAUSE)
        else: return
        self.dispatch_signame('player.status')

    def stop(self):
        if self.get_state() != PLAYER_STOP:
            self._source.queue_reset()
            self._change_file(None)
            self.dispatch_signame('player.status')

    def set_avoffset(self, offset):
        if self._media_file["type"] == "video":
            self.__do_set_property(XINE_PARAM_AV_OFFSET, offset * 90)
            self._media_file["av_offset"] = offset
            self._osd_set("Audio/Video offset: %d ms" % offset)

    def set_suboffset(self, offset):
        if "subtitle" in self._media_file.keys():
            self.__do_set_property(XINE_PARAM_SPU_OFFSET, offset * 90)
            self._media_file["sub_offset"] = offset
            self._osd_set("Subtitle offset: %d ms" % offset)

    def _player_set_alang(self,lang_idx):
        self.__do_set_property(XINE_PARAM_AUDIO_CHANNEL_LOGICAL, lang_idx)

    def _player_set_slang(self,lang_idx):
        self.__do_set_property(XINE_PARAM_SPU_CHANNEL, lang_idx)

    def _player_get_alang(self):
        return self.__do_get_property(XINE_PARAM_AUDIO_CHANNEL_LOGICAL)

    def _player_get_slang(self):
        return self.__do_get_property(XINE_PARAM_SPU_CHANNEL)

    def get_volume(self):
        return self.__volume

    def set_volume(self, vol, sig = True):
        self.__volume = min(100, int(vol))
        # replaygain support
        vol = self.__volume
        if self._replaygain and self._media_file is not None:
            try: scale = self._media_file.replay_gain()
            except AttributeError: pass # replaygain not supported
            else:
                vol = max(0.0, min(4.0, float(vol)/100.0 * scale))
                vol = min(100, int(vol * 100))
        self.__do_set_property(XINE_PARAM_AUDIO_VOLUME, vol)
        if sig:
            self._osd_set("Volume: %s" % int(vol))
            self.dispatch_signame('player.status')

    def get_position(self):
        if not self.__stream: return 0
        # Workaround for problems when you seek too quickly
        i = 0
        while i < 4:
            pos_s, pos_t, length = xine_get_pos_length(self.__stream)
            if int(pos_t) > 0:  break
            xine_usec_sleep(100000)
            i += 1

        return int(pos_t / 1000)

    def set_position(self,pos):
        pos = int(pos * 1000)
        state = self.get_state()
        if state == PLAYER_PAUSE:
            xine_play(self.__stream, 0, pos)
            xine_set_param(self.__stream, XINE_PARAM_SPEED, XINE_SPEED_PAUSE)
        elif state == PLAYER_PLAY:
            xine_play(self.__stream, 0, pos)
        self.dispatch_signame('player.status')

    def get_state(self):
        if not self.__stream: return PLAYER_STOP

        status = xine_get_status(self.__stream)
        if status == XINE_STATUS_PLAY:
            if self.__do_get_property(XINE_PARAM_SPEED) == XINE_SPEED_NORMAL:
                return PLAYER_PLAY
            return PLAYER_PAUSE
        return PLAYER_STOP

    def is_supported_uri(self,uri_type):
        if self.plugins == None:
            self.plugins = []
            for plugin in xine_list_input_plugins(self.__xine):
                if not plugin:
                    break
                self.plugins.append(plugin.lower())

        if uri_type == "dvd":
            # test lsdvd  installation
            if not self._is_lsdvd_exists(): return False
        return uri_type in self.plugins

    def is_supported_format(self,format):
        if self.supported_extensions == None:
            extensions = xine_get_file_extensions(self.__xine)
            self.supported_extensions = extensions.split()
        return format.strip(".") in self.supported_extensions

    def get_video_file_info(self,file):
        if not xine_open(self.__mine_stream, file):
            raise PlayerError

        rs = {}
        rs["videowidth"] = xine_get_stream_info(self.__mine_stream,\
            XINE_STREAM_INFO_VIDEO_WIDTH)
        rs["videoheight"] = xine_get_stream_info(self.__mine_stream,\
            XINE_STREAM_INFO_VIDEO_HEIGHT)
        pos_s, pos_t, length = xine_get_pos_length(self.__mine_stream)
        rs["length"] = length / 1000
        # close stream
        xine_stop(self.__mine_stream)
        xine_close(self.__mine_stream)

        return rs

    def get_dvd_info(self):
        dvd_info = self._get_dvd_info()
        ix = 0
        for track in dvd_info['track']:
            if not xine_open(self.__mine_stream, "dvd://%d"%track['ix']):
                raise PlayerError
            # get audio channels info
            channels_number = len(track['audio'])
            audio_channels = [{"lang":"none","ix":-2},{"lang":"auto","ix":-1}]
            for ch in range(0,channels_number):
                lang = xine_get_audio_lang(self.__mine_stream,ch)
                audio_channels.append({'ix':ch, "lang":lang.encode("utf-8")})
            dvd_info['track'][ix]["audio"] = audio_channels

            # get subtitles channels info
            channels_number = len(track['subp'])
            sub_channels = [{"lang":"none","ix":-2},{"lang":"auto","ix":-1}]
            for ch in range(0,channels_number):
                lang = xine_get_spu_lang(self.__mine_stream,ch)
                sub_channels.append({'ix':ch, "lang":lang.encode("utf-8")})
            dvd_info['track'][ix]["subp"] = sub_channels

            ix += 1

        return dvd_info

    def close(self):
        UnknownPlayer.close(self)
        if self.__mine_stream:
            xine_close(self.__mine_stream)
            xine_dispose(self.__mine_stream)
        xine_exit(self.__xine)

    #
    # Specific xine functions
    #
    def __do_set_property(self, property, v):
        if not self.__stream: return
        xine_set_param(self.__stream, property, v)

    def __do_get_property(self, property):
        if not self.__stream: return -1
        return xine_get_param(self.__stream, property)

    def _create_stream(self, has_video = True):
        if self.__stream != None:
            self._destroy_stream()

        # open audio driver
        driver_name = self.config.get("xine", "audio_output")
        self.__audio_port = xine_open_audio_driver(self.__xine,driver_name,None)
        if not self.__audio_port:
            raise PlayerError(_("Unable to open audio driver"))

        # open video driver
        if has_video and self._video_support\
                 and self.__xine_options["video"] != "none":
            try: self.__display.create()
            except x11.X11Error, err:
                raise PlayerError(str(err))

            # Those callbacks are required to be kept in this list in order to
            # be safe from the garbage collector.
            self.__x11_callbacks = [
                xine_dest_size_cb(self._dest_size_cb),
                xine_frame_output_cb(self._frame_output_cb)
                ]

            x11_infos = self.__display.get_infos()
            vis = x11_visual_t()
            vis.display = x11_infos["dsp"]
            vis.screen = x11_infos["screen"]
            vis.d = x11_infos["window"]
            vis.user_data = None
            vis.dest_size_cb = cast(self.__x11_callbacks[0], c_void_p)
            vis.frame_output_cb = cast(self.__x11_callbacks[1],c_void_p)
            vis.lock_display = None
            vis.unlock_display = None

            self.__video_port = xine_open_video_driver(self.__xine,\
                self.__xine_options["video"], XINE_VISUAL_TYPE_X11,\
                cast(byref(vis), c_void_p))
            if not self.__video_port:
                msg = _("Unable to open video driver")
                log.err(msg)
                raise PlayerError(msg)

        # create stream
        self.__stream = xine_stream_new(self.__xine, self.__audio_port,\
                            self.__video_port)
        if not self.__video_port:
            xine_set_param(self.__stream, XINE_PARAM_IGNORE_VIDEO, 1)
            xine_set_param(self.__stream, XINE_PARAM_IGNORE_SPU, 1)
        elif self.__xine_options["osd_support"]: # osd qupport
            video_area = self.__display.get_and_lock_video_area()
            self.__osd = xine_osd_new(self.__stream, 0, 0,\
                video_area["width"], video_area["height"])
            xine_osd_set_font(self.__osd, "sans",\
                self.__xine_options["osd_font_size"])
            xine_osd_set_text_palette(self.__osd,\
                XINE_TEXTPALETTE_WHITE_BLACK_TRANSPARENT, XINE_OSD_TEXT1)
            self.__display.release_video_area()
            self.__osd_unscaled = xine_osd_get_capabilities(self.__osd) \
                & XINE_OSD_CAP_UNSCALED

        # gapless support
        if self.__supports_gapless:
            xine_set_param(self.__stream, XINE_PARAM_EARLY_FINISHED_EVENT, 1)

        # add event listener
        if self.__event_queue:
            xine_event_dispose_queue(self.__event_queue)
        self.__event_queue = xine_event_new_queue(self.__stream)
        xine_event_create_listener_thread(self.__event_queue,
            self._event_callback, None)

        # restore volume
        self.__do_set_property(XINE_PARAM_AUDIO_VOLUME, self.__volume)

    def _destroy_stream(self):
        if self.__stream:
            xine_stop(self.__stream)
            xine_close(self.__stream)
            xine_set_param(self.__stream, XINE_PARAM_AUDIO_CLOSE_DEVICE, 1)
            if self.__event_queue:
                xine_event_dispose_queue(self.__event_queue)
                self.__event_queue = None
            # close osd
            if self.__osd:
                xine_osd_clear(self.__osd)
                xine_osd_free(self.__osd)
                self.__osd = None
            xine_dispose(self.__stream)
            self.__stream = None

            xine_close_audio_driver(self.__xine, self.__audio_port)
            self.__audio_port = None

            # close video driver
            if self.__video_port:
                xine_close_video_driver(self.__xine, self.__video_port)
                self.__video_port = None
                self.__display.destroy()
                self.__x11_callbacks = None

    def _osd_set(self, text):
        if not self.__osd: return
        xine_osd_clear(self.__osd)
        xine_osd_draw_text(self.__osd, 0, 0, text, XINE_OSD_TEXT1)
        xine_osd_set_position(self.__osd, 60, 20)
        if self.__osd_unscaled: xine_osd_show_unscaled(self.__osd, 0)
        else: xine_osd_show(self.__osd, 0)
        # hide osd 2 seconds later
        self.__osd_text = text
        reactor.callLater(2, self._osd_hide, text)

    def _osd_hide(self, text):
        if self.__osd and self.__osd_text == text:
            xine_osd_hide(self.__osd, 0)

    #
    # callbacks
    #
    def _eof(self):
        new_file = self._source.next()
        try: self._change_file(new_file, gapless = True)
        except PlayerError:
            pass
        return False

    def _update_metadata(self):
        if not self._media_file or self._media_file["type"] != "webradio":
            return False

        # update webradio song info
        meta = [
            (XINE_META_INFO_TITLE, 'song-title'),
            (XINE_META_INFO_ARTIST, 'song-artist'),
            (XINE_META_INFO_ALBUM, 'song-album'),
        ]
        for info, name in meta:
            text = xine_get_meta_info(self.__stream, info)
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
        event = event.contents
        if event.type == XINE_EVENT_UI_PLAYBACK_FINISHED:
            log.info("Xine event : playback finished")
            reactor.callFromThread(self._eof)
        elif event.type == XINE_EVENT_UI_SET_TITLE:
            log.info("Xine event : set title")
            reactor.callFromThread(self._update_metadata)
        elif event.type == XINE_EVENT_UI_MESSAGE:
            log.info("Xine event : message")
            msg = cast(event.data, POINTER(xine_ui_message_data_t)).contents
            if msg.type != XINE_MSG_NO_ERROR:
                if msg.explanation:
                    message = string_at(addressof(msg) + msg.explanation)
                else:
                    message = _("Xine error %s") % msg.type
                reactor.callFromThread(log.err, message)
        return True

    def _dest_size_cb(self, data, video_width, video_height,\
                      video_pixel_aspect, dest_width, dest_height,\
                      dest_pixel_aspect):
        infos = self.__display.get_and_lock_video_area()
        dest_width[0] = infos["width"]
        dest_height[0] = infos["height"]
        dest_pixel_aspect[0] = c_double(infos["pixel_aspect"])
        self.__display.release_video_area()
        return True

    def _frame_output_cb(self, data, video_width, video_height,\
                      video_pixel_aspect, dest_x, dest_y, dest_width,\
                      dest_height, dest_pixel_aspect, win_x, win_y):
        infos = self.__display.get_and_lock_video_area()
        win_x[0] = 0
        win_y[0] = 0
        dest_x[0] = 0
        dest_y[0] = 0
        dest_width[0] = infos["width"]
        dest_height[0] = infos["height"]
        dest_pixel_aspect[0] = c_double(infos["pixel_aspect"])
        self.__display.release_video_area()
        return True

# vim: ts=4 sw=4 expandtab
