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

from sqlalchemy import text
from deejayd.jsonrpc.interfaces import LibraryModule, jsonrpc_module
from deejayd.db.connection import Session
from deejayd.library._base import BaseLibrary
from deejayd.library.parsers.video import VideoParserFactory
from deejayd.db.models import Video


@jsonrpc_module(LibraryModule)
class VideoLibrary(BaseLibrary):
    OBJECT_CLASS = Video
    TYPE = "video"
    PARSER = VideoParserFactory
    DEFAULT_SORT = text('Media.title')
    UPDATE_SIGNAL_NAME = "library.vupdate"
    state_name = "videolib"

    def get_stats(self):
        return {
            "video_library_update": self.state["last_update"],
            "videos": Session.query(Video).count()
        }



if __name__ == "__main__":
    import sys
    import pprint
    from deejayd.ui.i18n import DeejaydTranslations
    from deejayd.db import connection

    pp = pprint.PrettyPrinter(indent=2)
    DeejaydTranslations().install()
    connection.init("sqlite://")
    library = VideoLibrary(sys.argv[1])
    library.update(sync=True)

    pp.pprint(library.get_dir_content(''))
    pp.pprint([v.to_json() for v in library.get_all_files([1])])
