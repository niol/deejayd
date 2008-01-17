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

import os
import random, urllib

class MediaNotFoundError(Exception):pass
class PlaylistNotFoundError(Exception):pass

class SimpleMediaList:

    def __init__(self, id = 0):
        self._list_id = id
        self._media_id = 0
        self._content = []

    def get(self):
        return self._content

    def get_ids(self):
        return [m["id"] for m in self._content]

    def set(self, medias):
        self._content = []
        self.add_media(medias)

    def length(self):
        return len(self._content)

    def add_media(self, medias, first_pos = None):
        if first_pos == None:
            first_pos = len(self._content)
        old_content = self._content[first_pos:]
        self._content = self._content[:first_pos]

        i = 0
        for m in medias:
            pos = first_pos + i
            m["pos"] = pos
            if "id" not in m.keys() or m["type"] == "song":
                m["id"] = self.set_media_id()
            self._content.append(m)
            i += 1

        for media in old_content:
            media["pos"] = first_pos + i
            i+=1

        self._content.extend(old_content)
        self._list_id += 1

    def clear(self):
        self._content = []
        self._list_id += 1

    def delete(self, id, type = "id"):
        i = 0
        for media in self._content:
            if media[type] == id:
                break
            i += 1
        if i == len(self._content):
            raise MediaNotFoundError

        pos = self._content[i]["pos"]
        del self._content[i]
        # Now we must reorder the media list
        for media in self._content:
            if media["pos"] > pos:
                media["pos"] -= 1
        self._list_id += 1

    def get_media(self, id, type = "id"):
        media = None
        for m in self._content:
            if m[type] == id:
                media = m
                break

        if media == None:
            raise MediaNotFoundError
        return media

    def get_list_id(self):
        return self._list_id

    def set_media_id(self):
        self._media_id += 1
        return self._media_id


class MediaList(SimpleMediaList):

    def __init__(self, db, id = 0):
        SimpleMediaList.__init__(self, id)
        self.db = db

    def __format_playlist_file(self, s, root_path):
        return {"dir":s[0],"filename":s[1],"pos":s[3],"id":self.set_media_id(),
            "title":s[6],"artist":s[7],"album":s[8],"genre":s[9],"track":s[10],
            "date":s[11],"length":s[12],"bitrate":s[13],
            "path":os.path.join(s[0],s[1]),
            "uri":"file://"+urllib.quote(os.path.join(root_path,s[0],s[1])),
            "type":"song"}

    def load_playlist(self, name, root_path, pos = None):
        content = self.db.get_audiolist(name)
        if len(content) == 0 and (not name.startswith("__") or \
                                  not name.endswith("__")):
            raise PlaylistNotFoundError

        medias = [self.__format_playlist_file(s, root_path) for s in content]
        self.add_media(medias, pos)

    def move(self, ids, new_pos, type):
        medias = []
        for id in ids:
            medias.append(self.get_media(id, type))

        old_content = self._content
        self._content = []
        for index, media in enumerate(old_content):
            if index == new_pos:
                self._content.extend(medias)
            if media not in medias:
                self._content.append(media)

        # Reorder the list
        ids = range(0,len(self._content))
        for id in ids:
            self._content[id]["pos"] = id
        # Increment sourceId
        self._list_id += 1

    def shuffle(self, current = None):
        new_content = []
        old_content = self._content
        pos = 0
        # First we have to put the current song at the first place
        if current != None:
            old_pos = current["pos"]
            del old_content[old_pos]
            new_content.append(current)
            new_content[pos]["pos"] = pos
            pos += 1

        while len(old_content) > 0:
            song = random.choice(old_content)
            del old_content[old_content.index(song)]
            new_content.append(song)
            new_content[pos]["pos"] = pos
            pos += 1

        self._content = new_content
        self._list_id += 1


class _BaseSource:
    name = "unknown"

    def __init__(self, db):
        self.db = db
        self._current = None
        self._played = []

    def get_recorded_id(self):
        id = int(self.db.get_state(self.name+"id"))
        return id

    def get_content(self):
        return self._media_list.get()

    def get_current(self):
        if self._current == None:
            self.go_to(0,"pos")

        return self._current

    def go_to(self, id, type = "id"):
        try: self._current = self._media_list.get_media(id, type)
        except MediaNotFoundError:
            self._current = None
        else:
            if self._current["id"] not in self._played:
                self._played.append(self._current["id"])

        return self._current

    def delete(self, id):
        self._media_list.delete(id)
        try: self._played.remove(id)
        except ValueError:
            pass

    def clear(self):
        self._media_list.clear()
        self._played = []

    def next(self, rd, rpt):
        if self._current == None:
            self.go_to(0,"pos")
            return self._current

        # add current media in played list
        if self._current["id"] not in self._played:
            self._played.append(self._current["id"])

        # Return a pseudo-random song
        l = self._media_list.length()
        if rd and l > 0:
            # first determine if the current song is in playedItems
            #id = self._played.index(self._current["id"])
            #try: new_id = self._played[id+1]
            #except IndexError: pass
            #else:
            #    self._current = self._media_list.get_media(new_id ,"id")
            #    return self._current

            # Determine the id of the next song
            values = [id for id in self._media_list.get_ids() \
                        if id not in self._played]
            try: new_id = random.choice(values)
            except IndexError: # All songs are played
                if rpt:
                    self._played = []
                    new_id = random.choice(self.current_source.get_item_ids())
                else:
                    self._current = None
                    return None

            # Obtain the choosed song
            try: self._current = self._media_list.get_media(new_id, "id")
            except MediaNotFoundError:
                self._current = None
            return self._current

        cur_pos = self._current["pos"]
        if cur_pos < self._media_list.length()-1:
            try: self._current = self._media_list.get_media(cur_pos + 1, "pos")
            except MediaNotFoundError:
                self._current = None
        elif rpt:
            self._current = self._media_list.get_media(0, "pos")
        else:
            self._current = None

        return self._current

    def previous(self,rd,rpt):
        if self._current == None:
            return None

        # add current media in played list
        if self._current["id"] not in self._played:
            self._played.append(self._current["id"])

        # Return the last pseudo-random media
        if rd:
            id = self._played.index(self._current["id"])
            if id == 0:
                self._current = None
                return self._current
            try: self._current = self._media_list.get_media(self._played[id-1])
            except MediaNotFoundError:
                self._current = None
            return self._current

        cur_pos= self._current["pos"]
        if cur_pos > 0:
            self._current = self._media_list.get_media(cur_pos - 1, "pos")
        else:
            self._current = None

        return self._current

    def get_status(self):
        return [
            (self.name, self._media_list.get_list_id()),
            (self.name+"length", self._media_list.length())
            ]

    def close(self):
        states = [
            (str(self._media_list.get_list_id()),self.__class__.name+"id")
            ]
        self.db.set_state(states)

# vim: ts=4 sw=4 expandtab
