from testdeejayd import TestCaseWithData
from deejayd.mediadb.database import sqliteDatabase
import os

class testSqliteDatabase(TestCaseWithData):

    def setUp(self):
        TestCaseWithData.setUp(self)

        self.dbfilename = '/tmp/testdeejayddb-' + self.testdata.getRandomString()
        self.db = sqliteDatabase(self.dbfilename)
        self.db.connect()

    def tearDown(self):
        TestCaseWithData.tearDown(self)

        self.db.close()

        os.remove(self.dbfilename)

    def testGetUnexistentPlaylist(self):
        randomName = self.testdata.getRandomString()
        self.assertRaises(PlaylistNotFound,self.db.getPlaylist(randomName))


# vim: ts=4 sw=4 expandtab
