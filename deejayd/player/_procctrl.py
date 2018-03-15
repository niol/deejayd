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


from twisted.internet import protocol

from deejayd.ui import log


class PlayerBackendProtocolClientFactory(protocol.ClientFactory):

    def clientConnectionFailed(self, connector, reason):
        log.err('ctrl: player process connection to deejayd failed: %s'
                % reason)

    def clientConnectionLost(self, connector, reason):
        log.debug('ctrl: player process connection to deejayd lost: %s'
                  % reason)


class PlayerProcessMonitoring(protocol.ProcessProtocol):

    def __init__(self, manager):
        self.manager = manager

    def childDataReceived(self, childFD, data):
        l = data.decode('utf-8').strip()
        if l:
            log.info('ctrl: %s' % l)

    def processEnded(self, status):
        if status.value.exitCode not in self.manager.EXIT_SUCCESS:
            log.err('ctrl: child process ended with status: %s' % status)
            self.manager._process_lost()


class PlayerProcess(object):

    EXIT_SUCCESS = [0]

    def __init__(self):
        self.tempdir = None
        self.__process_gone()

    def start(self):
        if self.pmonitor:
            return

        self.pmonitor = PlayerProcessMonitoring(self)
        self.start_process(self.pmonitor)

        self.connect(self)

    def stop(self):
        if not self.pmonitor:
            return

        self.stop_process()
        self.__process_gone()

    def __process_gone(self):
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

        self.pmonitor = None

    def _process_lost(self):
        pass
        # kill, restart?


# vim: ts=4 sw=4 expandtab
