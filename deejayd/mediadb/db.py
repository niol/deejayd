"""
"""

import os, sys, time
from deejayd.ui.config import DeejaydConfig

#
# Methods to initialise the database and connect to it
#
def initSqliteDB(con):
	cur = con.cursor()
	# creation of tables
	cur.execute("CREATE TABLE library(dir TEXT,filename TEXT,type TEXT,title TEXT,artist TEXT,album TEXT,genre TEXT,track_number INT, length INT, bitrate INT, PRIMARY KEY (dir,filename))")
	cur.execute("CREATE TABLE radio(name TEXT,url1 TEXT, url2 TEXT, url3 TEXT,PRIMARY KEY (name))")
	cur.execute("CREATE TABLE stat(name TEXT,value INT,PRIMARY KEY (name))")

	cur.execute("INSERT INTO stat(name,value)VALUES('last_updatedb_time',0)")
	con.commit()
	cur.close()

def createDB():

	db_type = DeejaydConfig().get("mediadb","db_type")
	if db_type == 'sqlite':
		from pysqlite2 import dbapi2 as sqlite
		db_file = DeejaydConfig().get("mediadb","db_file")
		# Initialise the database if necessary
		init = os.path.isfile(db_file) and (0,) or (1,)
		try:
			con = sqlite.connect(db_file)
		except :
			sys.exit("Unable to connect at the sqlite database. Verify your config file.")
		if init[0]:
			initSqliteDB(con)

		return con

	elif db_type == 'mysql':
		pass
#****************************************
#****************************************


class DeejaydFile:
	root_path =  DeejaydConfig().get("mediadb","music_directory")

	def __init__(self,cur,dir):
		self.cur = cur
		self.dir = dir

	def insert(self,f):
		try:
			# Test to see if it is a correct encoding name
			# TODO : find a better test
			f.decode()
			query = "INSERT INTO library(type,dir,filename,title,artist,album)VALUES\
				('file',?,?,?,?,?)"
			self.cur.execute(query, (self.dir,f,'','',''))
		except:
			print "Impossible to add file %s : %s" % (self.dir,f)

	def update(self,f):
		#query = "UPDATE library SET title='%s', album='%s' WHERE dir='%s' AND filename='%s'"\
		#		% ()
		#self.cur.execute(query)
		pass

	def remove(self,f):
		try:
			self.cur.execute("DELETE FROM library WHERE filename = ? AND dir = ?", (f,self.dir))
		except:
			print "Impossible to delete the file %s : %s from the database" % (self.dir, f)

	# Private functions
	def __getFileTags(self,f):
		realDir = os.path.join(self.__class__.root_path,self.dir)
		(filename,extension) = os.path.splitext(f)
		ext = extension.lower()

		fileTags = {}
		if ext == ".mp3":
			pass

		elif ext == ".ogg":
			pass


class DeejaydDir:
	root_path =  DeejaydConfig().get("mediadb","music_directory")

	def __init__(self,cur):
		self.cur = cur

	def update(self,dir,lastUpdateTime):
		realDir = os.path.join(self.__class__.root_path,dir)
		dbRecord = self.__get(dir)

		# First we update the list of directory
		directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
				if os.path.isdir(os.path.join(realDir,d))]
		for d in [di for (di,t) in dbRecord if t == 'directory']:
			if os.path.isdir(os.path.join(realDir,d)):
				if d in directories:
					directories.remove(d)
			else:
				# directory do not exist, we erase it
				self.cur.execute("DELETE FROM library WHERE filename = ? AND dir = ?", (d,dir))
		# Add new diretory
		for d in directories:
			try:
				# Test to see if it is a correct encoding name
				# TODO : find a better test
				d.decode()
				self.cur.execute("INSERT INTO library(dir,filename,type)VALUES(?,?,'directory')" \
						, (dir,d))
			except:
				print "Impossible to add directory %s" % (d,)

		# Now we update the list of files if necessary
		if int(os.stat(realDir).st_mtime) >= lastUpdateTime:
			files = [ f for f in os.listdir(realDir) if os.path.isfile(os.path.join(realDir,f))]
			djFile = DeejaydFile(self.cur,dir)
			for f in [fi for (fi,t) in dbRecord if t == 'file']:
				if os.path.isfile(os.path.join(realDir,f)):
					djFile.update(f)
					if f in files:
						files.remove(f)
				else:
					djFile.remove(f)
			# Insert new files
			for f in files:
				djFile.insert(f)

		# Finally we update subdirectories
		directories = [ os.path.join(dir,d) for d in os.listdir(realDir) \
				if os.path.isdir(os.path.join(realDir,d))]
		for d in directories:
			self.update(d,lastUpdateTime)

	# Private functions
	def __get(self,dir):
		result = []
		try:
			self.cur.execute("SELECT filename,type FROM library WHERE dir = ?", (dir,))
			result = self.cur.fetchall()
		except:
			print "Impossible to get directory '%s' elements in the database" % (dir,)

		return result


class DeejaydDB:
	"""deejaydDB

	Class to manage the media database
	"""
	root_path =  DeejaydConfig().get("mediadb","music_directory")

	def __init__(self):
		self.con = createDB()
		self.cur = self.con.cursor()

	def getDir(self,dir):
		self.cur.execute("SELECT filename,type FROM library WHERE dir = ?",(dir,))
		print  self.cur.fetchall()

	def update(self,dir):
		self.__getUpdateTime()
		DeejaydDir(self.cur).update(dir,self.lastUpdateTime)
		self.__setUpdateTime()

		# record the change in the database
		self.con.commit()

	def close(self):
		self.cur.close()
		self.con.close()

	# Private functions
	def __getUpdateTime(self):
		self.cur.execute("SELECT value FROM stat WHERE name = 'last_updatedb_time'")
		(self.lastUpdateTime,) = self.cur.fetchone()

	def __setUpdateTime(self):
		t = time.time()
		self.cur.execute("UPDATE stat SET value = %d WHERE name = 'last_updatedb_time'" % (int(t),))
		self.con.commit()


# for test only
if __name__ == "__main__":
	djDB = DeejaydDB()

	t = int(time.time())
	djDB.update("")
	print int(time.time()) - t

	#djDB.update("Rock_Internationnal/Coldplay")
	#djDB.update("Rock_Internationnal")
	#djDB.getDir("Rock_Internationnal/Coldplay/X_and_Y")
	#djDB.getDir("Rock_Francais")

	djDB.close()

# vim: ts=4 sw=4 expandtab
