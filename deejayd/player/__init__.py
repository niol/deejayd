
class PlayerError(RuntimeError):

    def __init__(self,desc):
        self.desc = desc

def init(db,config):
    media_backend = config.get("general","media_backend")
    if media_backend == "gstreamer":
        from deejayd.player import gstreamer
        try: player = gstreamer.GstreamerPlayer(db,config)
        except gstreamer.NoSinkError:
            raise PlayerError(\
            "Unable to start deejayd : No audio sink found for Gstreamer \n")

    elif media_backend == "xine":
        from deejayd.player import xine
        player = xine.XinePlayer(db,config)

    else: raise PlayerError("Invalid audio backend")

    return player

# vim: ts=4 sw=4 expandtab
