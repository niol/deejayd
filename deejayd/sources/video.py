
from os import path
from deejayd.mediadb.library import NotFoundException
from deejayd.sources import ItemNotFoundException,UnknownSource,\
                            UnknownSourceManagement

class Video(UnknownSource):

    def add_files(self,files):
        init_pos = len(self.source_content)
        old_content = self.source_content[init_pos:len(self.source_content)]
        self.source_content = self.source_content[0:init_pos]

        i = 0
        for f in files:
            pos = init_pos+i
            self.source_content.append({"dir":f[0],"Title":f[4],\
                "filename":f[1],"Pos":pos,"Id":f[3],\
                "uri":"file://"+path.join(self.library.get_root_path(),\
                path.join(f[0],f[1])),"Time":f[5],"Videowidth":f[6],\
                "Videoheigth":f[7],"Subtitle":f[8]})
            i += 1

        for f in old_content:
            f["Pos"] = init_pos+i
            i += 1

        self.source_content.extend(old_content)
        self.source_id += len(files)

    def save(self):pass


class VideoSource(UnknownSourceManagement):

    def __init__(self, player, db, library):
        UnknownSourceManagement.__init__(self,player,db,library)

        # Init parms
        self.source_name = "video"
        self.current_source = Video(db,library)
        self.__current_dir = ""
        self.set_directory(self.db.get_state("videodir"))

    def set_directory(self,dir):
        self.current_source.clear()

        try: video_list = self.library.get_dir_files(dir)
        except NotFoundException: video_list = []

        self.current_source.add_files(video_list)
        self.__current_dir = dir

    def get_current_dir(self):
        return self.__current_dir

    def get_status(self):
        return [('video_dir',self.__current_dir)]

    def close(self):
        self.db.set_state([(self.__current_dir,"videodir")])

# vim: ts=4 sw=4 expandtab
