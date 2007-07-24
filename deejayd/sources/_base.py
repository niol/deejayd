from os import path
import random


class ItemNotFoundException:pass

class UnknownSource:

    def __init__(self,db,library, id = 0):
        self.db = db
        self.library = library
        self.source_content = []
        self.source_id = id
        self.__item_id = 0

    def get_content(self):
        return self.source_content

    def get_content_length(self):
        return len(self.source_content)

    def get_item(self,position, type = "pos"):
        item = None
        for it in self.source_content:
            if it[type] == position:
                item = it
                break

        if item == None:
            raise ItemNotFoundException
        return item

    def get_item_ids(self):
        return [item["id"] for item in self.source_content]

    def add_files(self,items,first_pos = 0):
        init_pos = first_pos or len(self.source_content)
        old_content = self.source_content[init_pos:len(self.source_content)]
        self.source_content = self.source_content[0:init_pos]

        i = 0
        for s in items:
            pos = init_pos+i
            s["pos"] = pos
            s["id"] = self.set_item_id()
            if "uri" not in s.keys():
                s["uri"] = "file://"+s["path"]
            self.source_content.append(s)
            i += 1

        for song in old_content:
            song["pos"] = init_pos+i
            i+=1

        self.source_content.extend(old_content)
        # Increment sourceId
        self.source_id += len(items)

    def clear(self):
        self.source_content = []
        # Increment sourceId
        self.source_id += 1

    def delete(self,nb,type = "id"):
        i = 0
        for item in self.source_content:
            if item[type] == nb:
                break
            i += 1
        if i == len(self.source_content):
            raise ItemNotFoundException
        pos = self.source_content[i]["pos"]
        del self.source_content[i]

        # Now we must reorder the item list
        for item in self.source_content:
            if item["pos"] > pos:
                item["pos"] -= 1

        # Increment sourceId
        self.source_id += 1

    def save(self):
        raise NotImplementedError
    
    def format_playlist_files(self,s):
        return {"dir":s[0],"filename":s[1],"pos":s[3],"id":self.set_item_id(),
            "title":s[6],"artist":s[7],"album":s[8],"genre":s[9],"track":s[10],
            "date":s[11],"length":s[12],"bitrate":s[13],
            "path":path.join(s[0],s[1]),
            "uri":"file://"+path.join(self.library.get_root_path(),\
            path.join(s[0],s[1])),"type":"song"}

    def set_item_id(self):
        self.__item_id += 1
        return self.__item_id
    

class UnknownSourceManagement:
    
    def __init__(self,player,db,library = None):
        self.db = db
        self.player = player
        self.library = library
        self.current_item = None
        self.played_items = []

    def get_recorded_id(self):
        id = int(self.db.get_state(self.source_name+"id"))
        return id

    def get_content(self):
        return self.current_source.get_content()

    def get_current(self):
        if self.current_item == None:
            self.go_to(0,"pos")

        return self.current_item

    def go_to(self,nb,type = "id"):
        try: self.current_item = self.current_source.get_item(nb,type)
        except ItemNotFoundException: self.current_item = None

        self.played_items = []
        return self.current_item
        
    def delete(self,id):
        self.current_source.delete(id)

    def clear(self):
        self.current_source.clear()

    def next(self,rd,rpt):
        if self.current_item == None:
            self.go_to(0,"pos")
            return self.current_item

        # Return a pseudo-random song
        l = self.current_source.get_content_length()
        if rd and l > 0: 
            # first determine if the current song is in playedItems
            try:
                id = self.played_items.index(self.current_item["id"])
                self.current_item = self.current_source.get_item(\
                    self.played_items[id+1],"id")
                return self.current_item
            except: pass

            # So we add the current song in playedItems
            self.played_items.append(self.current_item["id"])

            # Determine the id of the next song
            values = [v for v in self.current_source.get_item_ids() \
                if v not in self.played_items]
            try: song_id = random.choice(values)
            except: # All songs are played 
                if rpt:
                    self.played_items = []
                    song_id = random.choice(self.current_source.get_item_ids())
                else: return None

            # Obtain the choosed song
            try: self.current_item = self.current_source.get_item(song_id,"id")
            except ItemNotFoundException: return None
            return self.current_item
            
        # Reset random
        self.played_items = []

        current_position = self.current_item["pos"]
        if current_position < self.current_source.get_content_length()-1:
            try: self.current_item = self.current_source.get_item(\
                self.current_item["pos"] + 1)
            except ItemNotFoundException: self.current_item = None
        elif rpt:
            self.current_item = self.current_source.get_item(0)
        else:
            self.current_item = None

        return self.current_item

    def previous(self,rd,rpt):
        if self.current_item == None:
            return None

        # Return the last pseudo-random song
        l = len(self.played_items)
        if rd and l > 0:
            # first determine if the current song is in playedItems
            try:
                id = self.played_items.index(self.current_item["id"])
                if id == 0: return None
                self.current_item = self.current_source.get_item(\
                    self.played_items[id-1],"id")
                return self.current_item
            except ItemNotFoundException: return None 
            except ValueError: pass

            # So we add the current song in playedItems
            self.played_items.append(self.current_item["id"])

            self.current_item = self.current_source.\
                get_item(self.played_items[l-1],"id")
            return self.current_item

        # Reset random
        self.played_items = []

        current_position = self.current_item["pos"]
        if current_position > 0:
            self.current_item = self.current_source.\
                get_item(self.current_item["pos"] - 1)
        else:
            self.current_item = None

        return self.current_item

    def get_status(self):
        return [(self.source_name,self.current_source.source_id),\
          (self.source_name+"length",self.current_source.get_content_length())]

    def close(self):
        states = [(str(self.current_source.source_id),self.source_name+"id")]
        self.db.set_state(states)
        self.current_source.save()

# vim: ts=4 sw=4 expandtab
