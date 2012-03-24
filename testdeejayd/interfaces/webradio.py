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
        
        av_sources = ["local"]
        plugins = self.config.getlist("general", "enabled_plugins")
        if "icecast" in plugins:
            av_sources.append("icecast")
        sources = dict(wr_list.get_available_sources())
        self.assertEqual(av_sources, sources.keys())    
        
        # try to set wrong source
        self.assertRaises(DeejaydError,
                          wr_list.set_source, self.testdata.getRandomString())
        # set a source
        source = self.testdata.getRandomElement(sources.keys())
        self.assertAckCmd(wr_list.set_source(source))
        # verify
        status = self.deejayd.get_status()
        self.assertEqual(source, status["webradiosource"])
        
    def testWebradioCategories(self):
        """Test webradio commands related to category management"""
        pass

    def testWebradioManagement(self):
        """Test webradio commands related to webradio management"""
        wr_list = self.deejayd.webradio
        self.assertAckCmd(wr_list.set_source("local"))
        
        # Test for bad URI and inexistant playlist
        for badURI in [[self.testdata.getRandomString(50)],\
                   ['http://' + self.testdata.getRandomString(50) + '.pls']]:
            self.assertRaises(DeejaydError, wr_list.source_add_webradio, 
                              "local", self.testdata.getRandomString(), badURI)
        
        # Add correct URI
        testWrName = self.testdata.getRandomString()
        testWrUrls = []
        for urlCount in range(self.testdata.getRandomInt(10)):
            testWrUrls.append('http://' + self.testdata.getRandomString(50))
        self.assertAckCmd(wr_list.source_add_webradio("local",
                                                      testWrName, testWrUrls))

        # verify recorded webradios
        wr_names = [wr['title'] for wr in wr_list.get()["medias"]]
        self.assertTrue(testWrName in wr_names)
        retrievedWr = [wr for wr in wr_list.get()["medias"]\
                          if wr['title'] == testWrName][0]
        for url in testWrUrls:
            self.assertTrue(url in retrievedWr['urls'])

# vim: ts=4 sw=4 expandtab