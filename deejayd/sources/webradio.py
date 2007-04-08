
from deejayd.mediadb.deejaydDB import NotFoundException
from deejayd.sources.unknown import *
import urllib

class UnsupportedFormatException: pass

def getPlaylistFileLines(URL):
    try: 
        plsHandle = urllib.urlopen(URL)
        playlist = plsHandle.read()
    except:
        raise NotFoundException

    return playlist.splitlines()

def getUrisFromPls(URL):
    uris = []
    lines = getPlaylistFileLines(URL)
    for line in lines:
        if line.lower().startswith("file") and line.find("=")!=-1:
            uris.append(line[line.find("=")+1:].strip())

    return uris

def getUrisFromM3u(URL):
    uris = []
    lines = getPlaylistFileLines(URL)
    for line in lines:
        if not line.startswith("#") and line.strip()!="":
            uris.append(line.strip())

    return uris


class Webradio(UnknownSource):

    def __init__(self,library,id): 
        UnknownSource.__init__(self,library,id)

        webradios = self.db.getWebradios() 
        self.sourceContent = [{"Pos":webradio[0],"Id":self.setItemId(), \
            "Title":webradio[1], "uri":webradio[2]} for webradio in webradios]

    def add(self,uri,name):
        pos = len(self.sourceContent)
        self.sourceContent.append({"Pos":pos,"Id":self.setItemId(),\
            "Title":name,"uri":uri})

        # Increment webradioId
        self.sourceId += 1

    def save(self):
        self.db.clearWebradios()
        values = [(webradio["Pos"],webradio["Title"],webradio["uri"]) \
            for webradio in self.sourceContent]
        self.db.addWebradios(values)


class WebradioSource(UnknownSourceManagement):

    def __init__(self, player, djDB):
        UnknownSourceManagement.__init__(self,player,djDB)

        # Init parms
        self.sourceName = "webradio"
        self.currentItem = None
        self.currentSource = Webradio(self.djDB,self.getRecordedId())

    def add(self,URL,name):
        if URL.lower().startswith("http://"):
            if URL.lower().endswith(".pls"):
                uris = getUrisFromPls(URL)
            elif URL.lower().endswith(".m3u"):
                uris = getUrisFromM3u(URL)
            else: uris = [URL]
        else: raise UnsupportedFormatException

        i = 1
        for uri in uris:
            self.currentSource.add(uri,name + "-%d" % (i,))
            i += 1
        return True

    def getStatus(self):
        return [('webradio',self.currentSource.sourceId),\
            ("webradiolength",self.currentSource.getContentLength())]


# vim: ts=4 sw=4 expandtab
