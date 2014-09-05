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


from deejayd import DeejaydError
from deejayd.jsonrpc import mediafilters
from testdeejayd.interfaces import _TestInterfaces

class RecordedPlaylistInterfaceTests(_TestInterfaces):

    def __createRecordedPlaylist(self, pl_type='magic'):
        djplname = self.testdata.getRandomString()

        return self.deejayd.recpls.create(djplname, pl_type)

    def testRecPlsCreateGetListErase(self):
        """test recpls.create, recpls.erase and recpls.getList command"""
        recpls = self.deejayd.recpls

        # try to create playlist with wrong type
        rand_type = self.testdata.getRandomString()
        djplname = self.testdata.getRandomString()
        self.assertRaises(DeejaydError, recpls.create, djplname, rand_type)

        pl_infos = self.__createRecordedPlaylist()
        pl_list = recpls.get_list()
        self.assertEqual(len(pl_list), 1)
        for attr in ('type', 'name', 'pl_id'):
            self.assertEqual(pl_list[0][attr], pl_infos[attr])

        self.assertAckCmd(recpls.erase((pl_infos["pl_id"],)))
        pl_list = recpls.get_list()
        self.assertEqual(len(pl_list), 0)

    def testRecPlsGetContent(self):
        """test recpls.getContent command"""
        recpls = self.deejayd.recpls

        # try with a wrong pl id
        rand_id = self.testdata.getRandomInt()
        self.assertRaises(DeejaydError, recpls.get_content, rand_id)

    def testRecPlsStaticCommands(self):
        """test recpls.staticXXX commands (add, remove and clear)"""
        recpls = self.deejayd.recpls
        pl_id = self.__createRecordedPlaylist("static")["pl_id"]

        # add songs in a wrong playlist
        rand_id = self.testdata.getRandomInt(10000, 5000)
        self.assertRaises(DeejaydError, recpls.static_add_media_by_ids,
                          rand_id, [])

        # add songs in the new playlist
        media_ids = []
        for media_path in self.test_audiodata.getRandomMediaPaths(3):
            self.assertAckCmd(recpls.static_add_media_by_path(pl_id,
                                                              media_path))
        content = recpls.get_content(pl_id)["medias"]
        self.assertEqual(len(content), 3)

        # remove song from the playlist
        self.assertAckCmd(recpls.static_remove_media(pl_id, (1,)))
        content = recpls.get_content(pl_id)["medias"]
        self.assertEqual(len(content), 3 - 1)

        # clear playlist
        self.assertAckCmd(recpls.static_clear_media(pl_id))
        content = recpls.get_content(pl_id)["medias"]
        self.assertEqual(content, [])

    def testRecPlsMagicAddFilter(self):
        """test recpls.magicAddFilter command"""
        recpls = self.deejayd.recpls
        pl_id = self.__createRecordedPlaylist("magic")["pl_id"]

        genre = self.test_audiodata.getRandomGenre()
        r_filter = mediafilters.Equals('genre', genre)
        rnd_filter = mediafilters.Equals('genre',
                                         self.testdata.getRandomString())

        # add correct filter
        self.assertAckCmd(recpls.magic_add_filter(pl_id, r_filter))
        # verify playlist content
        ans = recpls.get_content(pl_id)
        self.assertEqual(len(ans["filter"]), 1)
        self.assertTrue(r_filter.equals(ans["filter"][0]))
        for m in ans['medias']:
            self.assertEqual(m['genre'], genre)

        # remove filter
        self.assertAckCmd(recpls.magic_remove_filter(pl_id, r_filter))
        ans = recpls.get_content(pl_id)
        self.assertEqual(len(ans["filter"]), 0)

        # add random filter
        self.assertAckCmd(recpls.magic_add_filter(pl_id, rnd_filter))
        # verify playlist content
        ans = recpls.get_content(pl_id)
        self.assertEqual(len(ans["filter"]), 1)
        self.assertEqual(len(ans["medias"]), 0)
        self.assertTrue(rnd_filter.equals(ans["filter"][0]))

        # clear filter
        self.assertAckCmd(recpls.magic_clear_filter(pl_id))
        ans = recpls.get_content(pl_id)
        self.assertEqual(len(ans["filter"]), 0)

    def testRecPlsMagicGetSetProperty(self):
        """test recpls.magicGetProperties/magicSetProperty commands"""
        recpls = self.deejayd.recpls

        pl_infos = self.__createRecordedPlaylist()
        pl_id = pl_infos["pl_id"]

        # test limit property
        self.assertAckCmd(recpls.magic_set_property(pl_id, "use-limit", "1"))
        self.assertAckCmd(recpls.magic_set_property(pl_id, "limit-value", "1"))

        # test getProperties
        known_keys = (
            'use-or-filter',
            'use-limit',
            'limit-value',
            'limit-sort-value',
            'limit-sort-direction',
        )
        properties = recpls.magic_get_properties(pl_id)
        for key in known_keys:
            self.assertTrue(key in properties.keys())
            if key in ("use-limit", "limit-value"):
                self.assertEqual(properties[key], "1")

# vim: ts=4 sw=4 expandtab
