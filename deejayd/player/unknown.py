
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
        self._fullscreen = int(self.db.get_state("fullscreen"))
        self._loadsubtitle = int(self.db.get_state("loadsubtitle"))

    def loadState(self):
        # Restore volume
        vol = float(self.db.get_state("volume"))
        self.setVolume(vol)

        # Restore current song
        curPos = int(self.db.get_state("currentPos"))
        self._source.go_to(curPos,"Pos")

        # Random and Repeat
        self.random(int(self.db.get_state("random")))
        self.repeat(int(self.db.get_state("repeat")))

    def setSource(self,source,name):
        self._source = source
        self._sourceName = name

    def setQueue(self,queue):
        self._queue = queue

    def getPlayingSourceName(self):
        return self._playingSourceName or self._sourceName

    def startPlay(self):
        if self._queue.get_current():
            self._playingSourceName = "queue"
            self._playingSource = self._queue
        else:
            self._playingSourceName = self._sourceName
            self._playingSource= self._source

    def play(self):
        if self.getState() == PLAYER_STOP:
            curSong = self._queue.go_to(0,"Pos") or self._source.get_current()
            if curSong: self.setURI(curSong["uri"])
            else: return
            self.startPlay()
        elif self.getState() == PLAYER_PAUSE:
            self.pause()

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
        song = s.go_to(nb,type)
        if song:
            self.setURI(song["uri"])
            self.startPlay()

    def random(self,val):
        self._random = val

    def repeat(self,val):
        self._repeat = val

    def fullscreen(self,val):
        self._fullscreen = val
        if self.getState() != PLAYER_STOP:
            self.setFullscreen(self._fullscreen)

    def loadsubtitle(self,val):
        self._loadsubtitle = val
        if self.getState() != PLAYER_STOP:
            self.setSubtitle(self._loadsubtitle)

    def getVolume(self):
        raise NotImplementedError

    def setVolume(self,v):
        raise NotImplementedError

    def getPosition(self):
        raise NotImplementedError

    def setPosition(self,pos):
        raise NotImplementedError

    def getState(self):
        return self._state

    def setState(self,state):
        self._state = state

    def getStatus(self):
        status = [("random",self._random),("repeat",self._repeat),\
            ("state",self.getState()),("volume",self.getVolume()),\
            ("mode",self._sourceName)]

        source = self._playingSource or self._source
        curSong = source.get_current()
        if curSong:
            status.extend([("song",curSong["Pos"]),("songid",curSong["Id"])])
        if self.getState() != PLAYER_STOP:
            if "Time" not in curSong.keys() or curSong["Time"] == 0:
                curSong["Time"] = self.getPosition()
            status.extend([ ("time","%d:%d" % (self.getPosition(),\
                curSong["Time"])) ])
                    
        # Specific video status
        if self._videoSupport:
            status.extend([("fullscreen",self._fullscreen),
                ("loadsubtitle",self._loadsubtitle)])

        return status

    def isPlay(self):
        return self.getState() != PLAYER_STOP

    def close(self):
        song = self._source.get_current()
        if song: curPos = song["Pos"]
        else: curPos = 0

        states = [(str(self.getVolume()),"volume"),(str(self._repeat),\
            "repeat"),(str(self._random),"random"),\
            (self._sourceName,"source"),(str(curPos),"currentPos")]
        if self._videoSupport:
            states.extend([(str(self._fullscreen),"fullscreen"),
                            (str(self._loadsubtitle),"loadsubtitle")])
        self.db.set_state(states)

        # stop player if necessary
        if self.getState() != PLAYER_STOP:
            self.stop()

# vim: ts=4 sw=4 expandtab
