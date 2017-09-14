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
from deejayd.db.models import Equals
from testdeejayd.interfaces import _TestInterfaces


class RecordedPlaylistInterfaceTests(_TestInterfaces):

    def __get_medias(self):
        library = self.deejayd.audiolib
        library_data = self.test_audiodata
        r_dir = library_data.get_random_dir()
        return library.get_dir_content(r_dir.rel_path)["files"]

    def __createRecordedPlaylist(self, pl_type='magic'):
        djplname = self.testdata.get_random_string()
        return self.deejayd.recpls.create(djplname, pl_type)

    def testRecPlsCreateErase(self):
        """test recpls.create, recpls.erase and recpls.getList command"""
        recpls = self.deejayd.recpls

        # try to create playlist with wrong type
        rand_type = self.testdata.get_random_string()
        djplname = self.testdata.get_random_string()
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
        rand_id = self.testdata.get_random_int()
        self.assertRaises(DeejaydError, recpls.get_content, rand_id)

    def testRecPlsStaticCommands(self):
        """test recpls.staticXXX commands (add, remove and clear)"""
        recpls = self.deejayd.recpls
        pl_id = self.__createRecordedPlaylist("static")["pl_id"]

        # add songs in a wrong playlist
        rand_id = self.testdata.get_random_int(10000, 5000)
        self.assertRaises(DeejaydError, recpls.static_load_medias,
                          rand_id, [])

        # add songs in the new playlist
        songs = self.__get_medias()
        song_ids = [s["m_id"] for s in songs]
        self.assertAckCmd(recpls.static_load_medias(pl_id, song_ids))
        content = recpls.get_content(pl_id)
        self.assertEqual(len(content), len(song_ids))

        # remove song from the playlist
        self.assertAckCmd(recpls.static_remove_medias(pl_id, (1,)))
        content = recpls.get_content(pl_id)
        self.assertEqual(len(content), len(song_ids) - 1)

        # clear playlist
        self.assertAckCmd(recpls.static_clear(pl_id))
        content = recpls.get_content(pl_id)
        self.assertEqual(content, [])

    def testRecPlsMagicAddFilter(self):
        """test recpls.magicAddFilter command"""
        recpls = self.deejayd.recpls
        pl_id = self.__createRecordedPlaylist("magic")["pl_id"]

        genre = self.test_audiodata.get_random_genre()
        r_filter = Equals('genre', genre)
        rnd_filter = Equals('genre', self.testdata.get_random_string())

        # add correct filter
        self.assertAckCmd(recpls.magic_add_filter(pl_id, r_filter))
        # verify playlist content
        medias = recpls.get_content(pl_id)
        filters = recpls.magic_get_filters(pl_id)
        self.assertEqual(len(filters), 1)
        self.assertTrue(r_filter.equals(filters[0]))
        for m in medias:
            self.assertEqual(m['genre'], genre)

        # remove filter
        self.assertAckCmd(recpls.magic_remove_filter(pl_id, r_filter))
        self.assertEqual(len(recpls.magic_get_filters(pl_id)), 0)

        # add random filter
        self.assertAckCmd(recpls.magic_add_filter(pl_id, rnd_filter))
        # verify playlist content
        medias = recpls.get_content(pl_id)
        filters = recpls.magic_get_filters(pl_id)
        self.assertEqual(len(filters), 1)
        self.assertEqual(len(medias), 0)
        self.assertTrue(rnd_filter.equals(filters[0]))

        # clear filter
        self.assertAckCmd(recpls.magic_clear_filter(pl_id))
        self.assertEqual(len(recpls.magic_get_filters(pl_id)), 0)

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
                self.assertEqual(properties[key], True)
