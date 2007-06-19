ALTER TABLE "{video}" ADD id INT DEFAULT 0;
ALTER TABLE "{video}" ADD title TEXT;
ALTER TABLE "{video}" ADD length INT DEFAULT 0;
ALTER TABLE "{video}" ADD videowidth TEXT;
ALTER TABLE "{video}" ADD videoheight TEXT;
ALTER TABLE "{video}" ADD subtitle TEXT;

ALTER TABLE "{library}" RENAME TO {audio_library};
ALTER TABLE "{video}" RENAME TO {video_library};

DELETE FROM "{stats}" WHERE name='db_update'; 
INSERT INTO "{stats}" VALUES('video_library_update',0);
INSERT INTO "{stats}" VALUES('audio_library_update',0);

INSERT INTO "{variables}" VALUES('fullscreen','0');
INSERT INTO "{variables}" VALUES('loadsubtitle','0');
INSERT INTO "{variables}" VALUES('queueid','0');
INSERT INTO "{variables}" VALUES('playlistid','1');
INSERT INTO "{variables}" VALUES('webradioid','0');
INSERT INTO "{variables}" VALUES('videodir','');
UPDATE "{variables}" SET value='2' WHERE name='database_version'; 
