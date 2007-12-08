"""The Deejayd python client library"""

import socket, asyncore, threading
import sys,time
from cStringIO import StringIO
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET

from Queue import Queue, Empty

import deejayd.interfaces
from deejayd.interfaces import DeejaydError, DeejaydKeyValue
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


class DeejaydKeyValue(deejayd.interfaces.DeejaydKeyValue, DeejaydAnswer):

    def __init__(self, server=None):
        DeejaydAnswer.__init__(self, server)

    def __getitem__(self, name):
        self.get_contents()
        return deejayd.interfaces.DeejaydKeyValue.__getitem__(self, name)

    def keys(self):
        self.get_contents()
        return deejayd.interfaces.DeejaydKeyValue.keys(self)

    def items(self):
        self.get_contents()
        return deejayd.interfaces.DeejaydKeyValue.items(self)


class DeejaydFileList(deejayd.interfaces.DeejaydFileList, DeejaydAnswer):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydFileList.__init__(self)
        DeejaydAnswer.__init__(self, server)

    def get_files(self):
        self.get_contents()
        return deejayd.interfaces.DeejaydFileList.get_files(self)

    def get_directories(self):
        self.get_contents()
        return deejayd.interfaces.DeejaydFileList.get_directories(self)


class DeejaydMediaList(deejayd.interfaces.DeejaydMediaList, DeejaydAnswer):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydMediaList.__init__(self)
        DeejaydAnswer.__init__(self, server)

    def get_medias(self):
        self.get_contents()
        return deejayd.interfaces.DeejaydMediaList.get_medias(self)


class DeejaydDvdInfo(deejayd.interfaces.DeejaydDvdInfo, DeejaydAnswer):

    def __init__(self, server = None):
        deejayd.interfaces.DeejaydDvdInfo.__init__(self)
        DeejaydAnswer.__init__(self, server)

    def get_dvd_contents(self):
        self.get_contents()
        return  deejayd.interfaces.DeejaydDvdInfo.get_dvd_contents(self)


class DeejaydWebradioList(deejayd.interfaces.DeejaydWebradioList):

    def __init__(self, server):
        self.server = server

    def get(self):
        cmd = DeejaydXMLCommand('webradioList')
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

    def add_songs(self, paths, position = None):
        cmd = DeejaydXMLCommand('queueAdd')
        cmd.add_multiple_arg('path', paths)
        if position != None:
            cmd.add_simple_arg('pos', position)
        return self.server._send_command(cmd)

    def loads(self, names, pos = None):
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


class ConnectError(Exception):
    pass


class _DeejayDaemon(deejayd.interfaces.DeejaydCore):
    """Abstract class for a deejay daemon client."""

    def __init__(self):
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

    def get_queue(self):
        return DeejaydQueue(self)

    def ping(self):
        return self._send_simple_command('ping')

    def play_toggle(self):
        return self._send_simple_command('play')

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
        cmd = DeejaydXMLCommand('play')
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

    def set_option(self, option_name, option_value):
        cmd = DeejaydXMLCommand('setOption')
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

    def set_alang(self, lang_idx):
        cmd = DeejaydXMLCommand('setAlang')
        cmd.add_simple_arg('lang_idx', lang_idx)
        return self._send_command(cmd)

    def set_slang(self, lang_idx):
        cmd = DeejaydXMLCommand('setSlang')
        cmd.add_simple_arg('lang_idx', lang_idx)
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

    def erase_playlist(self, name):
        cmd = DeejaydXMLCommand('playlistErase')
        cmd.add_simple_arg('name', name)
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

    def audio_search(self, search_txt, type):
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

    def set_video_dir(self, dir):
        cmd = DeejaydXMLCommand('setvideodir')
        cmd.add_simple_arg('directory', dir)
        return self._send_command(cmd)

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
        for event, elem in ET.iterparse(string_io,events=("start","end")):
            if event == "start":
                xmlpath.append(elem.tag)

                if elem.tag in ('error', 'response') and len(xmlpath) == 2:
                    expected_answer = self.expected_answers_queue.get()
                elif elem.tag in ("directory","file","media"):
                     assert xmlpath == ['deejayd', 'response',elem.tag]
                elif elem.tag == "track":
                    assert xmlpath == ['deejayd','response','dvd','track']
                    track = {"audio":[],"subtitle":[],"chapters":[]}
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
                    expected_answer._received(answer)
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
                    track[elem.tag].append({"id": elem.attrib['ix'],\
                        "lang": elem.attrib['lang']})
                elif elem.tag == "chapter":
                    track["chapters"].append({"id": elem.attrib['ix'],\
                        "length": elem.attrib['length']})
                elif elem.tag == "track":
                    track["id"] = elem.attrib["ix"]
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


class _DeejaydSocket(asyncore.dispatcher):
    ac_in_buffer_size = 256
    ac_out_buffer_size = 256

    def __init__(self,deejayd):
        asyncore.dispatcher.__init__(self)
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
            print "error in parse answer %s" % rawmsg
            self.__error_callbacks("Unable to parse server answer : %s" %rawmsg)
            self.close()

    def handle_write(self):
        cmd = self.deejayd.command_queue.get()
        self.send(cmd.to_xml()+MSG_DELIMITER)

    def writable(self):
        if self.state != "xml_protocol": return False
        return not self.deejayd.command_queue.empty()


class _DeejaydSocketThread(threading.Thread):

    def run(self):
        asyncore.loop(timeout=1)


class DeejayDaemonAsync(_DeejayDaemon):
    """Completely aynchroneous deejayd client library."""

    def __init__(self):
        _DeejayDaemon.__init__(self)
        #socket.setdefaulttimeout(5)
        self.command_queue = Queue()
        self.__con_cb = []
        self.__err_cb = []
        self.socket_to_server = None
        self.socket_thread = _DeejaydSocketThread()

    def __create_socket(self):
        self.socket_to_server = _DeejaydSocket(self)
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
        self.socket_to_server.connect((host, port))
        self.socket_thread.start()

    def disconnect(self):
        if self.socket_to_server != None:
            self.__stop_thread()
        self.connected = False

    def __stop_thread(self):
        # terminate socket thread
        self.socket_to_server.close()
        while self.socket_thread.isAlive():
            time.sleep(0.2)
        del self.socket_to_server
        self.socket_to_server = None

    def _send_command(self, cmd, expected_answer = None):
        # Set a default answer by default
        if expected_answer == None:
            expected_answer = DeejaydAnswer(self)

        self.expected_answers_queue.put(expected_answer)
        self.command_queue.put(cmd)
        return expected_answer


#############################################################################
#############################################################################
#             Old async library client
#############################################################################
#############################################################################
class _OldDeejaydSocketThread(threading.Thread):

    def __init__(self, deejayd, socket):
        threading.Thread.__init__(self)

        self.socket_die_callback = []

        self.deejayd = deejayd
        self.socket_to_server = socket

    def add_socket_die_callback(self, callback):
        self.socket_die_callback.append(callback)

    def run(self):
        self.should_stop = False
        try:
            while not self.should_stop:
                try:
                    self.really_run()
                except _StopException:
                    self.should_stop = True
                except SyntaxError:
                    # XML parsing failed, simply ignore. Client and server are
                    # misaligned, better disconnect.
                    self.socket_to_server.close()
        except socket.error, msg:
            for cb in self.socket_die_callback:
                cb(str(msg))

    def really_run(self):
        # This is implemented by daughter classes. This should be a blocking
        # function.
        raise NotImplementedError


class _StopException(Exception):
    pass


class _DeejaydCommandThread(_OldDeejaydSocketThread):

    def __init__(self, deejayd, socket, command_queue):
        _DeejaydSocketThread.__init__(self, deejayd, socket)
        self.command_queue = command_queue

    def really_run(self):
        cmd = self.command_queue.get()

        # If we've got a stop exception in the queue, raise it!
        if cmd.__class__ == _StopException:
            raise cmd

        self.deejayd._sendmsg(cmd.to_xml())


class _DeejaydAnswerThread(_OldDeejaydSocketThread):

    def __init__(self, deejayd, socket, expected_answers_queue):
        _DeejaydSocketThread.__init__(self, deejayd, socket)
        # socket.recv here is locking. Therefore, make the thread a daemon in
        # case something goes wrong. I don't like this but this will do for the
        # moment.
        self.setDaemon(True)

        self.expected_answers_queue = expected_answers_queue

    def really_run(self):
        rawmsg = self.deejayd._readmsg()
        self.deejayd._build_answer(StringIO(rawmsg))


class OldDeejayDaemonAsync(_DeejayDaemon):
    """Completely aynchroneous deejayd client library."""

    def __init__(self):
        _DeejayDaemon.__init__(self)

        self.command_queue = Queue()

        # Messaging threads
        self.sending_thread = _DeejaydCommandThread(self,
                                                    self.socket_to_server,
                                                    self.command_queue)
        self.receiving_thread = _DeejaydAnswerThread(self,
                                                    self.socket_to_server,
                                                    self.expected_answers_queue)
        self.receiving_thread.add_socket_die_callback(\
                                             self.__make_answers_obsolete)
        for thread in [self.sending_thread, self.receiving_thread]:
            thread.add_socket_die_callback(self.__disconnect)

    def __disconnect(self, msg):
        self.disconnect()

    def __make_answers_obsolete(self, msg):
        msg = "Could not obtain answer from server : " + msg
        try:
            while True:
                self.expected_answers_queue.get_nowait().set_error(msg)
        except Empty:
            # There is no more answer there, so no need to set any more errors.
            pass

    def connect(self, host, port):
        _DeejayDaemon.connect(self, host, port)
        self.sending_thread.start()
        self.receiving_thread.start()

    def disconnect(self):
        if not self.connected:
            return

        _DeejayDaemon.disconnect(self)
        # Stop our processing threads
        self.receiving_thread.should_stop = True
        # This is tricky because stopping must be notified in the queue for the
        # command thread...
        self.command_queue.put(_StopException())


    def _send_command(self, cmd, expected_answer = None):
        # Set a default answer by default
        if expected_answer == None:
            expected_answer = DeejaydAnswer(self)

        self.expected_answers_queue.put(expected_answer)
        self.command_queue.put(cmd)
        return expected_answer


# vim: ts=4 sw=4 expandtab
