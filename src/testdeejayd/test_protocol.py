# Deejayd, a media player daemon
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

from testdeejayd import TestCaseWithData

from deejayd.net.deejaydProtocol import CommandFactory
from deejayd.net.xmlbuilders import DeejaydXMLCommand, DeejaydXMLAnswerFactory


class TestDeejaydProtocol(TestCaseWithData):

    def setUp(self):
        super(TestDeejaydProtocol, self).setUp()
        self.cmdFactory = CommandFactory()
        self.rspFactory = DeejaydXMLAnswerFactory()

    def testXMLPingCommand(self):
        """Send a ping command with the XML protocol"""
        xmlcmd = DeejaydXMLCommand('ping')
        cmd = self.cmdFactory.createCmdFromXML(xmlcmd.to_xml())
        ans = self.rspFactory.get_deejayd_xml_answer('Ack', xmlcmd.name)
        self.assertEqual(cmd.execute(), ans.to_xml())

    def testXMLUnknownCommand(self):
        """Send a unknown command with the XML protocol"""
        cmdName = self.testdata.getRandomString()
        xmlcmd = DeejaydXMLCommand(cmdName)
        cmd = self.cmdFactory.createCmdFromXML(xmlcmd)
        ans = self.rspFactory.get_deejayd_xml_answer('error', xmlcmd.name)
        ans.set_error_text("Unknown command : %s" % cmdName)
        self.failUnless(cmd.execute(), ans.to_xml())


# vim: ts=4 sw=4 expandtab
