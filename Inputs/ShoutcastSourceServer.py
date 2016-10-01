import BaseHTTPServer, json, threading, urlparse
from SocketServer import ThreadingMixIn,TCPServer

class SourceServer(ThreadingMixIn, TCPServer):
	pass

class MetadataServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

class ShoutcastSourceServerTitleQueue:
	def __init__(self):
		self.queue=[]
	def addtitle(self,title):
		self.queue.add(title)
	def gettitle(self):
		return self.queue.pop(0)

class ShoutcastSourceServerFragmentsManager:
	def __init__(self,store,logger,config):
		self.store=store
		self.logger=logger
		self.config=config
		self.currentfrag=''
		fragkeys=store.getFragments().keys()
		if len(fragkeys)>0:
			self.fragcounter=max(fragkeys)+1
		else:
			self.fragcounter=1
		self.poscounter=0
	def push(self,piece):
		while len(piece)>=self.config['fragmentsize']-self.poscounter:
			last=self.config['fragmentsize']-self.poscounter
			self.currentfrag=self.currentfrag+piece[:last]
			fragments=self.store.getFragments()
			fragments[self.fragcounter]=self.currentfrag
			self.logger.log('Created fragment '+str(self.fragcounter),'ShoutcastSourceServer',3)
			self.deleteOldFragments(fragments)
			self.store.setFragments(fragments)
			self.currentfrag=''
			self.fragcounter+=1
			self.poscounter=0
			piece=piece[last:]
		self.currentfrag=self.currentfrag+piece
		self.poscounter+=len(piece)
	def deleteOldFragments(self,fragments):
		icylist=self.store.getIcyList()
		while len(fragments)>self.config['fragmentsnumber']:
			todelete=min(fragments.keys())
			del fragments[todelete]
			if icylist.has_key(todelete):
				del icylist[todelete]
			self.logger.log("Deleted fragment "+str(todelete),'ShoutcastSourceServer',3)
		self.store.setIcyList(icylist)
	def setIcyPos(self):
		icylist=self.store.getIcyList()
		if not icylist.has_key(self.fragcounter):
			icylist[self.fragcounter]=[]
		icylist[self.fragcounter].append(self.poscounter)
		self.store.setIcyList(icylist)

def makeMetadataServerHandler(store,logger,config,titlequeue):
	class ShoutcastSourceMetadataServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		def __init__(s, *args, **kwargs):
			s.store=store
			s.logger=logger
			s.config=config
			s.titlequeue=titlequeue
			super(ShoutcastSourceServerHandler, s).__init__(*args, **kwargs)
		def do_HEAD(s):
			path=urlparse.urlparse('http://distreamer'+s.path).path
			if path='/admin.cgi':
				s.send_response(200)
				s.send_header("Server", "DiStreamer")
				s.send_header("Content-Type", "text/plain")
			else:
				s.send_response(404)
				s.send_header("Server", "DiStreamer")

		def formatTitle(song):
			''' TODO '''
			return song

		def do_GET(s):
			path=urlparse.urlparse('http://distreamer'+s.path).path
			if path='/admin.cgi':
				s.send_response(200)
				s.send_header("Server", "DiStreamer")
				s.send_header("Content-Type", "text/plain")
				s.end_headers()
				params=urlparse.parse_qs(urlparse.urlparse('http://distreamer'+s.path).query)
				s.store.setIcyTitle(s.formatTitle(params['song']))
			else:
				s.send_response(404)
				s.send_header("Server", "DiStreamer")

		def log_message(self, format, *args):
			return
	return ShoutcastSourceMetadataServerHandler

class MetadataServerThread(threading.Thread):
	def __init__(self,metadataserver,logger,lisclosing):
		threading.Thread.__init__(self)
		self.metadataserver=metadataserver
		self.logger=logger
		self.lisclosing=lisclosing
	def run(self):
		try:
			self.metadataserver.serve_forever()
		except:
			if self.lisclosing[0]:
				pass
		self.logger.log('Metadata server terminated','ShoutcastSourceServer',2)
	def close(self):
		self.logger.log('Closing metadata server','ShoutcastSourceServer',2)
		self.metadataserver.close()

class ShoutcastSourceServer:

	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False
		self.lisclosing=[False]
		self.sourceserver=None

	def getDefaultConfig(self):
		return {
			'hostname': '0.0.0.0',
			'port': '8080',
			'password': 'distreamer',
			'fragmentsnumber': 5,
			'fragmentsize': 81920,
			'getmetadata': True,
			'httptimeout': 5,
			'icyint': 8192
		}

	def setConfig(self,config):
		self.config=config
		self.config_set=True

	def run(self):
		if not self.config_set:
			raise ValueError('Config not set')
		metadatahandler=makeMetadataServerHandler(self.store,self.logger,self.config)
		metadataserver=MetadataServer((self.config['hostname'], int(self.config['port'])), metadatahandler)
		self.logger.log('Metadata server initialized','ShoutcastSourceServer',2)
		self.metadatathread=MetadataServerThread(metadataserver,self.logger,self.lisclosing)
		sourcehandler=makeSourceServerHandler(self.store,self.logger,self.config)
		self.sourceserver=SourceServer((self.config['hostname'],int(self.config['port'])+1), sourcehandler)
		try:
			self.sourceserver.serve_forever()
		except:
			if self.lisclosing[0]:
				pass
		self.logger.log('Source server terminated','ShoutcastSourceServer',2)

	def close(self):
		self.logger.log('Closing source server','ShoutcastSourceServer',2)
		self.lisclosing[0]=True
		self.metadatathread.close()
		self.sourceserver.server_close()
