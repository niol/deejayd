
class DvdError: pass

class DvdSource:

    def __init__(self, player, db, config):
        self.source_name = "dvd"
        self.player = player
        self.db = db
        self.current_id = int(self.db.get_state("dvdid"))

        self.dvd_info = None
        self.selected_track = None

        # FIXME add configuration options
        self.options = {"alang": "en", "slang": "en"}

        # FIXME test lsdvd support

        # load dvd content
        try: self.load()
        except: pass

    def get_content(self):
        return self.dvd_info

    def load(self):
        # Reinit var and update id
        self.dvd_info = None
        self.selected_track = None
        self.current_id +=1

        import popen2,sys
        r, w, e = popen2.popen3('lsdvd -c -a -s -Oy')
        # read error
        error = e.read()
        if error: raise DvdError("Unable to load the dvd : %s" % error)

        output = r.read()
        # close socket
        r.close()
        e.close()
        w.close()

        exec(output)
        self.dvd_info = lsdvd
        # select the default track of the dvd
        self.select_track()

    def select_track(self,nb = None,alang_idx = None, slang_idx = None):
        if not self.dvd_info: return

        if not nb: nb = self.dvd_info['longest_track']
        for track in self.dvd_info['track']:
            if track['ix'] == nb:
                self.selected_track = track
                self.selected_track["selected_chapter"] = None

                # select alang index
                found = False
                if not alang_idx: 
                    alang = self.options['alang']
                    for lang in track['audio']:
                        if lang == alang:
                            found = True
                            self.selected_track["alang_ix"] = lang['idx']
                            break
                    if not found: self.selected_track["alang_ix"] = 1
                else: self.selected_track["alang_ix"] = alang_idx

                # select slang index
                found = False
                if not slang_idx: 
                    slang = self.options['slang']
                    for lang in track['subp']:
                        if lang == slang:
                            found = True
                            self.selected_track["slang_ix"] = lang['idx']
                            break
                    if not found: self.selected_track["slang_ix"] = 1
                else: self.selected_track["slang_ix"] = slang_idx

                break

    def select_chapter(self,track = None, chapter = 1, alang = None, \
                        slang = None):
        self.selected_track = self.select_track(track,alang,slang)
        self.selected_track["selected_chapter"] = chapter

    def select_alang(self,alang_idx):
        pass

    def select_alang(self,alang_idx):
        pass

    def get_current(self):
        if not self.dvd_info or not self.selected_track: return None

        # Construct item info for player
        id = str(self.selected_track["ix"])
        if self.selected_track["selected_chapter"]:
            id += ".%d" % self.selected_track["selected_chapter"]
        uri = "dvd://%d" % self.selected_track["ix"]
        return {"title": self.dvd_info["title"], "type": "video", \
                "uri": uri, "alang":self.selected_track["alang_ix"],\
                "slang":self.selected_track["slang_ix"],\
                "chapter":self.selected_track["selected_chapter"],\
                "length": self.selected_track["length"],\
                "id": id,
                "audio": self.selected_track["audio"]}
                #"Subtitle": self.selected_track["subp"]}

    def go_to(self,id,type = "track"):
        if type == "track": self.select_track(id)
        elif type == "chapter": self.select_chapter(None,id)
        elif type == "id":
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
        if (self.dvd_info):
            status.extend([('dvd_lang','en')])
        return status

    def close(self):
        states = [(str(self.current_id),self.source_name+"id")]
        self.db.set_state(states)

# vim: ts=4 sw=4 expandtab
