#!/usr/bin/env python
"""
This is the test suite launcher.
"""

import os, glob
import unittest

import testdeejayd

suitelist = []
runner = unittest.TextTestRunner(verbosity = 2)

testNamespace = 'testdeejayd'
testSuitesDirectory = os.path.join(os.path.dirname(__file__), testNamespace)

# Workaround for __import__ behavior, see
# http://docs.python.org/lib/built-in-funcs.html
def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

for fn in glob.glob(os.path.join(testSuitesDirectory, "test_*.py")):
    modulePath = '.'.join([testNamespace, os.path.basename(fn[:-3])])
    testModule = my_import(modulePath)

    testSuite = unittest.defaultTestLoader.loadTestsFromModule(testModule)
    suitelist.append(testSuite)


runner.run(unittest.TestSuite(suitelist))

# vim: ts=4 sw=4 expandtab
