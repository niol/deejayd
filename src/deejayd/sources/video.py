
from os import path
from deejayd.mediadb.library import NotFoundException
from deejayd.sources._base import ItemNotFoundException,UnknownSource,\
                            UnknownSourceManagement
class Video(UnknownSource):

    def save(self):pass


class VideoSource(UnknownSourceManagement):
    name = "video"

    def __init__(self, db, library):
        UnknownSourceManagement.__init__(self,db,library)

        # Init parms
        self.current_source = Video(db,library)
        self.__current_dir = ""
        try: self.set_directory(self.db.get_state("videodir"))
        except NotFoundException: pass

    def set_directory(self,dir):
        try: video_list = self.library.get_dir_files(dir)
        except NotFoundException:
            dirs = self.library.get_dir_content(dir)
            video_list = []

        self.current_source.clear()
        self.current_source.add_files(video_list)
        self.__current_dir = dir

    def get_current_dir(self):
        return self.__current_dir

    def get_status(self):
        return [('video_dir',self.__current_dir)]

    def close(self):
        self.db.set_state([(self.__current_dir,"videodir")])

# vim: ts=4 sw=4 expandtab
