# Deejayd, a media player daemon
# Copyright (C) 2013 Mickael Royer <mickael.royer@gmail.com>
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


from twisted.internet import reactor
import threading


TWISTED_REACTOR = False

def need_twisted_reactor():
    global TWISTED_REACTOR
    if not TWISTED_REACTOR:
        #from twisted.python import log
        #log.startLogging(sys.stdout)
        TWISTED_REACTOR = threading.Thread(target=reactor.run,
                                           kwargs={'installSignalHandlers':0})
        TWISTED_REACTOR.start()

def stop_twisted_reactor():
    if TWISTED_REACTOR:
        reactor.callFromThread(reactor.stop)
        TWISTED_REACTOR.join()


# vim: ts=4 sw=4 expandtab
