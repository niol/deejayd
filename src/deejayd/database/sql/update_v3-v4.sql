INSERT INTO "{variables}" VALUES('videoid','1');
DELETE FROM "{variables}" WHERE name='videodir';
DELETE FROM "{variables}" WHERE name='fullscreen';
INSERT INTO "{stats}" VALUES('videos',0);
ALTER TABLE "{playlist}" RENAME TO "{medialist}";

CREATE TABLE "{new_video_library}"(
    dir TEXT,
    filename TEXT,
    type TEXT,
    title TEXT,
    length INT,
    videowidth TEXT,
    videoheight TEXT,
    subtitle TEXT,
    PRIMARY KEY (dir,filename));
INSERT INTO "{new_video_library}" SELECT dir,filename,type,title,length,
    videowidth,videoheight,subtitle FROM "{video_library}";
DROP TABLE "{video_library}";
ALTER TABLE "{new_video_library}" RENAME TO "{video_library}";

UPDATE "{variables}" SET value='4' WHERE name='database_version';
