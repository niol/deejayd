
New features and significant updates in version...

0.14.0 (2018-07-07)
-------------------
  * Python 3 support
  * Manage database with sqlalchemy library
  * Rewrite webui with angular, angular-material and webpack
  * Add new player backend based on mpv

0.13.1 (2014-01-10)
-------------------
  * Fix bug about log files

0.13.0 (2014-01-10)
-------------------
  * Add vlc backend
  * Use twisted inotify API instead of pyinotify
  * Remove kaa-metadata dependency and implements video parser in deejayd
  * Rewrite some core components
  * Remove mysql backend
  * A lot of bug fixes

0.12.0 (2012-11-11)
-------------------
  * Restructure the code to reduce its size
     WARNING : there are some changes in the JSON-RPC interface, see docs
  * Rewrite gstreamer player
     * Add video support
     * Add gapless support
    Now, deejayd requires gstreamer >= 0.10.24
  * Add new player command : player.getAvailableVideoOptions to know
    video capabilities of the active player
  * Rewrite webradio module
    * replace shoutcast plugin with an icecast plugin
    * enable use of categories for recorded webradio
  * Rewrite test module
    * require python >= 2.7 or unittest2 module installed
    * optimize media library init
    * add new options in test launcher
      * --player to select active player : xine or gstreamer
      * --db to select active database backend : sqlite or mysql

0.11.0 (2010-12-27)
-------------------
  * Replace XUL ui with a new webui built with Google Web Toolkit
  * In the same way, replace mobile webui with a new one based on GWT
  * Set volume by media type (song, video, webradio) and save all volume
    states when deejayd quit
  * Several bug fixes

0.10.0 (2010-03-31)
--------------------
  * Improve webradio mode
  * Add shoutcast webradio support (disabled by default)
  * Add lastfm audioscrobbler support (disabled by default)
  * Update firefox extension to work with 3.6 version
  * Several bug fixes

0.9.0 (2009-09-21)
--------------------
  * Replace XML protocol by a JSON-RPC protocol
  * Rewrite XUL/Mobile webui to use new JSON-RPC protocol
  * Xine : Add a new player option 'aspect_ratio" to change video aspect ratio
  * Improve mobile webui
  * Use kaa-metradata instead of hachoir-metadata/lsdvd to get video infos
  * Xine : handle separate volume levels for audio and video media tracks

0.8.3 (2009-07-05)
--------------------
  * update extension to work with firefox 3.5
  * several bug fixes

0.8.2 (2009-05-24)
--------------------
  * fix a important bug in library

0.8.1 (2009-05-19)
--------------------
  * add cdnumber info for audio media in database
  * support multiple audio/video channels in video files
  * fixes in xul webui

0.8.0 (2009-04-27)
--------------------
  * update database schema to be more evolutive
  * add new mode : navigation panel (like rhythmbox panel mode)
  * implement mediafilters to filter audio/video library
  * add rating support
  * add new playorder mode
    * weigthed random
    * one media
  * set xine binding as an independant module (pytyxi)
  * add a html interface optimized for mobile device (http://host:port/m/)
  * add full support of cover album
  * set xul webui as an firefox extension
  * add intelligent playlist support
  * add support of pyinotify-0.8

0.7.2 (2008-05-15)
--------------------
  * xine: add osd support (disabled by default)
  * xine: add zoom option
  * many fix in signal infrastructure
  * fix in sql requests

0.7.1 (2008-04-16)
--------------------
  * add queue random option
  * use XUL notification to display messages
  * fix dvd playback
  * minor fix in client library

0.7.0 (2008-03-28)
--------------------
  * database : add mysql backend support
  * add new player options : Audio/Video offset and Subtitle offset
  * add flac support
  * add replaygain support (track profile only)
  * add script to process an audio library and
    record replaygain track gain/peak in songs
  * log reopen on SIGHUP
  * inotify watches out of root directory symlink
  * save full status on exit and restore it on startup

0.6.3 (2008-02-10)
--------------------
  * xine : disable DPMS while playing videos

0.6.2 (2008-02-03)
--------------------
  * fix in xine backend
    * correctly hide cursor
    * fix xine event callback
  * fix in mediadb (skip file with bad caracter)

0.6.1 (2008-01-28)
--------------------
  * fix important bug in xine backend
  * fix symlinks support in audio/video library

0.6.0 (2008-01-26)
--------------------
  * rewrite xine backend to use ctypes
  * xine : add gapless support
  * improve video mode
  * add signaling support
  * add inotify support to update audio/video library
  * improve webui performance
  * add i18n support (only french translation is available for now)
  * A lot of cleanups and bugfixes

0.5.0 (2007-12-26)
------------------
  * xine backend : close stream when no media has been played
  * integrate webui in deejayd. Ajaxdj is useless now
  * support all commands in library client and djc
  * A lot of cleanups and bugfixes

0.4.1 (2007-11-11)
------------------
  * Fix bugs in mediadb and video source
  * Fix documentation generation and update it

0.4.0 (2007-11-04)
------------------
  * Add dvd support
  * Add a python library client
  * Add a command line client : djc
  * Improve performance and memory usage with the use of celementtree module
  * A lot of cleanups and bugfixes

0.2.0 (2007-06-24)
------------------
  * Add a song queue
  * Add video support
  * Add xine backend
  * Rewrite library
  * A lot of cleanups and bugfixes

0.1.0 (2007-02-28)
------------------
  * First release !!
