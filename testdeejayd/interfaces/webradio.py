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
from testdeejayd.interfaces import _TestInterfaces

class WebradioInterfaceTests(_TestInterfaces):
    
    def testWebradioSource(self):
        """Test webradio commands related to source management"""
        wr_list = self.deejayd.webradio
        
        av_sources = [{
            "name": "local",
            "editable": True,
        }]
        plugins = self.config.getlist("general", "enabled_plugins")
        if "icecast" in plugins:
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

        cat_name = self.testdata.getRandomString()
        self.__add_category(cat_name)

        # verify
        categories = wr_list.get_source_categories("local")
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]["name"], cat_name)

    def __add_webradio(self, testWrName):
        wr_list = self.deejayd.webradio
        testWrUrls = []
        for urlCount in range(self.testdata.getRandomInt(10)):
            testWrUrls.append('http://' + self.testdata.getRandomString(50))
        self.assertAckCmd(wr_list.source_add_webradio("local",
                                                      testWrName, testWrUrls))
        return testWrUrls

    def testWebradioAdd(self):
        """Test webradio.sourceAddWebradio command"""
        wr_list = self.deejayd.webradio

        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],\
                   ['http://' + self.testdata.getRandomString(50) + '.pls']]:
            self.assertRaises(DeejaydError, wr_list.source_add_webradio, 
                              "local", self.testdata.getRandomString(), badURI)
        
        # Add correct URI
        testWrName = self.testdata.getRandomString()
        testWrUrls = self.__add_webradio(testWrName)

        # verify recorded webradios
        webradios = wr_list.get_source_content("local")
        wr_names = [wr['title'] for wr in webradios]
        self.assertTrue(testWrName in wr_names)
        retrievedWr = [wr for wr in webradios\
                          if wr['title'] == testWrName][0]
        for url in testWrUrls:
            self.assertTrue(url in retrievedWr['urls'])

    def testWebradioClear(self):
        """Test webradio.sourceClearWebradios command"""
        wr_list = self.deejayd.webradio

        testWrName = self.testdata.getRandomString()
        testWrUrls = self.__add_webradio(testWrName)
        webradios = wr_list.get_source_content("local")
        self.assertEqual(len(webradios), 1)

        # clear recorded webradios
        self.assertAckCmd(wr_list.source_clear_webradios("local"))
        webradios = wr_list.get_source_content("local")
        self.assertEqual(webradios, [])

    def testWebradioDelete(self):
        """Test webradio.sourceDeleteWebradios command"""
        wr_list = self.deejayd.webradio

        testWrName = self.testdata.getRandomString()
        self.__add_webradio(testWrName)
        webradios = wr_list.get_source_content("local")
        self.assertEqual(len(webradios), 1)

        # delete recorded webradios
        wb = webradios[0]
        self.assertAckCmd(wr_list.source_delete_webradios("local",
                                                          [wb["wb_id"]]))
        webradios = wr_list.get_source_content("local")
        self.assertEqual(webradios, [])

# vim: ts=4 sw=4 expandtab