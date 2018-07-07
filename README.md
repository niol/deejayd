deejayd
===========

Actual version : 0.14.0 (2018-07-07)
------------------------------------

Description:
------------
deejayd is an media player written in python and based on twisted.
So, it is a network daemon which can be controlled with a client application
like MPD. The protocol used to control deejayd is a JSON-RPC protocol.
Documentation of this protocol can be found in source archive (doc directory)

Clients:
--------
  * djc :
    -----
      djc is a command line client available in this package
  * deejayd-webui :
    --------
      It is a web based client included in this package and built 
      with angular.io (https://angular.io) and angular material 
      (https://material.angular.io/). It has to work with recent versions of 
      firefox and chrome.
      url to use this interface : http://host:webuiport/

Requirements:
-------------
    * python >= 3.4
    * twisted >= 16.6.0 (http://twistedmatrix.com/trac)
    * sqlalchemy >= 1.0.0 (https://www.sqlalchemy.org/)
    * mutagen >= 1.30
        (http://www.sacredchao.net/quodlibet/wiki/Development/Mutagen)
    * if you want to use gstreamer backend
        * gstreamer >= 1.2.0 (http://gstreamer.freedesktop.org)
    * if you want to use vlc backend
        * libvlc >= 2.2.0
    * if you want to use mpv backend
        * mpv >= 0.23
    * To be abble to play video medias
        * libX11, libXext
    * nodejs 6 or higher and npm to build the webui

If you want to build deejayd (distutils distribution), you also need
the python3-babel package installed to build .mo file

Installation:
-------------
Download deejayd and extract it:
  $tar xzvf deejayd-0.14.0.tar.gz

Then, install it with:
  $cd deejayd-0.14.0
  $python setup.py install

Usage:
------
  To launch deejayd just do
    $deejayd
  See "deejayd --help" for more informations

  To launch djc (command line client), just do
    $djc COMMANDS ARGS
  See "djc --help" to see available commands

Test deejayd without installing it:
-----------------------------------
If you want to test deejayd without installing it, you need to build the webui:
  $ ./setup.py build
Then prepare a configuration file based on deejayd/ui/defaults.conf. After that,
you can launch deejayd with
  $ PYTHONPATH=. python scripts/deejayd -n -c $cfg_file

