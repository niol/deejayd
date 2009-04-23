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

import random

__all__ = ["SimpleMediaList", "SortedMediaList", "UnsortedMediaList"]

class SimpleMediaList(object):

    def __init__(self, list_id = 0):
        self._media_id = 0
        self._order, self._content = [], {}
        self.repeat = False

        self.list_id = list_id
        self.time_length = 0

    def __len__(self):
        return len(self._order)

    def _set_media_id(self):
        self._media_id += 1
        return self._media_id

    def _set_media_ans(self, id, pos = -1):
        try: ans = self._content[id]
        except KeyError:
            return None
        ans.update({"id": id, "pos": pos})
        return ans

    def get(self, start = 0, stop = None):
        stop = stop or len(self._order)
        return map(self._set_media_ans, self._order[start:stop],\
                    range(start, stop))

    def get_item(self, id):
        try: return self._set_media_ans(id, self._order.index(id))
        except ValueError:
            return None

    def get_item_first(self):
        if self._order:
            return self._set_media_ans(self._order[0], 0)
        return None

    def get_item_last(self):
        if self._order:
            return self._set_media_ans(self._order[-1], len(self._order)-1)
        return None

    def get_ids(self):
        return self._order

    def reload_item_pos(self, media):
        try: pos = self._order.index(media["id"])
        except TypeError: return
        except ValueError:
            pos = -1
        media["pos"] = pos

    def set(self, medias):
        self._order, self._content = [], {}
        self.time_length = 0
        self.add_media(medias)

    def add_media(self, medias, first_pos = None):
        first_pos = first_pos or len(self._order)

        for index, m in enumerate(medias):
            id = self._set_media_id()
            self._order.insert(first_pos + index, id)
            self._content[id] = m
            # update medialist time length
            try: length = int(m["length"])
            except (ValueError, KeyError, TypeError):
                continue
            self.time_length += length
        self.list_id += 1

    def clear(self):
        self._order, self._content = [], {}
        self.time_length = 0
        self.list_id += 1

    def delete(self, ids, type = "id"):
        if type == "pos": ids = [self._order[p] for p in ids]
        missing_ids = [id for id in ids if id not in self._order]
        if missing_ids: return False

        for id in ids:
            self._order.remove(id)
            # update time length
            try: length = int(self._content[id]["length"])
            except (ValueError, KeyError, TypeError): continue
            else: self.time_length -= length
            del self._content[id]
        self.list_id += 1
        return True

    def next(self, media):
        try:
            idx = self._order.index(media["id"])
            id = self._order[idx+1]
        except ValueError: # id not found, try to find by media_id
            id = None
            if media:
                for list_id, m in self._content.items():
                    if m["media_id"] == media["media_id"]:
                        idx = self._order.index(m["id"])
                        try: id = self._order[idx+1]
                        except IndexError: # end of medialist
                            return None
                        break
            if id is None: return None
        except (IndexError, KeyError, TypeError):
            return None
        return self._set_media_ans(id, idx+1)

    def previous(self, media):
        try:
            idx = self._order.index(media["id"])
            id = idx and self._order[idx-1] or None
        except (ValueError, KeyError):
            return None
        return self._set_media_ans(id, idx-1)

    def find_id(self, media_id):
        for id, m in self._content.items():
            if m["media_id"] == media_id:
                return id
        raise ValueError


class _MediaList(SimpleMediaList):

    #
    # library changes action
    #
    def remove_media(self, media_id):
        ans = False
        for key, media in self._content.items():
            if media["media_id"] == media_id:
                self._order.remove(key)
                del self._content[key]
                ans = True
                try: length = int(media["length"])
                except (ValueError, KeyError, TypeError):
                    continue
                self.time_length -= length
        if ans: self.list_id += 1
        return ans

    def update_media(self, new_media):
        ans = False
        for key, m in self._content.items():
            if m["media_id"] == new_media["media_id"]:
                self._content[key] = new_media
                ans = True
        if ans: self.list_id += 1
        return ans


class UnsortedMediaList(_MediaList):

    def move(self, ids, new_pos, type = "id"):
        if type == "pos": ids = [self._order[p] for p in ids]
        missing_ids = [id for id in ids if id not in self._order]
        if missing_ids: return False

        s_list = [id for id in self._order[:new_pos] if id not in ids]
        e_list = [id for id in self._order[new_pos:] if id not in ids]
        self._order = s_list + ids + e_list
        self.list_id += 1
        return True

    def shuffle(self, current = None):
        if not self._order: return
        random.shuffle(self._order)
        if current and current["id"]:
            try: self._order.remove(current["id"])
            except ValueError: pass
            else:
                self._order = [current["id"]] + self._order
        self.list_id += 1


class SortedMediaList(_MediaList):

    def __init__(self, list_id = 0):
        super(SortedMediaList, self).__init__(list_id)

    #
    # sort actions
    #
    def __compare_tag(self, id1, id2, tag, direction):
        m1 = self._content[id1]
        m2 = self._content[id2]
        if m1[tag] < m2[tag]:
            return direction == "ascending" and -1 or 1
        elif m1[tag] == m2[tag]:
            return 0
        else:
            return direction == "ascending" and 1 or -1

    def sort(self, sorts):

        def compare(id1, id2):
            for (tag, direction) in sorts:
                result = self.__compare_tag(id1, id2, tag, direction)
                if result != 0: return result
            return 0

        self._order.sort(cmp=compare)
        self.list_id += 1

# vim: ts=4 sw=4 expandtab