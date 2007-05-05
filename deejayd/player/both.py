from deejayd.player.unknown import unknownPlayer

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class Both(unknownPlayer):

    def __init__(self,db,config):
        unknownPlayer.__init__(self,db,config)

        # init audio backend
        from deejayd.player.gstreamer import Gstreamer
        self.audio_player = Gstreamer(db,config)
            
        # init video backend
        from deejayd.player.mplayer import Mplayer
        self.video_player = Mplayer(db,config)

        self.current_player = None

    def initVideoSupport(self):
        unknownPlayer.initVideoSupport(self)
        self.video_player.initVideoSupport()

    def setQueue(self,queue):
        unknownPlayer.setQueue(self,queue)
        self.audio_player.setQueue(queue)
        self.video_player.setQueue(queue)

    def setSource(self,source,name):
        unknownPlayer.setSource(self,source,name)
        if name == "video": self.video_player.setSource(source,name)
        else: self.audio_player.setSource(source,name)

    def setURI(self,uri):
        self.video_player.setURI(uri)
        self.audio_player.setURI(uri)

    def startPlay(self):
        unknownPlayer.startPlay(self)

        self.current_player = self._playingSourceName == "video" and \
            self.video_player or self.audio_player
        self.current_player.startPlay(False)

    def stop(self):
        if self.current_player:
            self.current_player.stop()

    def pause(self):
        if self.current_player:
            self.current_player.pause()

    def random(self,val):
        self._random = val
        self.video_player.random(val)
        self.audio_player.random(val)

    def repeat(self,val):
        self._repeat = val
        self.video_player.repeat(val)
        self.audio_player.repeat(val)

    def fullscreen(self,val):
        self._fullscreen = val
        self.video_player.fullscreen(val)

    def loadsubtitle(self,val):
        self._loadsubtitle = val
        self.video_player.loadsubtitle(val)

    def getVolume(self):
        return self.audio_player.getVolume()

    def setVolume(self,vol):
        self.video_player.setVolume(vol)
        self.audio_player.setVolume(vol)
        self._volume = vol

    def getPosition(self):
        if self.current_player: return self.current_player.getPosition()
        else: return 0

    def setPosition(self,pos):
        if self.current_player:
            self.current_player.setPosition(pos)

    def setFullscreen(self,val):
        self.video_player.setFullscreen(val)

    def setSubtitle(self,val):
        self.video_player.setSubtitle(val)

    def getState(self):
        if self.current_player: return self.current_player.getState()
        else: return PLAYER_STOP

    def setState(self,state):
        unknownPlayer.setState(state)
        if self.current_player: self.current_player.setState(state)

    def webradioSupport(self):
        return self.audio_player.webradioSupport()

    def isSupportedFormat(self,format):
        if format in (".avi",".mpeg",".mpg"):
            return self.video_player.isSupportedFormat(format)
        else:
            return self.audio_player.isSupportedFormat(format)

    def getVideoFileInfo(self,file):
        return self.video_player.getVideoFileInfo(file)

# vim: ts=4 sw=4 expandtab
