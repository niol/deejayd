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

        # FIXME : This is not a good thing to do but sometimes reactor.run does
        # not exit after shutdown...
        self.setDaemon(True)

        self.__reactorRunning = False
        self.__reactorNotBusy = threading.Event()

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

        # Set a shutdown callback to confirm shutdown
        reactor.addSystemEventTrigger('after', 'startup',
            self.__setReactorRunning, True)

        # Set a shutdown callback to confirm shutdown
        reactor.addSystemEventTrigger('after', 'shutdown',
            self.__setReactorRunning, False)

        # run reactor disabling SIG handlers (those are only allowed in
        # the main thread)
        reactor.run(False)

    def __setReactorRunning(self, status):
        self.__reactorRunning = status

        # No need to wait for the reactor anymore
        self.__reactorNotBusy.set()

    def start(self):
        # Reactor is now busy starting
        self.__reactorNotBusy.clear()

        if self.__reactorRunning:
            raise ReactorException("Reactor already running")

        threading.Thread.start(self)

        # Wait for the reactor to really be running
        self.__reactorNotBusy.wait()

    def stop(self):
        # Reactor is now busy shutting down
        self.__reactorNotBusy.clear()

        if not self.__reactorRunning:
            raise ReactorException("Reactor not running")

        reactor.callFromThread(reactor.stop)

        # Wait for the reactor to really be stopped
        self.__reactorNotBusy.wait()

        os.unlink(self.dbfilename)


# vim: ts=4 sw=4 expandtab
