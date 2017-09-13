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

import base64
from sqlalchemy import text
from deejayd.jsonrpc.interfaces import AudioLibraryModule, jsonrpc_module
from deejayd.library._base import BaseLibrary
from deejayd.library.parsers.audio import AudioParserFactory
from deejayd.db.models import Song, Album
from deejayd.db.connection import Session


@jsonrpc_module(AudioLibraryModule)
class AudioLibrary(BaseLibrary):
    OBJECT_CLASS = Song
    TYPE = "audio"
    PARSER = AudioParserFactory
    UPDATE_SIGNAL_NAME = "library.aupdate"
    DEFAULT_SORT = text('Song.discnumber, Song.tracknumber')
    state_name = "audiolib"

    def get_stats(self):
        return {
            "audio_library_update": self.state["last_update"],
            "songs": Session.query(Song).count(),
            "albums": Session.query(Album).count(),
            "artists": Session.query(Song.artist).distinct().count()
        }

    def album_list(self, ft=None, cover=False):
        query = Session.query(Album)
        if ft is not None:
            query = query.join(Song)\
                         .filter(ft.get_filter(Song))\
                         .order_by(Album.name)

        return [a.to_json(cover=cover) for a in query.all()]

    def album_details(self, a_id):
        album = Session.query(Album)\
                       .filter(Album.id == a_id)\
                       .one_or_none()
        if album is not None:
            return album.to_json(cover=True, songs=True)
        return None

    def get_cover(self, a_id):
        album = Session.query(Album)\
                       .filter(Album.id == a_id)\
                       .one_or_none()
        if album.cover is not None:
            return {
                "data": base64.b64decode(album.cover),
                "mimetype": album.cover_type
            }
        return None


if __name__ == "__main__":
    import sys
    import pprint
    from deejayd.ui.i18n import DeejaydTranslations
    from deejayd.db import connection
    from deejayd.db.models import Equals
    
    pp = pprint.PrettyPrinter(indent=2)
    # init filter and audio library
    f = Equals(tag="artist", pattern="J.A.H.O.")
    DeejaydTranslations().install()
    connection.init("sqlite://")
    Session()
    library = AudioLibrary(sys.argv[1])
    library.update(sync=True)

    # display root content
    print("------------ Library content -------------")
    pp.pprint(library.get_dir_content(''))

    # display album list
    print("------------ Album list -------------")
    pp.pprint(library.album_list())
    print(library.album_details(2))
    # test simple filter
    print("------------ Simple equal filter -------------")
    pp.pprint(library.album_list(f))
    pp.pprint(library.search(f))

    Session.remove()
