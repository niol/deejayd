#!/usr/bin/env python

# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
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
          e.g. : ./tests.py jsonrpc
        - a test module name without the 'test_' prefix, a slash, and a test
          name in unittest dotted notation (See the documentation of
          loadTestsFromName at
          http://docs.python.org/lib/testloader-objects.html)
          e.g. : ./tests.py jsonrpc/TestJSONRPCBuilders
              or ./tests.py jsonrpc/TestJSONRPCBuilders.test_response_builder
    * If the fist argument is 'list', list all the possibles tests that can be
      combined on the command line restricted by the same arguments.
      e.g. : ./tests.py list jsonrpc library
      would list all the tests that are to be run from those test modules.
    * Test suite has several options :
      * --player to select media backend : gstreamer(default) or xine
      * --db to select database backend : sqlite(default) or mysql
      * --dbopts to specify options to connect to mysql database
"""

import sys, os, glob
python_version = sys.version_info
if python_version[0] < 3 and python_version[1] < 7:
    try:
        import unittest2 as unittest
    except ImportError:
        sys.exit("For python version < 2.7, deejayd tests require unittest2 mpdule")
else:
    import unittest
from optparse import OptionParser
from copy import copy
from optparse import Option, OptionValueError

def check_dboptions(option, opt, value):
    db_options = [opt.split("=") for opt in value.split(";")]
    try:
        return dict(db_options)
    except ValueError:
        raise OptionValueError("option %s: invalid format: %r" % (opt, value))

class DbOption(Option):
    TYPES = Option.TYPES + ("dboptions",)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["dboptions"] = check_dboptions

import testdeejayd

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

def get_id_from_module(module):
    return module.__name__[len(TEST_NAMESPACE+'.'+'test_'):]

def get_all_tests():
    return [(x, None) for x in glob.glob(get_testfile_from_id("*"))]

usage = "usage: %prog [options] [tests-list]"
parser = OptionParser(option_class=DbOption, usage=usage)
parser.add_option("-p","--player",dest="player",type="string",\
    help="media backend used for this test suite")
parser.add_option("-b","--db",dest="db",type="string",\
    help="database backend used for this test suite")
parser.add_option("-o","--dbopts",dest="dbopts",type="dboptions",\
    help="options to connect to mysql database")
parser.set_defaults(player="gstreamer", db="sqlite", dbopts={})
(options, myargs) = parser.parse_args()

# update options
from testdeejayd import _DeejaydTest
_DeejaydTest.media_backend = options.player
_DeejaydTest.db = options.db
if options.db == "mysql":
    _DeejaydTest.db_options = options.dbopts

tests_to_run = None
list_only = False
args = None
if len(myargs) > 0:
    if myargs[0] == 'list':
        list_only = True
        args = myargs[1:]
    else:
        args = myargs

if args:
    tests_to_consider = []
    for test_id in args:
        try:
            test_module, test_name = test_id.split('/')
        except ValueError:
            test_module = test_id
            test_name = None

        tests_to_consider.append((get_testfile_from_id(test_module), test_name))
else:
    tests_to_consider = get_all_tests()

def get_test_suite(test_module, test_name=None):
    test_suite = None
    if test_name:
        test_suite = unittest.defaultTestLoader.loadTestsFromName(test_name,
                                                                  test_module)
    else:
        test_suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
    return test_suite

def get_module_and_name(test_id):
    fn, test_name = test_id
    module_path = '.'.join([TEST_NAMESPACE, os.path.basename(fn[:-3])])
    test_module = my_import(module_path)
    return test_module, test_name

def print_tests(class_name, test_name=None):
    if class_name.startswith('Test'):
        has_tests = False
        for fun_name in dir(getattr(test_module, class_name)):
            if fun_name.startswith('test')\
            and (not test_name or fun_name == test_name):
                has_tests = True
                print "%s/%s.%s" % (get_id_from_module(test_module),
                                    class_name, fun_name)
        if has_tests:
            print "%s/%s" % (get_id_from_module(test_module), class_name)

if list_only:
    for test_id in tests_to_consider:
        test_module, test_name = get_module_and_name(test_id)
        if test_name:
            splitted_test_name = test_name.split('.')
            if len(splitted_test_name) > 1:
                class_name, test_name = splitted_test_name
            else:
                class_name, test_name = splitted_test_name[0], None
            print_tests(class_name, test_name)
        else:
            for class_name in dir(test_module):
                print_tests(class_name)
else:
    suitelist = []
    runner = unittest.TextTestRunner(verbosity = 2)
    for test_id in tests_to_consider:
        test_module, test_name = get_module_and_name(test_id)
        suitelist.append(get_test_suite(test_module, test_name))
    runner.run(unittest.TestSuite(suitelist))


# vim: ts=4 sw=4 expandtab
