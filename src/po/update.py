#!/usr/bin/env python

# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

import glob,os
from distutils.dep_util import newer
from distutils.spawn import spawn

def update_po():
    po_package = "deejayd"
    po_dir = "po"

    pot_file = os.path.join(po_dir, po_package + ".pot")
    po_files = glob.glob(os.path.join(po_dir, "*.po"))
    infilename = os.path.join(po_dir, "POTFILES.in")
    infiles = file(infilename).read().splitlines()

    for filename in infiles:
        if newer(filename, pot_file):
            oldpath = os.getcwd()
            os.chdir(po_dir)
            spawn(["intltool-update", "--pot", "--gettext-package", po_package])
            for po in po_files:
                spawn(["intltool-update", "--dist",
                            "--gettext-package", po_package,
                            os.path.basename(po[:-3])])
            os.chdir(oldpath)

if __name__ == "__main__":
    update_po()

# vim: ts=4 sw=4 expandtab
