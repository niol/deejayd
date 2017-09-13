# Deejayd, a media player daemon
# Copyright (C) 2007-2009 Mickael Royer <mickael.royer@gmail.com>
#                         Alexandre Rossi <alexandre.rossi@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import urllib, urllib2, time, ConfigParser
import Queue
try: from hashlib import md5
except ImportError: # python < 2.5
    from md5 import md5

from zope.interface import implements
from deejayd import DeejaydError
from deejayd.server.thread import DeejaydThread
from deejayd.ui import log
from deejayd.plugins import IPlayerPlugin, PluginError
from deejayd.server.utils import str_decode

class AudioScrobblerFatalError(DeejaydError): pass
class AudioScrobblerError(DeejaydError):

    def __init__(self, msg):
        self._message = _("AudioScrobbler Error: %s") % str_decode(msg)


class AudioScrobblerPlugin(DeejaydThread):
    implements(IPlayerPlugin)
    NAME="audioscrobbler"

    AUDIOSCROBBLER_URL = "post.audioscrobbler.com"
    AUDIOSCROBBLER_PROTOCOL_VERSION = "1.2.1"
    AUDIOSCROBBLER_CLIENT="tst"
    AUDIOSCROBBLER_VERSION="1.0"
    AUDIOSCROBBLER_WAIT_INTERVAL=30

    def __init__(self, config):
        super(AudioScrobblerPlugin, self).__init__()

        self.enabled = True
        self.authenticated = False
        self.last_request = None
        self.session_id = None
        self.nowplaying_url = None
        self.submit_url = None

        self.queue = Queue.Queue()
        try:
            self.__auth_details = {
                    "login": config.get("lastfm", "login"),
                    "password": config.get("lastfm", "password"),
                }
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise PluginError(_("Lastfm configuration has not been set."))
        # start thread
        self.start()

    def on_media_played(self, media):
        if self.enabled and media["type"] == "song":
            self.queue.put((media, self.__get_stamp(media)))

    def __open_request(self, request):
        try:
            url_handle = urllib2.urlopen(request)
        except urllib2.HTTPError, error:
            err_msg = _("Unable to connect to server: %s - %s")
            code = str_decode(error.code, errors="ignore")
            msg = str_decode(error.msg, errors="ignore")
            raise AudioScrobblerError(err_msg % (code, msg))
        except urllib2.URLError, error:
            args = getattr(error.reason, 'args', None)
            code = '000'
            message = str(error)
            if args is not None:
                if len(args) == 1:
                    message = error.reason.args[0]
                elif len(args) == 2:
                    code = str(error.reason.args[0])
                    message = error.reason.args[1]
            code = str_decode(code, errors="ignore")
            message = str_decode(message, errors="ignore")
            err_msg = _("Unable to connect to server: %s - %s")
            raise AudioScrobblerError(err_msg % (code, message))

        self.last_request = int(time.time())
        return url_handle

    def auth(self):
        if self.authenticated:
            return True

        timestamp = int(time.time())
        token = md5(self.__auth_details["password"]+str(timestamp)).hexdigest()
        p = {
            "hs": "true",
            "u": self.__auth_details["login"],
            "c": self.AUDIOSCROBBLER_CLIENT,
            "v": self.AUDIOSCROBBLER_VERSION,
            "p": self.AUDIOSCROBBLER_PROTOCOL_VERSION,
            "t": str(timestamp),
            "a": token,
        }
        plist = [(k, urllib.quote_plus(v.encode('utf8'))) for k, v in p.items()]

        authparams = urllib.urlencode(plist)
        url = 'http://%s/?%s' % (self.AUDIOSCROBBLER_URL, authparams)
        req = urllib2.Request(url)
        url_handle = self.__open_request(req)

        # check answer
        response = url_handle.read().rstrip().split("\n")
        if len(response) == 0:
            raise AudioScrobblerError(_('Got nothing back from the server'))

        status = response.pop(0)
        if status == "OK":
            self.session_id = response.pop(0)
            self.nowplaying_url = response.pop(0)
            self.submit_url = response.pop(0)
            self.authenticated = True
        elif status == "UPTODATE":
            self.authenticated = True
        elif status == "BADAUTH":
            raise AudioScrobblerFatalError(_("Bad login/password"))
        elif status == "BADTIME":
            raise AudioScrobblerFatalError(_("Bad time"))
        elif status == "BANNED":
            raise AudioScrobblerFatalError(_("Application has be banned"))
        elif status.startswith("FAILED"):
            raise AudioScrobblerError(_("Failed to handshake: %s") % status)
        else:
            raise AudioScrobblerFatalError(_("Unknown status %s") % status)

    def submit_track(self, queue):
        data = {"s": self.session_id}
        for i, (track, stamp) in enumerate(queue):
            data["a[%d]" % i] = track["artist"].encode('utf-8')
            data["t[%d]" % i] = track["title"].encode('utf-8')
            data["l[%d]" % i] = track["length"].encode('utf-8')
            data["b[%d]" % i] = track['album'].encode('utf-8')
            data["m[%d]" % i] = "".encode('utf-8')
            data["i[%d]" % i] = stamp
            data["o[%d]" % i] = "P".encode('utf-8')
            data["n[%d]" % i] = "".encode('utf-8')
            data["r[%d]" % i] = "".encode('utf-8')

        postdata = urllib.urlencode(data)
        req = urllib2.Request(url=self.submit_url, data=postdata)
        url_handle = self.__open_request(req)

        response = url_handle.read().rstrip().split("\n")
        if len(response) == 0:
            raise AudioScrobblerError(_('Got nothing back from the server'))
        status = response.pop(0)
        if status == "OK":
            return True
        if status == "BADSESSION":
            raise AudioScrobblerFatalError(_("Bad session ID"))
        elif status.startswith("FAILED"):
            raise AudioScrobblerError(_("Failed to submit songs: %s") % status)
        else:
            raise AudioScrobblerError(_("Unknown status %s") % status)

    def run(self):
        while not self.should_stop.isSet():
            try: self.auth()
            except AudioScrobblerFatalError, ex: # fatal error, disable plugin
                log.err(_("Fatal error in audioscrobbler: %s") % ex)
                log.err(_("Disable audioscrobbler plugin"))
                self.enabled = False
                break
            except AudioScrobblerError, ex: # log error and try later
                log.err(_("Unable to authenticate: %s") % ex)
            else:
                tracks = []
                if not self.queue.empty():
                    if (int(time.time()) - self.last_request) > 3600:
                        log.info(_("Last FM : force reauthentification"))
                        self.authenticated = False
                        continue
                    for i in range(1,10):
                        if self.queue.empty():
                            break
                        tracks.append(self.queue.get())

                if len(tracks):
                    submission_failures = 0
                    while submission_failures < 3:
                        try: self.submit_track(tracks)
                        except AudioScrobblerError, err:
                            log.err(_("Unable to submit songs: %s") % err)
                            # wait 10 sec before retry
                            self.should_stop.wait(10)
                            submission_failures += 1
                        except AudioScrobblerFatalError, err:
                            log.err(_("Fatal error in submission process: %s")\
                                     % err)
                            log.err(_("Force lastfm reauthentification"))
                            submission_failures = 3
                            break
                        else:
                            break
                    if submission_failures == 3:
                        self.authenticated = False
                        for track in tracks:
                            self.queue.put(track)
            self.should_stop.wait(self.AUDIOSCROBBLER_WAIT_INTERVAL)

    def __get_stamp(self, track):
        stamp = str(int(time.time())--int(int(track['length'])/2))
        return stamp.encode("utf-8")
