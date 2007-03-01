"""
Deejayd DB testing module
"""
from testdeejayd import TestCaseWithFileData, TestCaseWithProvidedMusic
from deejayd.mediadb.database import sqliteDatabase
from deejayd.mediadb.deejaydDB import DeejaydDB, NotFoundException
import os

class testDeejayDB(TestCaseWithProvidedMusic):

    def setUp(self):
        TestCaseWithProvidedMusic.setUp(self)

        self.dbfilename = '/tmp/testdeejayddb-' + self.testdata.getRandomString()
        self.db = sqliteDatabase(self.dbfilename)
        self.db.connect()

        self.ddb = DeejaydDB(self.db, self.testdata.getRootDir())
        self.ddb.updateDir('.')

    def tearDown(self):
        TestCaseWithProvidedMusic.tearDown(self)

        self.db.close()

        os.remove(self.dbfilename)

    def testGetDir(self):
        """Dir detected by deejayddb"""
        self.assertRaises(NotFoundException,
                        self.ddb.getDir, self.testdata.getRandomString())

        for root, dirs, files in os.walk(self.testdata.getRootDir()):
            current_root = self.testdata.stripRoot(root)

            inDBdirsDump = self.ddb.getDir(current_root)

            inDBdirs = []
            for record in inDBdirsDump:
                inDBdirs.append(record[1])

            for dir in dirs:
                self.assert_(os.path.join(current_root, dir) in inDBdirs,
                    "'%s' is in directory tree but was not found in DB" % dir)


# vim: ts=4 sw=4 expandtab
