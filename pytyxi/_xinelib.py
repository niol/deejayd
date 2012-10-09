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


import sys, ctypes
from pytyx11._libX11 import Display


try:
    if sys.platform == 'linux2':
        _xinelib = ctypes.cdll.LoadLibrary('libxine.so.2')
    elif sys.platform == 'darwin':
        # FIXME: should find a means to configure path
        _xinelib = ctypes.cdll.LoadLibrary('/opt/local/lib/libxine.2.dylib')
except (ImportError, OSError), e:
    raise ImportError, e

#
# xine_t structure base definition
#
class xine_t(ctypes.Structure):
    pass

# void xine_get_version (int *major, int *minor, int *sub)
_xinelib.xine_get_version.argstype = (ctypes.POINTER(ctypes.c_int),
                                      ctypes.POINTER(ctypes.c_int),
                                      ctypes.POINTER(ctypes.c_int),)
_xinelib.xine_get_version.restype = None

# int  xine_check_version (int major, int minor, int sub)
_xinelib.xine_check_version.argtypes = (ctypes.c_int, ctypes.c_int,
                                        ctypes.c_int)

# char *xine_get_file_extensions (xine_t *self)
_xinelib.xine_get_file_extensions.argtypes = (ctypes.POINTER(xine_t), )
_xinelib.xine_get_file_extensions.restype = ctypes.c_char_p

# char *const *xine_list_input_plugins(xine_t *self)
_xinelib.xine_list_input_plugins.argtypes = (ctypes.POINTER(xine_t), )
_xinelib.xine_list_input_plugins.restype = ctypes.POINTER(ctypes.c_char_p)

# xine_t *xine_new (void)
_xinelib.xine_new.restype = ctypes.POINTER(xine_t)

# void xine_config_load  (xine_t *self, const char *cfg_filename)
_xinelib.xine_config_load.argstype = (ctypes.POINTER(xine_t), ctypes.c_char_p)
_xinelib.xine_config_load.restype = None

class xine_cfg_entry_t(ctypes.Structure):
    pass

# typedef void (*xine_config_cb_t) (void *user_data, xine_cfg_entry_t *entry);
xine_config_cb_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p,
                                    ctypes.POINTER(xine_cfg_entry_t))

xine_cfg_entry_t._fields_ = (
    ('key', ctypes.c_char_p),
    ('type', ctypes.c_int),
    ('exp_level', ctypes.c_int),
    ('unknown_value', ctypes.c_char_p),
    ('str_value', ctypes.c_char_p),
    ('str_default', ctypes.c_char_p),
    ('num_value', ctypes.c_int),
    ('num_default', ctypes.c_int),
    ('range_min', ctypes.c_int),
    ('range_max', ctypes.c_int),
    ('enum_values', ctypes.POINTER(ctypes.c_char_p)), # char **enum_values
    ('description', ctypes.c_char_p),
    ('help', ctypes.c_char_p),
    ('callback', xine_config_cb_t),
    ('callback_data', ctypes.c_void_p),
)

# int  xine_config_get_first_entry (xine_t *self, xine_cfg_entry_t *entry)
_xinelib.xine_config_get_first_entry.argstype = (ctypes.POINTER(xine_t),
                                             ctypes.POINTER(xine_cfg_entry_t), )

# int  xine_config_get_next_entry (xine_t *self, xine_cfg_entry_t *entry)
_xinelib.xine_config_get_next_entry.argstype = (ctypes.POINTER(xine_t),
                                             ctypes.POINTER(xine_cfg_entry_t), )

# int  xine_config_lookup_entry (xine_t *self, const char *key,
#                  xine_cfg_entry_t *entry)
_xinelib.xine_config_lookup_entry.argstype = (ctypes.POINTER(xine_t),
                                          ctypes.c_char_p,
                                          ctypes.POINTER(xine_cfg_entry_t), )

# void xine_config_update_entry (xine_t *self,
#                   const xine_cfg_entry_t *entry)
_xinelib.xine_config_update_entry.argstype = (ctypes.POINTER(xine_t),
                                          ctypes.POINTER(xine_cfg_entry_t), )
_xinelib.xine_config_update_entry.restype = None

# const char *xine_get_homedir(void)
_xinelib.xine_get_homedir.restype = ctypes.c_char_p

# void xine_init (xine_t *self)
_xinelib.xine_init.argstype = (ctypes.POINTER(xine_t), )
_xinelib.xine_init.restype = None

# void xine_exit (xine_t *self)
_xinelib.xine_exit.argstype = (ctypes.POINTER(xine_t), )
_xinelib.xine_exit.restype = None

# void xine_engine_set_param(xine_t *self, int param, int value)
_xinelib.xine_engine_set_param.argstype = (ctypes.POINTER(xine_t),
                                           ctypes.c_int, ctypes.c_int, )
_xinelib.xine_engine_set_param.restype = None

#
# xine_audio_port_t and xine_video_port_t structure base definition
#
class xine_audio_port_t(ctypes.Structure):
    pass
class xine_video_port_t(ctypes.Structure):
    pass
# xine_audio_port_t *xine_open_audio_driver (xine_t *self, const char *id,
#                       void *data)
_xinelib.xine_open_audio_driver.argstype = (ctypes.POINTER(xine_t),
                                            ctypes.c_char_p, ctypes.c_void_p, )
_xinelib.xine_open_audio_driver.restype = ctypes.POINTER(xine_audio_port_t)

# xine_video_port_t *xine_open_video_driver (xine_t *self, const char *id,
#                       int visual, void *data)
_xinelib.xine_open_video_driver.argstype = (ctypes.POINTER(xine_t),
                                            ctypes.c_char_p,
                                            ctypes.c_int, ctypes.c_void_p, )
_xinelib.xine_open_video_driver.restype = ctypes.POINTER(xine_video_port_t)

# void xine_close_audio_driver (xine_t *self, xine_audio_port_t  *driver)
_xinelib.xine_close_audio_driver.argstype = (ctypes.POINTER(xine_t),
                                             ctypes.POINTER(xine_audio_port_t),)
_xinelib.xine_close_audio_driver.restype = None

# void xine_close_video_driver (xine_t *self, xine_video_port_t  *driver)
_xinelib.xine_close_video_driver.argstype = (ctypes.POINTER(xine_t),
                                             ctypes.POINTER(xine_video_port_t),)
_xinelib.xine_close_video_driver.restype = None

# int    xine_port_send_gui_data (xine_video_port_t *vo,
#                    int type, void *data)
_xinelib.xine_port_send_gui_data.argstype = (ctypes.POINTER(xine_video_port_t),
                                             ctypes.c_int, ctypes.c_void_p, )


#
# Stream structure base definition
#
class xine_stream_t(ctypes.Structure):
    pass
# xine_stream_t *xine_stream_new (xine_t *self,
#                xine_audio_port_t *ao, xine_video_port_t *vo)
_xinelib.xine_stream_new.argstype = (ctypes.POINTER(xine_t),
                                     ctypes.POINTER(xine_audio_port_t),
                                     ctypes.POINTER(xine_video_port_t),)
_xinelib.xine_stream_new.restype = ctypes.POINTER(xine_stream_t)

# int xine_open (xine_stream_t *stream, const char *mrl)
_xinelib.xine_open.argstype = (ctypes.POINTER(xine_stream_t), ctypes.c_char_p, )

# int  xine_play (xine_stream_t *stream, int start_pos, int start_time)
_xinelib.xine_play.argstype = (ctypes.POINTER(xine_stream_t), ctypes.c_int,
                               ctypes.c_int, )

# void xine_stop (xine_stream_t *stream)
_xinelib.xine_stop.argstype = (ctypes.POINTER(xine_stream_t), )
_xinelib.xine_stop.restype = None

# void xine_usec_sleep (int usec)
_xinelib.xine_usec_sleep.argtypes = (ctypes.c_int, )
_xinelib.xine_usec_sleep.restype = None

# void xine_close (xine_stream_t *stream)
_xinelib.xine_close.argstype = (ctypes.POINTER(xine_stream_t), )
_xinelib.xine_close.restype = None

# void xine_dispose (xine_stream_t *stream)
_xinelib.xine_dispose.argstype = (ctypes.POINTER(xine_stream_t), )
_xinelib.xine_dispose.restype = None

# dest size callback
xine_dest_size_cb = ctypes.CFUNCTYPE(None, ctypes.c_void_p,
                     ctypes.c_int, ctypes.c_int, ctypes.c_double,
                     ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                     ctypes.POINTER(ctypes.c_double))

# frame output callback
xine_frame_output_cb = ctypes.CFUNCTYPE(None, ctypes.c_void_p,
                  ctypes.c_int, ctypes.c_int, ctypes.c_double,
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                  ctypes.POINTER(ctypes.c_double),
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

class x11_visual_t(ctypes.Structure):
    _fields_ = (
        ('display', ctypes.POINTER(Display)),
        ('screen', ctypes.c_int),
        ('d', ctypes.c_ulong), # Drawable
        ('user_data', ctypes.c_void_p),
        ('dest_size_cb', xine_dest_size_cb),
        ('frame_output_cb', xine_frame_output_cb),
        ('lock_display', ctypes.c_void_p),
        ('unlock_display', ctypes.c_void_p),
    )

# struct timeval from the GNU C Library <sys/time.h>
class timeval(ctypes.Structure):
    _fields_ = (
        ('tv_sec', ctypes.c_long),
        ('tv_usec', ctypes.c_long),
    )

class xine_event_t(ctypes.Structure):
    _fields_ = (
        ('stream', ctypes.POINTER(xine_stream_t)),
        ('data', ctypes.c_void_p),
        ('data_length', ctypes.c_int),
        ('type', ctypes.c_int),
        ('tv', timeval),
    )

class xine_ui_data_t(ctypes.Structure):
    _fields_ = (
        ('num_buttons', ctypes.c_int),
        ('str_len', ctypes.c_int),
        ('str', 256 * ctypes.c_char),
    )

class xine_ui_message_data_t(ctypes.Structure):
    _fields_ = (
        ('compatibility', xine_ui_data_t),
        ('type', ctypes.c_int),
        ('explanation', ctypes.c_int),
        ('num_parameters', ctypes.c_int),
        ('parameters', ctypes.c_int),
        ('messages', ctypes.c_char),
    )

# event listener callback type
xine_event_listener_cb_t = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.POINTER(xine_event_t))

# Opaque xine_event_queue_t structure
class xine_event_queue_t(ctypes.Structure):
    pass
# void xine_event_create_listener_thread(xine_event_queue_t *queue,
#    xine_event_listener_cb_t callback,
#    void *user_data)
_xinelib.xine_event_create_listener_thread.argtypes = (\
                                       ctypes.POINTER(xine_event_queue_t),
                                       ctypes.c_void_p,
                                       ctypes.c_void_p)
_xinelib.xine_event_create_listener_thread.restype = None

# xine_event_queue_t *xine_event_new_queue(xine_stream_t *stream)
_xinelib.xine_event_new_queue.argtypes = (ctypes.POINTER(xine_stream_t), )
_xinelib.xine_event_new_queue.restype = ctypes.POINTER(xine_event_queue_t)

# void xine_event_dispose_queue(xine_event_queue_t *queue)
_xinelib.xine_event_dispose_queue.argtypes = \
        (ctypes.POINTER(xine_event_queue_t), )
_xinelib.xine_event_dispose_queue.restype = None

# void xine_set_param (xine_stream_t *stream, int param, int value)
_xinelib.xine_set_param.argtypes = (ctypes.POINTER(xine_stream_t),
                                    ctypes.c_int, ctypes.c_int)
_xinelib.xine_set_param.restype = None

# int xine_get_param (xine_stream_t *stream, int param)
_xinelib.xine_get_param.argtypes = (ctypes.POINTER(xine_stream_t), ctypes.c_int)

# char *xine_get_meta_info(xine_stream_t *stream, int info)
_xinelib.xine_get_meta_info.argtypes = (ctypes.POINTER(xine_stream_t),
                                        ctypes.c_int)
_xinelib.xine_get_meta_info.restype = ctypes.c_char_p

# int xine_get_stream_info(xine_stream_t *stream, int info)
_xinelib.xine_get_stream_info.argtypes = (ctypes.POINTER(xine_stream_t),
                                          ctypes.c_int)

# int xine_get_status (xine_stream_t *stream)
_xinelib.xine_get_status.argtypes = (ctypes.POINTER(xine_stream_t), )

# int xine_get_pos_length (xine_stream_t *stream, int *pos_stream,
#                          int *pos_time, int *length_time)
_xinelib.xine_get_pos_length.argtypes = (ctypes.POINTER(xine_stream_t),
                                         ctypes.POINTER(ctypes.c_int),
                                         ctypes.POINTER(ctypes.c_int),
                                         ctypes.POINTER(ctypes.c_int))

# int xine_get_audio_lang(xine_stream_t *stream, int channel, char *lang)
_xinelib.xine_get_audio_lang.argtypes = (ctypes.POINTER(xine_stream_t),
                                         ctypes.c_int, ctypes.c_char_p)

# int xine_get_spu_lang(xine_stream_t *stream, int channel, char *lang)
_xinelib.xine_get_spu_lang.argtypes = (ctypes.POINTER(xine_stream_t),
                                       ctypes.c_int, ctypes.c_char_p)

# Opaque xine_osd_t structure definition
class xine_osd_t(ctypes.Structure):
    pass
# xine_osd_t *xine_osd_new(xine_stream_t *self, int x, int y,
#                          int width, int height)
_xinelib.xine_osd_new.argtypes = (ctypes.POINTER(xine_stream_t),
                                  ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.c_int)
_xinelib.xine_osd_new.restype = ctypes.POINTER(xine_osd_t)

# void xine_osd_free(xine_osd_t *self)
_xinelib.xine_osd_free.argtypes = (ctypes.POINTER(xine_osd_t), )
_xinelib.xine_osd_free.restype = None

# uint32_t xine_osd_get_capabilities(xine_osd_t *self)
_xinelib.xine_osd_get_capabilities.argtypes = (ctypes.POINTER(xine_osd_t), )
_xinelib.xine_osd_get_capabilities.restype = ctypes.c_uint

# void xine_osd_set_text_palette(xine_osd_t *self,int palette_number,
#                                int color_base )
_xinelib.xine_osd_set_text_palette.argtypes = (ctypes.POINTER(xine_osd_t),
                                               ctypes.c_int, ctypes.c_int)

# int xine_osd_set_font(xine_osd_t *self, const char *fontname, int size)
_xinelib.xine_osd_set_font.argtypes = (ctypes.POINTER(xine_osd_t),
                                       ctypes.c_char_p, ctypes.c_int)

# void xine_osd_set_position(xine_osd_t *self, int x, int y)
_xinelib.xine_osd_set_position.argtypes = (ctypes.POINTER(xine_osd_t),
                                           ctypes.c_int, ctypes.c_int)
_xinelib.xine_osd_set_position.restype = None

# void xine_osd_draw_text(xine_osd_t *self, int x1, int y1, char *text,
#                         int color_base)
_xinelib.xine_osd_draw_text.argtypes = (ctypes.POINTER(xine_osd_t),
                                        ctypes.c_int,
                                        ctypes.c_int, ctypes.c_char_p,
                                        ctypes.c_int)
_xinelib.xine_osd_draw_text.restype = None

# void xine_osd_show(xine_osd_t *self, int64_t vpts)
_xinelib.xine_osd_show.argtypes = (ctypes.POINTER(xine_osd_t), ctypes.c_int)
_xinelib.xine_osd_show.restype = None

# void  xine_osd_show_unscaled (xine_osd_t *self, int64_t vpts)
_xinelib.xine_osd_show_unscaled.argtypes = (ctypes.POINTER(xine_osd_t),
                                            ctypes.c_int)
_xinelib.xine_osd_show_unscaled.restype = None

# void  xine_osd_hide(xine_osd_t *self, int64_t vpts)
_xinelib.xine_osd_hide.argtypes = (ctypes.POINTER(xine_osd_t), ctypes.c_int)
_xinelib.xine_osd_hide.restype = None

# void  xine_osd_clear(xine_osd_t *self)
_xinelib.xine_osd_clear.argtypes = (ctypes.POINTER(xine_osd_t), )
_xinelib.xine_osd_clear.restype = None


# copy functions from the library
module = sys.modules[__name__]
for name in dir(_xinelib):
    if name.startswith('xine_'):
        setattr(module, name, getattr(_xinelib, name))


# vim: ts=4 sw=4 expandtab
