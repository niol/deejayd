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

import urllib, traceback
from deejayd import DeejaydError
from deejayd.ui import log

def quote_uri(path):
    if type(path) is unicode:
        path = path.encode('utf-8')
    return "file://%s" % urllib.quote(path)

def str_decode(data, charset='utf-8', errors='strict'):
    """
    Decode the string given a supplied charset into a unicode string, and
    log errors.
    """
    if type(data) is unicode:
        return data
    try: rs = data.decode(charset, errors)
    except UnicodeError:
        err = _("'%s' string has badly encoded characters") % \
                data.decode(charset, "replace")
        log.err(err)
        raise
    return rs

def log_traceback(level="info"):
    log_func = level == "info" and log.info or log.err
    log_func("------------------Traceback lines--------------------")
    log_func(str_decode(traceback.format_exc(), errors='replace'))
    log_func("-----------------------------------------------------")

def format_time(time):
    """Turn a time value in seconds into hh:mm:ss or mm:ss."""
    if time >= 3600:  # 1 hour
        # time, in hours:minutes:seconds
        return "%d:%02d:%02d" % (time // 3600, (time % 3600) // 60, time % 60)
    else:
        # time, in minutes:seconds
        return "%d:%02d" % (time // 60, time % 60)

def format_time_long(time):
    """Turn a time value in seconds into x hours, x minutes, etc."""
    if time < 1: return _("No time information")
    cutoffs = [
        (60, "%d seconds", "%d second"),
        (60, "%d minutes", "%d minute"),
        (24, "%d hours", "%d hour"),
        (365, "%d days", "%d day"),
        (None, "%d years", "%d year"),
    ]
    time_str = []
    for divisor, plural, single in cutoffs:
        if time < 1: break
        if divisor is None: time, unit = 0, time
        else: time, unit = divmod(time, divisor)
        if unit: time_str.append(ngettext(single, plural, unit) % unit)
    time_str.reverse()
    if len(time_str) > 2: time_str.pop()
    return ", ".join(time_str)

    ngettext("%d second", "%d seconds", 1)
    ngettext("%d minute", "%d minutes", 1)
    ngettext("%d hour", "%d hours", 1)
    ngettext("%d day", "%d days", 1)
    ngettext("%d year", "%d years", 1)

def get_playlist_file_lines(URL):
    pls_handle = urllib.urlopen(URL)
    playlist = pls_handle.read()

    return playlist.splitlines()

def get_uris_from_pls(URL):
    uris = []
    lines = get_playlist_file_lines(URL)
    if not lines[0].startswith("[playlist]"):
        raise DeejaydError(_("Playlist has a wrong format"))

    for line in lines:
        if line.lower().startswith("file") and line.find("=") != -1:
            uris.append(line[line.find("=") + 1:].strip())

    return uris

def get_uris_from_m3u(URL):
    uris = []
    lines = get_playlist_file_lines(URL)
    if not lines[0].startswith("#EXTM3U"):
        raise DeejaydError(_("Playlist has a wrong format"))
    for line in lines:
        if not line.startswith("#") and line.strip() != "":
            uris.append(line.strip())

    return uris

# vim: ts=4 sw=4 expandtab