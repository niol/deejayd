# Deejayd, a media player daemon
# Copyright (C) 2007-2017 Mickael Royer <mickael.royer@gmail.com>
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


class Order(object):

    # Not called directly, but the default implementation of
    # next_explicit and next_implicit both just call this.
    def next(self, medialist, current):
        raise NotImplementedError

    # Not called directly, but the default implementation of
    # previous_explicit calls this. Right now there is no such thing
    # as previous_implicit.
    def previous(self, medialist, current):
        raise NotImplementedError

    # Not called directly, but the default implementation of
    # set_explicit calls this. Right now there is no such thing as
    # set_implicit.
    def set(self, medialist, media_id):
        return medialist.get_item(media_id)

    # Called when the user presses a "Next" button.
    def next_explicit(self, medialist, current):
        return self.next(medialist, current)

    # Called when a media ends passively, e.g. it plays through.
    def next_implicit(self, medialist, current):
        return self.next(medialist, current)

    # Called when the user presses a "Previous" button.
    def previous_explicit(self, medialist, current):
        return self.previous(medialist, current)

    # Called when the user manually selects a media
    # If desired the play order can override that
    def set_explicit(self, medialist, media_id):
        return self.set(medialist, media_id)

    def reset(self, medialist):
        pass


class OrderInOrder(Order):
    name = "inorder"

    def next(self, medialist, current):
        if current is None:
            return medialist.get_item_first()
        else:
            next = medialist.next(current)
            if next is None and medialist.repeat:
                next = medialist.get_item_first()
            return next

    def previous(self, medialist, current):
        if len(medialist) == 0:
            return None
        elif current is None:
            return medialist.get_item_last()
        else:
            previous = medialist.previous(current)
            if previous is None and medialist.repeat:
                previous = medialist.get_item_last()
            return previous


class OrderRemembered(Order):
    # Shared class for all the shuffle modes that keep a memory
    # of their previously played medias.

    def __init__(self):
        self._played = []

    def next(self, medialist, current):
        if current is not None:
            self._played.append(current["id"])

    def previous(self, medialist, current):
        try: 
            id = self._played.pop()
        except IndexError: 
            return None
        else: 
            return medialist.get_item(id)

    def set(self, medialist, media_id):
        self._played.append(media_id)
        return medialist.get_item(media_id)

    def reset(self, medialist):
        self._played = []


class OrderShuffle(OrderRemembered):
    name = "random"

    def next(self, medialist, current):
        super(OrderShuffle, self).next(medialist, current)
        played = set(self._played)
        medias = set([m["id"] for m in medialist.get()])
        remaining = medias.difference(played)

        if remaining:
            return medialist.get_item(random.choice(list(remaining)))
        elif medialist.repeat and not medialist.is_empty():
            del(self._played[:])
            return medialist.get_item(random.choice(medias))
        else:
            del(self._played[:])
            return None


class OrderWeighted(OrderRemembered):
    name = "random-weighted"

    def next(self, medialist, current):
        super(OrderWeighted, self).next(medialist, current)
        played = set(self._played)
        remaining = [(m["id"], int(m["rating"])) 
                     for m in medialist.get() if m["id"] not in played]

        max_score = sum([r for (id, r) in remaining])
        choice = int(random.random() * max_score)
        current = 0
        for id, rating in remaining:
            current += rating
            if current >= choice:
                return medialist.get_item(id)

        if medialist.repeat and not medialist.is_empty():
            del(self._played[:])
            return medialist.get_item_first()
        else:
            del(self._played[:])
            return None


class OrderOneMedia(OrderInOrder):
    name = "onemedia"

    def next_implicit(self, medialist, current):
        if medialist.repeat:
            return current
        else:
            return None


orders = {
    "onemedia": OrderOneMedia(),
    "inorder": OrderInOrder(),
    "random": OrderShuffle(),
    "random-weighted": OrderWeighted(),
    }
