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
        self.setFullscreen(self._fullscreen)

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
        self._state = PLAYER_STOP
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self._stopDeferred.pause()
            self.__cmd("quit")  
            try: self.mplayerProcess.wait()
            except: pass
        
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
    
    def setFullscreen(self,val):
         self.__setProperty("fullscreen",str(val))

    def __cmd(self, command):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self.mplayerProcess.stdin.write(command + "\n")
            self.mplayerProcess.stdin.flush()
        
    def __setProperty(self,name,value):
        self.__cmd("set_property %s %s" % (name,value))

    #
    # file format info
    #
    def isSupportedFormat(self,format):
        if format in (".avi",".mpeg",".mpg"):
            return self._videoSupport
        return True

    def getVideoFileInfo(self,file):
        args = ["midentify",file]
        try: self.__process = Popen(args,stdin=PIPE,stdout=PIPE)
        except OSError: return

        if self.__process.poll() == None:
            self.__process.wait()
        infoLines = self.__process.stdout.readlines()
        videoInfo = {}
        for line in infoLines:
            if line.startswith("ID_LENGTH"):
                rs = line.replace("ID_LENGTH=","")
                rs = rs.strip("\n")
                videoInfo["length"] = int(float(rs))
            elif line.startswith("ID_VIDEO_WIDTH"):
                rs = line.replace("ID_VIDEO_WIDTH=","")
                rs = rs.strip("\n")
                videoInfo["videowidth"] = rs
            elif line.startswith("ID_VIDEO_HEIGHT"):
                rs = line.replace("ID_VIDEO_HEIGHT=","")
                rs = rs.strip("\n")
                videoInfo["videoheight"] = rs

        return videoInfo


def errorHandler(failure):
    # Log the exception to debug pb later
    failure.printTraceback()
    return False

# vim: ts=4 sw=4 expandtab
