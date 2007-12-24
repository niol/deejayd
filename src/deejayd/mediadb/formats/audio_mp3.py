
extensions = [".mp3",".mp2"]
try:
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
except ImportError:
    extensions = []


class Mp3File:
    supported_tag = ("tracknumber","title","genre","artist","album","date")

    def parse(self, file):
        infos = {}
        mp3_info = MP3(file, ID3=EasyID3)
        infos["bitrate"] = int(mp3_info.info.bitrate)
        infos["length"] = int(mp3_info.info.length)

        for t in self.supported_tag:
            try: infos[t] = mp3_info[t][0]
            except: infos[t] = '';

        return infos

object = Mp3File
