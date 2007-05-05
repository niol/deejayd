# mplayer.py

from twisted.internet import threads
from deejayd.ui.config import DeejaydConfig
from subprocess import *
from exceptions import OSError
import time, fcntl, os

from deejayd.player.unknown import unknownPlayer

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

# FIXME : find a way to known mplayer state in order to remove all time.sleep
#         from this class

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

    def startPlay(self,init = True):
        if init: unknownPlayer.startPlay(self)

        if not self._uri: return
        self._uri = self._uri.replace("file://","")

        # Construc audio output
        ao = self.config.get("mplayer", "audio_output")
        if ao == "alsa":
            try: alsa_card = self.config.get("mplayer", "alsa_card")
            except: pass
            else: 
                alsa_card = alsa_card.replace(":","=")
                ao += ":device=%s" % alsa_card

        mpc = "mplayer -slave -softvol -quiet -ao %s -vo %s \"" % (ao,\
            self.config.get("mplayer", "video_output")) \
            + self._uri + "\" 2>/dev/null"

        try: self.mplayerProcess = Popen(mpc,stdin=PIPE,stdout=PIPE,shell=True)
        except OSError: return
        time.sleep(0.4)  #allow time for execute command
        fcntl.fcntl(self.mplayerProcess.stdout, fcntl.F_SETFL, os.O_NONBLOCK)
        self.__wait()

        self.setVolume(self._volume)
        self.setFullscreen(self._fullscreen)
        self.setSubtitle(self._loadsubtitle)

        self.setState(PLAYER_PLAY)
        self._stopDeferred = threads.deferToThread(self.wait)
        self._stopDeferred.addCallback(self.eofHandler)
        self._stopDeferred.addErrback(errorHandler)
    
    def wait(self):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            try: self.mplayerProcess.wait()
            except OSError: pass
        return True

    def eofHandler(self,res = False):
        if self.getState() == PLAYER_PLAY: self.next()
        else: self.setState(PLAYER_STOP)

    def pause(self):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            if self.getState() == PLAYER_PLAY: 
                self._position = self.getPosition()
                self.setState(PLAYER_PAUSE)
            elif self.getState() == PLAYER_PAUSE: 
                self.setState(PLAYER_PLAY)
                self._position = 0
            else: return
            self.__cmd("pause")
            self.__wait()
        
    def stop(self):
        self.setState(PLAYER_STOP)
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
        if self.getState() == PLAYER_PAUSE: return self._position
        elif self.getState() == PLAYER_STOP: return 0

        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self.mplayerProcess.stdout.flush()
            self.__cmd("get_time_pos")
            time.sleep(0.3)  #allow time for output

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
        self.__wait()
    
    def setFullscreen(self,val):
         self.__setProperty("fullscreen",str(val))

    def setSubtitle(self,val):
         self.__setProperty("sub_visibility",str(val))

    def __cmd(self, command):
        if self.mplayerProcess and self.mplayerProcess.poll() == None:
            self.mplayerProcess.stdout.flush()
            pause = command == "pause" and "" or "pausing_keep "
            self.mplayerProcess.stdin.write(pause + command + "\n")
            self.mplayerProcess.stdin.flush()
        
    def __setProperty(self,name,value):
        self.__cmd("set_property %s %s" % (name,value))
        self.__wait()

    def __wait(self):
        time.sleep(0.05)

    #
    # file format info
    #
    def webradioSupport(self):
        return True

    def isSupportedFormat(self,format):
        if format in (".avi",".mpeg",".mpg"):
            return self._videoSupport
        return True

    def getVideoFileInfo(self,file):
        args = ["midentify",file]
        try: self.__process = Popen(args,stdin=PIPE,stdout=PIPE)
        except OSError: return None

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
