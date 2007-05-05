from testdeejayd import TestCaseWithCommand, TestCaseWithData
from deejayd.net.deejaydProtocol import CommandFactory


class testDeejaydProtocol(TestCaseWithCommand):

    def setUp(self):
        TestCaseWithCommand.setUp(self)
        self.cmdFactory = CommandFactory()
        randomName = self.testcmd().getRandomString()

    def tearDown(self):
        TestCaseWithCommand.tearDown(self)

    def testLinePingCommand(self):
        """Send a ping command with the line protocol"""
        cmd = self.cmdFactory.createCmdFromLine("ping")
        self.assertEqual(cmd.execute(), "OK\n")

    def testXMLPingCommand(self):
        """Send a ping command with the XML protocol"""
        cmdContent = self.testcmd().createXMLCmd("ping")
        cmd = self.cmdFactory.createCmdFromXML(cmdContent)
        self.assertEqual(cmd.execute(), self.testcmd().createSimpleOkanswer("ping"))

    def testLineUnknownCommand(self):
        """Send a unknown command with the line protocol"""
        cmdName =  self.testcmd().getRandomString()
        cmd = self.cmdFactory.createCmdFromLine(cmdName)
        rs = cmd.execute()
        self.assert_(rs.startswith("ACK"))

    def testXMLUnknownCommand(self):
        """Send a unknown command with the XML protocol"""
        cmdName =  self.testcmd().getRandomString()
        cmdContent = self.testcmd().createXMLCmd(cmdName)
        cmd = self.cmdFactory.createCmdFromXML(cmdContent)
        rs = cmd.execute()

        self.assert_(self.testcmd().isError(rs))

# vim: ts=4 sw=4 expandtab
