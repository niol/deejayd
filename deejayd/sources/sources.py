class unknownSourceException: pass

class sourcesFactory:
    __supportedSources__ = ("playlist","webradio")

    def __init__(self,player,db):
        self.sourcesObj = {}
        self.player = player

        from deejayd.sources import playlist
        self.sourcesObj["playlist"] = playlist.PlaylistSource(player,db)

        import gst
        if gst.element_make_from_uri(gst.URI_SRC, "http://", ""):
            from deejayd.sources import webradio
            self.sourcesObj["webradio"] = webradio.WebradioSource(player)


        # For the moment we choose "playlist" for default source
        self.setSource("playlist")

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
