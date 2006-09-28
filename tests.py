#!/usr/bin/env python
"""
This is the test suite launcher.
"""

import unittest

print "Test Database functions\n"
import testdeejayd.mediadb.database
dbsuite = unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.mediadb.database)
unittest.TextTestRunner(verbosity=2).run(dbsuite)

print "\nTest DeejaydProtocol functions\n"
import testdeejayd.net.deejaydProtocol
dbsuite = unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.net.deejaydProtocol)
unittest.TextTestRunner(verbosity=2).run(dbsuite)

# vim: ts=4 sw=4 expandtab
