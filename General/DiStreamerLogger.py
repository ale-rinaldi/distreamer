import time

class DiStreamerLogger:
	def __init__(self,config):
		self.outputlevel=int(config['outputlevel'])
		self.logfile=config['logfile']
		self.loglevel=int(config['loglevel'])
	
	def log(self,string,origin,level):
		fmtstring=str(time.asctime())+": ["+origin+"] "+string
		if level<=self.outputlevel:
			print fmtstring
		if level<=self.loglevel:
			with open(self.logfile, 'a') as file:
				file.write(fmtstring+'\r\n')
