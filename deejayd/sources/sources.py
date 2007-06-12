import sys

from deejayd.ui import log

class UnknownSourceException: pass

class SourcesFactory:

    def __init__(self,player,db,audio_library,video_library):
        self.sources_obj = {}
        self.player = player

        # Playlist and Queue
        from deejayd.sources import playlist,queue
        self.sources_obj["playlist"] = playlist.PlaylistSource(player,db,\
                audio_library)
        self.sources_obj["queue"] = queue.QueueSource(player,db,audio_library)

        # Webradio
        if self.player.webradio_support():
            from deejayd.sources import webradio
            self.sources_obj["webradio"] = webradio.WebradioSource(player, db)
        else: log.msg("Webradio support disabled.")

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

        self.player.set_queue(self.sources_obj["queue"])
        self.player.load_state()

    def get_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        return self.sources_obj[s]

    def set_source(self,s):
        if s not in self.sources_obj.keys():
            raise UnknownSourceException

        self.player.set_source(self.sources_obj[s],s)
        return True

    def get_status(self):
        status = []
        for k in self.sources_obj.keys():
            status.extend(self.sources_obj[k].get_status())

        return status

    def get_available_sources(self):
        return self.sources_obj.keys()

    def close(self):
        for k in self.sources_obj.keys():
            self.sources_obj[k].close()


# vim: ts=4 sw=4 expandtab
