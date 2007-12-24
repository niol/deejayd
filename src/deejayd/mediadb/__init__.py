# vim: ts=4 sw=4 expandtab

from deejayd.ui import log
from deejayd.mediadb import library,inotify
import sys

def init(db, player, config):
    audio_library,video_library,lib_watcher = None, None, None

    try: audio_dir = config.get("mediadb","music_directory")
    except NoOptionError:
        sys.exit("You have to choose a music directory")
    else:
        try: audio_library = library.AudioLibrary(db,player,audio_dir)
        except library.NotFoundException,msg:
            sys.exit("Unable to init audio library : %s" % msg)

    if config.get('general', 'video_support') != 'yes':
        log.info("Warning : Video support disabled.")
        video_library = None
    else:
        try: video_dir = config.get('mediadb', 'video_directory')
        except NoOptionError:
            log.err(\
              'Supplied video directory not found. Video support disabled.')
            video_library = None
        else:
            try: video_library = library.VideoLibrary(db,player,video_dir)
            except library.NotFoundException,msg:
                sys.exit("Unable to init video library : %s" % msg)

    if inotify.inotify_support:
        lib_watcher = inotify.DeejaydInotify(db, audio_library, video_library)
        lib_watcher.start()
    else: log.info("inotify support disabled")

    return audio_library,video_library,lib_watcher
