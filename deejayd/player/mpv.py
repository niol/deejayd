# Deejayd, a media player daemon
# Copyright (C) 2018 Mickael Royer <mickael.royer@gmail.com>
#                    Alexandre Rossi <alexandre.rossi@gmail.com>
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


"""
This is the mpv backend module. mpv is launched as a new process and is
controlled using mpv's JSON IPC interface.

The interface documentation is available at the following address:
    https://mpv.io/manual/stable/#json-ipc
"""


import os
import json
import tempfile
import math

from twisted.internet import reactor
from twisted.internet import task
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import defer

from deejayd.jsonrpc.interfaces import jsonrpc_module, PlayerModule
from deejayd.player import PlayerError
from deejayd.player._base import _BasePlayer, PLAYER_PAUSE, \
                                 PLAYER_PLAY, PLAYER_STOP
from deejayd.player import _procctrl as procctrl
from deejayd.ui import log


class MpvIpcProtocol(LineOnlyReceiver):

    delimiter = b'\n'

    def connectionMade(self):
        log.debug('ctrl:mpv: connection to player process made')
        self.factory.conn = self
        self.__property_watch = {}
        self.__property_watch_lastid = 0
        self.__commands_cb = {}
        self.__commands_cb_lastid = 0

        for p in self.factory.handler.PROPERTIES:
            self.observe_property(p)
            (self.command('get_property', p)
             .addCallback(self.factory.handler.got_property, p))

        self.factory.handler.starting.callback(True)

    def connectionLost(self, reason):
        log.debug('ctrl:mpv: connection to player process lost')
        self.factory.conn = None

    def lineReceived(self, raw_message):
        try:
            log.debug('ctrl:mpv: received %s' % raw_message)
            msg = json.loads(raw_message.decode('utf-8'))
        except ValueError:
            self.transport.loseConnection()
        else:
            if 'request_id' in msg \
            and int(msg['request_id']) in self.__commands_cb:
                cb = self.__commands_cb[int(msg['request_id'])]
                cb.callback(msg)
            elif 'error' in msg:
                if msg['error'] != 'success':
                    self.factory.handler.error(msg['error'])
            elif 'event' in msg:
                try:
                    f = getattr(self.factory.handler,
                                'EVENT_%s' % msg['event'].replace('-', '_'))
                except AttributeError:
                    log.debug('ctrl:mpv: unknown event received: %s'
                              % msg['event'])
                else:
                    for unwanted_arg in ('event', 'id'):
                        if unwanted_arg in msg:
                            del msg[unwanted_arg]
                    f(**msg)
            else:
                log.err('ctrl:mpv: unhandled message received: %s' % msg)

    def command(self, name, *args):
        cmd_args = list(args)
        cmd_args.insert(0, name)
        cmd = { 'command': cmd_args, }

        d = defer.Deferred()
        self.__commands_cb[self.__commands_cb_lastid] = d
        cmd['request_id'] = self.__commands_cb_lastid
        def base_cb(msg, cmd):
            del self.__commands_cb[cmd['request_id']]
            if 'error' in msg and msg['error'] != 'success':
                raise PlayerError(cmd, msg)
            return msg
        d.addCallback(base_cb, cmd)
        self.__commands_cb_lastid = self.__commands_cb_lastid + 1

        self.sendLine(json.dumps(cmd).encode('utf-8'))
        log.debug('ctrl:mpv: sent command %s' % cmd)

        return d

    def observe_property(self, p):
        if p in self.__property_watch:
            return

        prop_watch_id = self.__property_watch_lastid
        def record_id(msg, p):
            self.__property_watch[p] = prop_watch_id
            return msg
        d = self.command('observe_property', prop_watch_id, p)
        d.addCallback(record_id, p)
        self.__property_watch_lastid = self.__property_watch_lastid + 1


class MpvPlayerProcess(procctrl.PlayerProcess):

    EXIT_SUCCESS = [0, 4]

    PROPERTIES = {
        'volume',
        'pause',
        'idle-active',
        'video-aspect',
        'aid',
        'sid',
        'audio-delay',
        'sub-delay',
    }

    WHILE_PLAYING_PROPERTIES = {
        'playlist-pos',
        'duration',
        'path',
        'eof-reached',
        'seekable',
        'media-title',
    }

    state = {
        'playback': PLAYER_STOP,
        'time-pos': 0,
    }

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.factory = None
        self.__monitor = task.LoopingCall(self.__monitor_playback)
        self.__stop_watchdog = None

    def socket_path(self):
        if not self.tempdir:
            self.tempdir = tempfile.TemporaryDirectory(prefix='deejayd-player-')
        return os.path.join(self.tempdir.name, 'ipc.socket')

    def __set_starting(self):
        self.starting = defer.Deferred()
        def started(r):
            self.starting = None
            return r
        self.starting.addCallback(started)

    def start_process(self, pmonitor):
        if self.player.config.get('video', 'fullscreen'):
            fs_opts = '--fullscreen'
        else:
            fs_opts = '--no-fullscreen'

        env = os.environ.copy()
        reactor.spawnProcess(pmonitor, 'mpv',
                             ('mpv',
                              '--input-ipc-server=%s' % self.socket_path(),
                              '--idle',
                              '--quiet',
                              '--gapless-audio',
                              '--no-resume-playback', # handled by deejayd
                              fs_opts,
                             ), env=env)

        self.__set_starting()

    def __try_connect(self):
        if not self.factory.conn:
            if self.__connect_tries < 5:
                reactor.connectUNIX(self.socket_path(),  self.factory)
                reactor.callLater(1, self.__try_connect)
            else:
                log.err('ctrl:mpv: Could not connect to player process, '
                        'giving up.')

    def connect(self, handler):
        if self.factory and self.factory.conn:
            return # already connected

        if not self.starting:
            self.__set_starting()

        self.factory = procctrl.PlayerBackendProtocolClientFactory()
        self.factory.protocol = MpvIpcProtocol
        self.factory.handler = handler
        self.factory.process = self
        self.factory.conn = None

        self.__connect_tries = 0
        self.__try_connect()

    def stop_process(self):
        self.factory.conn.command('quit')
        self.factory = None
        self.tempdir.cleanup()
        self.tempdir = None
        self.starting = None

    def stop_if_idle(self):
        self.__stop_watchdog = None
        if self.state['playback'] == PLAYER_STOP:
            self.stop()

    def command(self, name, *args):
        self.connect(self)

        if self.starting:
            return self.starting.addCallback(lambda d:
                                    self.factory.conn.command(name, *args))
        else:
            return self.factory.conn.command(name, *args)

    def error(self, msg):
        log.err('ctrl:mpv: error received: %s' % msg)

    def got_property(self, p, msg):
        if 'error' in msg and msg['error'] == 'success' and 'data' in msg:
            self.EVENT_property_change(p, msg['data'])
        return msg

    def EVENT_property_change(self, name=None, data=None):
        assert name is not None
        self.state[name] = data
        try:
            f = getattr(self, 'PROPERTY_%s' % name.replace('-', '_'))
        except AttributeError:
            pass

    def __monitor_playback(self):
        if self.state['playback'] == PLAYER_PLAY:
            self.command('get_property', 'time-pos')

    def EVENT_playback_restart(self):
        if self.state['playback'] != PLAYER_PLAY:
            self.state['playback'] = PLAYER_PLAY
            
            for p in self.WHILE_PLAYING_PROPERTIES:
                self.factory.conn.observe_property(p)
                (self.command('get_property', p)
                .addCallback(self.factory.handler.got_property, p))

            self.__monitor.start(1)

            self.player.dispatch_signame('player.status')
            self.player.dispatch_signame('player.current')

    def EVENT_pause(self):
        self.state['playback'] = PLAYER_PAUSE
        self.player.dispatch_signame('player.status')

    def EVENT_unpause(self):
        self.state['playback'] = PLAYER_PLAY
        self.player.dispatch_signame('player.status')

    def EVENT_idle(self):
        self.state['playback'] = PLAYER_STOP
        if self.__monitor.running:
            self.__monitor.stop()

        if self.__stop_watchdog:
            self.__stop_watchdog.cancel()
        self.__stop_watchdog = reactor.callLater(600, self.stop_if_idle)
        self.player.dispatch_signame('player.status')

    def EVENT_end_file(self):
        if self.__monitor.running:
            self.__monitor.stop()
        self.player._playing_media.played()
        self.player._playing_media['last_position'] = 0
        self._playing_media = None

    def PROPERTY_eof_reached(self, reached):
        if reached != 'null':
            self.player._change_file(self.player._source.next(explicit=False))

    def PROPERTY_media_title(self, title):
        if title != self._playing_media['desc']:
            self._playing_media.set_description(title)
            self.player.dispatch_signame('player.current')


@jsonrpc_module(PlayerModule)
class MpvPlayer(_BasePlayer):

    NAME = 'mpv'
    supported_options = (
        'current-audio',
        'av-offset',
        'sub-offset',
        'current-sub',
        'aspect-ratio',
    )

    def __init__(self, config):
        super().__init__(config)
        self.__player = MpvPlayerProcess(self)

    def play(self):
        if self._playing_media is None:
            return

        def restore_state(r):
            if self._playing_media.has_video():
                p_state = self._playing_media["playing_state"]
                self._player_set_zoom(p_state["zoom"])
                self._player_set_aspectratio(p_state["aspect-ratio"])
            return r

        uris = iter(self._playing_media.get_uris())
        def try_play(r):
            try:
                return self.__player.command('loadfile', next(uris)) \
                    .addCallback(restore_state) \
                    .addErrback(try_play)
            except StopIteration:
                raise PlayerError(_("unable to play file "
                                    "%s") % self._playing_media['title'])

        self.__player.start()
        if self.__player.starting:
            self.__player.starting.addCallback(try_play)
        else:
            try_play(None)
            
    def pause(self):
        if self.__player.state['playback'] == PLAYER_PLAY:
            self.__player.command('set_property', 'pause', True)
        elif self.__player.state['playback'] == PLAYER_PAUSE:
            self.__player.command('set_property', 'pause', False)

    def get_position(self):
        if self.get_state() != PLAYER_STOP:
            return int(self.__player.state['time-pos'])
        return 0

    def _set_position(self, pos):
        if self.get_state() != PLAYER_STOP and self.__player.state['seekable']:
            self.__player.command('seek', pos, 'absolute')
            self.__player.command('show-progress')

    def get_state(self):
        return self.__player.state['playback']

    def is_supported_uri(self, uri_type):
        # TODO : find a way to know list of available module to implement this
        return True

    def _change_file(self, new_file):
        if new_file:
            self.__player.start()
            # replaygain reset
            self.set_volume(self.get_volume(), sig=False)
            self._playing_media = new_file
            self.play()
        else:
            self.__player.command('stop')

    def _set_volume(self, vol, sig=True):
        self.__player.command('set_property', 'volume', int(vol))

    def _player_set_zoom(self, zoom):
        value = math.log(float(zoom) / float(100), 2)
        self.__player.command('set_property', 'video-zoom', value)

    def _player_set_aspectratio(self, aspect_ratio):
        if aspect_ratio == 'auto':
            aspect_ratio = -1
        self.__player.command('set_property', 'video-aspect', aspect_ratio)

    def _player_set_avoffset(self, offset):
        self.__player.command('set_property', 'audio-delay', offset)

    def _player_set_suboffset(self, offset):
        self.__player.command('set_property', 'sub-delay', offset)

    def _player_set_alang(self, lang_idx):
        if lang_idx == -1:
            lang_idx = 'no'
        self.__player.command('set_property', 'aid', lang_idx)

    def _player_set_slang(self, lang_idx):
        if lang_idx == -1:
            lang_idx = 'no'
        self.__player.command('set_property', 'sid', lang_idx)

    def _player_get_alang(self):
        return self.__player.state['aid']

    def _player_get_slang(self):
        return self.__player.state['sid']

    def _osd_set(self, text):
        self.__player.command('show-text', text, 2)


