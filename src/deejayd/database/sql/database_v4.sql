CREATE TABLE {audio_library}(
    dir TEXT,
    filename TEXT,
    type TEXT,
    title TEXT,
    artist TEXT,
    album TEXT,
    genre TEXT,
    tracknumber INT,
    date TEXT,
    length INT,
    bitrate INT,
    PRIMARY KEY (dir,filename));
CREATE TABLE {video_library}(
    dir TEXT,
    filename TEXT,
    type TEXT,
    title TEXT,
    length INT,
    videowidth TEXT,
    videoheight TEXT,
    subtitle TEXT,
    PRIMARY KEY (dir,filename));
CREATE TABLE {webradio}(
    wid INT,
    name TEXT,
    url TEXT,
    PRIMARY KEY (wid));
CREATE TABLE {medialist}(
    name TEXT,
    position INT,
    dir TEXT,
    filename TEXT,
    PRIMARY KEY (name,position));
CREATE TABLE {stats}(
    name TEXT,
    value INT,
    PRIMARY KEY (name));
INSERT INTO "{stats}" VALUES('video_library_update',0);
INSERT INTO "{stats}" VALUES('audio_library_update',0);
INSERT INTO "{stats}" VALUES('songs',0);
INSERT INTO "{stats}" VALUES('videos',0);
INSERT INTO "{stats}" VALUES('artists',0);
INSERT INTO "{stats}" VALUES('albums',0);
CREATE TABLE {variables}(
    name TEXT,
    value TEXT,
    PRIMARY KEY (name));
INSERT INTO "{variables}" VALUES('volume','0');
INSERT INTO "{variables}" VALUES('currentPos','0');
INSERT INTO "{variables}" VALUES('source','playlist');
INSERT INTO "{variables}" VALUES('random','0');
INSERT INTO "{variables}" VALUES('repeat','0');
INSERT INTO "{variables}" VALUES('queueid','1');
INSERT INTO "{variables}" VALUES('playlistid','1');
INSERT INTO "{variables}" VALUES('webradioid','1');
INSERT INTO "{variables}" VALUES('dvdid','1');
INSERT INTO "{variables}" VALUES('videoid','1');
INSERT INTO "{variables}" VALUES('database_version','4');
