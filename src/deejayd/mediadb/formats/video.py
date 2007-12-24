
import os
extensions = [".avi", ".mpeg", ".mpg", ".mkv"]

class VideoFile:
    supported_tag = ("videowidth","length","videoheight")

    def __init__(self, player):
        self.player = player

    def parse(self, file):
        (path,filename) = os.path.split(file)
        def format_title(f):
            (filename,ext) = os.path.splitext(f)
            title = filename.replace(".", " ")
            title = title.replace("_", " ")

            return title.title()

        infos = self.parse_sub(file)
        infos["title"] = format_title(filename)
        video_info = self.player.get_video_file_info(file)
        for t in self.supported_tag:
            infos[t] = video_info[t]

        return infos

    def parse_sub(self, file):
        infos = {}
        # Try to find a subtitle (same name with a srt/sub extension)
        (base_path,ext) = os.path.splitext(file)
        sub = ""
        for ext_type in (".srt",".sub"):
            if os.path.isfile(base_path + ext_type):
                sub = "file://" + base_path + ext_type
                break
        infos["subtitle"] = sub
        return infos

object = VideoFile

# vim: ts=4 sw=4 expandtab
