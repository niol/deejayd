"""
Tools to create a test server.
"""
import os, signal, os.path, sys, subprocess

logfile = '/tmp/testdeejayd.log'
if os.path.isfile(logfile):
    os.unlink(logfile)


class TestServer:
    """Implements a server ready for testing."""
    
    def __init__(self, testServerPort, musicDir, dbfilename):
        self.testServerPort = testServerPort
        self.musicDir = musicDir
        self.dbfilename = dbfilename

        self.serverExecRelPath = 'scripts/testserver'
        self.srcpath = self.findSrcPath()

    def findSrcPath(self):
        # Get the server executable path, assuming it is names scripts/deejayd
        # in a subdirectory of $PYTHONPATH
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
            print self.__serverProcess.stderr.read(16000)
            raise Exception('Reactor does not seem to be ready')

    def stop(self):
        # Send kill signal
        os.kill(self.__serverProcess.pid, signal.SIGKILL)

        # Wait for the process to finish
        self.__serverProcess.wait()

        # Clean up temporary db file
        os.unlink(self.dbfilename)


# vim: ts=4 sw=4 expandtab
