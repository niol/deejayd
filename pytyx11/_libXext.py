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

import sys
import ctypes

from pytyx11._libX11 import Display


lib = ctypes.util.find_library('Xext')
if lib is not None:
    _libXext = ctypes.cdll.LoadLibrary(lib)
else:
    if sys.platform.startswith('darwin'):
        p = '/opt/X11/lib/libXext.dylib'
        _libXext = ctypes.cdll.LoadLibrary(p)
    else:
        raise ImportError('Could not load Xext shared library.')


# Bool DPMSQueryExtension (Display *display, int *event_base, int *error_base)
_libXext.DPMSQueryExtension.argtypes = (ctypes.POINTER(Display),
                                        ctypes.POINTER(ctypes.c_int),
                                        ctypes.POINTER(ctypes.c_int))
_libXext.DPMSQueryExtension.restype = ctypes.c_int

# Status DPMSEnable (Display *display )
_libXext.DPMSEnable.argtypes = (ctypes.POINTER(Display), )
_libXext.DPMSEnable.restype = ctypes.c_int

# Status DPMSDisable (Display *display )
_libXext.DPMSDisable.argtypes = (ctypes.POINTER(Display), )
_libXext.DPMSDisable.restype = ctypes.c_int


# copy functions from the library
module = sys.modules[__name__]
for name in dir(_libXext):
    if name.startswith('DPMS'):
        setattr(module, name, getattr(_libXext, name))
