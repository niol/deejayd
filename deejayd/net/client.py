"""The Deejayd python client library"""

import socket, threading

from Queue import Queue, Empty

from deejayd.net.xmlbuilders import DeejaydXMLCommand

from StringIO import StringIO
from xml.sax import make_parser, SAXParseException
from xml.sax.handler import ContentHandler

msg_delimiter = 'ENDXML\n'


class DeejaydError(Exception):
    pass

class DeejaydAnswer:

    def __init__(self, server = None):
        self.answer_received = threading.Event()
        self.contents = None
        self.error = False
        self.server = server

    def wait(self):
        self.answer_received.wait()

    def received(self, contents):
        self.contents = contents
        self.answer_received.set()

    def set_error(self, msg):
        self.contents = msg
        self.error = True
        self.answer_received.set()

    def get_contents(self):
        self.wait()
        if self.error:
            raise DeejaydError(self.contents)
        return self.contents


class DeejaydKeyValue(DeejaydAnswer):

    def __getitem__(self, name):
        self.get_contents()
        return self.contents[name]


class DeejaydFileList(DeejaydAnswer):

    def __init__(self, server = None):
        DeejaydAnswer.__init__(self, server)
        self.files = []
        self.directories = []

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


class DeejaydWebradioList(DeejaydAnswer):

    def add_webradio(self, name, urls):
        cmd = DeejaydXMLCommand('webradioAdd')
        cmd.add_simple_arg('name', name)
        # FIXME : Provision for the future where one webradio may have multiple
        # urls.
        # cmd.add_multiple_arg('url', urls)
        cmd.add_simple_arg('url', urls)
        return self.server.send_command(cmd)

    def delete_webradio(self, name):
        cmd = DeejaydXMLCommand('webradioRemove')
        wr_id = self.get_webradio(name)['Id']
        cmd.add_multiple_arg('id', [wr_id])
        return self.server.send_command(cmd)

    def names(self):
        names = []
        for wr in self.get_contents():
            names.append(wr['Title'])
        return names

    def get_webradio(self, name):
        return self.__get_webradio_by_field('Title', name)

    def __get_webradio_by_field(self, field, value):
        i_wr = iter(self.get_contents())
        try:
            while True:
                wr = i_wr.next()
                if wr[field] == value:
                    return wr
        except StopIteration:
            raise DeejaydError('Webradio not found')


class DeejaydPlaylist(DeejaydKeyValue):

    def save(self, name):
        cmd = DeejaydXMLCommand('playlistSave')
        cmd.add_simple_arg('name', name)
        return self.server.send_command(cmd)

    def add_song(self, path, position = None, name = None):
        return self.add_songs([path], position, name)

    def add_songs(self, paths, position = None, name = None):
        cmd = DeejaydXMLCommand('playlistAdd')
        cmd.add_multiple_arg('path', paths)
        if position != None:
            cmd.add_simple_arg('pos', position)
        if name != None:
            cmd.add_simple_arg('name', name)
        return self.server.send_command(cmd)

    def load(self, name, loading_position = 0):
        cmd = DeejaydXMLCommand('playlistLoad')
        cmd.add_simple_arg('name', name)
        cmd.add_simple_arg('pos', loading_position)
        return self.server.send_command(cmd)


class _AnswerFactory(ContentHandler):

    def __init__(self, expected_answers_queue):
        self.expected_answers_queue = expected_answers_queue

        self.answer = None
        self.originating_command = ''

        self.xmlpath = []
        self.response_type = ''
        self.parms = {}

    def startElement(self, name, attrs):
        self.xmlpath.append(name)

        if name in ['error', 'response'] and len(self.xmlpath) == 2:
            self.originating_command = attrs.get('name')
            self.expected_answer = self.expected_answers_queue.get()

        if name == 'response':
            self.response_type = attrs.get('type')
            if self.response_type == 'Ack':
                self.answer = True
            elif self.response_type in ['FileList', 'WebradioList',
                                       'SongList', 'PlaylistList']:
                self.answer = []
            elif self.response_type == 'KeyValue':
                self.answer = {}
        elif name == 'parm':
            # Parse value into a int if possible
            val = attrs.get('value')
            try:
                real_val = int(val)
            except(ValueError):
                real_val = val

            if self.response_type == 'KeyValue':
                self.answer[attrs.get('name')] = real_val
            else:
                self.parms[attrs.get('name')] = real_val
        elif name == 'directory':
            assert self.response_type == 'FileList'
            assert self.xmlpath == ['deejayd', 'response', 'directory']
            self.expected_answer.add_dir(attrs.get('name'))
        elif name == 'playlist':
            assert self.response_type == 'PlaylistList'
            assert self.xmlpath == ['deejayd', 'response', 'playlist']
            self.answer.append(attrs.get('name'))
        elif name == 'error':
            self.response_type = 'error'

    def characters(self, str):
        if self.xmlpath == ['deejayd', 'error']:
            self.answer = str

    def endElement(self, name):
        self.xmlpath.pop()

        if name in ['song', 'webradio']:
            self.answer.append(self.parms)
            self.parms = {}
        elif name == 'file':
            self.expected_answer.add_file(self.parms)
            self.parms = {}
        elif name in ['response', 'error']:
            if name == 'response':
                self.expected_answer.received(self.answer)
            elif name == 'error':
                self.expected_answer.set_error(self.answer)

            self.answer = None
            self.expected_answer = None

    def get_originating_command(self):
        return self.originating_command


class _DeejaydSocketThread(threading.Thread):

    def __init__(self, socket):
        threading.Thread.__init__(self)

        self.socket_die_callback = []

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
                except SAXParseException:
                    # XML parsing failed, simply ignore. What should we do here?
                    pass
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

    def __init__(self, socket, command_queue):
        _DeejaydSocketThread.__init__(self, socket)
        self.command_queue = command_queue

    def really_run(self):
        cmd = self.command_queue.get()

        # If we've got a stop exception in the queue, raise it!
        if cmd.__class__ == _StopException:
            raise cmd

        self.__send(cmd.to_xml())

    def __send(self, buf):
        self.socket_to_server.send(buf + msg_delimiter)


class _DeejaydAnswerThread(_DeejaydSocketThread):

    def __init__(self, socket, expected_answers_queue):
        _DeejaydSocketThread.__init__(self, socket)
        self.expected_answers_queue = expected_answers_queue

        self.parser = make_parser()
        self.answer_builder = _AnswerFactory(self.expected_answers_queue)
        self.parser.setContentHandler(self.answer_builder)

    def really_run(self):
        rawmsg = self.__readmsg()
        self.parser.parse(StringIO(rawmsg))

    def __readmsg(self):
        msg_chunks = []

        # This is dirty, but there is no msgdelim in answers...
        msg_delimiter = '</deejayd>'

        msg_chunk = ''
        while msg_chunk[-len(msg_delimiter):len(msg_chunk)] != msg_delimiter:
            msg_chunk = self.socket_to_server.recv(4096)

            # socket.recv returns an empty string if the socket is closed, so
            # catch this.
            if msg_chunk == '':
                raise socket.error()
            else:
                msg_chunks.append(msg_chunk)

        # We should strip the msgdelim, but in our hack, it is part of the XML,
        # so it may not be a good idea to strip it...
        #return ''.joint(msg_chunks)[0:len(msg) - 1 - len(msg_delimiter)]
        return ''.join(msg_chunks)


class ConnectError(Exception):
    pass


class DeejayDaemon:

    def __init__(self, async = True):
        # Queue setup
        self.command_queue = Queue()
        self.expected_answers_queue = Queue()

        # Socket setup
        self.socket_to_server = socket.socket(socket.AF_INET,
                                              socket.SOCK_STREAM)
        self.connected = False

        # Messaging threads
        self.sending_thread = _DeejaydCommandThread(self.socket_to_server,
                                                   self.command_queue)
        self.receiving_thread = _DeejaydAnswerThread(self.socket_to_server,
                                                    self.expected_answers_queue)
        self.receiving_thread.add_socket_die_callback(\
                                             self.__make_answers_obsolete)
        for thread in [self.sending_thread, self.receiving_thread]:
            thread.add_socket_die_callback(self.__disconnect)

        # Library behavior, asynchroneous or not
        self.async = async

    def connect(self, host, port):
        if self.connected:
            self.disconnect()

        self.host = host
        self.port = port

        try:
            self.socket_to_server.connect((self.host, self.port))
        except socket.error, msg:
            print msg
            return

        socketFile = self.socket_to_server.makefile()

        # Catch version
        self.version = socketFile.readline()

        # Go in XML mode
        self.socket_to_server.send('setXML\n')
        init_answer = socketFile.readline()

        if init_answer == 'OK\n':
            self.sending_thread.start()
            self.receiving_thread.start()
            self.connected = True
        else:
            self.disconnect()
            raise ConnectError('Initialisation with server failed')

    def disconnect(self):
        if not self.connected:
            return

        # Stop our processing threads
        self.receiving_thread.should_stop = True
        # This is tricky because stopping must be notified in the queue for the
        # command thread...
        self.command_queue.put(_StopException())

        self.socket_to_server.close()
        self.connected = False
        self.host = None
        self.port = None

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

    def is_async(self):
        return self.async

    def set_async(self, async):
        self.async = async

    def __return_async_or_result(self, answer):
        if not self.async:
           answer.get_contents()
        return answer

    def send_command(self, cmd, expected_answer = None):
        # Set a default answer by default
        if expected_answer == None:
            expected_answer = DeejaydAnswer(self)

        self.expected_answers_queue.put(expected_answer)
        self.command_queue.put(cmd)
        return self.__return_async_or_result(expected_answer)

    def ping(self):
        cmd = DeejaydXMLCommand('ping')
        return self.send_command(cmd)

    def get_status(self):
        cmd = DeejaydXMLCommand('status')
        return self.send_command(cmd, DeejaydKeyValue())

    def get_playlist(self, name):
        cmd = DeejaydXMLCommand('playlistInfo')
        if name != None:
            cmd.add_simple_arg('name', name)
        ans = DeejaydPlaylist(self)
        return self.send_command(cmd, ans)

    def get_current_playlist(self):
        return self.get_playlist(None)

    def get_playlist_list(self):
        cmd = DeejaydXMLCommand('playlistList')
        return self.send_command(cmd)

    def get_webradios(self):
        cmd = DeejaydXMLCommand('webradioList')
        ans = DeejaydWebradioList(self)
        return self.send_command(cmd, ans)


# vim: ts=4 sw=4 expandtab
