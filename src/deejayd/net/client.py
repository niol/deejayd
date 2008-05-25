# Deejayd, a media player daemon
# Copyright (C) 2007-2008 Mickael Royer <mickael.royer@gmail.com>
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
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET

from Queue import Queue, Empty

import deejayd.interfaces
from deejayd.interfaces import DeejaydError, DeejaydKeyValue, DeejaydSignal
from deejayd.net.xmlbuilders import DeejaydXMLCommand


MSG_DELIMITER = 'ENDXML\n'


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

    def add_medias(self, paths, pos = None):
        cmd = DeejaydXMLCommand('queueAdd')
        cmd.add_multiple_arg('path', paths)
        if pos!= None:
            cmd.add_simple_arg('pos', pos)
        return self.server._send_command(cmd)

    def load_playlists(self, names, pos = None):
        cmd = DeejaydXMLCommand('queueLoadPlaylist')
        cmd.add_multiple_arg('name', names)
        if pos != None:
            cmd.add_simple_arg('pos', pos)
        return self.server._send_command(cmd)

    def clear(self):
        cmd = DeejaydXMLCommand('queueClear')
        return self.server._send_command(cmd)

    def del_songs(self, ids):
        cmd = DeejaydXMLCommand('queueRemove')
        cmd.add_multiple_arg('id', ids)
        return self.server._send_command(cmd)


class DeejaydPlaylist(deejayd.interfaces.DeejaydPlaylist):

    def __init__(self, server, pl_name = None):
        deejayd.interfaces.DeejaydPlaylist.__init__(self, pl_name)
        self.server = server

    def get(self, first = 0, length = None):
        cmd = DeejaydXMLCommand('playlistInfo')
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
        cmd.add_simple_arg('first', first)
        if length != None:
            cmd.add_simple_arg('length', length)
        ans = DeejaydMediaList(self)
        return self.server._send_command(cmd, ans)

    def save(self, name):
        cmd = DeejaydXMLCommand('playlistSave')
        cmd.add_simple_arg('name', name or self.__pl_name)
        return self.server._send_command(cmd)

    def add_songs(self, paths, position = None):
        cmd = DeejaydXMLCommand('playlistAdd')
        cmd.add_multiple_arg('path', paths)
        if position != None:
            cmd.add_simple_arg('pos', position)
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
        return self.server._send_command(cmd)

    def loads(self, names, pos = None):
        cmd = DeejaydXMLCommand('playlistLoad')
        cmd.add_multiple_arg('name', names)
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
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
        return self.server._send_command(cmd)

    def clear(self):
        cmd = DeejaydXMLCommand('playlistClear')
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
        return self.server._send_command(cmd)

    def del_songs(self, ids):
        cmd = DeejaydXMLCommand('playlistRemove')
        cmd.add_multiple_arg('id', ids)
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
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


class ConnectError(Exception):
    pass


class _DeejayDaemon(deejayd.interfaces.DeejaydCore):
    """Abstract class for a deejay daemon client."""

    def __init__(self):
        deejayd.interfaces.DeejaydCore.__init__(self)

        self.__timeout = 2
        self.expected_answers_queue = Queue()
        self.next_msg = ""

        # Socket setup
        self.socket_to_server = socket.socket(socket.AF_INET,
                                              socket.SOCK_STREAM)
        self.socket_to_server.settimeout(self.__timeout)
        self.connected = False

    def connect(self, host, port):
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
        self.version = socketFile.readline()
        self.connected = True
        if self.version.startswith("OK DEEJAYD"):
            # FIXME extract version number
            self.connected = True
        else:
            self.disconnect()
            raise ConnectError('Connection with server failed')

    def is_connected(self):
        return self.connected

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

    def _send_simple_command(self, cmd_name):
        cmd = DeejaydXMLCommand(cmd_name)
        return self._send_command(cmd)

    def get_playlist(self, name = None):
        return DeejaydPlaylist(self,name)

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

    def erase_playlist(self, names):
        cmd = DeejaydXMLCommand('playlistErase')
        cmd.add_multiple_arg('name', names)
        return self._send_command(cmd)

    def get_playlist_list(self):
        cmd = DeejaydXMLCommand('playlistList')
        return self._send_command(cmd,DeejaydMediaList())

    def get_audio_dir(self,dir = None):
        cmd = DeejaydXMLCommand('getdir')
        if dir != None:
            cmd.add_simple_arg('directory', dir)
        ans = DeejaydFileList(self)
        return self._send_command(cmd, ans)

    def audio_search(self, search_txt, type = 'all'):
        cmd = DeejaydXMLCommand('search')
        cmd.add_simple_arg('type', type)
        cmd.add_simple_arg('txt', search_txt)
        ans = DeejaydFileList(self)
        return self._send_command(cmd, ans)

    def get_video_dir(self,dir = None):
        cmd = DeejaydXMLCommand('getvideodir')
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

    def _build_answer(self, string_io):
        xmlpath = []
        originating_command = ''
        parms = {}
        answer = True
        signal = None
        for event, elem in ET.iterparse(string_io,events=("start","end")):
            if event == "start":
                xmlpath.append(elem.tag)
                if len(xmlpath) == 2:
                    if elem.tag in ('error', 'response'):
                        expected_answer = self.expected_answers_queue.get()
                    elif elem.tag == 'signal':
                        signal = DeejaydSignal()
                elif elem.tag in ("directory","file","media"):
                     assert xmlpath == ['deejayd', 'response',elem.tag]
                elif elem.tag == "track":
                    assert xmlpath == ['deejayd','response','dvd','track']
                    track = {"audio":[],"subtitle":[],"chapter":[]}
                elif elem.tag in ("audio","subtitle","chapter"):
                    assert xmlpath == ['deejayd','response','dvd','track',\
                                            elem.tag]
                elif elem.tag == "listparm":
                    list_parms = []
                elif elem.tag == "dictparm":
                    dict_parms = {}
            else: # event = "end"
                xmlpath.pop()

                if elem.tag in ('error','response'):
                    expected_answer.set_originating_command(elem.attrib['name'])
                elif elem.tag == 'signal':
                    signal.set_name(elem.attrib['name'])
                    self._dispatch_signal(signal)
                    signal = None

                if elem.tag == "error":
                    expected_answer.set_error(elem.text)
                elif elem.tag == "response":
                    rsp_type = elem.attrib['type']
                    if rsp_type == "KeyValue":
                        answer = parms
                    elif rsp_type == "FileAndDirList":
                        if 'directory' in elem.attrib.keys():
                            expected_answer.set_rootdir(elem.\
                                                           attrib['directory'])
                    elif rsp_type == "MediaList":
                        if 'total_length' in elem.attrib.keys():
                            expected_answer.set_total_length(elem.\
                                attrib['total_length'])
                    expected_answer._received(answer)
                    expected_answer = None
                elif elem.tag == "listparm":
                    parms[elem.attrib["name"]] = list_parms
                elif elem.tag == "listvalue":
                    list_parms.append(elem.attrib["value"])
                elif elem.tag == "dictparm":
                    list_parms.append(dict_parms)
                elif elem.tag == "dictitem":
                    dict_parms[elem.attrib["name"]] = elem.attrib["value"]
                elif elem.tag == "parm":
                    value = elem.attrib["value"]
                    try: value = int(value)
                    except ValueError: pass
                    parms[elem.attrib["name"]] = value
                elif elem.tag == "media":
                    expected_answer.add_media(parms)
                elif elem.tag == "directory":
                    expected_answer.add_dir(elem.attrib['name'])
                elif elem.tag == "file":
                    expected_answer.add_file(parms)
                elif elem.tag in ("audio","subtitle"):
                    track[elem.tag].append({"ix": elem.attrib['ix'],\
                        "lang": elem.attrib['lang']})
                elif elem.tag == "chapter":
                    track["chapter"].append({"ix": elem.attrib['ix'],\
                        "length": elem.attrib['length']})
                elif elem.tag == "track":
                    track["ix"] = elem.attrib["ix"]
                    track["length"] = elem.attrib["length"]
                    expected_answer.add_track(track)
                elif elem.tag == "dvd":
                    infos = {"title": elem.attrib['title'], \
                             "longest_track": elem.attrib['longest_track']}
                    expected_answer.set_dvd_content(infos)
                parms = elem.tag in ("parm","listparm","dictparm","listvalue",\
                        "dictitem") and parms or {}

                elem.clear()


class DeejayDaemonSync(_DeejayDaemon):
    """Synchroneous deejayd client library."""

    def __init__(self):
        _DeejayDaemon.__init__(self)

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

    # No subscription for the sync client
    def subscribe(self, signal_name, callback): raise NotImplementedError
    def unsubscribe(self, sub_id): raise NotImplementedError


class _DeejaydSocket(asyncore.dispatcher):
    ac_in_buffer_size = 256
    ac_out_buffer_size = 256

    def __init__(self, socket_map, deejayd):
        asyncore.dispatcher.__init__(self, map=socket_map)
        self.deejayd = deejayd
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
            # Catch version 17 character exactly
            self.version = self.recv(17)
            if self.version.startswith("OK DEEJAYD"):
                self.state = 'xml_protocol'
                # now we are sure to be connected
                for cb in self.__connect_callback:
                    cb(True,"")

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

    def __create_socket(self):
        self.socket_to_server = _DeejaydSocket(self.socket_thread.socket_map,
                                               self)
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

    def connect(self, host, port):
        if self.connected:
            self.disconnect()

        self.__create_socket()
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
