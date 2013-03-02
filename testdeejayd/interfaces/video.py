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

from deejayd import DeejaydError
from testdeejayd.interfaces import require_video_support, _TestInterfaces

class VideoInterfaceTests(_TestInterfaces):

    @require_video_support
    def testVideoSet(self):
        """Test video.set command"""
        video_obj = self.deejayd.video
        # choose a wrong directory
        rand_dir = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, video_obj.set,
                          rand_dir, "directory")

        # get contents of root dir and try to set video directory
        ans = self.deejayd.videolib.get_dir_content()
        directory = self.testdata.getRandomElement(ans["directories"])
        self.assertAckCmd(video_obj.set(directory, "directory"))

        expected_files = self.deejayd.videolib.get_dir_content(directory)["files"]
        expected_uris = [f["uri"] for f in expected_files]
        # test videolist content
        uris = [m["uri"] for m in video_obj.get()["medias"]]
        self.assertEqual(expected_uris.sort(), uris.sort())

        # search a wrong title
        rand = self.testdata.getRandomString()
        video_obj.set(rand, "search")
        self.assertEqual(len(video_obj.get()["medias"]), 0)

    @require_video_support
    def testVideoSort(self):
        """Test video.sort command"""
        video_obj = self.deejayd.video

        # sort videolist content
        sort = [["rating", "ascending"]]
        self.assertAckCmd(video_obj.set_sort(sort))
        self.assertEqual(video_obj.get()["sort"], sort)
        # set bad sort
        rnd_sort = [(self.testdata.getRandomString(), "ascending")]
        self.assertRaises(DeejaydError, video_obj.set_sort, rnd_sort)



# vim: ts=4 sw=4 expandtab
