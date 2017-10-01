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

from testdeejayd.interfaces import _TestInterfaces


class CoreInterfaceTests(_TestInterfaces):

    def testPing(self):
        """Test ping command"""
        self.assertAckCmd(self.deejayd.ping())

    def testGetStats(self):
        """Test getStats command"""
        ans = self.deejayd.get_stats()
        print(ans)
        keys = ["audio_library_update", "songs", "artists", "albums"]
        if self.hasVideoSupport():
            keys.extend(["video_library_update", "videos"])
        for k in keys:
            self.assertTrue(k in ans, "%s is no in stats" % k)

    def testGetStatus(self):
        """Test getStatus command"""
        ans = self.deejayd.get_status()
        keys = [
            "audiopls_id",
            "audiopls_repeat",
            "audiopls_playorder",
            "audiopls_length",
            "audiopls_timelength",
            "audioqueue_id",
            "audioqueue_playorder",
            "audioqueue_length",
            "audioqueue_timelength",
            "state",
            "volume",
        ]
        if self.hasVideoSupport():
            keys.extend([
                "videopls_id",
                "videopls_repeat",
                "videopls_playorder",
                "videopls_length",
                "videopls_timelength",
            ])
        for k in keys:
            self.assertTrue(k in ans)
            if k == "state":
                self.assertTrue(ans[k] in ('stop', 'play', 'pause'))

    def testGetServerInfo(self):
        """Test getServerInfo command"""
        ans = self.deejayd.get_server_info()
        keys = ('server_version', 'protocol_version')
        for k in keys:
            self.assertTrue(k in ans)
