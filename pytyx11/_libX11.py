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

import sys
import ctypes


lib = ctypes.util.find_library('X11')
if lib is not None:
    _libX11 = ctypes.cdll.LoadLibrary(lib)
else:
    raise ImportError('Could not load X11 shared library.')


# int XInitThreads()
_libX11.XInitThreads.restype = ctypes.c_int

# Display base class definition
class Display(ctypes.Structure):
    pass

# Display *XOpenDisplay(char *display_name)
_libX11.XOpenDisplay.restype = ctypes.POINTER(Display)
_libX11.XOpenDisplay.argtypes = (ctypes.c_char_p, )

# int XDefaultScreen(Display *display)
_libX11.XDefaultScreen.restype = ctypes.c_int
_libX11.XDefaultScreen.argtypes = (ctypes.POINTER(Display),)

# int XDisplayWidth(Display *display, int screen_number);
_libX11.XDisplayWidth.restype = ctypes.c_int
_libX11.XDisplayWidth.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# int XDisplayHeight(Display *display, int screen_number);
_libX11.XDisplayHeight.restype = ctypes.c_int
_libX11.XDisplayHeight.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# int XDisplayWidthMM(Display *display, int screen_number);
_libX11.XDisplayWidthMM.restype = ctypes.c_int
_libX11.XDisplayWidthMM.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# int XDisplayHeightMM(Display *display, int screen_number);
_libX11.XDisplayHeightMM.restype = ctypes.c_int
_libX11.XDisplayHeightMM.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# void XCloseDisplay(Display *display)
_libX11.XCloseDisplay.restype = None
_libX11.XCloseDisplay.argtypes = (ctypes.POINTER(Display), )

# void XLockDisplay(Display *display)
_libX11.XLockDisplay.restype = None
_libX11.XLockDisplay.argtypes = (ctypes.POINTER(Display), )

# void XUnlockDisplay(Display *display)
_libX11.XUnlockDisplay.restype = None
_libX11.XUnlockDisplay.argtypes = (ctypes.POINTER(Display), )

# Window XDefaultRootWindow(Display *display)
_libX11.XDefaultRootWindow.restype = ctypes.c_ulong
_libX11.XDefaultRootWindow.argtypes = (ctypes.POINTER(Display), )

# Window XCreateSimpleWindow(Display *display, Window parent, int x, int y,
#                            uint width, uint height, uint border_width,
#                            ulong border, ulong background)
_libX11.XCreateSimpleWindow.restype = ctypes.c_ulong
_libX11.XCreateSimpleWindow.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
                                        ctypes.c_int, ctypes.c_int,
                                        ctypes.c_uint, ctypes.c_uint,
                                        ctypes.c_uint, ctypes.c_ulong,
                                        ctypes.c_ulong)

# void XMapRaised(Display *display, Window w)
_libX11.XMapRaised.restype = None
_libX11.XMapRaised.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong)

# void XUnmapWindow(Display *display, Window w)
_libX11.XUnmapWindow.restype = None
_libX11.XUnmapWindow.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong)

# void XSelectInput(Display *display, Window w, long event_mask)
_libX11.XSelectInput.restype = None
_libX11.XSelectInput.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
                                 ctypes.c_long)

# int XGetGeometry(Display *display, Drawable d, Window *root_return,
#                  int *x_return, int *y_return, uint *width_return,
#                  uint *height_return, uint *border_width_return,
#                  uint *depth_return)
_libX11.XGetGeometry.restype = ctypes.c_int
_libX11.XGetGeometry.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint))

# void XSync(Display *display, Bool discard)
_libX11.XSync.restype = None
_libX11.XSync.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# void XDestroyWindow(Display *display, Window w)
_libX11.XDestroyWindow.restype = None
_libX11.XDestroyWindow.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong)

class XColor(ctypes.Structure):
    _fields_ = (
                 ('pixel', ctypes.c_ulong),
                 ('red', ctypes.c_ushort),
                 ('green', ctypes.c_ushort),
                 ('blue', ctypes.c_ushort),
                 ('flags', ctypes.c_char),
                 ('pad', ctypes.c_char),
               )

class MWMHints(ctypes.Structure):
    MWM_HINTS_DECORATIONS   = (1L << 1)
    PROP_MWM_HINTS_ELEMENTS = 5

    _fields_ = (
                 ('flags', ctypes.c_uint),
                 ('functions', ctypes.c_uint),
                 ('decorations', ctypes.c_uint),
                 ('input_mode', ctypes.c_int),
                 ('status', ctypes.c_uint),
               )

# Atom XInternAtom(Display *display,char *atom_name, Bool only_if_exists)
_libX11.XInternAtom.restype = ctypes.c_ulong
_libX11.XInternAtom.argtypes = (ctypes.POINTER(Display),
                                ctypes.c_char_p, ctypes.c_int)

# XChangeProperty(Display *display, Window w, Atom property, Atom type,
#                 int format, int mode, uchar *data, int nelements)
_libX11.XChangeProperty.restype = None
_libX11.XChangeProperty.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
                                    ctypes.c_ulong, ctypes.c_ulong,
                                    ctypes.c_int, ctypes.c_int,
                                    ctypes.c_char_p, ctypes.c_int)

class PropertyModes:
    PropModeReplace = 0
    PropModePrepend = 1
    PropModeAppend = 2

class XSetWindowAttributes(ctypes.Structure):
    _fields_ = (
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
               )

# XChangeWindowAttributes(Display *display, Window w, ulong valuemask,
#                         XSetWindowAttributes *attributes)
_libX11.XChangeWindowAttributes.restype = None
_libX11.XChangeWindowAttributes.argtypes = (ctypes.POINTER(Display),
                                    ctypes.c_ulong, ctypes.c_ulong,
                                    ctypes.POINTER(XSetWindowAttributes))

CWOverrideRedirect = (1L<<9)

# Colormap XDefaultColormap(Display *display, int screen)
_libX11.XDefaultColormap.restype = ctypes.c_ulong
_libX11.XDefaultColormap.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# int XAllocNamedColor(Display *display, Colormap cmap, char *color_name,
#                      XColor *screen_def_return, XColor *exact_def_return)
_libX11.XAllocNamedColor.restype = ctypes.c_int
_libX11.XAllocNamedColor.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
                                     ctypes.c_char_p, ctypes.POINTER(XColor),
                                     ctypes.POINTER(XColor))

# XDefineCursor(Display *display, Window w, Cursor cursor)
_libX11.XDefineCursor.restype = None
_libX11.XDefineCursor.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
                                  ctypes.c_ulong)

# XUndefineCursor(Display *display, Window w)
_libX11.XUndefineCursor.restype = None
_libX11.XUndefineCursor.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong)

# Cursor XCreatePixmapCursor(Display *display, Pixmap source, Pixmap mask,
#                            XColor *foreground_color,
#                            XColor *background_color, uint x, uint y)
_libX11.XCreatePixmapCursor.restype = ctypes.c_ulong
_libX11.XCreatePixmapCursor.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
    ctypes.c_ulong, ctypes.POINTER(XColor),
    ctypes.POINTER(XColor), ctypes.c_uint, ctypes.c_uint)

# XFreeCursor(Display *display, Cursor cursor)
_libX11.XFreeCursor.restype = None
_libX11.XFreeCursor.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong)

# Colormap XDefaultColormap(Display *display, int screen)
_libX11.XDefaultColormap.restype = ctypes.c_ulong
_libX11.XDefaultColormap.argtypes = (ctypes.POINTER(Display), ctypes.c_int)

# int XAllocNamedColor(Display *display, Colormap cmap, char *color_name,
#                  XColor *screen_def_return, XColor *exact_def_return)
_libX11.XAllocNamedColor.restype = ctypes.c_int
_libX11.XAllocNamedColor.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
    ctypes.c_char_p, ctypes.POINTER(XColor), ctypes.POINTER(XColor))

# Pixmap XCreateBitmapFromData(Display *display, Drawable d, char *data,
#                              uint width, uint height)
_libX11.XCreateBitmapFromData.restype = ctypes.c_ulong
_libX11.XCreateBitmapFromData.argtypes = (ctypes.POINTER(Display),
                                          ctypes.c_ulong, ctypes.c_char_p,
                                          ctypes.c_uint, ctypes.c_uint)

# void XFreePixmap(Display *display, Pixmap p)
_libX11.XFreePixmap.restype = None
_libX11.XFreePixmap.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong)

# void XFreeColors(Display *display, Colormap colormap, ulong pixels[],
#                  int npixels, ulong planes))
_libX11.XFreeColors.restype = None
_libX11.XFreeColors.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_ulong), ctypes.c_int, ctypes.c_ulong)

# XResizeWindow(Display *display, Window w, uint width, uint height)
_libX11.XResizeWindow.restype = None
_libX11.XResizeWindow.argtypes = (ctypes.POINTER(Display), ctypes.c_ulong,
                                  ctypes.c_uint, ctypes.c_uint)


# copy functions from the library
module = sys.modules[__name__]
for name in dir(_libX11):
    if name.startswith('X'):
        setattr(module, name, getattr(_libX11, name))


# vim: ts=4 sw=4 expandtab
