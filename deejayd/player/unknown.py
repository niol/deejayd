
import sys
import time

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class unknownPlayer:

    def __init__(self,db,config):
        self.config = config
        self.db = db
        # Initialise var
        self._videoSupport = False
        self._state = PLAYER_STOP
        self._queue = None
        self._source = None
        self._sourceName = None
        self._playingSourceName = None
        self._playingSource = None
        self._random = 0
        self._repeat = 0

    def initVideoSupport(self):
        self._videoSupport = True
        self._fullscreen = int(self.db.getState("fullscreen"))

    def loadState(self):
        # Restore volume
        vol = float(self.db.getState("volume"))
        self.setVolume(vol)

        # Restore current song
        curPos = int(self.db.getState("currentPos"))
        self._source.goTo(curPos,"Pos")

        # Random and Repeat
        self._random = int(self.db.getState("random"))
        self._repeat = int(self.db.getState("repeat"))

    def setSource(self,source,name):
        self._source = source
        self._sourceName = name

    def setQueue(self,queue):
        self._queue = queue

    def getPlayingSourceName(self):
        return self._playingSourceName or self._sourceName

    def startPlay(self):
        if self._queue.getCurrent():
            self._playingSourceName = "queue"
            self._playingSource = self._queue
        else:
            self._playingSourceName = self._sourceName
            self._playingSource= self._source

    def play(self):
        if self._state == PLAYER_STOP:
            curSong = self._queue.goTo(0,"Pos") or self._source.getCurrent()
            if curSong: self.setURI(curSong["uri"])
            else: return
        self.startPlay()

    def pause(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def reset(self,sourceName):
        if sourceName == self._playingSourceName:
            self.stop()
            self.setURI("")

    def next(self):
        self.stop()
        song = self._queue.next(self._random,self._repeat) or\
                self._source.next(self._random,self._repeat)

        if song:
            self.setURI(song["uri"])
            self.startPlay()

    def previous(self):
        self.stop()
        song = self._source.previous(self._random,self._repeat)
        if song:
            self.setURI(song["uri"])
            self.startPlay()

    def goTo(self,nb,type,queue = False):
        self.stop()
        s = queue and self._queue or self._source
        song = s.goTo(nb,type)
        if song:
            self.setURI(song["uri"])
            self.startPlay()

    def random(self,val):
        self._random = val

    def repeat(self,val):
        self._repeat = val

    def fullscreen(self,val):
        self._fullscreen = val
        if self._state != PLAYER_STOP:
            self.setFullscreen(self._fullscreen)

    def getVolume(self):
        raise NotImplementedError

    def setVolume(self,v):
        raise NotImplementedError

    def getPosition(self):
        raise NotImplementedError

    def setPosition(self,pos):
        raise NotImplementedError

    def getStatus(self):
        status = [("random",self._random),("repeat",self._repeat),\
            ("state",self._state),("volume",self.getVolume()),\
            ("mode",self._sourceName)]

        source = self._playingSource or self._source
        curSong = source.getCurrent()
        if curSong:
            status.extend([("song",curSong["Pos"]),("songid",curSong["Id"])])
        if self._state != PLAYER_STOP:
            if "Time" not in curSong.keys() or curSong["Time"] == 0:
                curSong["Time"] = self.getPosition()
            status.extend([ ("time","%d:%d" % (self.getPosition(),\
                curSong["Time"])) ])
                    
        # Specific video status
        if self._videoSupport:
            status.extend([("fullscreen",self._fullscreen)])

        return status

    def isPlay(self):
        return self._state != PLAYER_STOP

    def close(self):
        song = self._source.getCurrent()
        if song: curPos = song["Pos"]
        else: curPos = 0

        states = [(str(self.getVolume()),"volume"),(str(self._repeat),\
            "repeat"),(str(self._random),"random"),\
            (self._sourceName,"source"),(str(curPos),"currentPos")]
        if self._videoSupport:
            states.extend([(str(self._fullscreen),"fullscreen")])
        self.db.setState(states)

        # stop player if necessary
        if self._state != PLAYER_STOP:
            self.stop()

# vim: ts=4 sw=4 expandtab
