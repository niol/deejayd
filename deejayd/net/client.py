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
import sys, inspect, re, new, posixpath

from Queue import Queue, Empty

from deejayd import DeejaydError
from deejayd.jsonrpc import Fault, DEEJAYD_PROTOCOL_VERSION
from deejayd.jsonrpc.interfaces import JSONRPC_MODULES
from deejayd.jsonrpc.jsonbuilders import JSONRPCRequest
from deejayd.jsonrpc.jsonparsers import loads_response
from deejayd.model.mediafilters import MediaFilter


MSG_DELIMITER = 'ENDJSON\n'
MAX_BANNER_LENGTH = 50

#
# generic functions used by client library
#
def camelcase_to_underscore(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def build_command(cmd_name, cmd_args, cmd_doc, prefix):
    def func(*args, **kwargs):
        request_args = []
        for idx, arg in enumerate(cmd_args):
            try: value = args[idx + 1]
            except IndexError:
                if arg["req"] is True:
                    raise DeejaydError("argument %s is required" % arg["name"])
                # perhaps argument is available in key/value arguments
                try : value = kwargs[arg["name"]]
                except KeyError:
                    continue
            # TODO verify arguments
            if arg["type"] == "filter" and value is not None:
                try: value = value.to_json()
                except:
                    raise DeejaydError("arg %s is not a valid filter"\
                            % arg["name"])
            request_args.append(value)
        self = args[0]

        cmd = prefix == "" and cmd_name or prefix + "." + cmd_name
        request = JSONRPCRequest(cmd, request_args)
        try: return self._send_command(request)
        except AttributeError:  # we are in a submodule
            return self.core._send_command(request)
    func.__name__ = camelcase_to_underscore(cmd_name)
    func.__doc__ = cmd_doc

    return func

def build_module(instance, CmdClass, prefix=""):
    cmd_names = [n for n in dir(CmdClass) if not n.startswith("__")]
    for cmd_name in cmd_names:
        cmd = getattr(CmdClass, cmd_name)
        if inspect.isclass(cmd):
            args = getattr(cmd, 'args', [])
            setattr(instance, camelcase_to_underscore(cmd_name),
                    build_command(cmd_name, args, cmd.__doc__, prefix))

def parse_deejayd_answer(answer):
    if answer["error"] is not None:  # an error is returned
            error = "Deejayd Server Error - %s - %s"\
                % (answer["error"]["code"], answer["error"]["message"])
            raise DeejaydError(error)
    result = answer["result"]["answer"]
    type = answer["result"]["type"]
    if type == "recordedPlaylist":
        if result["filter"] is not None:
            try: result["filter"] = MediaFilter.load_from_json(result["filter"])
            except Fault:
                raise DeejaydError("Unable to parse filter in answer")
    return result

############################################################
############################################################

class ConnectError(DeejaydError):
    pass

class _DeejayDaemon(object):
    """Abstract class for a deejayd daemon client."""

    def __init__(self):
        super(_DeejayDaemon, self).__init__()
        self.connected = False

        # builds commands based on JSONRPC_COMMANDS attr
        for module, CmdClass in JSONRPC_MODULES.items():
            if module == "core":
                prefix = ""
                instance = self.__class__
            else:
                prefix = module
                instance = new.classobj(module + "Class", (object,), {})
                obj = instance()
                # add core attr to allow this module to send commands
                setattr(obj, "core", self)
                setattr(self, module, obj)
            build_module(instance, CmdClass, prefix)

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
        protocol_version = versions[1]
        return protocol_version == DEEJAYD_PROTOCOL_VERSION

    def _send_simple_command(self, cmd_name):
        cmd = JSONRPCRequest(cmd_name, [])
        return self._send_command(cmd)

    def _build_answer(self, msg):
        try: msg = loads_response(msg)
        except Fault, f:
            raise DeejaydError("JSONRPC error - %s - %s" % (f.code, f.message))
        if msg["id"] is None:  # it is a notification
            result = msg["result"]["answer"]
            type = msg["result"]["type"]
            if type == 'signal':
                signal = DeejaydSignal(result["name"], result["attrs"])
                return self._dispatch_signal(signal)
            return None
        return msg


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

    def _send_command(self, cmd):
        self._sendmsg(cmd.to_json())
        rawmsg = self._readmsg()
        return parse_deejayd_answer(self._build_answer(rawmsg))

    def disconnect(self):
        if not self.connected:
            return

        self.socket_to_server.settimeout(self.__timeout)
        try: self.close()
        except socket.timeout:
            pass

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
        def split_msg(msg, index):
            return (msg[0:index], msg[index + len(MSG_DELIMITER):len(msg)])

        while 1:
            try: index = self.next_msg.index(MSG_DELIMITER)
            except ValueError: pass
            else:
                (rs, self.next_msg) = split_msg(self.next_msg, index)
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
                (rs, self.next_msg) = split_msg(msg_chunks, index)
                break

        return rs

    # No subscription for the sync client
    def subscribe(self, signal_name, callback): raise NotImplementedError
    def unsubscribe(self, sub_id): raise NotImplementedError


###########################################################################
##### Asynchronous client
###########################################################################

class DeejaydAsyncAnswer(object):

    def __init__(self):
        self.answer_received_evt = threading.Event()
        self.callbacks = []
        self.errbacks = []
        self.answer, self.error = None, None
        self.__id = None

    def set_id(self, id):
        self.__id = id

    def get_id(self):
        return self.__id

    def add_callback(self, cb):
        if self.answer_received_evt.isSet() and self.answer is not None:
            cb(self.answer)
        else:
            self.callbacks.append(cb)

    def add_errback(self, cb):
        if self.answer_received_evt.isSet() and self.error is not None:
            cb(self.error)
        else:
            self.errbacks.append(cb)

    def answer_received(self, answer):
        try: answer = parse_deejayd_answer(answer)
        except DeejaydError, err:
            self.error = str(err)
            for cb in self.errbacks:
                cb(self.error)
        else:
            self.answer = answer
            for cb in self.callbacks:
                cb(self.answer)
        self.answer_received_evt.set()

    def wait_for_answer(self):
        self.answer_received_evt.wait()
        if self.error is not None:
            raise DeejaydError(self.error)
        return self.answer

class DeejaydListAnswer(DeejaydAsyncAnswer):

    def __getitem__(self, i):
        self.wait_for_answer()
        return self.answer[i]

    def __contains__(self, item):
        self.wait_for_answer()
        return item in self.answer

    def __len__(self):
        self.wait_for_answer()
        return len(self.answer)

class DeejaydDictAnswer(DeejaydAsyncAnswer):

    def __repr__(self):
        self.wait_for_answer()
        return repr(self.answer)

    def __getitem__(self, key):
        self.wait_for_answer()
        return self.answer[key]

    def __iter__(self):
        self.wait_for_answer()
        return iter(self.data)

    def keys(self):
        self.wait_for_answer()
        return self.answer.keys()

    def items(self):
        self.wait_for_answer()
        return self.answer.items()

    def iteritems(self):
        self.wait_for_answer()
        return self.answer.iteritems()

    def iterkeys(self):
        self.wait_for_answer()
        return self.answer.iterkeys()

    def itervalues(self):
        self.wait_for_answer()
        return self.answer.itervalues()

    def values(self):
        self.wait_for_answer()
        return self.answer.values()

    def has_key(self, key):
        self.wait_for_answer()
        return key in self.answer

    def get(self, key, failobj=None):
        self.wait_for_answer()
        if key not in self.answer:
            return failobj
        return self[key]


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
        assert tb  # Must have a traceback
        if self.state != "json_protocol":
            # error appears when we try to connect
            for cb in self.__connect_callback:
                cb(False, str(v))

    def handle_connect(self):
        self.state = "connected"

    def handle_close(self):
        if self.state == "json_protocol":
            self.__error_callbacks('disconnected')
        self.state = "disconnected"
        self.close()

    def handle_read(self):
        def split_msg(msg, index):
            return (msg[0:index], msg[index + len(MSG_DELIMITER):len(msg)])

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
                    for cb in self.__connect_callback:
                        cb(False, 'Initial version dialog with server failed')
                if self.ignore_version\
                or self.deejayd._version_is_supported(versions):
                    self.state = 'json_protocol'
                    # now we are sure to be connected
                    for cb in self.__connect_callback:
                        cb(True, "")
                else:
                    for cb in self.__connect_callback:
                        cb(False, \
          'This server version protocol is not handled by this client version')

        elif self.state == "json_protocol":
            msg_chunk = self.recv(256)
            # socket.recv returns an empty string if the socket is closed, so
            # catch this.
            if msg_chunk == '':
                self.close()
            self.msg_chunks += msg_chunk
            try: index = self.msg_chunks.index(MSG_DELIMITER)
            except ValueError: return
            else:
                (rawmsg, self.next_msg) = split_msg(self.msg_chunks, index)
                self.msg_chunks = ""
                self.answer_received(rawmsg)

                while self.next_msg != '':
                    try: index = self.next_msg.index(MSG_DELIMITER)
                    except ValueError:
                        self.msg_chunks = self.next_msg
                        self.next_msg = ""
                        break
                    else:
                        (rawmsg, self.next_msg) = split_msg(self.next_msg, index)
                        self.answer_received(rawmsg)

        elif self.state == "disconnected":
            # This should not happen
            raise AttributeError

    def answer_received(self, rawmsg):
        try: ans = self.deejayd._build_answer(rawmsg)
        except DeejaydError:
            self.__error_callbacks("Unable to parse server answer : %s" % rawmsg)
            self.close()
        else:
            if ans is None:  # it's a notification (signal) and not an answer
                return

            try:
                expected_answer = self.deejayd.expected_answers_queue\
                                               .get(timeout=10)
            except Empty:
                self.__error_callbacks("No expected answer for this command")
                self.close()
            else:
                if expected_answer.get_id() != ans["id"]:
                    self.__error_callbacks("Bad id for JSON server answer")
                    self.close()
                else:
                    expected_answer.answer_received(ans)

    def handle_write(self):
        cmd = self.deejayd.command_queue.get()
        self.send(cmd.to_json() + MSG_DELIMITER)

    def writable(self):
        if self.state != "json_protocol": return False
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
        self.expected_answers_queue = Queue()
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

    def __connect_callback(self, rs, msg=""):
        self.connected = rs
        if not rs:  # error happens, reset socket
            del self.socket_to_server
            self.socket_to_server = None
        for cb in self.__con_cb:
            cb(rs, msg)

    def add_connect_callback(self, cb):
        self.__con_cb.append(cb)

    def add_error_callback(self, cb):
        self.__err_cb.append(cb)

    def connect(self, host, port, ignore_version=False):
        if self.connected:
            self.disconnect()

        self.__create_socket(ignore_version)
        try: self.socket_to_server.connect((host, port))
        except socket.error, msg:
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

    def _send_command(self, cmd):
        expected_answer = DeejaydAsyncAnswer()
        expected_answer.set_id(cmd.get_id())

        self.expected_answers_queue.put(expected_answer)
        self.command_queue.put(cmd)
        return expected_answer

    def subscribe(self, signal_name, callback):
        # TODO: rewrite async subscribe/unsubscribe command in client library
        pass

    def unsubscribe(self, sub_id):
        pass


#
# HTTP client
#
import httplib

class DeejayDaemonHTTP(_DeejayDaemon):
    """HTTP deejayd client library."""

    def __init__(self, host, port=6880, root_url="/"):
        _DeejayDaemon.__init__(self)
        self.host = host
        self.port = port
        self.url = posixpath.join(root_url, "rpc/")
        self.connection = httplib.HTTPConnection(self.host, self.port)
        self.hdrs = {
                "Content-Type": "text/json",
                "Accept": "text/json",
                "User-Agent": "Deejayd Client Library",
            }

    def _send_command(self, cmd):
        # send http request
        try: self.connection.request("POST", self.url, cmd.to_json(), self.hdrs)
        except Exception, ex:
            raise DeejaydError("Unable to send request : %s" % str(ex))

        # get answer
        response = self.connection.getresponse()
        if response.status != 200:
            raise DeejaydError("Server return error code %d - %s" % \
                    (response.status, response.reason))
        rawmsg = response.read()
        return parse_deejayd_answer(self._build_answer(rawmsg))

    # No subscription for the http client
    def subscribe(self, signal_name, callback): raise NotImplementedError
    def unsubscribe(self, sub_id): raise NotImplementedError

# vim: ts=4 sw=4 expandtab
