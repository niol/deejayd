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
#
# This work is based on the perl Video::Xine API.
# http://search.cpan.org/~stephen/Video-Xine/


import ctypes, os
import locale
import _xinelib as xinelib
from pytyx11 import x11


class XineError(Exception): pass


class Osd(object):

    XINE_TEXT_PALETTE_SIZE = 11

    XINE_OSD_TEXT1  = (0 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT2  = (1 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT3  = (2 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT4  = (3 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT5  = (4 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT6  = (5 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT7  = (6 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT8  = (7 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT9  = (8 * XINE_TEXT_PALETTE_SIZE)
    XINE_OSD_TEXT10 = (9 * XINE_TEXT_PALETTE_SIZE)

    # white text, black border, transparent background
    XINE_TEXTPALETTE_WHITE_BLACK_TRANSPARENT    = 0
    # white text, noborder, transparent background
    XINE_TEXTPALETTE_WHITE_NONE_TRANSPARENT     = 1
    # white text, no border, translucid background
    XINE_TEXTPALETTE_WHITE_NONE_TRANSLUCID      = 2
    # yellow text, black border, transparent background
    XINE_TEXTPALETTE_YELLOW_BLACK_TRANSPARENT   = 3

    XINE_OSD_CAP_FREETYPE2 = 0x0001
    XINE_OSD_CAP_UNSCALED  = 0x0002

    def __init__(self, stream, width, height):
        self.__osd_p = xinelib.xine_osd_new(stream.stream_p(),
                                            0, 0, width, height)
        self.color_base = Osd.XINE_OSD_TEXT1
        self.__last_text = None

    def set_font(self, font_name, font_size):
        xinelib.xine_osd_set_font(self.__osd_p, font_name, font_size)

    def set_text_palette(self, palette_number, color_base):
        self.color_base = color_base
        xinelib.xine_osd_set_text_palette(self.__osd_p,
                                          palette_number,
                                          color_base)

    def is_unscaled(self):
        unscaled = xinelib.xine_osd_get_capabilities(self.__osd_p)\
                   & Osd.XINE_OSD_CAP_UNSCALED
        return unscaled and True or False

    def clear(self):
        xinelib.xine_osd_clear(self.__osd_p)

    def draw_text(self, posx, posy, text):
        xinelib.xine_osd_draw_text(self.__osd_p,
                                   0, 0, text, self.color_base)
        xinelib.xine_osd_set_position(self.__osd_p, posx, posy)
        self.__last_text = text

    def show(self):
        if self.is_unscaled:
            xinelib.xine_osd_show_unscaled(self.__osd_p, 0)
        else:
            xinelib.xine_osd_show(self.__osd_p, 0)

    def hide(self, text):
        if text == self.__last_text:
            xinelib.xine_osd_hide(self.__osd_p, 0)

    def close(self):
        self.clear()
        xinelib.xine_osd_free(self.__osd_p)
        self.__osd_p = None


class Event(object):

    XINE_EVENT_UI_PLAYBACK_FINISHED = 1
    XINE_EVENT_UI_CHANNELS_CHANGED  = 2
    XINE_EVENT_UI_SET_TITLE         = 3
    XINE_EVENT_UI_MESSAGE           = 4
    XINE_EVENT_FRAME_FORMAT_CHANGE  = 5
    XINE_EVENT_AUDIO_LEVEL          = 6
    XINE_EVENT_QUIT                 = 7
    XINE_EVENT_PROGRESS             = 8

    def __init__(self, type, contents):
        self.type = type
        if self.type == Event.XINE_EVENT_UI_MESSAGE:
            self.data = ctypes.cast(contents.data,
                             ctypes.POINTER(xinelib.xine_ui_message_data_t))
        else:
            self.data = None

    def message(self):
        if not self.data: return None
        msg = self.data.contents
        if msg.type != XinePlayer.XINE_MSG_NO_ERROR:
            if msg.explanation:
                message_txt = ctypes.string_at(ctypes.addressof(msg)\
                                               + msg.explanation)
                message_parameters = []
                param_address = ctypes.addressof(msg) + msg.parameters
                for param_index in range(0, msg.num_parameters):
                    message_par = ctypes.string_at(param_address)
                    param_address += len(message_par) + 1 # Skip '\0'
                    message_parameters.append(message_par)
                message_params = ' '.join(message_parameters)
                message = "%s %s" % (message_txt, message_params)
            else:
                raise XineError(msg.type)
        else:
            message = None
        return message.decode(locale.getpreferredencoding())


class EventQueue(object):

    def __init__(self, stream):
        self.__callbacks = []
        self.__event_queue_p = xinelib.xine_event_new_queue(stream.stream_p())

    def add_callback(self, callback, user_data=None):
        cb = xinelib.xine_event_listener_cb_t(self.__get_cb(callback))
        self.__callbacks.append(cb)
        xinelib.xine_event_create_listener_thread(self.__event_queue_p,
                                                  cb, user_data)

    def __get_cb(self, callback):
        def c_cb(user_data, event):
            callback(user_data, Event(event.contents.type, event.contents))
        return c_cb

    def close(self):
        xinelib.xine_event_dispose_queue(self.__event_queue_p)
        self.__callbacks = []


class AudioDriver(object):

    def __init__(self, xine, id=None, data=None):
        self.__xine_p = xine.xine_p()
        self.__driver_p = xinelib.xine_open_audio_driver(self.__xine_p,
                                                         id, data)
        if not self.__driver_p:
            raise XineError('Could not open audio driver')

    def driver_p(self):
        return self.__driver_p

    def destroy(self):
        xinelib.xine_close_audio_driver(self.__xine_p, self.__driver_p)
        self.__driver_p = None


class VideoDriver(object):

    XINE_VISUAL_TYPE_NONE    = 0
    XINE_VISUAL_TYPE_X11     = 1
    XINE_VISUAL_TYPE_X11_2   = 10
    XINE_VISUAL_TYPE_AA      = 2
    XINE_VISUAL_TYPE_FB      = 3
    XINE_VISUAL_TYPE_GTK     = 4
    XINE_VISUAL_TYPE_DFB     = 5
    XINE_VISUAL_TYPE_PM      = 6
    XINE_VISUAL_TYPE_DIRECTX = 7
    XINE_VISUAL_TYPE_CACA    = 8
    XINE_VISUAL_TYPE_MACOSX  = 9
    XINE_VISUAL_TYPE_XCB     = 11

    def __init__(self, xine, id=None, display_id=':0.0', fullscreen=False):
        self.__xine_p = xine.xine_p()

        try:
            visual = self.__make_x11_visual(display_id, fullscreen)
        except x11.X11Error:
            raise XineError('Could not initialize Xine on %s', display_id)

        self.__driver_p = xinelib.xine_open_video_driver(self.__xine_p,
                           id,
                           VideoDriver.XINE_VISUAL_TYPE_X11,
                           ctypes.cast(ctypes.byref(visual), ctypes.c_void_p))

        if not self.__driver_p:
            raise XineError('Could not open video driver')

    def driver_p(self):
        return self.__driver_p

    def __make_x11_visual(self, display_id, fullscreen=False):
        self.display = x11.X11Display(display_id)
        if fullscreen:
            self.window = self.display.do_create_window(fullscreen=True)
        else:
            self.window = self.display.do_create_window(320, 200)

        # Those callbacks are required to be kept in this tuple in order to
        # be safe from the garbage collector.
        self.__x11_callbacks = ( xinelib.xine_dest_size_cb(self.__dest_size_cb),
                           xinelib.xine_frame_output_cb(self.__frame_output_cb),
                               )

        vis = xinelib.x11_visual_t()
        vis.display = self.display.display_p()
        vis.screen = self.display.get_default_screen_number()
        vis.d = self.window.window_p()
        vis.frame_output_cb = ctypes.cast(self.__x11_callbacks[1],
                                          ctypes.c_void_p)
        vis.dest_size_cb = ctypes.cast(self.__x11_callbacks[0], ctypes.c_void_p)
        return vis

    def __frame_output_cb(self, user_data,
                                video_width, video_height, video_pixel_aspect,
                                dest_x, dest_y,
                                dest_width, dest_height, dest_pixel_aspect,
                                win_x, win_y):
        dest_x[0] = 0
        dest_y[0] = 0
        win_x[0] = self.window.video_area_info['win_x']
        win_y[0] = self.window.video_area_info['win_y']
        self.__dest_size_cb(user_data,
                            video_width, video_height, video_pixel_aspect,
                            dest_width, dest_height, dest_pixel_aspect)

    def __dest_size_cb(self, user_data,
                             video_width, video_height, video_pixel_aspect,
                             dest_width, dest_height, dest_pixel_aspect):
        dest_width[0] = self.window.video_area_info['width']
        dest_height[0] = self.window.video_area_info['height']
        dest_pixel_aspect[0] = self.window.video_area_info['aspect']

    XINE_GUI_SEND_DRAWABLE_CHANGED       = 2
    XINE_GUI_SEND_EXPOSE_EVENT           = 3
    XINE_GUI_SEND_TRANSLATE_GUI_TO_VIDEO = 4
    XINE_GUI_SEND_VIDEOWIN_VISIBLE       = 5
    XINE_GUI_SEND_SELECT_VISUAL          = 8
    XINE_GUI_SEND_WILL_DESTROY_DRAWABLE  = 9

    def send_gui_data(self, type, data=None):
        xinelib.xine_port_send_gui_data(self.__driver_p, ctypes.c_int(type),
                                        ctypes.cast(data, ctypes.c_void_p))

    def destroy(self):
        xinelib.xine_close_video_driver(self.__xine_p, self.__driver_p)
        self.__x11_callbacks = None
        self.__driver = None

        self.window.close()
        self.window = None
        self.display.destroy()
        self.display = None


class Stream(object):

    XINE_SPEED_PAUSE                 =  0
    XINE_SPEED_SLOW_4                =  1
    XINE_SPEED_SLOW_2                =  2
    XINE_SPEED_NORMAL                =  4
    XINE_SPEED_FAST_2                =  8
    XINE_SPEED_FAST_4                = 16

    def __init__(self, xine, audio_port=None, video_port=None):
        self.__xine = xine
        self.__event_queue = None
        self.__software_mixer = False
        self.__audio_port = audio_port or AudioDriver(xine)
        self.__video_port = video_port
        if self.__video_port:
            video_driver_p = self.__video_port.driver_p()
        else:
            video_driver_p = None
        self.__stream_p = xinelib.xine_stream_new(self.__xine.xine_p(),
                                                  self.__audio_port.driver_p(),
                                                  video_driver_p)

        if self.__xine.has_gapless():
            self.set_param(Stream.XINE_PARAM_EARLY_FINISHED_EVENT, 1)

        if self.__video_port:
            self.__video_port.send_gui_data(\
                              VideoDriver.XINE_GUI_SEND_DRAWABLE_CHANGED,
                              self.__video_port.window.window_p())
            self.__video_port.send_gui_data(\
                              VideoDriver.XINE_GUI_SEND_VIDEOWIN_VISIBLE,
                              1)
        else:
            self.set_param(Stream.XINE_PARAM_IGNORE_VIDEO, 1)
            self.set_param(Stream.XINE_PARAM_IGNORE_SPU, 1)

        self.__osd = None

    def has_video(self):
        if self.__video_port:
            return True
        else:
            return False

    def stream_p(self):
        return self.__stream_p

    def add_event_callback(self, callback):
        if not self.__event_queue:
            self.__event_queue = EventQueue(self)
        self.__event_queue.add_callback(callback)

    def open(self, mrl):
        if not xinelib.xine_open(self.__stream_p, mrl):
            raise XineError('Could not open %s' % mrl)

    def play(self, start_pos=0, start_time=0):
        if not xinelib.xine_play(self.__stream_p, ctypes.c_int(start_pos),
                                                  ctypes.c_int(start_time)):
            raise XineError('Could not play stream')
        else:
            self.set_dpms(False)

    def stop(self):
        self.set_dpms(True)
        xinelib.xine_stop(self.__stream_p)

    def get_pos_length(self):
        _pos_stream = ctypes.c_int()
        _pos_time = ctypes.c_int()
        _length_time = ctypes.c_int()
        result = xinelib.xine_get_pos_length(self.__stream_p,
                                             ctypes.byref(_pos_stream),
                                             ctypes.byref(_pos_time),
                                             ctypes.byref(_length_time))
        if result:
            return _pos_stream.value, _pos_time.value, _length_time.value
        else:
            return 0, 0, 0

    def get_pos(self):
        # Workaround for problems when you seek too quickly
        i = 0
        while i < 4:
            pos_s, pos_t, length = self.get_pos_length()
            if int(pos_t) > 0:  break
            xinelib.xine_usec_sleep(100000)
            i += 1
        return int(pos_t / 1000)

    def get_length(self):
        pos_s, pos_t, length = self.get_pos_length()
        return length / 1000

    XINE_STATUS_IDLE = 0
    XINE_STATUS_STOP = 1
    XINE_STATUS_PLAY = 2
    XINE_STATUS_QUIT = 3

    def get_status(self):
        return xinelib.xine_get_status(self.__stream_p)

    def set_fullscreen(self, fullscreen):
        # FIXME : This does not work yet.
        raise NotImplementedError
        if not self.__video_port:
            raise XineError('Stream is audio only')
        self.__video_port.window.set_fullscreen(fullscreen)
        self.__video_port.send_gui_data(\
                              VideoDriver.XINE_GUI_SEND_DRAWABLE_CHANGED,
                              self.__video_port.window.window_p())

    XINE_PARAM_SPEED                 =  1 # see below
    XINE_PARAM_AV_OFFSET             =  2 # unit: 1/90000 sec
    XINE_PARAM_AUDIO_CHANNEL_LOGICAL =  3 # 1 => auto, -2 => off
    XINE_PARAM_SPU_CHANNEL           =  4
    XINE_PARAM_VIDEO_CHANNEL         =  5
    XINE_PARAM_AUDIO_VOLUME          =  6 # 0..100
    XINE_PARAM_AUDIO_MUTE            =  7 # 1=>mute, 0=>unmute
    XINE_PARAM_AUDIO_COMPR_LEVEL     =  8 # <100=>off, % compress otherw
    XINE_PARAM_AUDIO_AMP_LEVEL       =  9 # 0..200, 100=>100% (default)
    XINE_PARAM_AUDIO_REPORT_LEVEL    = 10 # 1=>send events, 0=> don't
    XINE_PARAM_VERBOSITY             = 11 # control console output
    XINE_PARAM_SPU_OFFSET            = 12 # unit: 1/90000 sec
    XINE_PARAM_IGNORE_VIDEO          = 13 # disable video decoding
    XINE_PARAM_IGNORE_AUDIO          = 14 # disable audio decoding
    XINE_PARAM_IGNORE_SPU            = 15 # disable spu decoding
    XINE_PARAM_BROADCASTER_PORT      = 16 # 0: disable, x: server port
    XINE_PARAM_METRONOM_PREBUFFER    = 17 # unit: 1/90000 sec
    XINE_PARAM_EQ_30HZ               = 18 # equalizer gains -100..100
    XINE_PARAM_EQ_60HZ               = 19 # equalizer gains -100..100
    XINE_PARAM_EQ_125HZ              = 20 # equalizer gains -100..100
    XINE_PARAM_EQ_250HZ              = 21 # equalizer gains -100..100
    XINE_PARAM_EQ_500HZ              = 22 # equalizer gains -100..100
    XINE_PARAM_EQ_1000HZ             = 23 # equalizer gains -100..100
    XINE_PARAM_EQ_2000HZ             = 24 # equalizer gains -100..100
    XINE_PARAM_EQ_4000HZ             = 25 # equalizer gains -100..100
    XINE_PARAM_EQ_8000HZ             = 26 # equalizer gains -100..100
    XINE_PARAM_EQ_16000HZ            = 27 # equalizer gains -100..100
    XINE_PARAM_AUDIO_CLOSE_DEVICE    = 28 # force closing audio device
    XINE_PARAM_AUDIO_AMP_MUTE        = 29 # 1=>mute, 0=>unmute
    XINE_PARAM_FINE_SPEED            = 30 # 1.000.000 => normal speed
    XINE_PARAM_EARLY_FINISHED_EVENT  = 31 # send event when demux finish
    XINE_PARAM_GAPLESS_SWITCH        = 32 # next stream only gapless swi
    XINE_PARAM_DELAY_FINISHED_EVENT  = 33 # 1/10sec,0=>disable,-1=>f

    XINE_PARAM_VO_DEINTERLACE        = 0x01000000 # bool
    XINE_PARAM_VO_ASPECT_RATIO       = 0x01000001 # see below
    XINE_PARAM_VO_HUE                = 0x01000002 # 0..65535
    XINE_PARAM_VO_SATURATION         = 0x01000003 # 0..65535
    XINE_PARAM_VO_CONTRAST           = 0x01000004 # 0..65535
    XINE_PARAM_VO_BRIGHTNESS         = 0x01000005 # 0..65535
    XINE_PARAM_VO_ZOOM_X             = 0x01000008 # percent
    XINE_PARAM_VO_ZOOM_Y             = 0x0100000d # percent
    XINE_PARAM_VO_PAN_SCAN           = 0x01000009 # bool
    XINE_PARAM_VO_TVMODE             = 0x0100000a # ???
    XINE_PARAM_VO_WINDOW_WIDTH       = 0x0100000f # readonly
    XINE_PARAM_VO_WINDOW_HEIGHT      = 0x01000010 # readonly
    XINE_PARAM_VO_CROP_LEFT          = 0x01000020 # crop frame pixels
    XINE_PARAM_VO_CROP_RIGHT         = 0x01000021 # crop frame pixels
    XINE_PARAM_VO_CROP_TOP           = 0x01000022 # crop frame pixels
    XINE_PARAM_VO_CROP_BOTTOM        = 0x01000023 # crop frame pixels

    XINE_VO_ZOOM_STEP                = 100
    XINE_VO_ZOOM_MAX                 = 400
    XINE_VO_ZOOM_MIN                 = -85

    XINE_VO_ASPECT_AUTO              = 0
    XINE_VO_ASPECT_SQUARE            = 1 # 1:1
    XINE_VO_ASPECT_4_3               = 2 # 4:3
    XINE_VO_ASPECT_ANAMORPHIC        = 3 # 16:9
    XINE_VO_ASPECT_DVB               = 4 # 2.11:1
    XINE_VO_ASPECT_NUM_RATIOS        = 5

    def set_param(self, param, value):
        xinelib.xine_set_param(self.__stream_p, param, value)

    def get_param(self, param):
        return xinelib.xine_get_param(self.__stream_p, param)

    def set_software_mixer(self, software_mixer):
        self.__software_mixer = software_mixer

    def set_volume(self, volume):
        param = Stream.XINE_PARAM_AUDIO_VOLUME
        if self.__software_mixer:
            param = Stream.XINE_PARAM_AUDIO_AMP_LEVEL
        self.set_param(param, volume)

    XINE_META_INFO_TITLE             = 0
    XINE_META_INFO_COMMENT           = 1
    XINE_META_INFO_ARTIST            = 2
    XINE_META_INFO_GENRE             = 3
    XINE_META_INFO_ALBUM             = 4
    XINE_META_INFO_YEAR              = 5
    XINE_META_INFO_VIDEOCODEC        = 6
    XINE_META_INFO_AUDIOCODEC        = 7
    XINE_META_INFO_SYSTEMLAYER       = 8
    XINE_META_INFO_INPUT_PLUGIN      = 9

    def get_meta_info(self, info):
        return xinelib.xine_get_meta_info(self.__stream_p, info)

    XINE_STREAM_INFO_BITRATE         = 0
    XINE_STREAM_INFO_SEEKABLE        = 1
    XINE_STREAM_INFO_VIDEO_WIDTH     = 2
    XINE_STREAM_INFO_VIDEO_HEIGHT    = 3
    XINE_STREAM_INFO_VIDEO_RATIO     = 4

    def get_stream_info(self, info):
        return xinelib.xine_get_stream_info(self.__stream_p, info)

    XINE_LANG_MAX = 256

    def get_audio_lang(self, channel):
        _lang = ctypes.create_string_buffer(Stream.XINE_LANG_MAX)

        result = xinelib.xine_get_audio_lang(self.__stream_p, channel, _lang)
        if not result:
            _lang.raw = 'unknown'

        return _lang.value

    def get_spu_lang(self, channel):
        _lang = ctypes.create_string_buffer(Stream.XINE_LANG_MAX)

        result = xinelib.xine_get_spu_lang(self.__stream_p, channel, _lang)
        if not result:
            _lang.raw = 'unknown'

        return _lang.value

    def set_dpms(self, activated):
        if self.__video_port:
            self.__video_port.display.set_dpms(activated)

    def osd_new(self, font_size):
        if not self.__video_port:
            raise XineError('This Stream is audio only.')

        # Does this need locking the video area?
        self.__osd = Osd(self,
                         self.__video_port.window.video_area_info['width'],
                         self.__video_port.window.video_area_info['height'])
        self.__osd.set_font('sans', font_size)
        self.__osd.set_text_palette(\
                                   Osd.XINE_TEXTPALETTE_WHITE_BLACK_TRANSPARENT,
                                   Osd.XINE_OSD_TEXT1)
        return self.__osd

    def close(self):
        self.stop()
        xinelib.xine_close(self.__stream_p)

    def destroy(self):
        self.close()
        self.set_param(Stream.XINE_PARAM_AUDIO_CLOSE_DEVICE, 1)

        if self.__event_queue:
            self.__event_queue.close()
            self.__event_queue = None
        if self.__osd:
            self.__osd.close()
            self.__osd = None

        xinelib.xine_dispose(self.__stream_p)
        self.__stream_p = None

        self.__audio_port.destroy()
        self.__audio_port = None
        if self.__video_port:
            self.__video_port.destroy()
            self.__video_port = None


class XinePlayer(object):

    XINE_MSG_NO_ERROR              = 0 # (messages to UI)
    XINE_MSG_GENERAL_WARNING       = 1 # (warning message)
    XINE_MSG_UNKNOWN_HOST          = 2 # (host name)
    XINE_MSG_UNKNOWN_DEVICE        = 3 # (device name)
    XINE_MSG_NETWORK_UNREACHABLE   = 4 # none
    XINE_MSG_CONNECTION_REFUSED    = 5 # (host name)
    XINE_MSG_FILE_NOT_FOUND        = 6 # (file name or mrl)
    XINE_MSG_READ_ERROR            = 7 # (device/file/mrl)
    XINE_MSG_LIBRARY_LOAD_ERROR    = 8 # (library/decoder)
    XINE_MSG_ENCRYPTED_SOURCE      = 9 # none
    XINE_MSG_SECURITY              = 10 # (security message)
    XINE_MSG_AUDIO_OUT_UNAVAILABLE = 11 # none
    XINE_MSG_PERMISSION_ERROR      = 12 # (file name or mrl)
    XINE_MSG_FILE_EMPTY            = 13 # file is empty

    def __init__(self, config_file_path=None):
        self.__xine = xinelib.xine_new()
        if not self.__xine:
            raise XineError('Error during Xine instance initialisation')

        if config_file_path:
            xinelib.xine_config_load(self.__xine, config_file_path)
        else: # load default config file
            default = os.path.join(xinelib.xine_get_homedir(),".xine/config")
            xinelib.xine_config_load(self.__xine, default)

        xinelib.xine_init(self.__xine)

    def xine_p(self):
        return self.__xine

    def get_version(self):
        major = ctypes.c_int()
        minor = ctypes.c_int()
        sub = ctypes.c_int()
        xinelib.xine_get_version(ctypes.byref(major),
                                 ctypes.byref(minor),
                                 ctypes.byref(sub))
        return (major.value, minor.value, sub.value)

    def has_gapless(self):
        return xinelib.xine_check_version(1, 1, 1) == 1

    def get_supported_extensions(self):
        return xinelib.xine_get_file_extensions(self.__xine).split()

    def list_input_plugins(self):
        plugins = []
        for plugin in xinelib.xine_list_input_plugins(self.__xine):
            if not plugin:
                break
            plugins.append(plugin.lower())
        return plugins

    XINE_CONFIG_TYPE_UNKNOWN = 0
    XINE_CONFIG_TYPE_RANGE   = 1
    XINE_CONFIG_TYPE_STRING  = 2
    XINE_CONFIG_TYPE_ENUM    = 3
    XINE_CONFIG_TYPE_NUM     = 4
    XINE_CONFIG_TYPE_BOOL    = 5
    # string type stored in num_value of config entry struct
    XINE_CONFIG_STRING_IS_STRING         = 0
    XINE_CONFIG_STRING_IS_FILENAME       = 1
    XINE_CONFIG_STRING_IS_DEVICE_NAME    = 2
    XINE_CONFIG_STRING_IS_DIRECTORY_NAME = 3

    def __get_config_entry_value(self, entry):
        if entry.type == XinePlayer.XINE_CONFIG_TYPE_UNKNOWN:
            return entry.unknown_value
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_RANGE:
            return (entry.range_min, entry.range_max)
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_STRING:
            return entry.str_value or entry.str_default
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_ENUM:
            enum_values = []
            for enum_value_index in range(0, entry.num_value):
                enum_values.append(entry.enum_values[enum_value_index])
            return enum_values
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_NUM:
            return entry.num_value or entry.num_default
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_BOOL:
            if entry.num_value == 1:
                return True
            elif entry.num_value == 0:
                return False
            else:
                return False

    def get_all_config(self):
        entries = {}
        entry = xinelib.xine_cfg_entry_t()
        xinelib.xine_config_get_first_entry(self.__xine, ctypes.byref(entry))
        entries[entry.key] = self.__get_config_entry_value(entry)
        while xinelib.xine_config_get_next_entry(self.__xine,
                                                 ctypes.byref(entry)):
            entries[entry.key] = self.__get_config_entry_value(entry)
        return entries

    def get_config_entry(self, key):
        entry = xinelib.xine_cfg_entry_t()
        xinelib.xine_config_lookup_entry(self.__xine, key, ctypes.byref(entry))
        return self.__get_config_entry_value(entry)

    def update_config_entry(self, key, value):
        entry = xinelib.xine_cfg_entry_t()
        xinelib.xine_config_lookup_entry(self.__xine, key, ctypes.byref(entry))
        if entry.type == XinePlayer.XINE_CONFIG_TYPE_UNKNOWN:
            entry.unknown_value = value
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_RANGE:
            entry.range_min = value[0]
            entry.range_max = value[1]
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_STRING:
            entry.str_value = value
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_ENUM:
            enum_values = '\0'.join(value)
            entry.enum_values = ctypes.byref(enum_values)
            entry.num_value = len(value)
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_NUM:
            entry.num_value = value
        elif entry.type == XinePlayer.XINE_CONFIG_TYPE_BOOL:
            if value:
                entry.num_value = 1
            else:
                entry.num_value = 0
        xinelib.xine_config_update_entry(self.__xine, ctypes.byref(entry))

    def destroy(self):
        xinelib.xine_exit(self.__xine)
        self.__xine = None

    XINE_ENGINE_PARAM_VERBOSITY_NONE = 0
    XINE_ENGINE_PARAM_VERBOSITY_LOG =  1

    def set_param(self, param, value):
        xinelib.xine_engine_set_param(self.__xine, param, value)

    def stream_new(self, audio_port=None, video_port=None, video=False):
        if video and not video_port:
            video_port = VideoDriver(self)
        return Stream(self, audio_port, video_port)


if __name__ == '__main__':
    import sys, os, time
    x = XinePlayer(os.path.expanduser('~/.xine/config'))
    print 'Xine %d.%d.%d ' % x.get_version()
    x.set_param(XinePlayer.XINE_ENGINE_PARAM_VERBOSITY_LOG, 1)
    vd = VideoDriver(x, fullscreen=False)
    # force audio driver to alsa to test config entry set/get
    ad = AudioDriver(x, "alsa")
    s = x.stream_new(video_port=vd, audio_port=ad)
    s.set_param(Stream.XINE_PARAM_VERBOSITY, 2) # DEBUG
    x.update_config_entry('audio.device.alsa_front_device', 'hw:0,1')
    print '\tOutput to : %s'\
          % x.get_config_entry('audio.device.alsa_default_device')
    print x.get_all_config()['audio.device.alsa_default_device']

    def print_message(data, event):
        if event.type == Event.XINE_EVENT_UI_MESSAGE:
            try:
                print "Xine error message : %s" % event.message()
            except XineError, e:
                print "Xine exception message : %s " % e
    s.add_event_callback(print_message)

    file_path = sys.argv[1]
    if not file_path.startswith('/') and not file_path.startswith('http://'):
       file_path = os.path.join(os.getcwd(), file_path)
    if file_path.startswith('/'):
       file_path = 'file:/' + file_path
    s.open(file_path)
    s.play()
    time.sleep(15)
    s.stop()
    s.destroy()
    x.destroy()


# vim: ts=4 sw=4 expandtab
