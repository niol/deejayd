from deejayd.player._base import PlayerError

class DvdError(Exception): pass

class DvdSource:

    def __init__(self, player, db, config):
        self.source_name = "dvd"
        self.player = player
        self.db = db
        self.current_id = int(self.db.get_state("dvdid"))

        self.dvd_info = None
        self.selected_track = None

        # load dvd content
        try: self.load()
        except DvdError: pass

    def get_content(self):
        return self.dvd_info

    def load(self):
        # Reinit var and update id
        self.dvd_info = None
        self.selected_track = None
        self.current_id +=1

        try: self.dvd_info = self.player.get_dvd_info()
        except PlayerError, err: 
            raise DvdError("Unable to load the dvd %s " % err)
        # select the default track of the dvd
        self.select_track()

    def select_track(self,nb = None,alang_idx = None, slang_idx = None):
        if not self.dvd_info: return

        if not nb: nb = self.dvd_info['longest_track']
        for track in self.dvd_info['track']:
            if track['ix'] == nb:
                self.selected_track = track
                self.selected_track["selected_chapter"] = -1
                break

    def select_chapter(self,track = None, chapter = 1, alang = None, \
                        slang = None):
        self.selected_track = self.select_track(track,alang,slang)
        self.selected_track["selected_chapter"] = chapter

    def get_current(self):
        if not self.dvd_info or not self.selected_track: return None

        # Construct item info for player
        id = str(self.selected_track["ix"])
        if self.selected_track["selected_chapter"] != -1:
            id += ".%d" % self.selected_track["selected_chapter"]
        uri = "dvd://%d" % self.selected_track["ix"]
        return {"title": self.dvd_info["title"], "type": "video", \
                "uri": uri, "chapter":self.selected_track["selected_chapter"],\
                "length": self.selected_track["length"],\
                "id": id, "audio": self.selected_track["audio"],\
                "subtitle": self.selected_track["subp"]}

    def go_to(self,id,type = "track"):
        if type == "track": self.select_track(id)
        elif type == "chapter": self.select_chapter(None,id)
        elif type == "dvd_id":
            ids = id.split('.')
            self.select_track(int(ids[0]))
            if len(ids) > 1 and self.selected_track:
                self.selected_track["selected_chapter"] = int(ids[1])

        return self.get_current()

    def next(self,random,repeat):
        if not self.dvd_info or not self.selected_track: return None

        if self.selected_track["selected_chapter"]:
            # go to next chapter
            self.selected_track["selected_chapter"] += 1
        else:
            # go to next title
            current_title = self.selected_track["ix"]
            self.select_track(current_title+1,self.selected_track["alang_idx"],\
                              self.selected_track["slang_idx"])

        return self.get_current()
            

    def previous(self,random,repeat):
        if not self.dvd_info or not self.selected_track: return None

        if self.selected_track["selected_chapter"]:
            # go to previous chapter
            self.selected_track["selected_chapter"] -= 1
        else:
            # go to next title
            current_title = self.selected_track["ix"]
            self.select_track(current_title+1,self.selected_track["alang_idx"],\
                              self.selected_track["slang_idx"])

        return self.get_current()

    def get_status(self):
        status = [("dvd",self.current_id)]
        return status

    def close(self):
        states = [(str(self.current_id),self.source_name+"id")]
        self.db.set_state(states)

# vim: ts=4 sw=4 expandtab
