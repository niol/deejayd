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

import threading
from ctypes import byref, cast, c_char_p, pointer, c_int
from deejayd.player.display._X11 import *

class X11Error(Exception): pass

class X11Display:

    def __init__(self, opts, fullscreen):
        self.__dsp_name = opts["display"]
        self.__fullscreen = fullscreen
        if not XInitThreads():
            raise X11Error("Unable to init X Threads")

        # init options
        self.__lock = threading.Lock()
        self.infos = None
        self.video_area = None

    def create(self):
        self.infos = {}
        self.video_area = {}
        # open display
        self.infos['dsp'] = XOpenDisplay(self.__dsp_name)
        if not self.infos['dsp']:
            raise X11Error("Unable to open display %s" % self.__dsp_name)

        # calculate screen pixel aspect
        screen = XDefaultScreen(self.infos['dsp'])
        screen_width = float(XDisplayWidth(self.infos['dsp'], screen)*1000)/\
            float(XDisplayWidthMM(self.infos['dsp'], screen))
        screen_height = float(XDisplayHeight(self.infos['dsp'], screen)*1000)/\
            float(XDisplayHeightMM(self.infos['dsp'], screen))
        self.video_area["pixel_aspect"] = screen_height / screen_width

        if self.__fullscreen:
            width = XDisplayWidth(self.infos['dsp'], screen)
            height = XDisplayHeight(self.infos['dsp'], screen)
        else:
            width = 320
            height = 200

        # create window
        root_window = XDefaultRootWindow(self.infos['dsp'])
        self.infos["window"] = XCreateSimpleWindow(self.infos['dsp'],\
            root_window, 0, 0, width, height, 1, 0, 0)
        self.infos["screen"] = screen

        # hide cursor
        XSetNullCursor(self.infos['dsp'], self.infos['screen'],\
            self.infos['window'])

        # remove window decoration
        mwmhints = MWMHints()
        mwmhints.decorations = 0
        mwmhints.flags = MWM_HINTS_DECORATIONS
        data = cast(byref(mwmhints), c_char_p)
        XA_NO_BORDER = XInternAtom(self.infos['dsp'], "_MOTIF_WM_HINTS", False)
        XChangeProperty(self.infos['dsp'], self.infos['window'],\
            XA_NO_BORDER, XA_NO_BORDER, 32, PropModeReplace, data,\
            PROP_MWM_HINTS_ELEMENTS)

        # do not manage this window with the WM
        attr = XSetWindowAttributes()
        attr.override_redirect = True
        XChangeWindowAttributes(self.infos['dsp'], self.infos["window"],\
            CWOverrideRedirect, byref(attr))

        # update video area
        self.__update_video_area()

        self.set_dpms(False)

    def destroy(self):
        if not self.infos:
            return
        # destroy windows
        XLockDisplay(self.infos['dsp'])
        XUnmapWindow(self.infos['dsp'], self.infos["window"])
        XDestroyWindow(self.infos['dsp'], self.infos["window"])
        XSync(self.infos['dsp'], False)
        XUnlockDisplay(self.infos['dsp'])

        self.set_dpms(True)

        # close display
        XCloseDisplay(self.infos['dsp'])

        # reset options
        self.infos = None
        self.video_area = None

    def show(self, do_show = True):
        """ show/hide window """
        if not self.infos:
            raise X11Error("No window exists")
        XLockDisplay(self.infos['dsp'])
        if do_show:
            XMapRaised(self.infos['dsp'], self.infos["window"])
        else:
            XUnmapWindow(self.infos['dsp'], self.infos["window"])
        XSync(self.infos['dsp'], False)
        XUnlockDisplay(self.infos['dsp'])

    def get_infos(self):
        return self.infos

    def get_and_lock_video_area(self):
        self.__lock.acquire()
        return self.video_area

    def release_video_area(self):
        self.__lock.release()

    def __update_video_area(self):
        self.__lock.acquire()
        x, y, width, height = XGetGeometry(self.infos["dsp"],\
            self.infos["window"])
        self.video_area["x"] = x
        self.video_area["y"] = y
        self.video_area["width"] = width
        self.video_area["height"] = height
        self.__lock.release()

    def set_dpms(self, activated):
        dummy = pointer(c_int(51))
        if DPMSQueryExtension(self.infos['dsp'], dummy, dummy):
            if activated:
                DPMSEnable(self.infos['dsp'])
            else:
                DPMSDisable(self.infos['dsp'])


# vim: ts=4 sw=4 expandtab
