
import os, glob

def get_audio_extensions(player):
    base = os.path.dirname(__file__)
    base_import = "deejayd.mediadb.formats"
    ext_dict = {}

    modules = [os.path.basename(f[:-3]) \
                for f in glob.glob(os.path.join(base, "[!_]*.py"))\
                if os.path.basename(f).startswith("audio")]
    for m in modules:
        mod = __import__(base_import+"."+m, {}, {}, base)
        inst = mod.object()
        for ext in mod.extensions:
            if player.is_supported_format(ext):
                ext_dict[ext] = inst

    return ext_dict

def get_video_extensions(player):
    ext_dict = {}

    from deejayd.mediadb.formats import video
    inst = video.object(player)
    for ext in video.extensions:
            if player.is_supported_format(ext):
                ext_dict[ext] = inst

    return ext_dict

# vim: ts=4 sw=4 expandtab
