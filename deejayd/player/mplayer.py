# mplayer.py

from twisted.python import log
from twisted.internet import threads
from deejayd.ui.config import DeejaydConfig
from subprocess import *
from exceptions import OSError
import time, fcntl, os

from deejayd.player.unknown import unknownPlayer

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class Mplayer(unknownPlayer):
    
    def __init__(self,db,config):
        unknownPlayer.__init__(self,db,config)

        self._uri = None
        self._volume = 0
        self._position = 0
        self._stopDeferred = None
        self.mplayerProcess = None

    def setURI(self,uri):
        self._uri = uri

    def startPlay(self):
        unknownPlayer.startPlay(self)

        if not self._uri:
            return

        mpc = "mplayer -slave -quiet -ao %s -vo %s \"" % \
            (self.config.get("player", "audio_output"),\
            self.config.get("player", "video_output")) \
            + self._uri + "\" 2>/dev/null"

        try: self.mplayerProcess = Popen(mpc,stdin=PIPE,stdout=PIPE,shell=True)
        except OSError: return
        fcntl.fcntl(self.mplayerProcess.stdout, fcntl.F_SETFL, os.O_NONBLOCK)
        self.setVolume(self._volume)

        self._state = PLAYER_PLAY
        self._stopDeferred = threads.deferToThread(self.wait)
        self._stopDeferred.addCallback(self.eofHandler)
        self._stopDeferred.addErrback(errorHandler)
        
    def wait(self):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            try: self.mplayerProcess.wait()
            except OSError: pass
        return True

    def eofHandler(self,res = False):
        if self._state == PLAYER_PLAY:
            self.next()

    def play(self):
        if self._state == PLAYER_STOP:
            curSong = self._queue.goTo(0,"Pos") or self._source.getCurrent()
            if curSong: self.setURI(curSong["uri"])
            else: return
            self.startPlay()
        elif self._state == PLAYER_PAUSE:
            self.pause()

    def pause(self):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            if self._state == PLAYER_PLAY: 
                self._position = self.getPosition()
                self._state = PLAYER_PAUSE
            else: 
                self._state = PLAYER_PLAY
                self._position = 0
            self.__cmd("pause")
        
    def stop(self):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self._stopDeferred.pause()
            self._state = PLAYER_STOP
            self.__cmd("quit")  
            try: self.mplayerProcess.wait()
            except: pass
        
    def fullscreen(self,val):
        if  self._videoSupport:
            if val == 0: self._fullscreen = False
            else: self._fullscreen = True
            self.__setProperty("fullscreen",str(val))

    def getVolume(self):
        return self._volume

    def setVolume(self,vol):
        self.__setProperty("volume",str(vol))
        self._volume = vol

    def getPosition(self):
        if self._state == PLAYER_PAUSE: return self._position
        elif self._state == PLAYER_STOP: return 0

        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self.mplayerProcess.stdout.flush()
            self.__cmd("get_time_pos")
            time.sleep(0.05)  #allow time for output

            posLine = []
            while True:
                try: line = self.mplayerProcess.stdout.readline()
                except StandardError: break

                if not line: break
                if line.startswith("ANS_TIME_POSITION"):
                    line = line.split("=")
                    posLine.append(int(float(line[1])))

            if len(posLine) > 0:
                return posLine[-1]

        return 0

    def setPosition(self, pos):
        cmd = "seek %d 2" % pos
        self.__cmd(cmd)
        time.sleep(0.05)  #allow time for execute command
    
    def __cmd(self, command):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self.mplayerProcess.stdin.write(command + "\n")
            self.mplayerProcess.stdin.flush()
        
    def __setProperty(self,name,value):
        self.__cmd("set_property %s %s" % (name,value))


def errorHandler(failure):
    # Log the exception to debug pb later
    failure.printTraceback()
    return False

# vim: ts=4 sw=4 expandtab
