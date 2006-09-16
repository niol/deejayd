
from deejayd.mediadb.deejaydDB import djDB,database,NotFoundException
import urllib

class NotFoundException: pass
class UnsupportedFormatException: pass

def getUrisFromPls(URL):
    try: 
        plsHandle = urllib.urlopen(URL)
        playlist = plsHandle.read()
    except: return None

    uris = []
    lines = playlist.splitlines()
    for line in lines:
        if line.lower().startswith("file") and line.find("=")!=-1:
            uris.append(line[line.find("=")+1:].strip())

    return uris

def getUrisFromM3u(URL):
    try: 
        plsHandle = urllib.urlopen(URL)
        playlist = plsHandle.read()
    except: return None

    uris = []
    lines = playlist.splitlines()
    for line in lines:
        if not line.startswith("#") and line.strip()!="":
            uris.append(line.strip())

    return uris


class Webradio:

    def __init__(self,db): 
        self.db = db
        self.__wrId = 0
        self.webradioId = 0
        webradios = self.db.getWebradios() 
        self.wrContent = [{"Pos":webradio[0],"Id":self.__getId(), "Title":webradio[1], "uri":webradio[2]} \
                            for webradio in webradios]

    def getList(self):
        return self.wrContent

    def get(self,id,type):
        wr = None
        for w in self.wrContent:
            if w[type] == id:
                wr = w
                break

        if wr == None: raise NotFoundException
        return wr

    def add(self,uri,name):
        pos = len(self.wrContent)
        self.wrContent.append({"Pos":pos,"Id":self.__getId(), "Title":name, "uri":uri})

        # Increment webradioId
        self.webradioId += 1

    def erase(self,nb,type = "Id"):
        i = 0
        for w in self.wrContent:
            if w[type] == nb:
                break
            i += 1
        if i == len(self.wrContent):
            raise NotFoundException
        pos = self.wrContent[i]["Pos"]
        del self.wrContent[i]

        # Now we must reorder the playlist
        for w in self.wrContent:
            if w["Pos"] > pos:
                w["Pos"] -= 1

        # Increment webradioId
        self.webradioId += 1

    def clear(self):
        self.wrContent = []
        # Increment webradioId
        self.webradioId += 1

    def save(self):
        self.db.clearWebradios()
        values = [(webradio["Pos"],webradio["Title"],webradio["uri"]) for webradio in self.wrContent]
        self.db.addWebradios(values)

    def __getId(self):
        self.__wrId +=1
        return self.__wrId


class WebradioManagement:

    def __init__(self,player):
        # Init player
        self.player = player
        # Open a connection to the database
        self.db = database.openConnection()
        self.db.connect()
        # Init parms
        self.webradioCurrent = None
        self.wrContent = Webradio(self.db)

    def getList(self):
        return self.wrContent.getList() 

    def addWebradio(self,URL,name):
        if URL.lower().startswith("http://"):
            if URL.lower().endswith(".pls"):
                uris = getUrisFromPls(URL)
            elif URL.lower().endswith(".m3u"):
                uris = getUrisFromM3u(URL)
            else: uris = [URL]
        else: raise UnsupportedFormatException

        i = 1
        for uri in uris:
            self.wrContent.add(uri,name + "-%d" % (i,))
            i += 1
        return True

    def erase(self,id):
        self.wrContent.erase(id)

    def clear(self):
        self.wrContent.clear()

    def next(self,rd,rpt):
        pass

    def previous(self,rd,rpt):
        pass

    def getCurrent(self):
        if self.webradioCurrent == None:
            self.webradioCurrent = self.wrContent.get(0,"Pos")

        return self.webradioCurrent

    def goTo(self,nb,type):
        self.webradioCurrent = self.wrContent.get(nb,type)
        return self.webradioCurrent

    def getStatus(self):
        return [('webradio',self.wrContent.webradioId)]

    def close(self):
        self.wrContent.save()
        self.db.close()


# vim: ts=4 sw=4 expandtab
