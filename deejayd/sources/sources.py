from deejayd.sources import playlist,webradio

class unknownSourceException: pass

class sourcesFactory:
    __supportedSources__ = ("playlist","webradio")

    def __init__(self,player):
        self.player = player
        # Initialise all the source
        self.sourcesObj = {}
        self.sourcesObj["playlist"] = playlist.PlaylistManagement(player)
        self.sourcesObj["webradio"] = webradio.WebradioManagement(player)

        # For the moment we choose "playlist" for default source
        self.setSource("playlist")

    def getSource(self,s):
        if s not in self.__class__.__supportedSources__:
            raise unknownSourceException

        return self.sourcesObj[s]

    def setSource(self,s):
        if s not in self.__class__.__supportedSources__:
            raise unknownSourceException

        self.player.setSource(self.sourcesObj[s],s)
        return True

    def getStatus(self):
        status = []
        for k in self.sourcesObj.keys():
            status.extend(self.sourcesObj[k].getStatus())

        return status

    def close(self):
        for k in self.sourcesObj.keys():
            self.sourcesObj[k].close()


# vim: ts=4 sw=4 expandtab
