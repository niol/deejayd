# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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
Tools to create a test server.
"""
import os, signal, os.path, sys, subprocess

logfile = '/tmp/testdeejayd.log'
if os.path.isfile(logfile):
    os.unlink(logfile)


class TestServer:
    """Implements a server ready for testing."""

    def __init__(self, testServerPort, musicDir, videoDir, dbfilename):
        self.testServerPort = testServerPort
        self.musicDir = musicDir
        self.videoDir = videoDir
        self.dbfilename = dbfilename

        self.serverExecRelPath = 'scripts/testserver'
        self.srcpath = self.findSrcPath()

    def findSrcPath(self):
        # Get the server executable path, assuming it is names
        # scripts/testserver in a subdirectory of $PYTHONPATH
        absPath = ''
        notFound = True
        sysPathIterator = iter(sys.path)
        while notFound:
            absPath = sysPathIterator.next()
            serverScriptPath = os.path.join(absPath, self.serverExecRelPath)
            if os.path.exists(serverScriptPath):
                notFound = False

        if notFound:
            raise Exception('Cannot find server executable')

        return os.path.abspath(absPath)

    def start(self):
        serverExec = os.path.join(self.srcpath, self.serverExecRelPath)

        if not os.access(serverExec, os.X_OK):
            sys.exit("The test server executable '%s' is not executable."\
                     % serverExec)

        args = [serverExec, str(self.testServerPort),
                            self.musicDir,
                            self.videoDir,
                            self.dbfilename]
        env = {}
        env['PYTHONPATH'] = self.srcpath
        self.__serverProcess = subprocess.Popen(args = args,
                                                env = env,
                                                stderr = subprocess.PIPE,
                                                stdout = sys.stdout.fileno(),
                                                close_fds = True)

        firstLine = self.__serverProcess.stderr.readline()
        if not firstLine == 'ready\n':
            # Should not occur
            print firstLine
            self.stop()
            raise Exception('Reactor does not seem to be ready')

    def stop(self):
        # Send stop signal to reactor
        os.kill(self.__serverProcess.pid, signal.SIGINT)

        # Wait for the process to finish
        self.__serverProcess.wait()

        # Clean up temporary db file
        os.unlink(self.dbfilename)


# vim: ts=4 sw=4 expandtab
