
extensions = [".ogg"]
try: from mutagen.oggvorbis import OggVorbis
except ImportError:
    extensions = []

class OggFile:
    supported_tag = ("tracknumber","title","genre","artist","album","date")

    def parse(self, file):
        infos = {}
        ogg_info = OggVorbis(file)
        infos["bitrate"] = int(ogg_info.info.bitrate)
        infos["length"] = int(ogg_info.info.length)

        for t in self.supported_tag:
            try: infos[t] = ogg_info[t][0]
            except: infos[t] = '';

        return infos

object = OggFile

# vim: ts=4 sw=4 expandtab
