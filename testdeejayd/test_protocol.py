from testdeejayd import TestCaseWithMediaData

from deejayd.net.deejaydProtocol import CommandFactory
from deejayd.net.xmlbuilders import DeejaydXMLCommand, DeejaydXMLAnswerFactory


class TestDeejaydProtocol(TestCaseWithMediaData):

    def setUp(self):
        TestCaseWithMediaData.setUp(self)
        self.cmdFactory = CommandFactory()
        self.rspFactory = DeejaydXMLAnswerFactory()

    def tearDown(self):
        TestCaseWithMediaData.tearDown(self)

    def testLinePingCommand(self):
        """Send a ping command with the line protocol"""
        cmd = self.cmdFactory.createCmdFromLine("ping")
        self.assertEqual(cmd.execute(), "OK\n")

    def testXMLPingCommand(self):
        """Send a ping command with the XML protocol"""
        xmlcmd = DeejaydXMLCommand('ping')
        cmd = self.cmdFactory.createCmdFromXML(xmlcmd.to_xml())
        ans = self.rspFactory.get_deejayd_xml_answer('Ack', xmlcmd.name)
        self.assertEqual(cmd.execute(), ans.to_xml())

    def testLineUnknownCommand(self):
        """Send a unknown command with the line protocol"""
        cmdName =  self.testdata.getRandomString()
        cmd = self.cmdFactory.createCmdFromLine(cmdName)
        rs = cmd.execute()
        self.assert_(rs.startswith("ACK"))

    def testXMLUnknownCommand(self):
        """Send a unknown command with the XML protocol"""
        cmdName = self.testdata.getRandomString()
        xmlcmd = DeejaydXMLCommand(cmdName)
        cmd = self.cmdFactory.createCmdFromXML(xmlcmd)
        ans = self.rspFactory.get_deejayd_xml_answer('error', xmlcmd.name)
        ans.set_error_text("Unknown command : %s" % cmdName)
        self.failUnless(cmd.execute(), ans.to_xml())


# vim: ts=4 sw=4 expandtab
