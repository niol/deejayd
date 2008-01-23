# Deejayd, a media player daemon
# Copyright (C) 2007 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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

import os,subprocess

from deejayd.component import SignalingComponent
from deejayd.player import PlayerError

PLAYER_PLAY = "play"
PLAYER_PAUSE = "pause"
PLAYER_STOP = "stop"

class UnknownPlayer(SignalingComponent):

    def __init__(self, db, config):
        SignalingComponent.__init__(self)
        self.config = config
        self.db = db

        # Initialise var
        self._video_support = False
        self._source = None
        self._media_file = None
        self.options = {"random":0, "repeat":0}

    def load_state(self):
        # Restore volume
        self.set_volume(float(self.db.get_state("volume")))

        # Restore Random and Repeat
        self.options["random"] = int(self.db.get_state("random"))
        self.options["repeat"] = int(self.db.get_state("random"))

        # Restore the last media_file
        cur_id = self.db.get_state("currentPos")
        if cur_id != 0:
            self._media_file = self._source.get(cur_id,"id")

    def init_video_support(self):
        self._video_support = True
        self._fullscreen = self.config.getboolean("general", "fullscreen")

    def set_source(self,source):
        self._source = source

    def play(self):
        if self.get_state() == PLAYER_STOP:
            file = self._media_file or self._source.get_current()
            self._change_file(file)
        elif self.get_state() in (PLAYER_PAUSE, PLAYER_PLAY):
            self.pause()
        self.dispatch_signame('player.status')

    def pause(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def _change_file(self,new_file):
        self.stop()
        self._media_file = new_file
        self.start_play()
        self.dispatch_signame('player.current')

    def next(self):
        self._change_file(self._source.next(self.options["random"],\
            self.options["repeat"]))

    def previous(self):
        self._change_file(self._source.previous(self.options["random"],\
            self.options["repeat"]))

    def go_to(self,nb,type,source = None):
        self._change_file(self._source.get(nb,type,source))

    def get_volume(self):
        raise NotImplementedError

    def set_volume(self,v):
        raise NotImplementedError

    def get_position(self):
        raise NotImplementedError

    def set_position(self,pos):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def set_alang(self,lang_idx):
        if not self._media_file or self.get_state() == PLAYER_STOP: return

        try: audio_tracks = self._media_file["audio"]
        except KeyError: raise PlayerError
        else:
            if lang_idx in (-2,-1): # disable/auto audio channel
                self._player_set_alang(lang_idx)
                self._media_file["audio_idx"] = self._player_get_alang()
                return
            found = False
            for track in audio_tracks:
                if track['ix'] == lang_idx: # audio track exists
                    self._player_set_alang(lang_idx)
                    found = True
                    break
            if not found: raise PlayerError
            self._media_file["audio_idx"] = self._player_get_alang()

    def set_slang(self,lang_idx):
        if not self._media_file or self.get_state() == PLAYER_STOP: return

        try: sub_tracks = self._media_file["subtitle"]
        except KeyError: raise PlayerError
        else:
            if lang_idx in (-2,-1): # disable/auto subtitle channel
                self._player_set_slang(lang_idx)
                self._media_file["subtitle_idx"] = self._player_get_slang()
                return
            found = False
            for track in sub_tracks:
                if track['ix'] == lang_idx: # audio track exists
                    self._player_set_slang(lang_idx)
                    found = True
                    break
            if not found: raise PlayerError
            self._media_file["subtitle_idx"] = self._player_get_slang()

    def get_playing(self):
        return self.get_state() != PLAYER_STOP and self._media_file or None

    def set_option(self,name,value):
        if name not in self.options.keys():
            raise PlayerError
        self.options[name] = value
        self.dispatch_signame('player.status')

    def is_playing(self):
        return self.get_state() != PLAYER_STOP

    def get_status(self):
        status = []
        for key in self.options.keys():
            status.append((key,self.options[key]))

        status.extend([("state",self.get_state()),("volume",self.get_volume())])

        if self._media_file:
            status.append(("mediaid",self._media_file["id"]))
            if "pos" in self._media_file:
                status.append(("mediapos",self._media_file["pos"]))

        if self.get_state() != PLAYER_STOP:
            if "length" not in self._media_file.keys() or \
                                              self._media_file["length"] == 0:
                self._media_file["length"] = self.get_position()
            status.extend([ ("time","%d:%d" % (self.get_position(),\
                self._media_file["length"])) ])

        return status

    def close(self):
        cur_id = self._media_file and self._media_file["id"] or 0

        states = []
        for key in self.options:
            states.append((str(self.options[key]),key))

        states.append((str(self.get_volume()),"volume"))
        states.append((str(cur_id),"currentPos"))
        self.db.set_state(states)

        # stop player if necessary
        if self.get_state() != PLAYER_STOP:
            self.stop()

    def _is_lsdvd_exists(self):
        path = os.getenv('PATH')
        if not path: return False
        for p in path.split(':'):
            if os.path.isfile(os.path.join(p,"lsdvd")):
                return True
        return False

    def _get_dvd_info(self):
        command = 'lsdvd -Oy -s -a -c'
        lsdvd_process = subprocess.Popen(command, shell=True, stdin=None,\
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lsdvd_process.wait()

        # read error
        error = lsdvd_process.stderr.read()
        if error: raise PlayerError(error)

        output = lsdvd_process.stdout.read()
        exec(output)
        return lsdvd

# vim: ts=4 sw=4 expandtab
