from twisted.python import log

class unknownSourceException: pass

class sourcesFactory:

    def __init__(self,player,db,config):
        self.sourcesObj = {}
        self.player = player

        # Playlist and Queue
        from deejayd.sources import playlist,queue
        self.sourcesObj["playlist"] = playlist.PlaylistSource(player,db)
        self.sourcesObj["queue"] = queue.QueueSource(player,db)

        # Webradio
        import gst
        if gst.element_make_from_uri(gst.URI_SRC, "http://", ""):
            from deejayd.sources import webradio
            self.sourcesObj["webradio"] = webradio.WebradioSource(player, db)
        else:
            log.msg("Webradio support disabled : require gst-plugins-gnomevfs")

        # Video
        video_support = config.get("general","video_support")== "true"
        if video_support:
            from deejayd.sources import video
            self.sourcesObj["video"] = video.VideoSource(player, db)
            self.player.initVideoSupport()

        # restore recorded source 
        source = db.getState("source")
        self.setSource(source)
        self.player.setQueue(self.sourcesObj["queue"])
        self.player.loadState()

    def getSource(self,s):
        if s not in self.sourcesObj.keys():
            raise unknownSourceException

        return self.sourcesObj[s]

    def setSource(self,s):
        if s not in self.sourcesObj.keys():
            raise unknownSourceException

        self.player.setSource(self.sourcesObj[s],s)
        return True

    def getStatus(self):
        status = []
        for k in self.sourcesObj.keys():
            status.extend(self.sourcesObj[k].getStatus())

        return status

    def getAvailableSources(self):
        return self.sourcesObj.keys()

    def close(self):
        for k in self.sourcesObj.keys():
            self.sourcesObj[k].close()


# vim: ts=4 sw=4 expandtab
