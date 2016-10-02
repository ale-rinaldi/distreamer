import BaseHTTPServer, json, threading, urlparse, SocketServer

class SourceServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass

class MetadataServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

class SourceConnectedManager:
	def __init__(self):
		self.connected=False
	def set(self,val)
		if type(val) is bool:
			self.connected=val
	def get(self):
		return self.connected
	
class ShoutcastSourceServerTitleQueue:
	def __init__(self):
		self.reset()
	def add(self,title):
		self.queue.add(title)
	def get(self):
		if len(self.queue)>0:
			return self.queue.pop(0)
		else:
			return ''
	def reset(self):
		self.queue=[]

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

def makeMetadataServerHandler(store,logger,config,titlequeue,sourceconn):
	class ShoutcastSourceMetadataServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		def do_HEAD(s):
			path=urlparse.urlparse('http://distreamer'+s.path).path
			if path='/admin.cgi' and sourceconn.get():
				s.send_response(200)
				s.send_header('Server', 'DiStreamer')
			elif path='/stats':
				s.send_response(200)
				s.send_header('Server', 'DiStreamer')
				s.send_header('Content-Type', 'text/plain')
			else:
				s.send_response(404)
				s.send_header('Server', 'DiStreamer')

		def formatTitle(song):
			formtitle='StreamTitle=\''+song+'\';'
			if len(formtitle)>4080:
				raise ValueError('Title too long')
			while len(formtitle)%16!=0:
				formtitle+='\0'
			return formtitle

		def do_GET(s):
			path=urlparse.urlparse('http://distreamer'+s.path).path
			if path='/admin.cgi' and sourceconn.get():
				s.send_response(200)
				s.send_header('Server', 'DiStreamer')
				s.end_headers()
				if config['icyint']>0:
					params=urlparse.parse_qs(urlparse.urlparse('http://distreamer'+s.path).query)
					if params['password']==s.config['password']:
						titlequeue.add(s.formatTitle(params['song']))
				s.close()
			elif path='/stats':
				s.send_response(200)
				s.send_header('Server','DiStreamer')
				s.send_header('Content-Type','text/plain')
				s.end_headers
				s.wfile.write(json.dumps({'sourceConnected':sourceconn.get()}))
			else:
				s.send_response(404)
				s.send_header("Server", "DiStreamer")

		def log_message(self, format, *args):
			return
	return ShoutcastSourceMetadataServerHandler
	
def makeSourceServerHandler(store,logger,config,sourceconn,titlequeue,lisclosing):
	class ShoutcastSourceServerHandler(SocketServer.StreamRequestHandler,object):
		timeout=config['timeout']
		def handle(self):
			self.haderror=True ''' Set to false after all the verifications '''
			password=self.rfile.readline()
			if password!=config['password']:
				self.wfile.write('invalid password\r\n')
				return None
			self.wfile.write('OK2\r\nicy-caps:11\r\n')
			headers={}
			headerscount=0
			while True:
				headerscount+=1
				if headerscount>100:
					s.close()
					raise ValueError('Too many headers received')
				lheader=self.rfile.readline(65537)
				''' The real Shoutcast Server closes connection with the source after it receives the first header if another source is already connected, so let's keep this strange behaviour '''
				if sourceconn.get():
					s.close()
					return None
				if len(lheader)>65536:
					s.close()
					raise ValueError('Header too long')
				header=lheader.strip()
				if header=='':
					break
				self.logger.log("Received header - "+header,'ShoutcastSourceServer',4)
				seppos=header.find(':')
				k=header[:seppos]
				v=header[seppos+1:]
				if k.lower()=='icy-metaint':
					self.store.setIcyInt(int(v))
				elif k.lower()[:4]=='icy-' or k.lower()=='content-type':
					headers[k]=v
			if headerscount==0:
				s.close()
				raise ValueError('No headers received')
			sourceconn.set(True)
			self.haderror=False
			store.reset()
			store.incrementSourceGen()
			store.setIcyHeaders(headers)
			store.setIcyInt(config['icyint'])
			fmanager=ShoutcastSourceServerFragmentsManager()
			icyint=self.config['icyint']
			if icyint>0:
				toread=icyint
			else:
				toread=self.config['fragmentsize']
			while not lisclosing[0]:
				try:
					buf=self.rfile.read(toread)
				except:
					if lisclosing[0]:
						return None
				if len(buf)!=toread:
					raise ValueError("Incomplete read of block")
				fmanager.push(buf)
				if icyint>0:
					title=titlequeue.get()
					if len(title)>0:
						store.setIcyTitle(title)
					chridx=len(title)/16
					fmanager.push(chr(chridx))
					fmanager.push(title)
		def finish(self):
			if not self.haderror:
				titlequeue.reset()
				sourceconn.set(False)
	return ShoutcastSourceServerHandler

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
		sourceconn=SourceConnectedManager()
		titlequeue=ShoutcastSourceServerTitleQueue()
		metadatahandler=makeMetadataServerHandler(self.store,self.logger,self.config,sourceconn,titlequeue)
		metadataserver=MetadataServer((self.config['hostname'], int(self.config['port'])), metadatahandler)
		self.metadatathread=MetadataServerThread(metadataserver,self.logger,self.lisclosing)
		self.logger.log('Metadata server initialized','ShoutcastSourceServer',2)
		sourcehandler=makeSourceServerHandler(self.store,self.logger,self.config,sourceconn,titlequeue,self.lisclosing)
		self.sourceserver=SourceServer((self.config['hostname'],int(self.config['port'])+1), sourcehandler)
		self.logger.log('Source server initialized','ShoutcastSourceServer',2)
		self.metadatathread.start()
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
