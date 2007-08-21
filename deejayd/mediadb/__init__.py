# vim: ts=4 sw=4 expandtab

from deejayd.ui import log
from deejayd.mediadb import library

def init(db, player, config):
    try: audio_dir = config.get("mediadb","music_directory")
    except NoOptionError:
        sys.exit("You have to choose a music directory")
    else: audio_library = library.AudioLibrary(db,player,audio_dir)

    if config.get('general', 'video_support') != 'yes':
        log.info("Warning : Video support disabled.")
        video_library = None
    else:
        try: video_dir = config.get('mediadb', 'video_directory')
        except NoOptionError:
            log.err(\
              'Supplied video directory not found. Video support disabled.')
            video_library = None
        else: video_library = library.VideoLibrary(db,player,video_dir)

    return audio_library,video_library
