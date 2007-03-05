#!/usr/bin/env python
"""
This is the test suite launcher.
"""

import unittest

suitelist = []

import testdeejayd.mediadb.database
suitelist.append(unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.mediadb.database))

import testdeejayd.mediadb.deejaydDB
suitelist.append(unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.mediadb.deejaydDB))

import testdeejayd.net.deejaydProtocol
suitelist.append(unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.net.deejaydProtocol))

import testdeejayd.net.client
suitelist.append(unittest.defaultTestLoader.loadTestsFromModule(testdeejayd.net.client))

unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suitelist))

# vim: ts=4 sw=4 expandtab
