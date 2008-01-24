#!/usr/bin/env python

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

"""
This is the test suite launcher :
    * Without arguments, it runs the whole test suite.
    * It accepts a list of arguments which can be :
        - a test module name without the 'test_' prefix.
          e.g. : ./tests.py xmlprocessing
        - a test module name without the 'test_' prefix, a slash, and a test
          name in unittest dotted notation (See the documentation of
          loadTestsFromName at
          http://docs.python.org/lib/testloader-objects.html)
          e.g. : ./tests.py xmlprocessing/TestAnswerParser
              or ./tests.py xmlprocessing/TestAnswerParser.testAnswerParserError
"""

import sys, os, glob
import unittest

import testdeejayd

suitelist = []
runner = unittest.TextTestRunner(verbosity = 2)

TEST_NAMESPACE = 'testdeejayd'
test_suites_dir = os.path.join(os.path.dirname(__file__), TEST_NAMESPACE)

# Workaround for __import__ behavior, see
# http://docs.python.org/lib/built-in-funcs.html
def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def get_testfile_from_id(id):
    return os.path.join(test_suites_dir, "test_%s.py" % id)

tests_to_run = None
if len(sys.argv) > 1:
    tests_to_run = []
    for test_id in sys.argv[1:]:
        try:
            test_module, test_name = test_id.split('/')
        except ValueError:
            test_module = test_id
            test_name = None

        tests_to_run.append((get_testfile_from_id(test_module), test_name))
else:
    tests_to_run = [(x, None) for x in glob.glob(get_testfile_from_id("*"))]

for test_id in tests_to_run:
    fn, test_name = test_id
    module_path = '.'.join([TEST_NAMESPACE, os.path.basename(fn[:-3])])
    test_module = my_import(module_path)

    test_suite = None
    if test_name:
        test_suite = unittest.defaultTestLoader.loadTestsFromName(test_name,
                                                                  test_module)
    else:
        test_suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
    suitelist.append(test_suite)

runner.run(unittest.TestSuite(suitelist))


# vim: ts=4 sw=4 expandtab
