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
# This work is based on the perl X11::FullScreen API.
# http://search.cpan.org/~stephen/X11-FullScreen-0.03/


import ctypes
import _libX11 as libX11
import _libXext as libXext


class X11Error(Exception): pass


class X11Event:
    NoEventMask              = 0L
    KeyPressMask             = (1L<<0)
    KeyReleaseMask           = (1L<<1)
    ButtonPressMask          = (1L<<2)
    ButtonReleaseMask        = (1L<<3)
    EnterWindowMask          = (1L<<4)
    LeaveWindowMask          = (1L<<5)
    PointerMotionMask        = (1L<<6)
    PointerMotionHintMask    = (1L<<7)
    Button1MotionMask        = (1L<<8)
    Button2MotionMask        = (1L<<9)
    Button3MotionMask        = (1L<<10)
    Button4MotionMask        = (1L<<11)
    Button5MotionMask        = (1L<<12)
    ButtonMotionMask         = (1L<<13)
    KeymapStateMask          = (1L<<14)
    ExposureMask             = (1L<<15)
    VisibilityChangeMask     = (1L<<16)
    StructureNotifyMask      = (1L<<17)
    ResizeRedirectMask       = (1L<<18)
    SubstructureNotifyMask   = (1L<<19)
    SubstructureRedirectMask = (1L<<20)
    FocusChangeMask          = (1L<<21)
    PropertyChangeMask       = (1L<<22)
    ColormapChangeMask       = (1L<<23)
    OwnerGrabButtonMask      = (1L<<24)


class X11Window(object):

    def __init__(self, display, width=None, height=None, fullscreen=False):
        self.__display = display
        self.__display_p = self.__display.display_p()

        libX11.XLockDisplay(self.__display_p)

        if fullscreen:
            self.__always_fulscreen = True
            self.__fullscreen = True
            self.width = self.__display.get_width()
            self.height = self.__display.get_height()
        elif width and height:
            self.__always_fulscreen = False
            self.__fullscreen = False
            self.width = width
            self.height = height
        elif not width and not height and not fullscreen:
            raise X11Error('A window is either fullscreen or has dimensions.')

        self.__window_p = libX11.XCreateSimpleWindow(self.__display_p,
                   libX11.XDefaultRootWindow(self.__display_p),
                   0, 0, self.width, self.height, 0, 0, 0)

        self.__hide_cursor()
        if self.__fullscreen:
            self.__remove_decorations()

        libX11.XSelectInput(self.__display_p, self.__window_p,
                            (X11Event.ExposureMask |\
                             X11Event.ButtonPressMask |\
                             X11Event.KeyPressMask |\
                             X11Event.ButtonMotionMask |\
                             X11Event.StructureNotifyMask |\
                             X11Event.PropertyChangeMask |\
                             X11Event.PointerMotionMask))
        libX11.XMapRaised(self.__display_p, self.__window_p)
        libX11.XSync(self.__display_p, False)
        libX11.XUnlockDisplay(self.__display_p)

        self.video_area_info = {}
        self.update_video_area_info()

    def window_p(self):
        return self.__window_p

    def __remove_decorations(self):
        mwmhints = libX11.MWMHints()
        mwmhints.decorations = 0
        mwmhints.flags = libX11.MWMHints.MWM_HINTS_DECORATIONS
        data = ctypes.cast(ctypes.byref(mwmhints), ctypes.c_char_p)
        xa_no_border = libX11.XInternAtom(self.__display_p,
                                          "_MOTIF_WM_HINTS",
                                          False)
        libX11.XChangeProperty(self.__display_p, self.__window_p,
                               xa_no_border, xa_no_border,
                               32, libX11.PropertyModes.PropModeReplace, data,
                               libX11.MWMHints.PROP_MWM_HINTS_ELEMENTS)

    def __ignore_wm(self):
        attr = libX11.XSetWindowAttributes()
        attr.override_redirect = True
        libX11.XChangeWindowAttributes(self.__display_p, self.__window_p,
                                       libX11.CWOverrideRedirect)

    def __hide_cursor(self):
        black = libX11.XColor()
        dummy = libX11.XColor()
        bitmap_struct = ctypes.c_char * 8
        bm_no_data = bitmap_struct('0', '0', '0', '0', '0', '0', '0', '0')

        cmap = libX11.XDefaultColormap(self.__display_p,
                                   self.__display.get_default_screen_number())
        libX11.XAllocNamedColor(self.__display_p, cmap, "black",
                                ctypes.byref(black), ctypes.byref(dummy))

        bm_no = libX11.XCreateBitmapFromData(self.__display_p,
                                             self.__window_p,
                                             bm_no_data, 1, 1)
        no_ptr = libX11.XCreatePixmapCursor(self.__display_p,
                                            bm_no, bm_no,
                                            ctypes.byref(black),
                                            ctypes.byref(black),
                                            0, 0)
        libX11.XDefineCursor(self.__display_p, self.__window_p, no_ptr)

        libX11.XFreeCursor(self.__display_p, no_ptr)

        if bm_no != None:
            libX11.XFreePixmap(self.__display_p, bm_no)

        pixel = ctypes.c_ulong(black.pixel)
        libX11.XFreeColors(self.__display_p, cmap, ctypes.byref(pixel), 1, 0)

    def get_geometry(self):
        root = ctypes.c_ulong()
        x = ctypes.c_int()
        y = ctypes.c_int()
        width =ctypes. c_uint()
        height = ctypes.c_uint()
        border_width = ctypes.c_uint()
        depth = ctypes.c_uint()

        libX11.XGetGeometry(self.__display_p, self.__window_p,
                            ctypes.byref(root),
                            ctypes.byref(x), ctypes.byref(y),
                            ctypes.byref(width), ctypes.byref(height),
                            ctypes.byref(border_width), ctypes.byref(depth))

        return x.value, y.value, width.value, height.value

    def update_video_area_info(self):
        # FIXME : This should be called when the window is resized.
        x, y, w, h = self.get_geometry()
        self.video_area_info['win_x'] = x
        self.video_area_info['win_y'] = y
        self.video_area_info['width'] = w
        self.video_area_info['height'] = h
        self.video_area_info['aspect'] = self.__display.get_pixel_aspect()

    def set_fullscreen(self, fson=True):
        if fson == self.__fulscreen or self.__always_fulscreen:
            return

        libX11.XLockDisplay(self.__display_p)
        if fson:
            new_width = self.__display.get_width()
            new_height = self.__display.get_height()
            self.__remove_decorations()
            self.__fulscreen = True
        else:
            new_width = self.width
            new_height = self.height
            self.__fulscreen = False
        libX11.XResizeWindow(self.__display_p, self.__window_p,
                             new_width, new_height)
        libX11.XUnlockDisplay(self.__display_p)
        self.update_video_area_info()

    def show(self, do_show=True):
        libX11.XLockDisplay(self.__display_p)
        if do_show:
            libX11.XMapRaised(self.__display_p, self.__window_p)
        else:
            libX11.XUnmapWindow(self.__display_p, self.__window_p)
        libX11.XUnlockDisplay(self.__display_p)

    def close(self):
        libX11.XLockDisplay(self.__display_p)
        libX11.XUnmapWindow(self.__display_p, self.__window_p)
        libX11.XDestroyWindow(self.__display_p, self.__window_p)
        libX11.XUnlockDisplay(self.__display_p)

        self.video_area_info = None

class X11Display(object):

    def __init__(self, id=':0.0'):
        self.id = id

        if not libX11.XInitThreads():
            raise X11Error('Could not init threads')

        self.__display_p = libX11.XOpenDisplay(self.id)
        if not self.__display_p:
            raise X11Error('Could not open display %s' % self.id)

        self.__dpms_orig = self.is_dpms_on()

    def display_p(self):
        return self.__display_p

    def get_default_screen_number(self):
        return libX11.XDefaultScreen(self.__display_p)

    def get_width(self, screen_number=None):
        if not screen_number:
            screen_number = self.get_default_screen_number()
        return libX11.XDisplayWidth(self.__display_p, screen_number)

    def get_height(self, screen_number=None):
        if not screen_number:
            screen_number = self.get_default_screen_number()
        return libX11.XDisplayHeight(self.__display_p, screen_number)

    def get_pixel_aspect(self, screen_number=None):
        if not screen_number:
            screen_number = self.get_default_screen_number()

        res_h = float(self.get_width(screen_number) * 1000 /\
                      libX11.XDisplayWidth(self.__display_p, screen_number))
        res_v = float(self.get_height(screen_number) * 1000 /\
                      libX11.XDisplayHeight(self.__display_p, screen_number))
        return res_v / res_h

    def is_dpms_on(self):
        dummy = ctypes.c_int()
        if libXext.DPMSQueryExtension(self.__display_p,
                                      ctypes.byref(dummy), ctypes.byref(dummy)):
            return True
        else:
            return False

    def set_dpms(self, activated):
        if self.is_dpms_on():
            if activated:
                libXext.DPMSEnable(self.__display_p)
            else:
                libXext.DPMSDisable(self.__display_p)

    def do_create_window(self, width=None, height=None, fullscreen=False):
        return X11Window(self, width, height, fullscreen)

    def destroy(self):
        self.set_dpms(self.__dpms_orig)
        libX11.XCloseDisplay(self.__display_p)


if __name__ == '__main__':
    import time
    d = X11Display()
    w = d.do_create_window(320, 200)
    time.sleep(5)
    w.close()
    d.destroy()


# vim: ts=4 sw=4 expandtab
