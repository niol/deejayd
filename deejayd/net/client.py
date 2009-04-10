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

"""The Deejayd python client library"""

import socket, asyncore, threading
import sys,time
from cStringIO import StringIO

from Queue import Queue, Empty

import deejayd.interfaces
from deejayd.interfaces import DeejaydError, DeejaydKeyValue
from deejayd.net.xmlbuilders import DeejaydXMLCommand
from deejayd.net.xmlparsers import DeejaydXMLAnswerParser
from __init__ import DEEJAYD_PROTOCOL_VERSION


MSG_DELIMITER = 'ENDXML\n'
MAX_BANNER_LENGTH = 50


class DeejaydAnswer(deejayd.interfaces.DeejaydAnswer):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydAnswer.__init__(self)
        self.answer_received = threading.Event()
        self.callbacks = []
        self.server = server
        self.originating_command = 'unknown'

    def wait(self):
        self.answer_received.wait()

    def _received(self, contents):
        self.contents = contents
        self.answer_received.set()
        self._run_callbacks()

    def set_error(self, msg):
        deejayd.interfaces.DeejaydAnswer.set_error(self, msg)
        self.answer_received.set()
        self._run_callbacks()

    def get_contents(self):
        self.wait()
        return deejayd.interfaces.DeejaydAnswer.get_contents(self)

    def add_callback(self, cb):
        if self.answer_received.isSet():
            cb(self)
        else:
            self.callbacks.append(cb)

    def _run_callbacks(self):
        self.wait()
        for cb in self.callbacks:
            cb(self)

    def set_originating_command(self, cmd):
        self.originating_command = cmd

    def get_originating_command(self):
        return self.originating_command


class DeejaydKeyValue(DeejaydAnswer, deejayd.interfaces.DeejaydKeyValue):

    def __init__(self, server=None):
        DeejaydAnswer.__init__(self, server)


class DeejaydList(DeejaydAnswer, deejayd.interfaces.DeejaydList):

    def __init__(self, server=None):
        DeejaydAnswer.__init__(self, server)


class DeejaydFileList(DeejaydAnswer, deejayd.interfaces.DeejaydFileList):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydFileList.__init__(self)
        DeejaydAnswer.__init__(self, server)


class DeejaydMediaList(DeejaydAnswer, deejayd.interfaces.DeejaydMediaList):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydMediaList.__init__(self)
        DeejaydAnswer.__init__(self, server)


class DeejaydDvdInfo(DeejaydAnswer, deejayd.interfaces.DeejaydDvdInfo):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydDvdInfo.__init__(self)
        DeejaydAnswer.__init__(self, server)


class DeejaydStaticPlaylist(deejayd.interfaces.DeejaydStaticPlaylist):

    def __init__(self, server, pl_id, name):
        self.server = server
        self.__pl_id = pl_id
        self.__name = name

    def get(self, first=0, length=-1):
        cmd = DeejaydXMLCommand('recordedPlaylistInfo')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        cmd.add_simple_arg('first', first)
        if length != -1:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def __add(self, values, type):
        cmd = DeejaydXMLCommand('staticPlaylistAdd')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        cmd.add_simple_arg('type', type)
        cmd.add_multiple_arg('values', values)
        return self.server._send_command(cmd)

    def add_songs(self, song_ids):
        return self.__add(song_ids, "id")

    def add_paths(self, paths):
        return self.__add(paths, "path")


class DeejaydMagicPlaylist(deejayd.interfaces.DeejaydMagicPlaylist):

    def __init__(self, server, pl_id, name):
        self.server = server
        self.__pl_id = pl_id
        self.__name = name

    def get(self, first=0, length=-1):
        cmd = DeejaydXMLCommand('recordedPlaylistInfo')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        cmd.add_simple_arg('first', first)
        if length != -1:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def add_filter(self, filter):
        cmd = DeejaydXMLCommand('magicPlaylistAddFilter')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        cmd.add_filter_arg('filter', filter)
        return self.server._send_command(cmd)

    def remove_filter(self, filter):
        cmd = DeejaydXMLCommand('magicPlaylistRemoveFilter')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        cmd.add_filter_arg('filter', filter)
        return self.server._send_command(cmd)

    def clear_filters(self):
        cmd = DeejaydXMLCommand('magicPlaylistClearFilter')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        return self.server._send_command(cmd)

    def get_properties(self):
        cmd = DeejaydXMLCommand('magicPlaylistGetProperties')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        return self.server._send_command(cmd, DeejaydKeyValue())

    def set_property(self, key, value):
        cmd = DeejaydXMLCommand('magicPlaylistSetProperty')
        cmd.add_simple_arg('playlist_id', self.__pl_id)
        cmd.add_simple_arg('key', key)
        cmd.add_simple_arg('value', value)
        return self.server._send_command(cmd)


class DeejaydWebradioList(deejayd.interfaces.DeejaydWebradioList):

    def __init__(self, server):
        self.server = server

    def get(self, first = 0, length = None):
        cmd = DeejaydXMLCommand('webradioList')
        cmd.add_simple_arg('first', first)
        if length != None:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def add_webradio(self, name, urls):
        cmd = DeejaydXMLCommand('webradioAdd')
        cmd.add_simple_arg('name', name)
        # FIXME : Provision for the future where one webradio may have multiple
        # urls.
        # cmd.add_multiple_arg('url', urls)
        cmd.add_simple_arg('url', urls)
        return self.server._send_command(cmd)

    def delete_webradios(self, wr_ids):
        cmd = DeejaydXMLCommand('webradioRemove')
        cmd.add_multiple_arg('id', wr_ids)
        return self.server._send_command(cmd)

    def clear(self):
        cmd = DeejaydXMLCommand('webradioClear')
        return self.server._send_command(cmd)


class DeejaydQueue(deejayd.interfaces.DeejaydQueue):

    def __init__(self, server):
        self.server = server

    def get(self, first = 0, length = None):
        cmd = DeejaydXMLCommand('queueInfo')
        cmd.add_simple_arg('first', first)
        if length != None:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def __add(self, values, type, pos):
        cmd = DeejaydXMLCommand('queueAdd')
        cmd.add_simple_arg('type', type)
        cmd.add_multiple_arg('values', values)
        if pos != None:
            cmd.add_simple_arg('pos', pos)
        return self.server._send_command(cmd)

    def add_songs(self, song_ids, pos = None):
        return self.__add(song_ids, "id", pos)

    def add_paths(self, paths, pos = None):
        return self.__add(paths, "path", pos)

    def load_playlists(self, pl_ids, pos = None):
        cmd = DeejaydXMLCommand('queueLoadPlaylist')
        cmd.add_multiple_arg('id', pl_ids)
        if pos != None:
            cmd.add_simple_arg('pos', pos)
        return self.server._send_command(cmd)

    def clear(self):
        cmd = DeejaydXMLCommand('queueClear')
        return self.server._send_command(cmd)

    def move(self, ids, new_pos):
        cmd = DeejaydXMLCommand('queueMove')
        cmd.add_multiple_arg('ids', ids)
        cmd.add_simple_arg('new_pos', new_pos)
        return self.server._send_command(cmd)

    def del_songs(self, ids):
        cmd = DeejaydXMLCommand('queueRemove')
        cmd.add_multiple_arg('id', ids)
        return self.server._send_command(cmd)


class DeejaydPlaylistMode(deejayd.interfaces.DeejaydPlaylistMode):

    def __init__(self, server):
        self.server = server

    def get(self, first = 0, length = None):
        cmd = DeejaydXMLCommand('playlistInfo')
        cmd.add_simple_arg('first', first)
        if length != None:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def save(self, name):
        cmd = DeejaydXMLCommand('playlistSave')
        cmd.add_simple_arg('name', name)
        return self.server._send_command(cmd, DeejaydKeyValue())

    def __add(self, values, type, pos):
        cmd = DeejaydXMLCommand('playlistAdd')
        cmd.add_simple_arg('type', type)
        cmd.add_multiple_arg('values', values)
        if pos != None:
            cmd.add_simple_arg('pos', pos)
        return self.server._send_command(cmd)

    def add_songs(self, song_ids, pos = None):
        return self.__add(song_ids, "id", pos)

    def add_paths(self, paths, pos = None):
        return self.__add(paths, "path", pos)

    def loads(self, pl_ids, pos = None):
        cmd = DeejaydXMLCommand('playlistLoad')
        cmd.add_multiple_arg('id', pl_ids)
        if pos != None:
            cmd.add_simple_arg('pos', pos)
        return self.server._send_command(cmd)

    def move(self, ids, new_pos):
        cmd = DeejaydXMLCommand('playlistMove')
        cmd.add_multiple_arg('ids', ids)
        cmd.add_simple_arg('new_pos', new_pos)
        return self.server._send_command(cmd)

    def shuffle(self):
        cmd = DeejaydXMLCommand('playlistShuffle')
        return self.server._send_command(cmd)

    def clear(self):
        cmd = DeejaydXMLCommand('playlistClear')
        return self.server._send_command(cmd)

    def del_songs(self, ids):
        cmd = DeejaydXMLCommand('playlistRemove')
        cmd.add_multiple_arg('id', ids)
        return self.server._send_command(cmd)


class DeejaydPanel(deejayd.interfaces.DeejaydPanel):

    def __init__(self, server):
        self.server = server

    def get(self, first = 0, length = None):
        cmd = DeejaydXMLCommand('panelInfo')
        cmd.add_simple_arg('first', first)
        if length != None:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self.server)
        return self.server._send_command(cmd, ans)

    def get_active_list(self):
        cmd = DeejaydXMLCommand('panelActiveList')
        ans = DeejaydList(self.server)
        return self.server._send_command(cmd, ans)

    def get_panel_tags(self):
        cmd = DeejaydXMLCommand('panelTags')
        return self.server._send_command(cmd, DeejaydList())

    def set_active_list(self, type, pl_id=""):
        cmd = DeejaydXMLCommand('panelSetActiveList')
        cmd.add_simple_arg('type', type)
        cmd.add_simple_arg('value', pl_id)
        return self.server._send_command(cmd)

    def set_panel_filters(self, tag, values):
        cmd = DeejaydXMLCommand('panelSetFilter')
        cmd.add_simple_arg('tag', tag)
        cmd.add_multiple_arg('values', values)
        return self.server._send_command(cmd)

    def remove_panel_filters(self, tag):
        cmd = DeejaydXMLCommand('panelRemoveFilter')
        cmd.add_simple_arg('tag', tag)
        return self.server._send_command(cmd)

    def clear_panel_filters(self):
        cmd = DeejaydXMLCommand('panelClearFilter')
        return self.server._send_command(cmd)

    def set_search_filter(self, tag, value):
        cmd = DeejaydXMLCommand('panelSetSearch')
        cmd.add_simple_arg('tag', tag)
        cmd.add_simple_arg('value', value)
        return self.server._send_command(cmd)

    def clear_search_filter(self):
        cmd = DeejaydXMLCommand('panelClearSearch')
        return self.server._send_command(cmd)

    def set_sorts(self, sort):
        cmd = DeejaydXMLCommand('panelSort')
        cmd.add_sort_arg('sort', sort)
        return self.server._send_command(cmd)


class DeejaydVideo(deejayd.interfaces.DeejaydVideo):

    def __init__(self, server):
        self.server = server

    def get(self, first = 0, length = None):
        cmd = DeejaydXMLCommand('videoInfo')
        cmd.add_simple_arg('first', first)
        if length != None:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def set(self, value, type = "directory"):
        cmd = DeejaydXMLCommand('setvideo')
        cmd.add_simple_arg('value', value)
        cmd.add_simple_arg('type', type)
        return self.server._send_command(cmd)

    def set_sorts(self, sort):
        cmd = DeejaydXMLCommand('videoSort')
        cmd.add_sort_arg('sort', sort)
        return self.server._send_command(cmd)


class ConnectError(Exception):
    pass


class _DeejayDaemon(deejayd.interfaces.DeejaydCore):
    """Abstract class for a deejay daemon client."""

    def __init__(self):
        deejayd.interfaces.DeejaydCore.__init__(self)

        self.expected_answers_queue = Queue()
        self.answer_parser = DeejaydXMLAnswerParser(\
                                              self.expected_answers_queue.get,
                                              self._dispatch_signal)

        self.connected = False

    def connect(self, host, port, ignore_version=False):
        raise NotImplementedError

    def is_connected(self):
        return self.connected

    def disconnect(self):
        raise NotImplementedError

    def _version_from_banner(self, banner_line):
        tokenized_banner = banner_line.split(' ')
        try:
            version = tokenized_banner[2]
        except IndexError:
            raise ValueError
        else:
            numerical_version = map(int, version.split('.'))
            try:
                if tokenized_banner[3] == 'protocol':
                    protocol_version = tokenized_banner[4]
                else:
                    raise IndexError
            except IndexError:
                # Assume protocol is first one
                protocol_version = 1
            else:
                protocol_version = int(protocol_version)
            return numerical_version, protocol_version

    def _version_is_supported(self, versions):
        numerical_version = versions[0]
        protocol_version = versions[1]
        return protocol_version == DEEJAYD_PROTOCOL_VERSION

    def _send_simple_command(self, cmd_name):
        cmd = DeejaydXMLCommand(cmd_name)
        return self._send_command(cmd)

    def get_recorded_playlist(self, pl_id):
        return DeejaydStaticPlaylist(self, pl_id)

    def get_playlist(self):
        return DeejaydPlaylistMode(self)

    def get_panel(self):
        return DeejaydPanel(self)

    def get_webradios(self):
        return DeejaydWebradioList(self)

    def get_video(self):
        return DeejaydVideo(self)

    def get_queue(self):
        return DeejaydQueue(self)

    def ping(self):
        return self._send_simple_command('ping')

    def play_toggle(self):
        return self._send_simple_command('playToggle')

    def stop(self):
        return self._send_simple_command('stop')

    def previous(self):
        return self._send_simple_command('previous')

    def next(self):
        return self._send_simple_command('next')

    def seek(self, pos):
        cmd = DeejaydXMLCommand('seek')
        cmd.add_simple_arg('time', pos)
        return self._send_command(cmd)

    def get_current(self):
        cmd = DeejaydXMLCommand('current')
        return self._send_command(cmd,DeejaydMediaList())

    def go_to(self, id, id_type = None, source = None):
        cmd = DeejaydXMLCommand('goto')
        cmd.add_simple_arg('id', id)
        if id_type:
            cmd.add_simple_arg('id_type', id_type)
        if source:
            cmd.add_simple_arg('source', source)
        return self._send_command(cmd)

    def set_volume(self, volume_value):
        cmd = DeejaydXMLCommand('setVolume')
        cmd.add_simple_arg('volume', volume_value)
        return self._send_command(cmd)

    def set_option(self, source, option_name, option_value):
        cmd = DeejaydXMLCommand('setOption')
        cmd.add_simple_arg('source', source)
        cmd.add_simple_arg('option_name', option_name)
        cmd.add_simple_arg('option_value', option_value)
        return self._send_command(cmd)

    def set_mode(self, mode_name):
        cmd = DeejaydXMLCommand('setMode')
        cmd.add_simple_arg('mode', mode_name)
        return self._send_command(cmd)

    def get_mode(self):
        cmd = DeejaydXMLCommand('getMode')
        return self._send_command(cmd, DeejaydKeyValue())

    def set_player_option(self, name, value):
        cmd = DeejaydXMLCommand('setPlayerOption')
        cmd.add_simple_arg('option_name', name)
        cmd.add_simple_arg('option_value', value)
        return self._send_command(cmd)

    def get_status(self):
        cmd = DeejaydXMLCommand('status')
        return self._send_command(cmd, DeejaydKeyValue())

    def get_stats(self):
        cmd = DeejaydXMLCommand('stats')
        return self._send_command(cmd, DeejaydKeyValue())

    def update_audio_library(self):
        cmd = DeejaydXMLCommand('audioUpdate')
        return self._send_command(cmd, DeejaydKeyValue())

    def update_video_library(self):
        cmd = DeejaydXMLCommand('videoUpdate')
        return self._send_command(cmd, DeejaydKeyValue())

    def create_recorded_playlist(self, name, type):
        cmd = DeejaydXMLCommand('playlistCreate')
        cmd.add_simple_arg('name', name)
        cmd.add_simple_arg('type', type)
        return self._send_command(cmd, DeejaydKeyValue())

    def get_recorded_playlist(self, pl_id, name, type):
        if type == "static":
            return DeejaydStaticPlaylist(self, pl_id, name)
        elif type == "magic":
            return DeejaydMagicPlaylist(self, pl_id, name)

    def erase_playlist(self, pl_ids):
        cmd = DeejaydXMLCommand('playlistErase')
        cmd.add_multiple_arg('ids', pl_ids)
        return self._send_command(cmd)

    def get_playlist_list(self):
        cmd = DeejaydXMLCommand('playlistList')
        return self._send_command(cmd,DeejaydMediaList())

    def set_media_rating(self, media_ids, rating, type = "audio"):
        cmd = DeejaydXMLCommand('setMediaRating')
        cmd.add_multiple_arg('ids', media_ids)
        cmd.add_simple_arg('value', rating)
        cmd.add_simple_arg('type', type)
        return self._send_command(cmd)

    def get_audio_dir(self,dir = None):
        cmd = DeejaydXMLCommand('getAudioDir')
        if dir != None:
            cmd.add_simple_arg('directory', dir)
        ans = DeejaydFileList(self)
        return self._send_command(cmd, ans)

    def audio_search(self, search_txt, type = 'all'):
        cmd = DeejaydXMLCommand('audioSearch')
        cmd.add_simple_arg('type', type)
        cmd.add_simple_arg('txt', search_txt)
        ans = DeejaydMediaList(self)
        return self._send_command(cmd, ans)

    def get_video_dir(self,dir = None):
        cmd = DeejaydXMLCommand('getVideoDir')
        if dir != None:
            cmd.add_simple_arg('directory', dir)
        ans = DeejaydFileList(self)
        return self._send_command(cmd, ans)

    def dvd_reload(self):
        cmd = DeejaydXMLCommand('dvdLoad')
        return self._send_command(cmd)

    def get_dvd_content(self):
        cmd = DeejaydXMLCommand('dvdInfo')
        ans = DeejaydDvdInfo(self)
        return self._send_command(cmd, ans)

    def mediadb_list(self, tag, filter):
        cmd = DeejaydXMLCommand('mediadbList')
        cmd.add_simple_arg('tag', tag)
        if filter is not None:
            cmd.add_filter_arg('filter', filter)
        ans = DeejaydList(self)
        return self._send_command(cmd, ans)

    def _build_answer(self, string_io):
        return self.answer_parser.parse(string_io)


class DeejayDaemonSync(_DeejayDaemon):
    """Synchroneous deejayd client library."""

    def __init__(self):
        _DeejayDaemon.__init__(self)

        self.socket_to_server = socket.socket(socket.AF_INET,
                                              socket.SOCK_STREAM)
        self.__timeout = 2
        self.socket_to_server.settimeout(self.__timeout)
        self.next_msg = ""

    def connect(self, host, port, ignore_version=False):
        if self.connected:
            self.disconnect()

        self.host = host
        self.port = port

        try: self.socket_to_server.connect((self.host, self.port))
        except socket.timeout, msg:
            # reset connection
            self._reset_socket()
            raise ConnectError('Connection timeout')
        except socket.error, msg:
            raise ConnectError('Connection with server failed : %s' % msg)

        self.socket_to_server.settimeout(None)
        socketFile = self.socket_to_server.makefile()

        # Catch version
        banner_line = socketFile.readline()
        self.connected = True
        if not banner_line.startswith("OK DEEJAYD")\
        or len(banner_line) > MAX_BANNER_LENGTH:
            self.disconnect()
            raise ConnectError('Connection with server failed')
        try:
            versions = self._version_from_banner(banner_line)
        except ValueError:
            self.disconnect()
            raise ConnectError('Initial version dialog with server failed')
        if not ignore_version and not self._version_is_supported(versions):
            self.disconnect()
            raise ConnectError('This server version protocol is not handled by this client version')

    def _send_command(self, cmd, expected_answer = None):
        # Set a default answer by default
        if expected_answer == None:
            expected_answer = DeejaydAnswer(self)
        self.expected_answers_queue.put(expected_answer)

        self._sendmsg(cmd.to_xml())

        rawmsg = self._readmsg()
        try: self._build_answer(StringIO(rawmsg))
        except SyntaxError:
            raise DeejaydError("Unable to parse server answer : %s" % rawmsg)
        return expected_answer

    def disconnect(self):
        if not self.connected:
            return

        self.socket_to_server.settimeout(self.__timeout)
        try: self._send_simple_command('close').get_contents()
        except socket.timeout: pass

        self._reset_socket()
        self.connected = False
        self.host = None
        self.port = None

    def _reset_socket(self):
        self.socket_to_server.close()
        # New Socket setup
        self.socket_to_server = socket.socket(socket.AF_INET,
                                              socket.SOCK_STREAM)
        self.socket_to_server.settimeout(self.__timeout)

    def _sendmsg(self, buf):
        self.socket_to_server.send(buf + MSG_DELIMITER)

    def _readmsg(self):
        msg_chunks = ''
        msg_chunk = ''
        def split_msg(msg,index):
            return (msg[0:index], msg[index+len(MSG_DELIMITER):len(msg)])

        while 1:
            try: index = self.next_msg.index(MSG_DELIMITER)
            except ValueError: pass
            else:
                (rs,self.next_msg) = split_msg(self.next_msg, index)
                break

            msg_chunk = self.socket_to_server.recv(4096)
            # socket.recv returns an empty string if the socket is closed, so
            # catch this.
            if msg_chunk == '':
                raise socket.error()

            msg_chunks += msg_chunk
            try: index = msg_chunks.index(MSG_DELIMITER)
            except ValueError: pass
            else:
                (rs,self.next_msg) = split_msg(msg_chunks, index)
                break

        return rs

    # No subscription for the sync client
    def subscribe(self, signal_name, callback): raise NotImplementedError
    def unsubscribe(self, sub_id): raise NotImplementedError


class _DeejaydSocket(asyncore.dispatcher):
    ac_in_buffer_size = 256
    ac_out_buffer_size = 256

    def __init__(self, socket_map, deejayd, ignore_version=False):
        asyncore.dispatcher.__init__(self, map=socket_map)
        self.deejayd = deejayd
        self.ignore_version = ignore_version

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket_die_callback = []
        self.__connect_callback = []

        self.state = "disconnected"
        self.msg_chunks = ""
        self.next_msg = ""

    def add_connect_callback(self, callback):
        self.__connect_callback.append(callback)

    def add_socket_die_callback(self, callback):
        self.socket_die_callback.append(callback)

    def __error_callbacks(self, msg):
        for cb in self.socket_die_callback:
            cb(msg)

    def handle_error(self):
        t, v, tb = sys.exc_info()
        assert tb # Must have a traceback
        if self.state != "xml_protocol":
            # error appears when we try to connect
            for cb in self.__connect_callback:
                cb(False,str(v))

    def handle_connect(self):
        self.state = "connected"

    def handle_close(self):
        if self.state == "xml_protocol":
            self.__error_callbacks('disconnected')
        self.state = "disconnected"
        self.close()

    def handle_read(self):
        def split_msg(msg,index):
            return (msg[0:index], msg[index+len(MSG_DELIMITER):len(msg)])

        if self.state == "connected":
            # Catch banner until first newline char
            banner_line = ''
            newchar = ''
            while newchar != '\n' and len(banner_line) < MAX_BANNER_LENGTH:
                banner_line += newchar
                newchar = self.recv(1)
            if banner_line.startswith("OK DEEJAYD"):
                try:
                    versions = self.deejayd._version_from_banner(banner_line)
                except ValueError:
                    cb(False, 'Initial version dialog with server failed')
                if self.ignore_version\
                or self.deejayd._version_is_supported(versions):
                    self.state = 'xml_protocol'
                    # now we are sure to be connected
                    for cb in self.__connect_callback:
                        cb(True,"")
                else:
                    cb(False, 'This server version protocol is not handled by this client version')

        elif self.state == "xml_protocol":
            msg_chunk = self.recv(256)
            # socket.recv returns an empty string if the socket is closed, so
            # catch this.
            if msg_chunk == '':
                self.close()
            self.msg_chunks += msg_chunk
            try: index = self.msg_chunks.index(MSG_DELIMITER)
            except ValueError: return
            else:
                (rawmsg,self.next_msg) = split_msg(self.msg_chunks, index)
                self.msg_chunks = ""
                self.answer_received(rawmsg)

                while self.next_msg != '':
                    try: index = self.next_msg.index(MSG_DELIMITER)
                    except ValueError:
                        self.msg_chunks = self.next_msg
                        self.next_msg = ""
                        break
                    else:
                        (rawmsg,self.next_msg) = split_msg(self.next_msg, index)
                        self.answer_received(rawmsg)

        elif self.state == "disconnected":
            # This should not happen
            raise AttributeError

    def answer_received(self,rawmsg):
        try: self.deejayd._build_answer(StringIO(rawmsg))
        except SyntaxError:
            self.__error_callbacks("Unable to parse server answer : %s" %rawmsg)
            self.close()

    def handle_write(self):
        cmd = self.deejayd.command_queue.get()
        self.send(cmd.to_xml()+MSG_DELIMITER)

    def writable(self):
        if self.state != "xml_protocol": return False
        return not self.deejayd.command_queue.empty()


class _DeejaydSocketThread:

    def __init__(self):
        self.__th = None
        self.socket_map = {}

    # Thanks
    # http://mail.python.org/pipermail/python-list/2004-November/290798.html
    def __asyncore_loop(self):
        self.__stop_asyncore_loop = False
        while self.socket_map and not self.__stop_asyncore_loop:
            asyncore.loop(timeout=1, map=self.socket_map, count=1)

    def stop(self):
        self.__stop_asyncore_loop = True
        self.__th.join()

    def start(self):
        self.__th = threading.Thread(target=self.__asyncore_loop)
        self.__th.start()


class DeejayDaemonAsync(_DeejayDaemon):
    """Completely aynchroneous deejayd client library."""

    # There is only one socket thread for all the async client instances
    socket_thread = _DeejaydSocketThread()

    def __init__(self):
        _DeejayDaemon.__init__(self)
        #socket.setdefaulttimeout(5)
        self.command_queue = Queue()
        self.__con_cb = []
        self.__err_cb = []
        self.socket_to_server = None

    def __create_socket(self, ignore_version=False):
        self.socket_to_server = _DeejaydSocket(self.socket_thread.socket_map,
                                               self, ignore_version)
        self.socket_to_server.add_socket_die_callback(\
            self.__make_answers_obsolete)
        self.socket_to_server.add_socket_die_callback(self.__disconnect)
        self.socket_to_server.add_connect_callback(self.__connect_callback)

    def __disconnect(self, msg):
        # socket die, so thread do not need to be stopped
        # just reset the socket
        self.connected = False
        del self.socket_to_server
        self.socket_to_server = None
        # execute error callback
        for cb in self.__err_cb:
            cb(msg)

    def __make_answers_obsolete(self, msg):
        msg = "Could not obtain answer from server : " + msg
        try:
            while True:
                self.expected_answers_queue.get_nowait().set_error(msg)
        except Empty:
            # There is no more answer there, so no need to set any more errors.
            pass

    def __connect_callback(self, rs, msg = ""):
        self.connected = rs
        if not rs: # error happens, reset socket
            del self.socket_to_server
            self.socket_to_server = None
        for cb in self.__con_cb:
            cb(rs, msg)

    def add_connect_callback(self,cb):
        self.__con_cb.append(cb)

    def add_error_callback(self,cb):
        self.__err_cb.append(cb)

    def connect(self, host, port, ignore_version=False):
        if self.connected:
            self.disconnect()

        self.__create_socket(ignore_version)
        try: self.socket_to_server.connect((host, port))
        except socket.connecterror, msg:
            raise ConnectError('Connection error %s' % str(msg))

        if len(self.socket_thread.socket_map) < 2:
            # This is the first client to ask for a connection
            self.socket_thread.start()

    def disconnect(self):
        if self.socket_to_server != None:
            self.__stop_thread()
        self.connected = False
        # clear subscriptions
        self._clear_subscriptions()

    def __stop_thread(self):
        # terminate socket thread
        self.socket_to_server.close()
        if len(self.socket_thread.socket_map) < 1:
            # This is the last client to disconnect
            self.socket_thread.stop()
        del self.socket_to_server
        self.socket_to_server = None

    def _send_command(self, cmd, expected_answer = None):
        # Set a default answer by default
        if expected_answer == None:
            expected_answer = DeejaydAnswer(self)

        self.expected_answers_queue.put(expected_answer)
        self.command_queue.put(cmd)
        return expected_answer

    def subscribe(self, signal_name, callback):
        if signal_name not in self.get_subscriptions().values():
            cmd = DeejaydXMLCommand('setSubscription')
            cmd.add_simple_arg('signal', signal_name)
            cmd.add_simple_arg('value', 1)
            ans = self._send_command(cmd)
            # Subscription are sync because there should be a way to tell the
            # client that subscription failed.
            ans.get_contents()
        return _DeejayDaemon.subscribe(self, signal_name, callback)

    def unsubscribe(self, sub_id):
        try:
            signal_name = self.get_subscriptions()[sub_id]
        except KeyError:
            # DeejaydError will be raised at local unsubscription
            pass
        _DeejayDaemon.unsubscribe(self, sub_id)
        # Remote unsubscribe if last local subscription laid off
        if signal_name not in self.get_subscriptions().values():
            cmd = DeejaydXMLCommand('setSubscription')
            cmd.add_simple_arg('signal', signal_name)
            cmd.add_simple_arg('value', 0)
            ans = self._send_command(cmd)
            # As subscription, unsubscription is sync.
            ans.get_contents()


# vim: ts=4 sw=4 expandtab
