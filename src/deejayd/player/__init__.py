
class PlayerError(Exception):pass

def init(db,config):
    media_backend = config.get("general","media_backend")
    if media_backend == "gstreamer":
        from deejayd.player import gstreamer
        try: player = gstreamer.GstreamerPlayer(db,config)
        except gstreamer.NoSinkError:
            raise PlayerError(\
            "Unable to start deejayd : No audio sink found for Gstreamer")

    elif media_backend == "xine":
        from deejayd.player import xine,_base
        try: player = xine.XinePlayer(db,config)
        except _base.PlayerError:
            raise PlayerError(\
            "Unable to start deejayd : xine initialisation failed")

    else: raise PlayerError("Invalid audio backend")

    return player

# vim: ts=4 sw=4 expandtab
