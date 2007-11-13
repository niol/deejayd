"""The Deejayd python client library"""

import socket, threading
from cStringIO import StringIO
try: from xml.etree import cElementTree as ET # python 2.5
except ImportError: # python 2.4
    import cElementTree as ET

from Queue import Queue, Empty

from deejayd.net.xmlbuilders import DeejaydXMLCommand


MSG_DELIMITER = 'ENDXML\n'


class DeejaydError(Exception):
    pass

class DeejaydAnswer:

    def __init__(self, server = None):
        self.answer_received = threading.Event()
        self.callbacks = []
        self.contents = None
        self.error = False
        self.server = server
        self.originating_command = 'unknown'

    def wait(self):
        self.answer_received.wait()

    def _received(self, contents):
        self.contents = contents
        self.answer_received.set()
        self._run_callbacks()

    def set_error(self, msg):
        self.contents = msg
        self.error = True
        self.answer_received.set()

    def get_contents(self):
        self.wait()
        if self.error:
            raise DeejaydError(self.contents)
        return self.contents

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


class DeejaydKeyValue(DeejaydAnswer):

    def __getitem__(self, name):
        self.get_contents()
        return self.contents[name]

    def items(self):
        self.get_contents()
        return self.contents.items()


class DeejaydFileList(DeejaydAnswer):

    def __init__(self, server = None):
        DeejaydAnswer.__init__(self, server)
        self.root_dir = ""
        self.files = []
        self.directories = []

    def set_rootdir(self, dir):
        self.root_dir = dir

    def add_file(self, file):
        self.files.append(file)

    def add_dir(self, dir):
        self.directories.append(dir)

    def get_files(self):
        self.get_contents()
        return self.files

    def get_directories(self):
        self.get_contents()
        return self.directories


class DeejaydMediaList(DeejaydAnswer):

    def __init__(self, server = None):
        DeejaydAnswer.__init__(self, server)
        self.medias = []

    def add_media(self, media):
        self.medias.append(media)

    def get_medias(self):
        self.get_contents()
        return self.medias


class DeejaydDvdInfo(DeejaydAnswer):

    def __init__(self, server = None):
        DeejaydAnswer.__init__(self, server)
        self.tracks = []
        self.dvd_content = {}

    def set_dvd_content(self, infos):
        self.dvd_content = infos

    def add_track(self, track):
        self.tracks.append(track)

    def get_dvd_contents(self):
        self.get_contents()
        self.dvd_content["tracks"] = self.tracks
        return self.dvd_content


class DeejaydWebradioList:

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

    def delete_webradio(self, wr_id):
        return self.delete_webradios([wr_id])

    def delete_webradios(self, wr_ids):
        cmd = DeejaydXMLCommand('webradioRemove')
        cmd.add_multiple_arg('id', wr_ids)
        return self.server._send_command(cmd)

    def clear(self):
        cmd = DeejaydXMLCommand('webradioClear')
        return self.server._send_command(cmd)


class DeejaydQueue:

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

    def clear(self):
        cmd = DeejaydXMLCommand('queueClear')
        return self.server._send_command(cmd)

    def del_song(self, id):
        return self.del_songs([id])

    def del_songs(self, ids):
        cmd = DeejaydXMLCommand('queueRemove')
        cmd.add_multiple_arg('id', ids)
        return self.server._send_command(cmd)


class DeejaydPlaylist:

    def __init__(self, server, pl_name = None):
        self.server = server
        self.__pl_name = pl_name

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

    def add_song(self, path, position = None):
        return self.add_songs([path], position)

    def add_songs(self, paths, position = None):
        cmd = DeejaydXMLCommand('playlistAdd')
        cmd.add_multiple_arg('path', paths)
        if position != None:
            cmd.add_simple_arg('pos', position)
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
        return self.server._send_command(cmd)

    def load(self, name, pos = None):
        return self.loads([name], pos)

    def loads(self, names, pos = None):
        cmd = DeejaydXMLCommand('playlistLoad')
        cmd.add_multiple_arg('name', names)
        if pos != None:
            cmd.add_simple_arg('pos', pos)
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

    def del_song(self, id):
        return self.del_songs([id])

    def del_songs(self, ids):
        cmd = DeejaydXMLCommand('playlistRemove')
        cmd.add_multiple_arg('id', ids)
        if self.__pl_name != None:
            cmd.add_simple_arg('name', self.__pl_name)
        return self.server._send_command(cmd)


class ConnectError(Exception):
    pass


class _DeejayDaemon:
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
        msg_chunks = []
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

            try: index = msg_chunk.index(MSG_DELIMITER)
            except ValueError:
                msg_chunks.append(msg_chunk)
            else:
                msg_chunks.append(msg_chunk[0:index])
                rs = self.next_msg.join(msg_chunks)
                self.next_msg = msg_chunk[index+len(MSG_DELIMITER):\
                                          len(msg_chunk)]
                break

        return rs

    def _send_simple_command(self, cmd_name):
        cmd = DeejaydXMLCommand(cmd_name)
        return self._send_command(cmd)

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

    def go_to(self, id, id_type = None):
        cmd = DeejaydXMLCommand('play')
        cmd.add_simple_arg('id', id)
        if id_type:
            cmd.add_simple_arg('id_type', id_type)
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
            else:
                xmlpath.pop()

                if elem.tag in ('error','response'):
                    expected_answer.set_originating_command(elem.attrib['name'])

                if elem.tag == "error":
                    expected_answer.set_error(elem.text)
                elif elem.tag == "response":
                    rsp_type = elem.attrib['type']
                    if rsp_type == "KeyValue":
                        answer = parms
                    expected_answer._received(answer)
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
                parms = elem.tag == "parm" and parms or {}

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


class _DeejaydSocketThread(threading.Thread):

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


class _DeejaydCommandThread(_DeejaydSocketThread):

    def __init__(self, deejayd, socket, command_queue):
        _DeejaydSocketThread.__init__(self, deejayd, socket)
        self.command_queue = command_queue

    def really_run(self):
        cmd = self.command_queue.get()

        # If we've got a stop exception in the queue, raise it!
        if cmd.__class__ == _StopException:
            raise cmd

        self.deejayd._sendmsg(cmd.to_xml())


class _DeejaydAnswerThread(_DeejaydSocketThread):

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


class DeejayDaemonAsync(_DeejayDaemon):
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
