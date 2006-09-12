#!/usr/bin/env python
"""
This is the test suite launcher.
"""

import unittest

import testdeejayd.mediadb.database
dbsuite = unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.mediadb.database)

unittest.TextTestRunner(verbosity=2).run(dbsuite)

# vim: ts=4 sw=4 expandtab
