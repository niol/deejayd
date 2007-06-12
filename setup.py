#!/usr/bin/env python

import glob
from distutils.core import setup
from distutils.extension import Extension
import subprocess
import deejayd
from Pyrex.Distutils import build_ext

def getCommandOutput(cmd, warnOnStderr = True, warnOnReturnCode = True):
    """Wait for a command and return its output.  Check for common errors and
    raise an exception if one of these occurs.
    """

    p = subprocess.Popen(cmd, shell=True, close_fds = True,
            stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    if warnOnStderr and stderr != '':
        raise RuntimeError("%s outputted the following error:\n%s" % 
                (cmd, stderr))
    if warnOnReturnCode and p.returncode != 0:
        raise RuntimeError("%s had non-zero return code %d" % 
                (cmd, p.returncode))
    return stdout

def parsePkgConfig(command, components, options_dict = None):
    """Helper function to parse compiler/linker arguments from 
    pkg-config and update include_dirs, library_dirs, etc.

    We return a dict with the following keys, which match up with keyword
    arguments to the setup function: include_dirs, library_dirs, libraries,
    extra_compile_args.

    Command is the command to run (pkg-config, etc).
    Components is a string that lists the components to get options for.

    If options_dict is passed in, we add options to it, instead of starting
    from scratch.
    """

    if options_dict is None:
        options_dict = {
            'include_dirs' : [],
            'library_dirs' : [],
            'libraries' : [],
            'extra_compile_args' : []
        }
    commandLine = "%s --cflags --libs %s" % (command, components)
    output = getCommandOutput(commandLine).strip()
    for comp in output.split():
        prefix, rest = comp[:2], comp[2:]
        if prefix == '-I':
            options_dict['include_dirs'].append(rest)
        elif prefix == '-L':
            options_dict['library_dirs'].append(rest)
        elif prefix == '-l':
            options_dict['libraries'].append(rest)
        else:
            options_dict['extra_compile_args'].append(comp)
    return options_dict

#### Xine Extension ####
xine_options = parsePkgConfig('pkg-config', 
        'libxine x11 xext')
xine_ext = Extension('deejayd.ext.xine', [
        'deejayd/ext/xinelib/xine.pyx',
        'deejayd/ext/xinelib/djdxine.c',
        ], **xine_options)

if __name__ == "__main__":
    setup( name="deejayd", version=deejayd.__version__,
           url="http://mroy31.dyndns.org/~roy/projects/deejayd",
           description="deejayd is a media player daemon based on twisted",
           author="Mikael Royer, Alexandre Rossi",
           author_email="mickael.royer@gmail.com",
           license="GNU GPL v2",
           scripts=["scripts/deejayd"],
           packages=["deejayd","deejayd.net","deejayd.mediadb",\
                     "deejayd.player","deejayd.sources","deejayd.ui",\
                     "deejayd.database","deejayd.ext"],
           package_data={'deejayd.ui': ['defaults.conf']},
           ext_modules=[xine_ext],
           data_files=[('share/doc/deejayd-'+deejayd.__version__, 
                            glob.glob("doc/*")),
                       ('share/doc/deejayd-'+deejayd.__version__,\
                       glob.glob("README*"))],
            cmdclass = {
                'build_ext': build_ext, 
            },
        )
