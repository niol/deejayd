CREATE TABLE {library}(
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
CREATE TABLE {video}(
    dir TEXT,
    filename TEXT,
    type TEXT,
    PRIMARY KEY (dir,filename));
CREATE TABLE {webradio}(
    wid INT,
    name TEXT,
    url TEXT,
    PRIMARY KEY (wid));
CREATE TABLE {playlist}(
    name TEXT,
    position INT, 
    dir TEXT,
    filename TEXT,
    PRIMARY KEY (name,position));
CREATE TABLE {stats}(
    name TEXT,
    value INT,
    PRIMARY KEY (name));
INSERT INTO "{stats}" VALUES('db_update',0);
INSERT INTO "{stats}" VALUES('songs',0);
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
INSERT INTO "{variables}" VALUES('database_version','1');
