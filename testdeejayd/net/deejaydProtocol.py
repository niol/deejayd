from testdeejayd import TestCaseWithData
from deejayd.net.deejaydProtocol import CommandFactory


class testDeejaydProtocol(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)
        self.cmdFactory = CommandFactory()
        randomName = self.testdata.getRandomString()

    def tearDown(self):
        TestCaseWithData.tearDown(self)

    def testLineProtocol(self):
        """Send a ping command with the line protocol"""
        cmd = self.cmdFactory.createCmdFromLine("ping")
        self.assertEqual(cmd.execute(), "OK\n")

    def testXMLProtocol(self):
        """Send a ping command with the XML protocol"""
        pass





# vim: ts=4 sw=4 expandtab
