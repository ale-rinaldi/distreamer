import BaseHTTPServer, json
from SocketServer import ThreadingMixIn

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

class TitleQueue:
	def __init__(self):
		self.queue=[]
	def addtitle(self,title):
		self.queue.add(title)
	def gettitle(self):
		return self.queue.pop(0)

def makeServerHandler(store,logger,config):
	class ShoutcastSourceServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		def __init__(s, *args, **kwargs):
			s.store=store
			s.logger=logger
			s.config=config
			super(ShoutcastSourceServerHandler, s).__init__(*args, **kwargs)
		def do_HEAD(s):
			frag=s.path[1:]
			seppos=frag.find('/')
			if seppos<0:
				path=frag
				password=''
			else:
				path=frag[:seppos]
				password=header[seppos+1:]
			if s.config['password']!='' and s.config['password']!=password:
				s.send_response(403)
				s.send_header("Server","DiStreamer")
			if(s.path=='/list'):
				s.send_response(200)
				s.send_header("Server","DiStreamer")
				s.send_header("Content-Type", "text/plain")
			else:
				key=int(s.path[1:])
				if s.store.getFragments().has_key(key):
					s.send_response(200)
					s.send_header("Server","DiStreamer")
				else:
					s.send_response(404)
					s.send_header("Server","DiStreamer")

		def do_GET(s):
			frag=s.path[1:]
			seppos=frag.find('/')
			if seppos<0:
				path=frag
				password=''
			else:
				path=frag[:seppos]
				password=frag[seppos+1:]
			if s.config['password']!='' and s.config['password']!=password:
				s.send_response(403)
				s.send_header("Server","DiStreamer")
				s.end_headers()
				s.wfile.write("Invalid password")
			elif path=='list':
				s.send_response(200)
				s.send_header("Server", "DiStreamer")
				s.send_header("Content-Type", "text/plain")
				flist=s.store.getFragments().keys()
				flist.sort()
				tosend=json.dumps({
					'fragmentslist': flist,
					'icyint': s.store.getIcyInt(),
					'icylist': s.store.getIcyList(),
					'icyheaders': s.store.getIcyHeaders(),
					'icytitle': s.store.getIcyTitle().encode('base64'),
					'sourcegen': s.store.getSourceGen()
				})
				s.logger.log('List: '+tosend,'ShoutcastSourceServer',4)
				s.send_header("Content-Length", str(len(tosend)))
				s.end_headers()
				s.wfile.write(tosend)
			else:
				key=-1
				try:
					key=int(path)
				except:
					pass
				if key>=0 and s.store.getFragments().has_key(key):
					fragment=s.store.getFragments()[key]
					s.send_response(200)
					s.send_header("Server", "DiStreamer")
					s.send_header("Content-Length", str(len(fragment)))
					s.end_headers()
					s.wfile.write(fragment)
				else:
					s.send_response(404)
					s.send_header("Server", "DiStreamer")
					s.end_headers()
					s.wfile.write("Invalid fragment "+path)
		def log_message(self, format, *args):
			return
	return ShoutcastSourceServerHandler

class ShoutcastSourceServer:

	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False

	def getDefaultConfig(self):
		return {
			'hostname': '0.0.0.0',
			'port': '8080',
			'password': 'distreamer'
		}
		
	def setConfig(self,config):
		self.config=config
		self.config_set=True
	
	def run(self):
		if not self.config_set:
			raise ValueError('Config not set')
		handler=makeServerHandler(self.store,self.logger,self.config)
		self.httpd = ThreadingSimpleServer((self.config['hostname'], int(self.config['port'])), handler)
		self.logger.log('Started','ShoutcastSourceServer',2)
		try:
			self.httpd.serve_forever()
		except:
			pass
		self.logger.log('Server terminated','ShoutcastSourceServer',2)

	def close(self):
		self.logger.log('Exiting normally','ShoutcastSourceServer',2)
		self.httpd.server_close()
