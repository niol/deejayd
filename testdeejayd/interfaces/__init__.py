# Deejayd, a media player daemon
# Copyright (C) 2007-2012 Mickael Royer <mickael.royer@gmail.com>
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
from functools import wraps
from testdeejayd import unittest

def require_video_support(test_item):
    @wraps(test_item)
    def skip_wrapper(self, *args, **kwargs):        
        if not self.hasVideoSupport():
            reason = "Video support is required for this test"
            raise unittest.case.SkipTest(reason)
        return test_item(self, *args, **kwargs)

    return skip_wrapper

class _TestInterfaces(object):
    possible_clients = ("core", "http", "net_sync", "net_async")
    

# vim: ts=4 sw=4 expandtab