# xine.py

import time
from os import path
from ctypes import *
from twisted.internet import threads
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
            "fullscreen": self.config.getboolean("xine", "fullscreen"),
            "subtitle": self.config.getint("xine", "subtitle_size"),
            }

        # init main instance
        self.__xine = xine_new()
        if not self.__xine:
            log.err("Unable to init a xine instance")
            raise PlayerError("Unable to open audio driver")
        xine_config_load(self.__xine, xine_get_homedir() + "/.xine/config")
        xine_init(self.__xine)

        # open audio driver
        driver_name = self.config.get("xine", "audio_output")
        self.__audio_port = xine_open_audio_driver(self.__xine,driver_name,None)
        if not self.__audio_port:
            log.err("Unable to open audio driver")
            raise PlayerError("Unable to open audio driver")

        # init vars
        self.__volume = 0
        self.__video_port = None
        self.__stream = None
        self.__event_queue = None
        self.__mine_xine = None

    def init_video_support(self):
        UnknownPlayer.init_video_support(self)
        # init display
        try: self.__display = x11.X11Display(self.__xine_options)
        except x11.X11Error, err:
            log.err(str(err))
            raise PlayerError(str(err))
        # init instance to get video informations
        self.__mine_xine = xine_new()
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

        isvideo = self._media_file["type"] == "video"
        if not self.__stream:
            self._create_stream(isvideo)
        if isvideo: self.__display.show()

        if not xine_open(self.__stream, uri) or \
           not xine_play(self.__stream, 0, 0):
            msg = "Unable to play files %s" % uri
            log.err(msg)
            raise PlayerError(msg)
        # if video get current audio/subtitle channel
        if self._media_file["type"] == "video":
            if "audio" in self._media_file:
                self._media_file["audio_idx"] = \
                    self.__do_get_property(XINE_PARAM_AUDIO_CHANNEL_LOGICAL)
            if "subtitle" in self._media_file:
                self._media_file["subtitle_idx"] = \
                    self.__do_get_property(XINE_PARAM_SPU_CHANNEL)

    def _change_file(self,new_file):
        if self._media_file == None or new_file == None:
            detach = True
        elif self._media_file["type"] != new_file["type"]:
            detach = True
        else: detach = False

        self.stop(detach)
        self._media_file = new_file
        self.start_play()

    def pause(self):
        if self.get_state() == PLAYER_PAUSE:
            self.__do_set_property(XINE_PARAM_SPEED, XINE_SPEED_NORMAL)
        elif self.get_state() == PLAYER_PLAY:
            self.__do_set_property(XINE_PARAM_SPEED, XINE_SPEED_PAUSE)

    def stop(self, detach = True):
        self._media_file = None
        # FIXME : try to remove this one day ...
        self._source.queue_reset()

        if not self.__stream: return
        xine_stop(self.__stream)
        if detach: self._destroy_stream()

    def _player_set_alang(self,lang_idx):
        self.__do_set_property(XINE_PARAM_AUDIO_CHANNEL_LOGICAL, lang_idx)

    def _player_set_slang(self,lang_idx):
        self.__do_set_property(XINE_PARAM_SPU_CHANNEL, lang_idx)

    def _player_get_alang(self):
        return self.__do_get_property(XINE_PARAM_AUDIO_CHANNEL_LOGICAL)

    def _player_get_slang(self):
        return self.__do_get_property(XINE_PARAM_SPU_CHANNEL)

    def set_fullscreen(self,val): pass

    def get_volume(self):
        rs = self.__do_get_property(XINE_PARAM_AUDIO_VOLUME)
        if rs != -1:
            return rs
        return self.__volume

    def set_volume(self,vol):
        self.__volume = min(100, vol)
        self.__do_set_property(XINE_PARAM_AUDIO_VOLUME, self.__volume)

    def get_position(self):
        if not self.__stream: return 0
        pos_stream, pos_time, length_time = xine_get_pos_length(self.__stream)
        return int(pos_time / 1000)

    def set_position(self,pos):
        pos = int(pos * 1000)
        state = self.get_state()
        if state == PLAYER_PAUSE:
            xine_play(self.__stream, 0, pos)
            xine_set_param(self.__stream, XINE_PARAM_SPEED, XINE_SPEED_PAUSE)
        elif state == PLAYER_PLAY:
            xine_play(self.__stream, 0, pos)
        time.sleep(0.2)

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
        if self.__mine_xine:
            xine_close(self.__mine_stream)
            xine_dispose(self.__mine_stream)
            xine_exit(self.__mine_xine)
        xine_close_audio_driver(self.__xine, self.__audio_port)
        xine_exit(self.__xine)

    #
    # Specefic xine functions
    #
    def __do_set_property(self, property, v):
        if not self.__stream: return
        xine_set_param(self.__stream, property, v)

    def __do_get_property(self, property):
        if not self.__stream: return -1
        return xine_get_param(self.__stream, property)

    def _create_stream(self, isvideo):
        if self.__stream != None:
            raise PlayerError("a stream already exists")
        # open video driver
        if isvideo and self._video_support and \
                        self.__xine_options["video"] != "none":
            try: self.__display.create()
            except x11.X11Error, err:
                raise PlayerError(str(err))

            x11_infos = self.__display.get_infos()
            vis = x11_visual_t()
            vis.display = x11_infos["dsp"]
            vis.screen = x11_infos["screen"]
            vis.d = x11_infos["window"]
            vis.user_data = None
            vis.dest_size_cb =\
                cast(xine_dest_size_cb(self._dest_size_cb),c_void_p)
            vis.frame_output_cb =\
                cast(xine_frame_output_cb(self._frame_output_cb),c_void_p)
            vis.lock_display = None
            vis.unlock_display = None

            self.__video_port = xine_open_video_driver(self.__xine,\
                self.__xine_options["video"], XINE_VISUAL_TYPE_X11,\
                cast(byref(vis), c_void_p))
            if not self.__video_port:
                log.err("Unable to open video driver")
                raise PlayerError("Unable to open video driver")

        # create stream
        self.__stream = xine_stream_new(self.__xine, self.__audio_port,\
                            self.__video_port)
        # add event listener
        self.__event_queue = xine_event_new_queue(self.__stream)
        xine_event_create_listener_thread(self.__event_queue,
            self._event_callback, None)

    def _destroy_stream(self):
        if self.__stream:
            xine_event_dispose_queue(self.__event_queue)
            xine_close(self.__stream)
            xine_dispose(self.__stream)

            # close video driver
            if self.__video_port:
                xine_close_video_driver(self.__xine, self.__video_port)
                self.__display.destroy()

            # reset vars
            self.__video_port = None
            self.__stream = None
            self.__event_queue = None

    #
    # callbacks
    #
    def _eof(self):
        new_file = self._source.next(self.options["random"],\
                    self.options["repeat"])
        if new_file == None:
            self._destroy_stream()
        else:
            detach = self._media_file["type"] != new_file["type"]
            self.stop(detach)
            self._media_file = new_file
            try: self.start_play()
            except PlayerError: pass

    def _event_callback(self, user_data, event):
        event = event.contents
        if event.type == XINE_EVENT_UI_PLAYBACK_FINISHED:
            threads.deferToThread(self._eof)
        elif event.type == XINE_EVENT_UI_MESSAGE:
            msg = cast(event.data, POINTER(xine_ui_message_data_t)).contents
            if msg.type != XINE_MSG_NO_ERROR:
                if msg.explanation:
                    message = string_at(addressof(msg) + msg.explanation)
                else:
                    message = "xine error %s" % msg.type
                threads.deferToThread(log.err, message)

    def _dest_size_cb(self, data, video_width, video_height,\
                      video_pixel_aspect, dest_width, dest_height,\
                      dest_pixel_aspect):
        infos = self.__display.get_and_lock_video_area()
        dest_width[0] = infos["width"]
        dest_height[0] = infos["height"]
        dest_pixel_aspect[0] = c_double(infos["pixel_aspect"])
        self.__display.release_video_area()

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

# vim: ts=4 sw=4 expandtab
