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

import ctypes
from pytyx11._libX11 import Display
from ctypes.util import find_library


glx = find_library('GL')
if glx is not None:
    _libGLX = ctypes.cdll.LoadLibrary(glx)
else:
    raise ImportError('Could not load GL shared library.')


# XVisualInfo base class definition
class XVisualInfo(ctypes.Structure):
    pass


class GLEnabled(ctypes.c_int):
    GL_FALSE = 0
    GL_TRUE = 1


class GLXAttr(ctypes.c_int):
    GLX_USE_GL = 1
    GLX_BUFFER_SIZE = 2
    GLX_LEVEL = 3
    GLX_RGBA = 4
    GLX_DOUBLEBUFFER = 5
    GLX_STEREO = 6
    GLX_AUX_BUFFERS = 7
    GLX_RED_SIZE = 8
    GLX_GREEN_SIZE = 9
    GLX_BLUE_SIZE = 10
    GLX_ALPHA_SIZE = 11
    GLX_DEPTH_SIZE = 12
    GLX_STENCIL_SIZE = 13
    GLX_ACCUM_RED_SIZE = 14
    GLX_ACCUM_GREEN_SIZE = 15
    GLX_ACCUM_BLUE_SIZE = 16
    GLX_ACCUM_ALPHA_SIZE = 17


# XVisualInfo* glXChooseVisual(Display * dpy,  int screen,  int *attribList);
_libGLX.glXChooseVisual.restype = ctypes.POINTER(XVisualInfo)
_libGLX.glXChooseVisual.argtypes = (ctypes.POINTER(Display), ctypes.c_int, 
                                    ctypes.POINTER(ctypes.c_int))

# GLXContext glXCreateContext(Display * dpy, XVisualInfo * vis,
#                             GLXContext shareList, Bool direct);
_libGLX.glXCreateContext.restype = ctypes.c_void_p
_libGLX.glXCreateContext.argtypes = (ctypes.POINTER(Display),
                                     ctypes.POINTER(XVisualInfo),
                                     ctypes.c_void_p, ctypes.c_int)

# void glXDestroyContext(Display *  dpy, GLXContext  ctx)
_libGLX.glXDestroyContext.restype = None
_libGLX.glXDestroyContext.argtypes = (ctypes.POINTER(Display), ctypes.c_void_p)

# Bool glXMakeCurrent(Display * dpy, GLXDrawable drawable, GLXContext ctx)
_libGLX.glXMakeCurrent.restype = ctypes.c_bool
_libGLX.glXMakeCurrent.argtypes = (ctypes.POINTER(Display),
                                   ctypes.c_ulong, ctypes.c_void_p)


def attach_opengl_context(dpy, wid):
    attrs = [
        GLXAttr.GLX_RGBA, True,
        GLXAttr.GLX_RED_SIZE, 1,
        GLXAttr.GLX_GREEN_SIZE, 1,
        GLXAttr.GLX_BLUE_SIZE, 1,
        GLXAttr.GLX_DOUBLEBUFFER, 0,
        0, 0
    ]
    cattrs = (ctypes.c_int * len(attrs))(*attrs)
    vi = _libGLX.glXChooseVisual(dpy.display_p(), 
                                 dpy.get_default_screen_number(), 
                                 cattrs)

    ctx = _libGLX.glXCreateContext(dpy.display_p(), vi, None, 
                                   GLEnabled.GL_TRUE)
    _libGLX.glXMakeCurrent(dpy.display_p(), wid, ctx)
    return ctx


def destroy_opengl_context(dpy, ctx):
    _libGLX.glXDestroyContext(dpy.display_p(), ctx)
