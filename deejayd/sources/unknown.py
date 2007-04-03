from os import path
import random


class ItemNotFoundException:pass

class UnknownSource:

    def __init__(self,library, id):
        self.db = library.getDB()
        self.sourceContent = []
        self.sourceId = id
        self.__itemId = 0

    def getContent(self):
        return self.sourceContent

    def getContentLength(self):
        return len(self.sourceContent)

    def getItem(self,position, type = "Pos"):
        item = None
        for it in self.sourceContent:
            if it[type] == position:
                item = it
                break

        if item == None:
            raise ItemNotFoundException
        return item

    def getItemIds(self):
        return [item["Id"] for item in self.sourceContent]

    def addMediadbFiles(self,items,firstPos):
        initPos = firstPos or len(self.sourceContent)
        oldContent = self.sourceContent[initPos:len(self.sourceContent)]
        self.sourceContent = self.sourceContent[0:initPos]

        i = 0
        for s in items:
            pos = initPos+i
            if isinstance(s,dict): # file extracted from a playlist
                self.sourceContent.append({"dir":s["dir"],
                    "filename":s["filename"],"Pos":pos,"Id":self.setItemId(),
                    "Title":s["Title"],"Artist":s["Artist"],"Album":s["Album"],
                    "Genre":s["Genre"],"Track":s["Track"],"Date":s["Date"],
                    "Time":s["Time"],"bitrate":s["bitrate"],"uri":s["uri"]})
            else: # file extracted from mediadb
                self.sourceContent.append({"dir":s[0],"filename":s[1],
                    "Pos":pos,"Id":self.setItemId(),"Title":s[3],
                    "Artist":s[4],"Album":s[5],"Genre":s[6],"Track":s[7],
                    "Date":s[8],"Time":s[9],"bitrate":s[10],"uri":"file://"+\
                    path.join(self.rootPath,path.join(s[0],s[1]))})
            i += 1

        for song in oldContent:
            song["Pos"] = initPos+i
            i+=1

        self.sourceContent.extend(oldContent)
        # Increment sourceId
        self.sourceId += len(items)

    def clear(self):
        self.sourceContent = []
        # Increment sourceId
        self.sourceId += 1

    def delete(self,nb,type = "Id"):
        i = 0
        for item in self.sourceContent:
            if item[type] == nb:
                break
            i += 1
        if i == len(self.sourceContent):
            raise ItemNotFoundException
        pos = self.sourceContent[i]["Pos"]
        del self.sourceContent[i]

        # Now we must reorder the item list
        for item in self.sourceContent:
            if item["Pos"] > pos:
                item["Pos"] -= 1

        # Increment sourceId
        self.sourceId += 1

    def save(self):
        raise NotImplementedError
    
    def formatMediadbPlaylistFiles(self,s):
        return {"dir":s[0],"filename":s[1],"Pos":s[3],"Id":self.setItemId(),
            "Title":s[6],"Artist":s[7],"Album":s[8],"Genre":s[9],"Track":s[10],
            "Date":s[11],"Time":s[12],"bitrate":s[13],
            "uri":"file://"+path.join(self.rootPath,path.join(s[0],s[1]))}

    def setItemId(self):
        self.__itemId += 1
        return self.__itemId
    

class UnknownSourceManagement:
    
    def __init__(self,player,djDB):
        self.player = player
        self.djDB = djDB
        self.currentItem = None

    def getRecordedId(self):
        id = int(self.djDB.getState(self.sourceName+"id"))
        return id

    def getContent(self):
        return self.currentSource.getContent()

    def getCurrent(self):
        if self.currentItem == None:
            self.goTo(0,"Pos")

        return self.currentItem

    def getPlayingItem(self):
        if self.currentItem and self.player.isPlay():
            return self.currentItem
        return None

    def goTo(self,nb,type = "Id"):
        try: self.currentItem = self.currentSource.getItem(nb,type)
        except ItemNotFoundException: self.currentItem = None

        return self.currentItem
        
    def delete(self,id):
        self.currentSource.delete(id)

    def clear(self):
        self.currentSource.clear()

    def next(self,rd,rpt):  
        if self.currentItem == None:
            self.goTo(0,'Pos')
            return self.currentItem

        currentPos = self.currentItem["Pos"]
        if currentPos < self.currentSource.getContentLength()-1:
            try: self.currentItem = self.currentSource.getItem(currentPos+1,\
                "Pos")
            except ItemNotFoundException: self.currentItem = None
        else: self.currentItem = None

        return self.currentItem

    def previous(self,rd,rpt):
        if self.currentItem == None:
            return None

        currentPos = self.currentItem["Pos"]
        if currentPos > 0:
            try: self.currentItem = self.currentSource.get(currentPos-1,"Pos")
            except ItemNotFoundException: self.currentItem = None
        else: self.currentItem = None

        return self.currentItem

    def close(self):
        states = [(str(self.currentSource.sourceId),self.sourceName+"id")]
        self.djDB.setState(states)
        self.currentSource.save()

# vim: ts=4 sw=4 expandtab
