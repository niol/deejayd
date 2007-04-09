#!/usr/bin/env python

import glob
from distutils.core import setup
import deejayd

if __name__ == "__main__":
    setup( name="deejayd", version=deejayd.__version__,
           url="http://mroy31.dyndns.org/~roy/projects/deejayd",
           description="deejayd is a media player daemon based on twisted",
           author="Mikael Royer",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd"],
           packages=["deejayd","deejayd.net","deejayd.mediadb",\
                     "deejayd.player","deejayd.sources","deejayd.ui"],
           package_data={'deejayd.ui': ['defaults.conf']},
           data_files=[('share/doc/deejayd-'+deejayd.__version__, 
                            glob.glob("doc/*")),
                       ('share/doc/deejayd-'+deejayd.__version__,\
                       glob.glob("README*"))])
