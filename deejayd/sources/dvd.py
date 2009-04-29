# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


from deejayd.component import SignalingComponent
from deejayd.player._base import PlayerError
from deejayd.player.xine import DvdParser

class DvdError(Exception): pass

class DvdSource(SignalingComponent):
    name = "dvd"

    def __init__(self, db, config):
        super(DvdSource, self).__init__()
        try: self.parser = DvdParser()
        except PlayerError, ex: # dvd parser does not work
            raise DvdError(ex)

        self.db = db
        self.current_id = int(self.db.get_state("dvdid")) + 1

        self.dvd_info = None
        self.selected_track = None

    def get_content(self):
        if not self.dvd_info:
            return {'title': "DVD NOT LOADED", 'longest_track': "0", \
                    'track': []}
        return self.dvd_info

    def load(self):
        # Reinit var and update id
        self.dvd_info = None
        self.selected_track = None
        self.current_id +=1

        try: self.dvd_info = self.parser.get_dvd_info()
        except PlayerError, err:
            raise DvdError("Unable to load the dvd : %s " % err)
        # select the default track of the dvd
        self.select_track()
        self.dispatch_signame('dvd.update')

    def select_track(self,nb = None,alang_idx = None, slang_idx = None):
        if not self.dvd_info: return

        if not nb: nb = self.dvd_info['longest_track']
        for track in self.dvd_info['track']:
            if int(track['ix']) == int(nb):
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
        pos = int(self.selected_track["ix"])
        if self.selected_track["selected_chapter"] != -1:
            id += ".%d" % self.selected_track["selected_chapter"]
            pos = self.selected_track["selected_chapter"]
        uri = "dvd://%d" % self.selected_track["ix"]
        return {"title": self.dvd_info["title"], "type": "video", \
                "uri": uri, "chapter":self.selected_track["selected_chapter"],\
                "length": self.selected_track["length"],\
                "id": id, "pos": pos,\
                "audio": self.selected_track["audio"],\
                "subtitle": self.selected_track["subp"]}

    def go_to(self,id,type = "track"):
        if type in ("track", "id"): self.select_track(id)
        elif type == "chapter": self.select_chapter(None,id)
        elif type == "dvd_id":
            ids = id.split('.')
            self.select_track(int(ids[0]))
            if len(ids) > 1 and self.selected_track:
                self.selected_track["selected_chapter"] = int(ids[1])

        return self.get_current()

    def next(self, explicit = True):
        if not self.dvd_info or not self.selected_track: return None

        if self.selected_track["selected_chapter"] != -1:
            # go to next chapter
            self.selected_track["selected_chapter"] += 1
        else:
            # go to next title
            current_title = self.selected_track["ix"]
            self.select_track(current_title+1)

        return self.get_current()


    def previous(self):
        if not self.dvd_info or not self.selected_track: return None

        if self.selected_track["selected_chapter"] != -1:
            # go to previous chapter
            self.selected_track["selected_chapter"] -= 1
        else:
            # go to previous title
            current_title = self.selected_track["ix"]
            self.select_track(current_title - 1)

        return self.get_current()

    def get_status(self):
        length = 0
        if self.dvd_info: length = len(self.dvd_info)
        status = [
            (self.name, self.current_id),
            (self.name+"length",length)
            ]
        return status

    def close(self):
        states = [(str(self.current_id),self.__class__.name+"id")]
        self.db.set_state(states)
        self.parser.close()

# vim: ts=4 sw=4 expandtab
