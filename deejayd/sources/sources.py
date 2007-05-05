import sys

from deejayd.ui import log
from deejayd.player.gstreamer import NoSinkError

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
        if self.player.webradioSupport():
            from deejayd.sources import webradio
            self.sourcesObj["webradio"] = webradio.WebradioSource(player, db)
        else: log.msg("Webradio support disabled.")

        # Video
        video_support = config.get("general","video_support") == "yes"
        if video_support:
            from deejayd.sources import video
            self.sourcesObj["video"] = video.VideoSource(player, db)
            try: self.player.initVideoSupport()
            except(NoSinkError):
                error = 'Cannot initialise video sink, either disable video support or check your gstreamer plugins (video sink).' 
                log.err(error)
                # FIXME : Perhaps we could continue here, but don't know if
                # this is critical to deejayd operation if video support is
                # half initialised.
                sys.exit(error)

        # restore recorded source 
        source = db.getState("source")
        try: self.setSource(source)
        except unknownSourceException:
            log.err("Unable to set recorded source")
            self.setSource("playlist")

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
