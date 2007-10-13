
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import ItemNotFoundException,UnknownSource,\
                            UnknownSourceManagement

class Queue(UnknownSource):
    queue_name = "__djqueue__"

    def __init__(self,db,library,id):
        UnknownSource.__init__(self,db,library,id)

        self.source_content = self.db.get_playlist(self.__class__.queue_name)
        # Format correctly queue content
        self.source_content = [self.format_playlist_files(s)
            for s in self.source_content]

    def save(self):
        # First we delete all previous record
        self.db.delete_playlist(self.__class__.queue_name)
        # After we record the new playlist
        self.db.save_playlist(self.source_content,self.__class__.queue_name)


class QueueSource(UnknownSourceManagement):
    name = "queue"

    def __init__(self,db,library): 
        UnknownSourceManagement.__init__(self,db,library)
        self.current_source = Queue(db,library,self.get_recorded_id())

    def add_path(self,paths,pos = None):
        songs = []
        if isinstance(paths,str):
            paths = [paths]
        for path in paths:
            try: songs.extend(self.library.get_all_files(path))
            except NotFoundException:
                try: songs.extend(self.library.get_file(path))
                except NotFoundException: raise ItemNotFoundException

        self.current_source.add_files(songs,pos)

    def load_playlist(self,playlists,pos = None):
        from deejayd.sources.playlist import Playlist
        songs = []
        if isinstance(playlists,str):
            playlists = [playlists]
        for playlist in playlists:
            source_content = Playlist(self.db,self.library,playlist)
            songs.extend(source_content.get_content())

        self.current_source.add_files(songs,pos)

    def go_to(self,nb,type = "id"):
        UnknownSourceManagement.go_to(self,nb,type)
        if self.current_item != None:
            self.current_source.delete(nb,type)
        return self.current_item

    def next(self,rd,rpt):
        self.go_to(0,'pos')
        return self.current_item

    def previous(self,rd,rpt):
        # Have to be never called
        raise NotImplementedError

    def reset(self):
        self.current_item = None

# vim: ts=4 sw=4 expandtab
