
import sys
from deejayd.ui import log

class UnknownSourceException: pass

class SourceError(RuntimeError):
    def __init__(self,desc):
        self.desc = desc


class SourceFactory:

    def __init__(self,player,db,audio_library,video_library):
        self.sources_obj = {}
        self.current = None
        self.player = player
        self.db = db

        # Playlist and Queue
        from deejayd.sources import playlist,queue
        self.sources_obj["playlist"] = playlist.PlaylistSource(player,db,\
                audio_library)
        self.sources_obj["queue"] = queue.QueueSource(player,db,audio_library)

        # Webradio
        if self.player.is_supported_uri("http"):
            from deejayd.sources import webradio
            self.sources_obj["webradio"] = webradio.WebradioSource(player, db)
        else: log.info("Webradio support disabled for the choosen backend")

        # Video
        if video_library:
            from deejayd.sources import video
            self.sources_obj["video"] = video.VideoSource(player,db,\
                                                                  video_library)
            try: self.player.init_video_support()
            except:
                # Critical error, we have to quit deejayd
                sys.exit('Cannot initialise video sink, either disable video support or check your gstreamer plugins (video sink).')

        # restore recorded source 
        source = db.get_state("source")
        try: self.set_source(source)
        except UnknownSourceException:
            log.err("Unable to set recorded source")
            self.set_source("playlist")

        self.player.set_source(self)
        self.player.load_state()

    def get_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        return self.sources_obj[s]

    def set_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        self.current = self.sources_obj[s]
        return True

    def get_status(self):
        status = []
        for k in self.sources_obj.keys():
            status.extend(self.sources_obj[k].get_status())

        return status

    def get_available_sources(self):
        return self.sources_obj.keys()

    def close(self):
        self.db.set_state([(self.current.source_name,"source")])    
        for k in self.sources_obj.keys():
            self.sources_obj[k].close()

    #
    # Functions called from the player
    #
    def get(self, nb = None, type = "Id", source_name = None):
        source = source_name and self.sources_obj[source_name] or \
                                 self.current
        return source.go_to(nb,type)        
    
    def get_current(self):
        return self.sources_obj["queue"].get_current() or \
               self.current.get_current()

    def next(self, random,repeat):
        return self.sources_obj["queue"].next(random,repeat) or \
               self.current.next(random,repeat)

    def previous(self,random,repeat):
        return self.current.previous(random,repeat)

    def queue_reset(self):
        self.sources_obj["queue"].reset()

# vim: ts=4 sw=4 expandtab
