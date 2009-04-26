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

import glob,os
from distutils.command.build import build as distutils_build
from distutils.core import setup,Command
from distutils.errors import DistutilsFileError
from distutils.dep_util import newer
from distutils.spawn import find_executable
from zipfile import ZipFile

import deejayd


class build_extension(Command):
    ext_directory = None
    extension = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.ext_directory = "extensions"
        self.extension = "deejayd-webui"

    def run(self):
        data_files = self.distribution.data_files

        ext_dir = os.path.join(self.ext_directory, self.extension)
        ext_path = "%s.xpi" % ext_dir
        # first remove old zip file
        try: os.unlink(ext_path)
        except OSError:
            pass
        ext_file = ZipFile(ext_path, 'w')
        for root, dirs, files in os.walk(ext_dir):
            for f in files:
                path = os.path.join(root, f)
                ext_file.write(path, path[len(ext_dir):])
        ext_file.close()

        target_path = os.path.join('share', 'deejayd', 'htdocs')
        data_files.append((target_path, (ext_path, ), ))


class build_manpages(Command):
    manpages = None
    db2mans = [
        # debian
        "/usr/share/sgml/docbook/stylesheet/xsl/nwalsh/manpages/docbook.xsl",
        # gentoo
        "/usr/share/sgml/docbook/xsl-stylesheets/manpages/docbook.xsl",
        ]
    mandir = "man/"
    executable = find_executable('xsltproc')

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.manpages = glob.glob(os.path.join(self.mandir, "*.xml"))

    def __get_man_section(self, filename):
        # filename should be file.mansection.xml
        return filename.split('.')[-2]

    def run(self):
        data_files = self.distribution.data_files
        db2man = None
        for path in self.__class__.db2mans:
            if os.path.exists(path):
                db2man = path
                continue

        for xmlmanpage in self.manpages:
            manpage = xmlmanpage[:-4] # remove '.xml' at the end
            if newer(xmlmanpage, manpage):
                cmd = (self.executable, "--nonet", "-o", self.mandir, db2man,
                       xmlmanpage)
                self.spawn(cmd)

            targetpath = os.path.join("share", "man","man%s" % manpage[-1])
            data_files.append((targetpath, (manpage, ), ))


class build_i18n(Command):
    user_options = []
    po_package = None
    po_directory = None
    po_files = None
    executable = find_executable('msgfmt')

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.po_directory = "po"
        self.po_package = "deejayd"
        self.po_files = glob.glob(os.path.join(self.po_directory, "*.po"))

    def run(self):
        data_files = self.distribution.data_files

        for po_file in self.po_files:
            lang = os.path.basename(po_file[:-3])
            mo_dir =  os.path.join("build", "mo", lang, "LC_MESSAGES")
            mo_file = os.path.join(mo_dir, "%s.mo" % self.po_package)
            if not os.path.exists(mo_dir):
                os.makedirs(mo_dir)

            cmd = (self.executable, po_file, "-o", mo_file)
            self.spawn(cmd)

            targetpath = os.path.join("share/locale", lang, "LC_MESSAGES")
            data_files.append((targetpath, (mo_file,)))


class deejayd_build(distutils_build):

    def __has_manpages(self, command):
        has_db2man = False
        for path in build_manpages.db2mans:
            if os.path.exists(path): has_db2man = True
        return self.distribution.cmdclass.has_key("build_manpages")\
            and has_db2man and build_manpages.executable != None

    def __has_i18n(self, command):
        return self.distribution.cmdclass.has_key("build_i18n")\
            and build_i18n.executable != None

    def __has_extension(self, command):
        return self.distribution.cmdclass.has_key("build_extension")

    def finalize_options(self):
        distutils_build.finalize_options(self)
        self.sub_commands.append(("build_i18n", self.__has_i18n))
        self.sub_commands.append(("build_manpages", self.__has_manpages))
        self.sub_commands.append(("build_extension", self.__has_extension))

#
# data files
#
def get_data_files(walking_root, dest_dir):
    data_files = []
    for root, dirs, files in os.walk(walking_root):
        paths = [os.path.join(root, f) for f in files]
        root = root.replace(walking_root, '').strip('/')
        dest_path = os.path.join(dest_dir, root)
        data_files.append((dest_path, paths))
    return data_files

def build_data_files_list():
    data = [
        ('share/doc/deejayd', ("doc/deejayd_xml_protocol", )),
        ('share/doc/deejayd', ("README", "NEWS", )),
        ('share/doc/deejayd', ["scripts/deejayd_rgscan"]),
        ]

    # htdocs
    data.extend(get_data_files('data/htdocs', 'share/deejayd/htdocs'))

    return data

if __name__ == "__main__":
    setup( name="deejayd", version=deejayd.__version__,
           url="http://mroy31.dyndns.org/~roy/projects/deejayd",
           description="Network controllable media player daemon",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd","scripts/djc"],
           packages=["deejayd","deejayd.net","deejayd.mediadb",\
                     "deejayd.mediadb.formats",
                     "deejayd.mediadb.formats.audio",\
                     "deejayd.mediadb.formats.video","deejayd.player",\
                     "deejayd.sources","deejayd.ui",\
                     "deejayd.database","deejayd.database.upgrade",\
                     "deejayd.database.backends",\
                     "deejayd.webui","deejayd.webui.mobile",\
                     "deejayd.webui.xul", "pytyxi"],
           package_data={'deejayd.ui': ['defaults.conf'],
                         'deejayd.webui.xul.templates': ['*.xml'],
                         'deejayd.webui.mobile': ["templates/*thtml",\
                                 "templates/modes/*thtml"],},
           data_files= build_data_files_list(),
           cmdclass={"build": deejayd_build,
                     "build_i18n": build_i18n,
                     "build_extension": build_extension,
                     "build_manpages": build_manpages,}
        )

# vim: ts=4 sw=4 expandtab
