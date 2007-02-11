#!/usr/bin/env python

import glob
import os

import shutil
import sys

from distutils.core import setup, Command
from distutils.command.clean import clean as distutils_clean
from distutils.command.sdist import sdist as distutils_sdist
import deejayd

if __name__ == "__main__":
    #setup(cmdclass={'clean': clean, 'test': test_cmd, 'coverage': coverage_cmd,
    #                "sdist": sdist, "release": release},
    setup( name="deejayd", version=deejayd.__version__,
           url="http://mroy31.dyndns.org/~roy/projects/deejayd",
           description="",
           author="Mikael Royer",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd"],
           packages=["deejayd","deejayd.net","deejayd.mediadb",\
                     "deejayd.player","deejayd.sources","deejayd.ui"],
           package_data={'deejayd.ui': ['defaults.conf']},
           data_files=[('share/doc/deejayd-0.1.0', glob.glob("doc/*"))])
           #data_files=[('share/doc/deejayd-0.1.0', glob.glob("doc/*")),
                       #('etc/deejayd.conf',"conf/deejayd.conf"))])
