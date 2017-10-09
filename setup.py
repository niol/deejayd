#!/usr/bin/env python3

# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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

import glob
import os
import shutil
import subprocess
from distutils.errors import DistutilsExecError
from distutils.command.build import build as distutils_build
from distutils.command.clean import clean as distutils_clean
from distutils.core import setup, Command
from distutils.dep_util import newer
from distutils.dir_util import remove_tree
from distutils.spawn import find_executable
import deejayd


def force_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def force_rmdir(path):
    try:
        shutil.rmtree(path)
    except OSError:
        pass


def spawn(cmdargs, cwd=None):
    try:
        subprocess.check_call(cmdargs, cwd=cwd)
    except subprocess.CalledProcessError as e:
        raise DistutilsExecError(e)


class build_manpages(Command):
    description = "Build deejayd man pages"
    user_options = []

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

    def __get_manpage(self, xmlmanpage):
        return xmlmanpage[:-4]  # remove '.xml' at the end

    def run(self):
        data_files = self.distribution.data_files
        db2man = None
        for path in self.__class__.db2mans:
            if os.path.exists(path):
                db2man = path
                continue

        for xmlmanpage in self.manpages:
            manpage = self.__get_manpage(xmlmanpage)
            if newer(xmlmanpage, manpage):
                cmd = (self.executable, "--nonet", "-o", self.mandir, db2man,
                       xmlmanpage)
                self.spawn(cmd)

            targetpath = os.path.join("share", "man", "man%s" % manpage[-1])
            data_files.append((targetpath, (manpage, ), ))

    def clean(self):
        for xmlmanpage in self.manpages:
            force_unlink(self.__get_manpage(xmlmanpage))


class build_i18n(Command):
    description = "Build deejayd .po files"
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
        self.mo_dir = os.path.join('build', 'mo')

    def run(self):
        data_files = self.distribution.data_files

        for po_file in self.po_files:
            lang = os.path.basename(po_file[:-3])
            mo_dir = os.path.join(self.mo_dir, lang, "LC_MESSAGES")
            mo_file = os.path.join(mo_dir, "%s.mo" % self.po_package)
            if not os.path.exists(mo_dir):
                os.makedirs(mo_dir)

            cmd = (self.executable, po_file, "-o", mo_file)
            self.spawn(cmd)

            targetpath = os.path.join("share/locale", lang, "LC_MESSAGES")
            data_files.append((targetpath, (mo_file,)))

    def clean(self):
        if os.path.isdir(self.mo_dir):
            remove_tree(self.mo_dir)


class build_webui(Command):
    description = "Install deejayd webui"
    webui_directory = "webui"

    def initialize_options(self):
        self.webuidir = os.path.join(os.path.dirname(__file__), 
                                     self.webui_directory)

    def finalize_options(self):
        pass

    def run(self):
        data_files = self.distribution.data_files
        for d in ('dist', 'ressources'):
            dist = os.path.join('share/deejayd/htdocs/', d)
            data_files.extend(get_data_files(os.path.join(self.webuidir, d),
                                             dist))


class deejayd_build(distutils_build):

    def finalize_options(self):
        distutils_build.finalize_options(self)

        self.sub_commands.append(("build_i18n", self.__has_i18n))
        self.sub_commands.append(("build_manpages", self.__has_manpages))
        self.sub_commands.append(("build_webui", self.__has_webui))

    def __has_manpages(self, command):
        has_db2man = False
        for path in build_manpages.db2mans:
            if os.path.exists(path):
                has_db2man = True
        return "build_manpages"in self.distribution.cmdclass\
            and has_db2man and build_manpages.executable is not None

    def __has_i18n(self, command):
        return "build_i18n" in self.distribution.cmdclass\
            and build_i18n.executable is not None

    def __has_webui(self, command):
        return "build_webui" in self.distribution.cmdclass

    def clean(self):
        for subcommand_name in self.get_sub_commands():
            subcommand = self.get_finalized_command(subcommand_name)
            if hasattr(subcommand, 'clean'):
                subcommand.clean()


class deejayd_clean(distutils_clean):

    def run(self):
        distutils_clean.run(self)

        for cmd in self.distribution.command_obj.values():
            if hasattr(cmd, 'clean'):
                cmd.clean()

        force_unlink('MANIFEST')
        force_rmdir('build')


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
        ('share/doc/deejayd', ("doc/deejayd_rpc_protocol", )),
        ('share/doc/deejayd', ("README", "NEWS", )),
        ('share/doc/deejayd', ["scripts/deejayd_rgscan"]),
    ]

    return data


if __name__ == "__main__":
    setup( name="deejayd", version=deejayd.__version__,
           url="http://mroy31.domring.net/~roy/projects/deejayd",
           description="Network controllable media player daemon",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd", "scripts/djc"],
           packages=["deejayd", "deejayd.common", "deejayd.library",
                     "deejayd.server",
                     "deejayd.dispatch",
                     "deejayd.library.parsers",
                     "deejayd.library.parsers.audio",
                     "deejayd.library.parsers.video", "deejayd.player",
                     "deejayd.sources", "deejayd.ui", "deejayd.jsonrpc",
                     "deejayd.db", "deejayd.db.dbmigrate",
                     "deejayd.db.dbmigrate.versions", "deejayd.webradio",
                     "deejayd.webui", "deejayd.playlist", "pytyx11"],
           package_data={'deejayd.ui': ['defaults.conf'],
                         'deejayd.webui': ['webui.thtml'], },
           data_files=build_data_files_list(),
           cmdclass={
               "build": deejayd_build,
               "build_i18n": build_i18n,
               "build_manpages": build_manpages,
               "build_webui": build_webui,
               "clean": deejayd_clean,
           }
        )
