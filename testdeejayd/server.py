"""
Tools to create a test server in a thread.
"""
import threading
import os, time

from testdeejayd.databuilder import TestData

from deejayd.net.deejaydProtocol import DeejaydFactory
from deejayd.mediadb.database import sqliteDatabase
from deejayd.mediadb.deejaydDB import DeejaydDB

from twisted.python import threadable
# Before creating the reactor, let's make it threadable, this allows us
# to use reactor.callFromThread(() to stop the reactor from the main thread.
threadable.init()
from twisted.internet import reactor


class ReactorException(Exception):

    def __init__(self, *args):
        Exception.__init__(self, *args)


class TestServer(threading.Thread):
    """The idea of this class is to run the twisted reactor in a thread. This
    must be done because reactor.run() is the main tread of the test
    application otherwise.
    
    from : http://wiki.osafoundation.org/bin/view/Projects/ChandlerTwistedInThreadedEnvironment"""

    def __init__(self, testServerPort, musicDir, dbfilename):
        threading.Thread.__init__(self, name = 'Deejayd test server reactor')
        self.__reactorRunning = False
        self.testServerPort = testServerPort
        self.musicDir = musicDir
        self.dbfilename = dbfilename

    def run(self):
        # Set up the test database
        db = sqliteDatabase(self.dbfilename)
        db.connect()

        # Set up the test deeajayd database
        ddb = DeejaydDB(db, self.musicDir)
        ddb.updateDir('.')

        # Set up the test server
        reactor.listenTCP(self.testServerPort, DeejaydFactory(ddb))

        # run reactor disabling SIG handlers (those are only allowed in
        # the main thread)
        reactor.run(False)

        # Set a shutdown callback to confirm shutdown
        reactor.addSystemEventTrigger('after', 'shutdown',
            self.__reactorShutDown)

    def __reactorShutDown(self):
        self.__reactorRunning = False

    def start(self):
        if self.__reactorRunning:
            raise ReactorException("Reactor already running")

        threading.Thread.start(self)

        # Wait for the reactor to really be running
        while not reactor.running:
            time.sleep(.1)

        self.__reactorRunning = True

    def stop(self):
        if not self.__reactorRunning:
            raise ReactorException("Reactor not running")

        reactor.callFromThread(reactor.stop)

        os.unlink(self.dbfilename)


# vim: ts=4 sw=4 expandtab
