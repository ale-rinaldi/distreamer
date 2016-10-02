import BaseHTTPServer,json
from SocketServer import ThreadingMixIn

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

def makeServerHandler(store,logger,config):
	class DiStreamerRevServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		def __init__(s, *args, **kwargs):
			s.store=store
			s.logger=logger
			s.config=config
			super(DiStreamerRevServerHandler, s).__init__(*args, **kwargs)
		
		def keysToInt(s,dictionary):
			''' THANKS!!! http://stackoverflow.com/questions/1254454/fastest-way-to-convert-a-dicts-keys-values-from-unicode-to-str '''
			if not isinstance(dictionary, dict):
				return dictionary
			return dict((int(k), s.keysToInt(v)) for k, v in dictionary.items())
		
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
			elif path in ['list','icyint','icylist','icyheaders','icytitle']:
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
				s.send_header("Content-Length", str(len(tosend)))
				s.end_headers()
				s.wfile.write(tosend)
			else:
				s.send_response(404)
				s.send_header("Server", "DiStreamer")
				s.end_headers()
				s.wfile.write("Invalid request: "+path)

		def do_POST(s):			
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
			else:
				content_len = int(s.headers.getheader('content-length', 0))
				post_body = s.rfile.read(content_len)
				if len(post_body)!=content_len:
					s.send_response(500)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('Incomplete read')
				elif path=='list':
					infolist=json.loads(post_body)
					s.store.setIcyInt(infolist['icyint'])
					s.store.setIcyList(s.keysToInt(infolist['icylist']))
					s.store.setIcyHeaders(infolist['icyheaders'])
					s.store.setSourceGen(infolist['sourcegen'])
					s.store.setIcyTitle(infolist['icytitle'].decode('base64'))
					list=infolist['fragmentslist']
					fragments=s.store.getFragments()
					for localfragn in s.store.getFragments().keys():
						if(localfragn not in list):
							del fragments[localfragn]
							s.logger.log('Deleted fragment '+str(localfragn),'DiStreamerRevServer',3)
					s.store.setFragments(fragments)
					s.send_response(200)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('OK')
				else:
					x=-1
					try:
						x=int(path)
					except:
						pass
					if x>=0:
						fragments=s.store.getFragments()
						fragments[x]=post_body
						s.store.setFragments(fragments)
						s.logger.log('Received fragment '+str(x),'DiStreamerRevServer',3)
						s.send_response(200)
						s.send_header("Server","DiStreamer")
						s.end_headers()
						s.wfile.write('OK')
					else:
						s.send_response(404)
						s.send_header("Server","DiStreamer")
						s.end_headers()
						s.wfile.write('Invalid request: '+path)
		
		def log_message(self, format, *args):
			return
	return DiStreamerRevServerHandler

class DiStreamerRevServer:
	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False

	def getDefaultConfig(self):
		return {
			'hostname': '0.0.0.0',
			'port': 5080,
			'password': ''
		}
		
	def setConfig(self,config):
		self.config=config
		self.config_set=True
	
	def run(self):
		if not self.config_set:
			raise ValueError('Config not set')
		handler=makeServerHandler(self.store,self.logger,self.config)
		self.httpd = ThreadingSimpleServer((self.config['hostname'], self.config['port']), handler)
		self.logger.log('Started','DiStreamerRevServer',2)
		try:
			self.httpd.serve_forever()
		except:
			pass
		self.logger.log('Server terminated','DiStreamerRevServer',2)

	def close(self):
		self.logger.log('Exiting normally','DiStreamerRevServer',2)
		self.httpd.server_close()
