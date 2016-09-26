import threading

class DiStreamerThread(threading.Thread): 
	def __init__(self, dsobject):
		threading.Thread.__init__(self)
		self.dsobject=dsobject
	
	def run(self):
		self.dsobject.run()
		
	def close(self):
		self.dsobject.close()
