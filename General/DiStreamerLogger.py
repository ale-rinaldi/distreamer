import time,os

class DiStreamerLogger:
	def __init__(self,config):
		self.outputlevel=int(config['outputlevel'])
		self.logfile=config['logfile']
		self.loglevel=int(config['loglevel'])
		self.logerror=False
		self.islogging=False
	
	def log(self,string,origin,level):
		while self.islogging:
			time.sleep(0.05)
		self.islogging=True
		fmtstring=str(time.asctime())+": ["+origin+"] "+string
		if level<=self.outputlevel:
			print fmtstring
		if level<=self.loglevel and not self.logerror:
			try:
				file=open(self.logfile, 'a')
				file.write(fmtstring+'\r\n')
				file.close()
			except:
				print "!!!WARNING!!! Cannot write to log file: "+self.logfile
				self.logerror=True
				pass
		self.islogging=False
