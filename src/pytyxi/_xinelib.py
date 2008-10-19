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


import sys, ctypes


try:
    _xinelib = ctypes.cdll.LoadLibrary('libxine.so.1')
except (ImportError, OSError), e:
    raise ImportError, e


# void xine_get_version (int *major, int *minor, int *sub)
_xinelib.xine_get_version.argstype = (ctypes.POINTER(ctypes.c_int),
                                      ctypes.POINTER(ctypes.c_int),
                                      ctypes.POINTER(ctypes.c_int),)

# int  xine_check_version (int major, int minor, int sub)
_xinelib.xine_check_version.argtypes = (ctypes.c_int, ctypes.c_int,
                                        ctypes.c_int)
_xinelib.xine_check_version.restype = ctypes.c_int

# char *xine_get_file_extensions (xine_t *self)
_xinelib.xine_get_file_extensions.argtypes = (ctypes.c_void_p, )
_xinelib.xine_get_file_extensions.restype = ctypes.c_char_p

# char *const *xine_list_input_plugins(xine_t *self)
_xinelib.xine_list_input_plugins.argtypes = (ctypes.c_void_p, )
_xinelib.xine_list_input_plugins.restype = ctypes.POINTER(ctypes.c_char_p)

# xine_t *xine_new (void)
_xinelib.xine_new.restype = ctypes.c_void_p

# void xine_config_load  (xine_t *self, const char *cfg_filename)
_xinelib.xine_config_load.argstype = (ctypes.c_void_p, ctypes.c_char_p)

# const char *xine_get_homedir(void)
_xinelib.xine_get_homedir.restype = ctypes.c_char_p

# void xine_init (xine_t *self)
_xinelib.xine_init.argstype = (ctypes.c_void_p, )

# void xine_exit (xine_t *self)
_xinelib.xine_exit.argstype = (ctypes.c_void_p, )

# void xine_engine_set_param(xine_t *self, int param, int value)
_xinelib.xine_engine_set_param.argstype = (ctypes.c_void_p,
                                           ctypes.c_int, ctypes.c_int, )

# xine_audio_port_t *xine_open_audio_driver (xine_t *self, const char *id,
#                       void *data)
_xinelib.xine_open_audio_driver.argstype = (ctypes.c_void_p,
                                            ctypes.c_char_p, ctypes.c_void_p, )
_xinelib.xine_open_audio_driver.restype = ctypes.c_void_p

# xine_video_port_t *xine_open_video_driver (xine_t *self, const char *id,
#                       int visual, void *data)
_xinelib.xine_open_video_driver.argstype = (ctypes.c_void_p,
                                            ctypes.c_char_p,
                                            ctypes.c_int, ctypes.c_void_p, )
_xinelib.xine_open_video_driver.restype = ctypes.c_void_p

# void xine_close_audio_driver (xine_t *self, xine_audio_port_t  *driver)
_xinelib.xine_close_audio_driver.argstype = (ctypes.c_void_p, ctypes.c_void_p, )

# void xine_close_video_driver (xine_t *self, xine_video_port_t  *driver)
_xinelib.xine_close_video_driver.argstype = (ctypes.c_void_p, ctypes.c_void_p, )

# int    xine_port_send_gui_data (xine_video_port_t *vo,
#                    int type, void *data)
_xinelib.xine_port_send_gui_data.argstype = (ctypes.c_void_p,
                                             ctypes.c_int, ctypes.c_void_p, )
_xinelib.xine_port_send_gui_data.restype = ctypes.c_int

# xine_stream_t *xine_stream_new (xine_t *self,
#                xine_audio_port_t *ao, xine_video_port_t *vo)
_xinelib.xine_stream_new.argstype = (ctypes.c_void_p,
                                     ctypes.c_void_p, ctypes.c_void_p,)
_xinelib.xine_stream_new.restype = ctypes.c_void_p

# int xine_open (xine_stream_t *stream, const char *mrl)
_xinelib.xine_open.argstype = (ctypes.c_void_p, ctypes.c_char_p, )
_xinelib.xine_open.restype = ctypes.c_int

# int  xine_play (xine_stream_t *stream, int start_pos, int start_time)
_xinelib.xine_play.argstype = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, )
_xinelib.xine_play.restype = ctypes.c_int

# void xine_stop (xine_stream_t *stream)
_xinelib.xine_stop.argstype = (ctypes.c_void_p, )

_xinelib.xine_usec_sleep.argtypes = (ctypes.c_int, )

# void xine_close (xine_stream_t *stream)
_xinelib.xine_close.argstype = (ctypes.c_void_p, )

# void xine_dispose (xine_stream_t *stream)
_xinelib.xine_dispose.argstype = (ctypes.c_void_p, )

class x11_visual_t(ctypes.Structure):
    _fields_ = (
        ('display', ctypes.c_void_p),
        ('screen', ctypes.c_int),
        ('d', ctypes.c_ulong), # Drawable
        ('user_data', ctypes.c_void_p),
        ('dest_size_cb', ctypes.c_void_p),
        ('frame_output_cb', ctypes.c_void_p),
        ('lock_display', ctypes.c_void_p),
        ('unlock_display', ctypes.c_void_p),
    )

# dest size callback
xine_dest_size_cb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
                     ctypes.c_int, ctypes.c_int, ctypes.c_double,
                     ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                     ctypes.POINTER(ctypes.c_double))

# frame output callback
xine_frame_output_cb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
                  ctypes.c_int, ctypes.c_int, ctypes.c_double,
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                  ctypes.POINTER(ctypes.c_double),
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

class xine_event_t(ctypes.Structure):
    _fields_ = (
        ('type', ctypes.c_int),
        ('stream', ctypes.c_void_p),
        ('data', ctypes.c_void_p),
        ('data_length', ctypes.c_int),
    )

class xine_ui_message_data_t(ctypes.Structure):
    _fields_ = (
        ('compatibility_num_buttons', ctypes.c_int),
        ('compatibility_str_len', ctypes.c_int),
        ('compatibility_str', 256 * ctypes.c_char),
        ('type', ctypes.c_int),
        ('explanation', ctypes.c_int),
        ('num_parameters', ctypes.c_int),
        ('parameters', ctypes.c_void_p),
        ('messages', ctypes.c_char),
    )

# event listener callback type
xine_event_listener_cb_t = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.POINTER(xine_event_t))

# void xine_event_create_listener_thread(xine_event_queue_t *queue,
#    xine_event_listener_cb_t callback,
#    void *user_data)
_xinelib.xine_event_create_listener_thread.argtypes = (ctypes.c_void_p,
                                                       ctypes.c_void_p,
                                                       ctypes.c_void_p)

# xine_event_queue_t *xine_event_new_queue(xine_stream_t *stream)
_xinelib.xine_event_new_queue.argtypes = (ctypes.c_void_p, )
_xinelib.xine_event_new_queue.restype = ctypes.c_void_p

# void xine_event_dispose_queue(xine_event_queue_t *queue)
_xinelib.xine_event_dispose_queue.argtypes = (ctypes.c_void_p, )

# void xine_set_param (xine_stream_t *stream, int param, int value)
_xinelib.xine_set_param.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)

# int xine_get_param (xine_stream_t *stream, int param)
_xinelib.xine_get_param.argtypes = (ctypes.c_void_p, ctypes.c_int)
_xinelib.xine_get_param.restype = ctypes.c_int

# char *xine_get_meta_info(xine_stream_t *stream, int info)
_xinelib.xine_get_meta_info.argtypes = (ctypes.c_void_p, ctypes.c_int)
_xinelib.xine_get_meta_info.restype = ctypes.c_char_p

# int xine_get_stream_info(xine_stream_t *stream, int info)
_xinelib.xine_get_stream_info.argtypes = (ctypes.c_void_p, ctypes.c_int)
_xinelib.xine_get_stream_info.restype = ctypes.c_int

# int xine_get_status (xine_stream_t *stream)
_xinelib.xine_get_status.argtypes = (ctypes.c_void_p, )
_xinelib.xine_get_status.restype = ctypes.c_int

# int xine_get_pos_length (xine_stream_t *stream, int *pos_stream,
#                          int *pos_time, int *length_time)
_xinelib.xine_get_pos_length.argtypes = (ctypes.c_void_p,
                                         ctypes.POINTER(ctypes.c_int),
                                         ctypes.POINTER(ctypes.c_int),
                                         ctypes.POINTER(ctypes.c_int))

# int xine_get_status (xine_stream_t *stream)
_xinelib.xine_get_status.argtypes = (ctypes.c_void_p, )
_xinelib.xine_get_status.restype = ctypes.c_int

# int xine_get_audio_lang(xine_stream_t *stream, int channel, char *lang)
_xinelib.xine_get_audio_lang.restype = ctypes.c_int
_xinelib.xine_get_audio_lang.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                         ctypes.c_char_p)

# int xine_get_spu_lang(xine_stream_t *stream, int channel, char *lang)
_xinelib.xine_get_spu_lang.restype = ctypes.c_int
_xinelib.xine_get_spu_lang.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                       ctypes.c_char_p)

# xine_osd_t *xine_osd_new(xine_stream_t *self, int x, int y,
#                          int width, int height)
_xinelib.xine_osd_new.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.c_int)
_xinelib.xine_osd_new.restype = ctypes.c_void_p

# void xine_osd_free(xine_osd_t *self)
_xinelib.xine_osd_free.argtypes = (ctypes.c_void_p, )

# uint32_t xine_osd_get_capabilities(xine_osd_t *self)
_xinelib.xine_osd_get_capabilities.restype = ctypes.c_int
_xinelib.xine_osd_get_capabilities.argtypes = (ctypes.c_void_p, )

# void xine_osd_set_text_palette(xine_osd_t *self,int palette_number,
#                                int color_base )
_xinelib.xine_osd_set_text_palette.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                               ctypes.c_int)

# int xine_osd_set_font(xine_osd_t *self, const char *fontname, int size)
_xinelib.xine_osd_set_font.restype = ctypes.c_int
_xinelib.xine_osd_set_font.argtypes = (ctypes.c_void_p, ctypes.c_char_p,
                                       ctypes.c_int)

# void xine_osd_set_position(xine_osd_t *self, int x, int y)
_xinelib.xine_osd_set_position.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                        ctypes.c_int)

# void xine_osd_draw_text(xine_osd_t *self, int x1, int y1, char *text,
#                         int color_base)
_xinelib.xine_osd_draw_text.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                        ctypes.c_int, ctypes.c_char_p,
                                        ctypes.c_int)

# void xine_osd_show(xine_osd_t *self, int64_t vpts)
_xinelib.xine_osd_show.argtypes = (ctypes.c_void_p, ctypes.c_int)

# void  xine_osd_show_unscaled (xine_osd_t *self, int64_t vpts)
_xinelib.xine_osd_show_unscaled.argtypes = (ctypes.c_void_p, ctypes.c_int)

# void  xine_osd_hide(xine_osd_t *self, int64_t vpts)
_xinelib.xine_osd_hide.argtypes = (ctypes.c_void_p, ctypes.c_int)

# void  xine_osd_clear(xine_osd_t *self)
_xinelib.xine_osd_clear.argtypes = (ctypes.c_void_p, )


# copy functions from the library
module = sys.modules[__name__]
for name in dir(_xinelib):
    if name.startswith('xine_'):
        setattr(module, name, getattr(_xinelib, name))


# vim: ts=4 sw=4 expandtab
