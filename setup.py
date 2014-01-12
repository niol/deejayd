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

import glob, os, shutil
from distutils.errors import DistutilsOptionError
from distutils.command.build import build as distutils_build
from distutils.command.clean import clean as distutils_clean
from distutils.core import setup,Command
from distutils.errors import DistutilsFileError
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
        return xmlmanpage[:-4] # remove '.xml' at the end

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

            targetpath = os.path.join("share", "man","man%s" % manpage[-1])
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
            mo_dir =  os.path.join(self.mo_dir, lang, "LC_MESSAGES")
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

gwt_option = [ ("gwt=", None,
                "location of GWT SDK used to compile deejayd webui"),
               ("ant-target=", None,
                "ant-target use to build webui with gwt : build or builddist")]

class build_webui(Command):
    description = "Build deejayd webui with GWT SDK"
    user_options = gwt_option

    ant = find_executable('ant')
    webui_directory = "webui"

    def initialize_options(self):
        self.gwt = None
        self.ant_target = None

        self.build_file = os.path.join(self.webui_directory, "build.xml")

    def finalize_options(self):
        if self.gwt is not None:
            os.environ["GWT_SDK"] = self.gwt
        if self.ant_target is None:
            self.ant_target = "builddist"

    def run(self):
        if "GWT_SDK" not in os.environ.keys():
            # TODO : try to find gwt sdk in default java classpath
            raise DistutilsOptionError("No GWT SDK found to build webui")
        if self.ant is None:
            raise DistutilsOptionError(\
                    "ant program not found, we can't build webui")

        os.environ["GWT_SDK"] = os.path.abspath(os.environ["GWT_SDK"])
        cmd = (self.ant, "-f", self.build_file, self.ant_target)
        self.spawn(cmd)

        if self.ant_target == "builddist":
            wdir = os.path.join("build", "webui")
            data_files = self.distribution.data_files
            for d in ('gwtwebui', 'gwtmobilewebui', 'static'):
                data_files.extend(get_data_files(os.path.join(wdir, d),
                                  os.path.join('share/deejayd/htdocs/', d)))

    def clean(self):
        if os.path.isfile(self.build_file) and self.ant is not None:
            self.spawn((self.ant, "-f", self.build_file, "clean"))


class deejayd_build(distutils_build):

    def finalize_options(self):
        distutils_build.finalize_options(self)

        self.sub_commands.append(("build_i18n", self.__has_i18n))
        self.sub_commands.append(("build_manpages", self.__has_manpages))
        self.sub_commands.append(("build_webui", self.__has_webui))

    def __has_manpages(self, command):
        has_db2man = False
        for path in build_manpages.db2mans:
            if os.path.exists(path): has_db2man = True
        return self.distribution.cmdclass.has_key("build_manpages")\
            and has_db2man and build_manpages.executable != None

    def __has_i18n(self, command):
        return self.distribution.cmdclass.has_key("build_i18n")\
            and build_i18n.executable != None

    def __has_webui(self, command):
        return self.distribution.cmdclass.has_key("build_webui")

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
           url="http://mroy31.dyndns.org/~roy/projects/deejayd",
           description="Network controllable media player daemon",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd","scripts/djc"],
           packages=["deejayd","deejayd.net","deejayd.mediadb",\
                     "deejayd.mediadb.parsers",
                     "deejayd.mediadb.parsers.audio",\
                     "deejayd.mediadb.parsers.video","deejayd.player",\
                     "deejayd.sources","deejayd.ui","deejayd.jsonrpc",\
                     "deejayd.database","deejayd.database.upgrade",\
                     "deejayd.model", "deejayd.webradio",
                     "deejayd.plugins",\
                     "deejayd.webui","deejayd.playlist","pytyxi", "pytyx11",\
                     "txsockjs", "txsockjs.protocols"],
           package_data={'deejayd.ui': ['defaults.conf'],},
           data_files= build_data_files_list(),
           cmdclass={"build": deejayd_build,
                     "build_i18n": build_i18n,
                     "build_manpages": build_manpages,
                     "build_webui": build_webui,
                     "clean"          : deejayd_clean,
                    }
        )

# vim: ts=4 sw=4 expandtab
