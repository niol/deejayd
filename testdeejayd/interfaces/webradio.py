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

from deejayd import DeejaydError
from testdeejayd.interfaces import _TestInterfaces


class WebradioInterfaceTests(_TestInterfaces):
    
    def testWebradioSource(self):
        """Test webradio commands related to source management"""
        wr_list = self.deejayd.webradio
        
        av_sources = [{
            "name": "local",
            "editable": True,
        }]
        icecast = self.config.getboolean("webradio", "icecast")
        if icecast:
            av_sources.append({
                "name": "icecast",
                "editable": False
            })
        self.assertEqual(av_sources, wr_list.get_available_sources())

    def __add_category(self, cat_name):
        wr_list = self.deejayd.webradio
        return wr_list.source_add_category("local", cat_name)

    def testWebradioCategoryAdd(self):
        """Test webradio.sourceCategoryAdd command"""
        wr_list = self.deejayd.webradio

        cat_name = self.testdata.get_random_string()
        self.__add_category(cat_name)

        # verify
        categories = wr_list.get_source_categories("local")
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]["name"], cat_name)

    def __add_webradio(self, testWrName):
        wr_list = self.deejayd.webradio
        testWrUrls = []
        for urlCount in range(self.testdata.get_random_int(10)):
            testWrUrls.append('http://' + self.testdata.get_random_string(50))
        self.assertAckCmd(wr_list.source_add_webradio("local",
                                                      testWrName, testWrUrls))
        return testWrUrls

    def testWebradioAdd(self):
        """Test webradio.sourceAddWebradio command"""
        wr_list = self.deejayd.webradio

        # Test for bad URI and inexistant playlist
        for badURI in [
                    [self.testdata.get_random_string(50)],
                    ['http://' + self.testdata.get_random_string(50) + '.pls']
                ]:
            self.assertRaises(DeejaydError, wr_list.source_add_webradio,
                              "local", self.testdata.get_random_string(), 
                              badURI)
        
        # Add correct URI
        testWrName = self.testdata.get_random_string()
        testWrUrls = self.__add_webradio(testWrName)

        # verify recorded webradios
        webradios = wr_list.get_source_content("local")
        wr_names = [wr['title'] for wr in webradios]
        self.assertTrue(testWrName in wr_names)
        retrievedWr = [wr for wr in webradios
                       if wr['title'] == testWrName][0]
        for url in testWrUrls:
            self.assertTrue(url in retrievedWr['urls'])

    def testWebradioClear(self):
        """Test webradio.sourceClearWebradios command"""
        wr_list = self.deejayd.webradio

        testWrName = self.testdata.get_random_string()
        self.__add_webradio(testWrName)
        webradios = wr_list.get_source_content("local")
        self.assertEqual(len(webradios), 1)

        # clear recorded webradios
        self.assertAckCmd(wr_list.source_clear_webradios("local"))
        webradios = wr_list.get_source_content("local")
        self.assertEqual(webradios, [])

    def testWebradioDelete(self):
        """Test webradio.sourceDeleteWebradios command"""
        wr_list = self.deejayd.webradio

        testWrName = self.testdata.get_random_string()
        self.__add_webradio(testWrName)
        webradios = wr_list.get_source_content("local")
        self.assertEqual(len(webradios), 1)

        # delete recorded webradios
        wb = webradios[0]
        self.assertAckCmd(wr_list.source_delete_webradios("local",
                                                          [wb["w_id"]]))
        webradios = wr_list.get_source_content("local")
        self.assertEqual(webradios, [])
