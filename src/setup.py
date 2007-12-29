#!/usr/bin/env python

import glob,os
from distutils.core import setup
import deejayd

#
# data files
#
def build_data_files_list():
    data = [
        ('share/doc/deejayd-'+deejayd.__version__, glob.glob("doc/*")),
        ('share/doc/deejayd-'+deejayd.__version__, glob.glob("README*")),
        ]

    htdocs_root = 'data/htdocs'
    for root, dirs, files in os.walk(htdocs_root):
        paths = [os.path.join(root,f) for f in files]
        root = root.replace(htdocs_root,'').strip("/")
        root_path = os.path.join('share/deejayd/htdocs',root)
        data.append((root_path,paths))

    return data

if __name__ == "__main__":
    setup( name="deejayd", version=deejayd.__version__,
           url="http://mroy31.dyndns.org/~roy/projects/deejayd",
           description="deejayd is a media player daemon based on twisted",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd","scripts/djc"],
           packages=["deejayd","deejayd.net","deejayd.mediadb",\
                     "deejayd.mediadb.formats", "deejayd.player",\
                     "deejayd.player.display","deejayd.sources","deejayd.ui",\
                     "deejayd.database","deejayd.database","deejayd.webui"],
           package_data={'deejayd.ui': ['defaults.conf'],
                         'deejayd.database': ['sql/*.sql'],
                         'deejayd.webui': ['templates/*.xml']},
           data_files= build_data_files_list(),
        )
# vim: ts=4 sw=4 expandtab
