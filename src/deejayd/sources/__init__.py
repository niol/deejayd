
import sys
from deejayd.ui import log

class UnknownSourceException: pass

class SourceError(RuntimeError):
    def __init__(self,desc):
        self.desc = desc


class SourceFactory:

    def __init__(self,player,db,audio_library,video_library,config):
        self.sources_obj = {}
        self.current = ""
        self.db = db
        video_support = config.get("general","video_support")

        # Playlist and Queue
        from deejayd.sources import playlist,queue
        self.sources_obj["playlist"] = playlist.PlaylistSource(player,db,\
                audio_library)
        self.sources_obj["queue"] = queue.QueueSource(db,audio_library)

        # Webradio
        if player.is_supported_uri("http"):
            from deejayd.sources import webradio
            self.sources_obj["webradio"] = webradio.WebradioSource(db)
        else: log.info("Webradio support disabled for the choosen backend")

        # Video
        if video_support == "yes" and video_library:
            from deejayd.sources import video
            self.sources_obj["video"] = video.VideoSource(db, video_library)
            try: player.init_video_support()
            except:
                # Critical error, we have to quit deejayd
                log.err('Cannot initialise video support, either disable video support or check your player video support.')
                sys.exit(1)

        # dvd
        if video_support == "yes" and player.is_supported_uri("dvd"):
            from deejayd.sources import dvd
            try: self.sources_obj["dvd"] = dvd.DvdSource(player,db,config)
            except dvd.DvdError:
                log.err("Unable to init dvd support")
        else: log.info("DVD support is disabled")

        # restore recorded source
        source = db.get_state("source")
        try: self.set_source(source)
        except UnknownSourceException:
            log.err("Unable to set recorded source")
            self.set_source("playlist")

        player.set_source(self)
        player.load_state()

    def get_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        return self.sources_obj[s]

    def set_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        self.current = s
        return True

    def get_status(self):
        status = [("mode",self.current)]
        for k in self.sources_obj.keys():
            status.extend(self.sources_obj[k].get_status())

        return status

    def get_available_sources(self):
        return self.sources_obj.keys()

    def close(self):
        self.db.set_state([(self.current,"source")])
        for k in self.sources_obj.keys():
            self.sources_obj[k].close()

    #
    # Functions called from the player
    #
    def get(self, nb = None, type = "id", source_name = None):
        src = source_name or self.current
        return self.sources_obj[src].go_to(nb,type)

    def get_current(self):
        return self.sources_obj["queue"].get_current() or \
               self.sources_obj[self.current].get_current()

    def next(self, random,repeat):
        return self.sources_obj["queue"].next(random,repeat) or \
               self.sources_obj[self.current].next(random,repeat)

    def previous(self,random,repeat):
        return self.sources_obj[self.current].previous(random,repeat)

    def queue_reset(self):
        self.sources_obj["queue"].reset()

# vim: ts=4 sw=4 expandtab
