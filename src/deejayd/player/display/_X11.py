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

import sys
import ctypes

try:
    _libX11 = ctypes.cdll.LoadLibrary('libX11.so.6')
except (ImportError, OSError), e:
    raise ImportError, e

class XColor(ctypes.Structure):
    _fields_ = [
        ('pixel', ctypes.c_ulong),
        ('red', ctypes.c_ushort),
        ('green', ctypes.c_ushort),
        ('blue', ctypes.c_ushort),
        ('flags', ctypes.c_char),
        ('pad', ctypes.c_char),
        ]

class XSetWindowAttributes(ctypes.Structure):
    _fields_ = [
        ('background_pixmap', ctypes.c_ulong),
        ('background_pixel', ctypes.c_ulong),
        ('border_pixmap', ctypes.c_ulong),
        ('border_pixel', ctypes.c_ulong),
        ('bit_gravity', ctypes.c_int),
        ('win_gravity', ctypes.c_int),
        ('backing_store', ctypes.c_int),
        ('backing_planes', ctypes.c_ulong),
        ('backing_pixel', ctypes.c_ulong),
        ('save_under', ctypes.c_int),
        ('event_mask', ctypes.c_long),
        ('do_not_propagate_mask', ctypes.c_long),
        ('override_redirect', ctypes.c_int),
        ('colormap', ctypes.c_ulong),
        ('cursor', ctypes.c_ulong),
        ]

# custom declaration
MWM_HINTS_DECORATIONS   = (1L << 1)
PROP_MWM_HINTS_ELEMENTS = 5
class MWMHints(ctypes.Structure):
    _fields_ = [
        ('flags', ctypes.c_uint),
        ('functions', ctypes.c_uint),
        ('decorations', ctypes.c_uint),
        ('input_mode', ctypes.c_int),
        ('status', ctypes.c_uint),
        ]

# Property modes
PropModeReplace = 0
PropModePrepend = 1
PropModeAppend  = 2

# Window attributes for CreateWindow and ChangeWindowAttributes
CWOverrideRedirect = (1L<<9)

# Input Event Masks
KeyPressMask         = (1L<<0)
VisibilityChangeMask = (1L<<16)
StructureNotifyMask  = (1L<<17)
ExposureMask         = (1L<<15)
PropertyChangeMask   = (1L<<22)

# int XInitThreads()
_libX11.XInitThreads.restype = ctypes.c_int

# Display *XOpenDisplay(char *display_name)
_libX11.XOpenDisplay.restype = ctypes.c_void_p
_libX11.XOpenDisplay.argtypes = [ctypes.c_char_p]

# void XCloseDisplay(Display *display)
_libX11.XCloseDisplay.argtypes = [ctypes.c_void_p]

# void XLockDisplay(Display *display)
_libX11.XLockDisplay.argtypes = [ctypes.c_void_p]

# void XUnlockDisplay(Display *display)
_libX11.XUnlockDisplay.argtypes = [ctypes.c_void_p]

# int XDefaultScreen(Display *display)
_libX11.XDefaultScreen.restype = ctypes.c_int
_libX11.XDefaultScreen.argtypes = [ctypes.c_void_p]

# int XDisplayWidth(Display *display, int screen_number);
_libX11.XDisplayWidth.restype = ctypes.c_int
_libX11.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]

# int XDisplayWidthMM(Display *display, int screen_number);
_libX11.XDisplayWidthMM.restype = ctypes.c_int
_libX11.XDisplayWidthMM.argtypes = [ctypes.c_void_p, ctypes.c_int]

# int XDisplayHeight(Display *display, int screen_number);
_libX11.XDisplayHeight.restype = ctypes.c_int
_libX11.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]

# int XDisplayHeightMM(Display *display, int screen_number);
_libX11.XDisplayHeightMM.restype = ctypes.c_int
_libX11.XDisplayHeightMM.argtypes = [ctypes.c_void_p, ctypes.c_int]

# void XSync(Display *display, Bool discard)
_libX11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]

# Window XCreateWindow(Display *display, Window parent, int x, int y,
#                      uint width, uint height, uint border_width, int depth,
#                      uint class, Visual *visual, ulong valuemask,
#                      XSetWindowAttributes *attributes)
_libX11.XCreateWindow.restype = ctypes.c_ulong
_libX11.XCreateWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, \
                                  ctypes.c_int,\
                                  ctypes.c_int, ctypes.c_uint, ctypes.c_uint,\
                                  ctypes.c_uint, ctypes.c_int, ctypes.c_uint,\
                                  ctypes.c_void_p, ctypes.c_ulong,\
                                  ctypes.c_void_p]

# Window XCreateSimpleWindow(Display *display, Window parent, int x, int y,
#                            uint width, uint height, uint border_width,
#                            ulong border, ulong background)
_libX11.XCreateSimpleWindow.restype = ctypes.c_ulong
_libX11.XCreateSimpleWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
                                        ctypes.c_int, ctypes.c_int,\
                                        ctypes.c_uint, ctypes.c_uint,\
                                        ctypes.c_uint, ctypes.c_ulong,\
                                        ctypes.c_ulong]

# void XDestroyWindow(Display *display, Window w)
_libX11.XDestroyWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

# void XSelectInput(Display *display, Window w, long event_mask)
_libX11.XSelectInput.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_long]

# Window XDefaultRootWindow(Display *display)
_libX11.XDefaultRootWindow.restype = ctypes.c_ulong
_libX11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]

# void XMapRaised(Display *display, Window w)
_libX11.XMapRaised.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

# void XUnmapWindow(Display *display, Window w)
_libX11.XUnmapWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

# XResizeWindow(Display *display, Window w, uint width, uint height)
_libX11.XResizeWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_uint, ctypes.c_uint]

# XChangeProperty(Display *display, Window w, Atom property, Atom type,
#                 int format, int mode, uchar *data, int nelements)
_libX11.XChangeProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int, ctypes.c_int,\
    ctypes.c_char_p, ctypes.c_int]

# XChangeWindowAttributes(Display *display, Window w, ulong valuemask,
#                         XSetWindowAttributes *attributes)
_libX11.XChangeWindowAttributes.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_ulong, ctypes.POINTER(XSetWindowAttributes)]

# Atom XInternAtom(Display *display,char *atom_name, Bool only_if_exists)
_libX11.XInternAtom.restype = ctypes.c_ulong
_libX11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p,\
    ctypes.c_int]

# int XGetGeometry(Display *display, Drawable d, Window *root_return,
#                  int *x_return, int *y_return, uint *width_return,
#                  uint *height_return, uint *border_width_return,
#                  uint *depth_return)
_libX11.XGetGeometry.restype = ctypes.c_int
_libX11.XGetGeometry.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),\
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),\
    ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),\
    ctypes.POINTER(ctypes.c_uint)]

# XDefineCursor(Display *display, Window w, Cursor cursor)
_libX11.XDefineCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_ulong]

# XUndefineCursor(Display *display, Window w)
_libX11.XUndefineCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

# Cursor XCreatePixmapCursor(Display *display, Pixmap source, Pixmap mask,
#                            XColor *foreground_color,
#                            XColor *background_color, uint x, uint y)
_libX11.XCreatePixmapCursor.restype = ctypes.c_ulong
_libX11.XCreatePixmapCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_ulong, ctypes.POINTER(XColor),\
    ctypes.POINTER(XColor), ctypes.c_uint, ctypes.c_uint]

# XFreeCursor(Display *display, Cursor cursor)
_libX11.XFreeCursor.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

# Colormap XDefaultColormap(Display *display, int screen)
_libX11.XDefaultColormap.restype = ctypes.c_ulong
_libX11.XDefaultColormap.argtypes = [ctypes.c_void_p, ctypes.c_int]

# int XAllocNamedColor(Display *display, Colormap cmap, char *color_name,
#                  XColor *screen_def_return, XColor *exact_def_return)
_libX11.XAllocNamedColor.restype = ctypes.c_int
_libX11.XAllocNamedColor.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_char_p, ctypes.POINTER(XColor), ctypes.POINTER(XColor)]

# Pixmap XCreateBitmapFromData(Display *display, Drawable d, char *data,
#                              uint width, uint height)
_libX11.XCreateBitmapFromData.restype = ctypes.c_ulong
_libX11.XCreateBitmapFromData.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint]

# void XFreePixmap(Display *display, Pixmap p)
_libX11.XFreePixmap.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

# void XFreeColors(Display *display, Colormap colormap, ulong pixels[],
#                  int npixels, ulong planes))
_libX11.XFreeColors.argtypes = [ctypes.c_void_p, ctypes.c_ulong,\
    ctypes.POINTER(ctypes.c_ulong), ctypes.c_int, ctypes.c_ulong]

# copy functions from the library
module = sys.modules[__name__]
for name in dir(_libX11):
    if name.startswith('X'):
        setattr(module, name, getattr(_libX11, name))

def XGetGeometry(display, window):
    root = ctypes.c_ulong()
    x = ctypes.c_int()
    y = ctypes.c_int()
    width =ctypes. c_uint()
    height = ctypes.c_uint()
    border_width = ctypes.c_uint()
    depth = ctypes.c_uint()

    _libX11.XGetGeometry(display, window, ctypes.byref(root), ctypes.byref(x),\
        ctypes.byref(y), ctypes.byref(width), ctypes.byref(height),\
        ctypes.byref(border_width), ctypes.byref(depth))

    return x.value, y.value, width.value, height.value

def XSetNullCursor(display, screen, window):
    black = XColor()
    dummy = XColor()
    bitmap_struct = ctypes.c_char * 8
    bm_no_data = bitmap_struct('0', '0', '0', '0', '0', '0', '0', '0')

    cmap = XDefaultColormap(display, screen)
    XAllocNamedColor(display, cmap, "black", ctypes.byref(black),\
        ctypes.byref(dummy))
    bm_no = XCreateBitmapFromData(display, window, bm_no_data, 1, 1)
    no_ptr = XCreatePixmapCursor(display, bm_no, bm_no, ctypes.byref(black),\
        ctypes.byref(black), 0, 0)

    XDefineCursor(display, window, no_ptr)

    XFreeCursor(display, no_ptr)
    if bm_no != None:
        XFreePixmap(display, bm_no)
    pixel = ctypes.c_ulong(black.pixel)
    XFreeColors(display, cmap, ctypes.byref(pixel), 1, 0)

# vim: ts=4 sw=4 expandtab
