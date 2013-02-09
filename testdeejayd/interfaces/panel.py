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
from deejayd.model.mediafilters import *
from testdeejayd.interfaces import _TestInterfaces

class PanelInterfaceTests(_TestInterfaces):

    def testPanelGetTags(self):
        """Test panel.getTags command"""
        tags_list = self.config.getlist("panel", "panel_tags")
        panel = self.deejayd.panel

        # get panel tags
        tags = panel.get_tags()
        self.assertEqual(tags_list, tags)

    def testPanelActiveList(self):
        """Test panel.get(set)ActiveList"""
        panel = self.deejayd.panel
        # first create a playlist
        pl_infos = self.deejayd.recpls.create("pl_test", "static")

        # try first with a wrong id
        bad_plid = self.testdata.getRandomInt(2000, 1000)
        self.assertRaises(DeejaydError, panel.set_active_list,
                          "playlist", bad_plid)

        self.assertAckCmd(panel.set_active_list("playlist", pl_infos["pl_id"]))
        panel_list = panel.get_active_list()
        self.assertEqual(panel_list["type"], "playlist")
        self.assertEqual(panel_list["value"], pl_infos["pl_id"])

        # try with a wrong source
        rand_source = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, panel.set_active_list, rand_source)

        # go back to panel
        self.assertAckCmd(panel.set_active_list("panel"))
        panel_list = panel.get_active_list()
        self.assertEqual(panel_list["type"], "panel")

    def testPanelFilter(self):
        """Test panel filter commands : setFilter, removeFilter, clearFilter"""
        panel = self.deejayd.panel
        tags = panel.get_tags()

        # set filter
        bad_tag = self.testdata.getRandomString()
        random_str = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, panel.set_filter,
                          bad_tag, [random_str])  # random tags

        tag = self.testdata.getRandomElement(tags)
        self.assertAckCmd(panel.set_filter(tag, [random_str]))
        self.assertEqual([], panel.get()["medias"])

        # remove bad filter
        self.assertAckCmd(panel.remove_filter(tag))
        self.assertTrue(len(panel.get()["medias"]) > 0)

        # get correct value for a tag
        result = self.deejayd.audiolib.tag_list(tag, None)
        value = self.testdata.getRandomElement(result)
        self.assertAckCmd(panel.set_filter(tag, [value]))
        self.assertTrue(len(panel.get()["medias"]) > 0)

        # clear tag
        panel.clear_filters()
        self.assertTrue(len(panel.get()["medias"]) > 0)

    def testPanelSearch(self):
        """Test panel search commands : setSearchFilter, clearSearchFilter"""
        panel = self.deejayd.panel
        bad_tag = self.testdata.getRandomString()
        random_str = self.testdata.getRandomString()

        # set search
        self.assertRaises(DeejaydError, panel.set_search_filter,
                          bad_tag, random_str)  # random tags

        search_tag = self.testdata.getRandomElement(['title', 'album', \
                'genre', 'artist'])
        self.assertAckCmd(panel.set_search_filter(search_tag, random_str))
        self.assertEqual([], panel.get()["medias"])

        # clear search
        self.assertAckCmd(panel.clear_search_filter())
        self.assertTrue(len(panel.get()["medias"]) > 0)

    def testPanelSort(self):
        """Test panel.setSort command"""
        panel = self.deejayd.panel
        bad_tag = self.testdata.getRandomString()

        self.assertRaises(DeejaydError, panel.set_sort,
                          [(bad_tag, 'ascending')])

        tag = self.testdata.getRandomElement(['title', 'rating', 'genre'])
        media_list = [m[tag] for m in panel.get()["medias"]]
        media_list.sort()
        panel.set_sort([(tag, 'ascending')])
        for idx, m in enumerate(panel.get()["medias"]):
            self.assertEqual(m[tag], media_list[idx])

# vim: ts=4 sw=4 expandtab