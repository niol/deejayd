
PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class UnknownPlayer:

    def __init__(self,db,config):
        self.config = config
        self.db = db

        # Initialise var
        self._video_support = False
        self._state = PLAYER_STOP
        self._queue = None
        self._source = None
        self._source_name = None
        self._playing_source_name = None
        self._playing_source = None
        self._uri = None
        self._random = 0
        self._repeat = 0

    def init_video_support(self):
        self._video_support = True
        self._fullscreen = int(self.db.get_state("fullscreen"))
        self._loadsubtitle = int(self.db.get_state("loadsubtitle"))

    def load_state(self):
        # Restore volume
        vol = float(self.db.get_state("volume"))
        self.set_volume(vol)

        # Restore current song
        cur_pos = int(self.db.get_state("currentPos"))
        self._source.go_to(cur_pos,"Pos")

        # Random and Repeat
        self.random(int(self.db.get_state("random")))
        self.repeat(int(self.db.get_state("repeat")))

    def set_source(self,source,name):
        self._source = source
        self._source_name = name

    def set_queue(self,queue):
        self._queue = queue

    def get_playing_source_name(self):
        return self._playing_source_name or self._source_name

    def set_uri(self,song):
        if song: self._uri = song["uri"]
        else: self._uri = ""

    def start_play(self):
        if self._queue.get_current():
            self._playing_source_name = "queue"
            self._playing_source = self._queue
        else:
            self._playing_source_name = self._source_name
            self._playing_source= self._source

    def play(self):
        if self.get_state() == PLAYER_STOP:
            cur_song = self._queue.go_to(0,"Pos") or self._source.get_current()
            if cur_song: self.set_uri(cur_song)
            else: return
            self.start_play()
        elif self.get_state() == PLAYER_PAUSE:
            self.pause()

    def pause(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def reset(self,source_name):
        if source_name == self._playing_source_name:
            self.stop()
            self.set_uri(None)

    def next(self):
        self.stop()
        song = self._queue.next(self._random,self._repeat) or\
                self._source.next(self._random,self._repeat)

        if song:
            self.set_uri(song)
            self.start_play()

    def previous(self):
        self.stop()
        song = self._source.previous(self._random,self._repeat)
        if song:
            self.set_uri(song)
            self.start_play()

    def go_to(self,nb,type,queue = False):
        self.stop()
        s = queue and self._queue or self._source
        song = s.go_to(nb,type)
        if song:
            self.set_uri(song)
            self.start_play()

    def random(self,val):
        self._random = val

    def repeat(self,val):
        self._repeat = val

    def fullscreen(self,val):
        self._fullscreen = val
        if self.get_state() != PLAYER_STOP: 
            self.set_fullscreen(self._fullscreen)

    def loadsubtitle(self,val):
        self._loadsubtitle = val
        if self.get_state() != PLAYER_STOP:
            self.set_subtitle(self._loadsubtitle)

    def get_volume(self):
        raise NotImplementedError

    def set_volume(self,v):
        raise NotImplementedError

    def get_position(self):
        raise NotImplementedError

    def set_position(self,pos):
        raise NotImplementedError

    def get_state(self):
        return self._state

    def set_state(self,state):
        self._state = state

    def get_status(self):
        status = [("random",self._random),("repeat",self._repeat),\
            ("state",self.get_state()),("volume",self.get_volume()),\
            ("mode",self._source_name)]

        source = self._playing_source or self._source
        cur_song = source.get_current()
        if cur_song:
            status.extend([("song",cur_song["Pos"]),("songid",cur_song["Id"])])
        if self.get_state() != PLAYER_STOP:
            if "Time" not in cur_song.keys() or cur_song["Time"] == 0:
                cur_song["Time"] = self.get_position()
            status.extend([ ("time","%d:%d" % (self.get_position(),\
                cur_song["Time"])) ])
                    
        # Specific video status
        if self._video_support:
            status.extend([("fullscreen",self._fullscreen),
                ("loadsubtitle",self._loadsubtitle)])

        return status

    def is_playing(self):
        return self.get_state() != PLAYER_STOP

    def close(self):
        song = self._source.get_current()
        if song: cur_pos = song["Pos"]
        else: cur_pos = 0

        states = [(str(self.get_volume()),"volume"),(str(self._repeat),\
            "repeat"),(str(self._random),"random"),\
            (self._source_name,"source"),(str(cur_pos),"currentPos")]
        if self._video_support:
            states.extend([(str(self._fullscreen),"fullscreen"),
                            (str(self._loadsubtitle),"loadsubtitle")])
        self.db.set_state(states)

        # stop player if necessary
        if self.get_state() != PLAYER_STOP:
            self.stop()

# vim: ts=4 sw=4 expandtab
