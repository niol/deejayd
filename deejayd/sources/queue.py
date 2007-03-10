
from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources.unknown import *

class Queue(UnknownSource):
    queueName = "__djqueue__"

    def __init__(self,library,id):
        UnknownSource.__init__(self,library,id)
        self.rootPath = library.getRootPath()

        self.sourceContent = self.db.getPlaylist(self.__class__.queueName)
        # Format correctly queue content
        self.sourceContent = [self.formatMediadbPlaylistFiles(s)
            for s in self.sourceContent]

    def save(self):
        # First we delete all previous record
        self.db.deletePlaylist(self.__class__.queueName)
        # After we record the new playlist
        self.db.savePlaylist(self.sourceContent,self.__class__.queueName)


class QueueSource(UnknownSourceManagement):

    def __init__(self,player,djDB): 
        UnknownSourceManagement.__init__(self,player,djDB)
        self.sourceName = "queue"
        self.currentSource = Queue(self.djDB,self.getRecordedId())

    def getCurrent(self):
        return self.currentItem

    def add(self,files,pos = None):
        songs = []
        if isinstance(files,str):
            files = [files]
        for file in files:
            try: songs.extend(self.djDB.getAll(file))
            except NotFoundException:
                try: songs.extend(self.djDB.getFile(file))
                except NotFoundException: raise ItemNotFoundException

        self.currentSource.addMediadbFiles(songs,pos)

    def loadPlaylist(self,playlists,pos = None):
        from deejayd.sources.playlist import Playlist
        songs = []
        if isinstance(playlists,str):
            playlists = [playlists]
        for playlist in playlists:
            sourceContent = Playlist(self.djDB,playlist)
            songs.extend(sourceContent.getContent())

        self.currentSource.addMediadbFiles(songs,pos)

    def getStatus(self):
        return [("queue",self.currentSource.sourceId),\
            ("queuelength",self.currentSource.getContentLength())]

    def goTo(self,nb,type = "Id"):
        UnknownSourceManagement.goTo(self,nb,type)
        if self.currentItem != None:
            self.currentSource.delete(nb,type)
        return self.currentItem

    def next(self,rd,rpt):
        self.goTo(0,'Pos')
        return self.currentItem

    def previous(self,rd,rpt):
        # Have to be never called
        raise NotImplementedError

    def reset(self):
        self.currentItem = None

# vim: ts=4 sw=4 expandtab
