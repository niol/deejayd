# Deejayd, a media player daemon
# Copyright (C) 2006 Lukas Lalinsky
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

import sys
import ctypes

try:
    _libxine = ctypes.cdll.LoadLibrary('libxine.so.1')
except (ImportError, OSError), e:
    raise ImportError, e

class xine_event_t(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_int),
        ('stream', ctypes.c_void_p),
        ('data', ctypes.c_void_p),
        ('data_length', ctypes.c_int),
    ]

class xine_ui_message_data_t(ctypes.Structure):
    _fields_ = [
        ('compatibility_num_buttons', ctypes.c_int),
        ('compatibility_str_len', ctypes.c_int),
        ('compatibility_str', 256 * ctypes.c_char),
        ('type', ctypes.c_int),
        ('explanation', ctypes.c_int),
        ('num_parameters', ctypes.c_int),
        ('parameters', ctypes.c_void_p),
        ('messages', ctypes.c_char),
    ]

class x11_visual_t(ctypes.Structure):
    _fields_ = [
        ('display', ctypes.c_void_p),
        ('screen', ctypes.c_int),
        ('d', ctypes.c_ulong), # Drawable
        ('user_data', ctypes.c_void_p),
        ('dest_size_cb', ctypes.c_void_p),
        ('frame_output_cb', ctypes.c_void_p),
        ('lock_display', ctypes.c_void_p),
        ('unlock_display', ctypes.c_void_p),
    ]

# dest size callback
xine_dest_size_cb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,\
    ctypes.c_int, ctypes.c_int, ctypes.c_double,\
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),\
    ctypes.POINTER(ctypes.c_double))

# frame output callback
xine_frame_output_cb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_int, ctypes.c_int, ctypes.c_double,\
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),\
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),\
    ctypes.POINTER(ctypes.c_double),\
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

# event listener callback type
xine_event_listener_cb_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p,
    ctypes.POINTER(xine_event_t))

# event types
XINE_EVENT_UI_PLAYBACK_FINISHED  = 1
XINE_EVENT_UI_CHANNELS_CHANGED   = 2
XINE_EVENT_UI_SET_TITLE          = 3
XINE_EVENT_UI_MESSAGE            = 4
XINE_EVENT_FRAME_FORMAT_CHANGE   = 5
XINE_EVENT_AUDIO_LEVEL           = 6
XINE_EVENT_QUIT                  = 7
XINE_EVENT_PROGRESS              = 8

# stream parameters
XINE_PARAM_SPEED                 = 1 # see below
XINE_PARAM_AV_OFFSET             = 2 # unit: 1/90000 ses
XINE_PARAM_AUDIO_CHANNEL_LOGICAL = 3 # -1 => auto, -2 => off
XINE_PARAM_SPU_CHANNEL           = 4
XINE_PARAM_VIDEO_CHANNEL         = 5
XINE_PARAM_AUDIO_VOLUME          = 6 # 0..100
XINE_PARAM_AUDIO_MUTE            = 7 # 1=>mute, 0=>unmute
XINE_PARAM_AUDIO_COMPR_LEVEL     = 8 # <100=>off, % compress otherw
XINE_PARAM_AUDIO_AMP_LEVEL       = 9 # 0..200, 100=>100% (default)
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
XINE_PARAM_DELAY_FINISHED_EVENT  = 33 # 1/10sec,0=>disable,-1=>forev

# video parameters
XINE_PARAM_VO_ZOOM_X             = 0x01000008 # percent
XINE_PARAM_VO_ZOOM_Y             = 0x0100000d # percent

XINE_VO_ZOOM_MAX                 = 400
XINE_VO_ZOOM_MIN                 = -85

# speeds
XINE_SPEED_PAUSE                 = 0
XINE_SPEED_SLOW_4                = 1
XINE_SPEED_SLOW_2                = 2
XINE_SPEED_NORMAL                = 4
XINE_SPEED_FAST_2                = 8
XINE_SPEED_FAST_4                = 16

# metadata
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

# stream info
XINE_STREAM_INFO_BITRATE         = 0
XINE_STREAM_INFO_SEEKABLE        = 1
XINE_STREAM_INFO_VIDEO_WIDTH     = 2
XINE_STREAM_INFO_VIDEO_HEIGHT    = 3
XINE_STREAM_INFO_VIDEO_RATIO     = 4

# statuses
XINE_STATUS_IDLE = 0
XINE_STATUS_STOP = 1
XINE_STATUS_PLAY = 2
XINE_STATUS_QUIT = 3

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

# valid visual types
XINE_VISUAL_TYPE_NONE             = 0
XINE_VISUAL_TYPE_X11              = 1
XINE_VISUAL_TYPE_X11_2            = 10
XINE_VISUAL_TYPE_AA               = 2
XINE_VISUAL_TYPE_FB               = 3
XINE_VISUAL_TYPE_GTK              = 4
XINE_VISUAL_TYPE_DFB              = 5
XINE_VISUAL_TYPE_PM               = 6 # used by the OS/2 port
XINE_VISUAL_TYPE_DIRECTX          = 7 # used by the win32/msvc port
XINE_VISUAL_TYPE_CACA             = 8
XINE_VISUAL_TYPE_MACOSX           = 9
XINE_VISUAL_TYPE_XCB              = 11

# "type" constants for xine_port_send_gui_data
XINE_GUI_SEND_DRAWABLE_CHANGED = 2
XINE_GUI_SEND_EXPOSE_EVENT     = 3
XINE_GUI_SEND_VIDEOWIN_VISIBLE = 5

# osd constants
XINE_TEXT_PALETTE_SIZE         = 11

XINE_OSD_TEXT1                 = (0 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT2                 = (1 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT3                 = (2 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT4                 = (3 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT5                 = (4 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT6                 = (5 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT7                 = (6 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT8                 = (7 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT9                 = (8 * XINE_TEXT_PALETTE_SIZE)
XINE_OSD_TEXT10                = (9 * XINE_TEXT_PALETTE_SIZE)

# white text, black border, transparent background  */
XINE_TEXTPALETTE_WHITE_BLACK_TRANSPARENT    = 0
# white text, noborder, transparent background      */
XINE_TEXTPALETTE_WHITE_NONE_TRANSPARENT     = 1
# white text, no border, translucid background      */
XINE_TEXTPALETTE_WHITE_NONE_TRANSLUCID      = 2
# yellow text, black border, transparent background */
XINE_TEXTPALETTE_YELLOW_BLACK_TRANSPARENT   = 3

XINE_OSD_CAP_FREETYPE2 = 0x0001
XINE_OSD_CAP_UNSCALED  = 0x0002

# xine_t *xine_new(void)
_libxine.xine_new.restype = ctypes.c_void_p

# void xine_init(xine_t *self)
_libxine.xine_init.argtypes = [ctypes.c_void_p]

# void xine_exit(xine_t *self)
_libxine.xine_exit.argtypes = [ctypes.c_void_p]

# void xine_config_load(xine_t *self, const char *cfg_filename)
_libxine.xine_config_load.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

# const char *xine_get_homedir(void)
_libxine.xine_get_homedir.restype = ctypes.c_char_p

# xine_audio_port_t *xine_open_audio_driver(xine_t *self, const char *id,
#    void *data)
_libxine.xine_open_audio_driver.argtypes = [ctypes.c_void_p,
    ctypes.c_char_p, ctypes.c_void_p]
_libxine.xine_open_audio_driver.restype = ctypes.c_void_p

# xine_video_port_t *xine_open_video_driver(xine_t *self, const char *id,
#    int visual, void *data)
_libxine.xine_open_video_driver.restype = ctypes.c_void_p
_libxine.xine_open_video_driver.argtypes = [ctypes.c_void_p,
    ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]

# int xine_port_send_gui_data (xine_video_port_t *vo, int type, void *data)
_libxine.xine_port_send_gui_data.restype = ctypes.c_int
_libxine.xine_port_send_gui_data.argtypes = [ctypes.c_void_p, ctypes.c_int,\
    ctypes.c_void_p]

# void xine_close_audio_driver(xine_t *self, xine_audio_port_t *driver)
_libxine.xine_close_audio_driver.argtypes = [ctypes.c_void_p,
    ctypes.c_void_p]

# void xine_close_video_driver(xine_t *self, xine_video_port_t *driver)
_libxine.xine_close_video_driver.argtypes = [ctypes.c_void_p,
    ctypes.c_void_p]

# xine_stream_t *xine_stream_new(xine_t *self,
#    xine_audio_port_t *ao, xine_video_port_t *vo)
_libxine.xine_stream_new.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_void_p]
_libxine.xine_stream_new.restype = ctypes.c_void_p

# void xine_close(xine_sxine_event_create_listener_threadtream_t *stream)
_libxine.xine_close.argtypes = [ctypes.c_void_p]

# int xine_open (xine_stream_t *stream, const char *mrl)
_libxine.xine_open.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_libxine.xine_open.restype = ctypes.c_int

# int xine_play(xine_stream_t *stream, int start_pos, int start_time)
_libxine.xine_play.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_libxine.xine_play.restype = ctypes.c_int

# void xine_stop(xine_stream_t *stream)
_libxine.xine_stop.argtypes = [ctypes.c_void_p]

# void xine_dispose(xine_stream_t *stream)
_libxine.xine_dispose.argtypes = [ctypes.c_void_p]

# xine_event_queue_t *xine_event_new_queue(xine_stream_t *stream)
_libxine.xine_event_new_queue.argtypes = [ctypes.c_void_p]
_libxine.xine_event_new_queue.restype = ctypes.c_void_p

# void xine_event_dispose_queue(xine_event_queue_t *queue)
_libxine.xine_event_dispose_queue.argtypes = [ctypes.c_void_p]

# void xine_event_create_listener_thread(xine_event_queue_t *queue,
#    xine_event_listener_cb_t callback,
#    void *user_data)
_libxine.xine_event_create_listener_thread.argtypes = [ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p]

# int xine_get_audio_lang(xine_stream_t *stream, int channel, char *lang)
_libxine.xine_get_audio_lang.restype = ctypes.c_int
_libxine.xine_get_audio_lang.argtypes = [ctypes.c_void_p, ctypes.c_int,\
    ctypes.c_char_p]

# int xine_get_spu_lang(xine_stream_t *stream, int channel, char *lang)
_libxine.xine_get_spu_lang.restype = ctypes.c_int
_libxine.xine_get_spu_lang.argtypes = [ctypes.c_void_p, ctypes.c_int,\
    ctypes.c_char_p]

_libxine.xine_usec_sleep.argtypes = [ctypes.c_int]

# void xine_set_param (xine_stream_t *stream, int param, int value)
_libxine.xine_set_param.argtypes = [ctypes.c_void_p, ctypes.c_int,
    ctypes.c_int]

# int xine_get_param (xine_stream_t *stream, int param)
_libxine.xine_get_param.argtypes = [ctypes.c_void_p, ctypes.c_int]
_libxine.xine_get_param.restype = ctypes.c_int

# char *xine_get_meta_info(xine_stream_t *stream, int info)
_libxine.xine_get_meta_info.argtypes = [ctypes.c_void_p, ctypes.c_int]
_libxine.xine_get_meta_info.restype = ctypes.c_char_p

# int xine_get_stream_info(xine_stream_t *stream, int info)
_libxine.xine_get_stream_info.argtypes = [ctypes.c_void_p, ctypes.c_int]
_libxine.xine_get_stream_info.restype = ctypes.c_int

# int xine_get_status (xine_stream_t *stream)
_libxine.xine_get_status.argtypes = [ctypes.c_void_p]
_libxine.xine_get_status.restype = ctypes.c_int

# int xine_get_pos_length (xine_stream_t *stream, int *pos_stream,
#                          int *pos_time, int *length_time)
_libxine.xine_get_pos_length.argtypes = [ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int)]

# char *xine_get_version_string(void)
_libxine.xine_get_version_string.restype = ctypes.c_char_p

# char *xine_get_file_extensions (xine_t *self)
_libxine.xine_get_file_extensions.argtypes = [ctypes.c_void_p]
_libxine.xine_get_file_extensions.restype = ctypes.c_char_p

# char *xine_get_mime_types (xine_t *self)
_libxine.xine_get_mime_types.argtypes = [ctypes.c_void_p]
_libxine.xine_get_mime_types.restype = ctypes.c_char_p

# char *const *xine_list_input_plugins(xine_t *self)
_libxine.xine_list_input_plugins.argtypes = [ctypes.c_void_p]
_libxine.xine_list_input_plugins.restype = ctypes.POINTER(ctypes.c_char_p)

# int  xine_check_version (int major, int minor, int sub)
_libxine.xine_check_version.argtypes = [ctypes.c_int, ctypes.c_int,\
    ctypes.c_int]
_libxine.xine_check_version.restype = ctypes.c_int;

# xine_osd_t *xine_osd_new(xine_stream_t *self, int x, int y,
#                          int width, int height)
_libxine.xine_osd_new.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,\
                                  ctypes.c_int, ctypes.c_int]
_libxine.xine_osd_new.restype = ctypes.c_void_p

# void xine_osd_free(xine_osd_t *self)
_libxine.xine_osd_free.argtypes = [ctypes.c_void_p]

# uint32_t xine_osd_get_capabilities(xine_osd_t *self)
_libxine.xine_osd_get_capabilities.restype = ctypes.c_int
_libxine.xine_osd_get_capabilities.argtypes = [ctypes.c_void_p]

# void xine_osd_set_text_palette(xine_osd_t *self,int palette_number,
#                                int color_base )
_libxine.xine_osd_set_text_palette.argtypes = [ctypes.c_void_p, ctypes.c_int,\
                                        ctypes.c_int]

# int xine_osd_set_font(xine_osd_t *self, const char *fontname, int size)
_libxine.xine_osd_set_font.restype = ctypes.c_int
_libxine.xine_osd_set_font.argtypes = [ctypes.c_void_p, ctypes.c_char_p,\
                                       ctypes.c_int]

# void xine_osd_set_position(xine_osd_t *self, int x, int y)
_libxine.xine_osd_set_position.argtypes = [ctypes.c_void_p, ctypes.c_int,\
                                        ctypes.c_int]

# void xine_osd_draw_text(xine_osd_t *self, int x1, int y1, char *text,
#                         int color_base)
_libxine.xine_osd_draw_text.argtypes = [ctypes.c_void_p, ctypes.c_int,\
                                        ctypes.c_int, ctypes.c_char_p,\
                                        ctypes.c_int]

# void xine_osd_show(xine_osd_t *self, int64_t vpts)
_libxine.xine_osd_show.argtypes = [ctypes.c_void_p, ctypes.c_int]

# void  xine_osd_show_unscaled (xine_osd_t *self, int64_t vpts)
_libxine.xine_osd_show_unscaled.argtypes = [ctypes.c_void_p, ctypes.c_int]

# void  xine_osd_hide(xine_osd_t *self, int64_t vpts)
_libxine.xine_osd_hide.argtypes = [ctypes.c_void_p, ctypes.c_int]

# void  xine_osd_clear(xine_osd_t *self)
_libxine.xine_osd_clear.argtypes = [ctypes.c_void_p]

# copy functions from the library
module = sys.modules[__name__]
for name in dir(_libxine):
    if name.startswith('xine_'):
        setattr(module, name, getattr(_libxine, name))

_evt_callbacks = []
def xine_event_create_listener_thread(queue, callback, user_data):
    cb = xine_event_listener_cb_t(callback)
    _evt_callbacks.append(cb)
    _libxine.xine_event_create_listener_thread(queue, cb, user_data)

def xine_event_dispose_queue(queue):
    _libxine.xine_event_dispose_queue(queue)
    _evt_callbacks = []

def xine_get_pos_length(stream):
    _pos_stream = ctypes.c_int()
    _pos_time = ctypes.c_int()
    _length_time = ctypes.c_int()
    result = _libxine.xine_get_pos_length(stream, ctypes.byref(_pos_stream),
        ctypes.byref(_pos_time), ctypes.byref(_length_time))
    if result:
        return _pos_stream.value, _pos_time.value, _length_time.value
    else:
        return 0, 0, 0

XINE_LANG_MAX = 256

def xine_get_audio_lang(stream, channel):
    _lang = ctypes.create_string_buffer(XINE_LANG_MAX)

    result = _libxine.xine_get_audio_lang(stream, channel, _lang)
    if not result:
        _lang.raw = "unknown"

    return _lang.value

def xine_get_spu_lang(stream, channel):
    _lang = ctypes.create_string_buffer(XINE_LANG_MAX)

    result = _libxine.xine_get_spu_lang(stream, channel, _lang)
    if not result:
        _lang.raw = "unknown"

    return _lang.value

# vim: ts=4 sw=4 expandtab
