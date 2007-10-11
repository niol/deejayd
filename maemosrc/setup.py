#!/usr/bin/env python

import glob
from distutils.core import setup
from djmote import __version__ as version

data_files = [
    ('share/pixmaps', [ 'data/djmote.png' ]),
    ('share/applications/hildon', [ 'data/djmote.desktop' ]),
    ('share/dbus-1/services', [ 'data/djmote.service' ]),
    ]

if __name__ == "__main__":
    setup( name="djmote", version=version,
           url="http://mroy31.dyndns.org/~roy/wiki/doku.php?id=djmote",
           description="djmote is a maemo client for deejayd",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/djmote"],
           packages=["deejayd","deejayd.net","djmote",\
                     "djmote.widgets","djmote.utils"],
           package_data={'djmote': ['pixmaps/*']},
           data_files=data_files
        )
# vim: ts=4 sw=4 expandtab
