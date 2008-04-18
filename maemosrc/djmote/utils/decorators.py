# Djmote, a graphical deejayd client designed for use on Maemo devices
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

import traceback
import gtk

# This is a decorator for our GUI callbacks : every GUI callback will be GTK
# thread safe that way.
def gui_callback(func):
    def gtk_thread_safe_func(*__args,**__kw):
        gtk.gdk.threads_enter()
        try: func(*__args, **__kw)
        except Exception, ex:
            print "---------------------Traceback lines-----------------------"
            print traceback.format_exc()
            print "-----------------------------------------------------------"
        gtk.gdk.threads_leave()
    return gtk_thread_safe_func

# vim: ts=4 sw=4 expandtab
