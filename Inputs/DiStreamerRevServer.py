import BaseHTTPServer
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
			elif s.path=='/list' or s.path='/icyint' or s.path='/icylist' or s.path='/icyheaders' or s.path='/icytitle':
				s.send_response(200)
				s.send_header("Server","DiStreamer")
			else:
				s.send_response(404)
				s.send_header("Server","DiStreamer")
				

		def do_GET(s):
			icylist=s.store.getIcyList()
			icyint=s.store.getIcyInt()
			icyheaders=s.store.getIcyHeaders()
			icytitle=s.store.getIcyTitle()
			fragments=s.store.getFragments()
			reconnect=s.store.getSourceGen()
			
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
				flist=fragments.keys()
				flist.sort()
				tosend=','.join(map(str,flist))
				tosend=tosend+'|'+str(icyint)+'|'
				tmplist=[]
				for frag in icylist:
					tmplist.append(str(frag)+':'+'-'.join(map(str,icylist[frag])))
				tosend=tosend+','.join(tmplist)+'|'
				tmplist=[]
				for metaidx in icyheaders:
					tmplist.append(metaidx+':'+icyheaders[metaidx])
				tosend=tosend+','.join(tmplist)+'|'+str(reconnect)+'|'
				tosend=tosend+icytitle
				s.send_header("Content-Length", str(len(tosend)))
				s.end_headers()
				s.wfile.write(tosend)
			else:
				s.send_response(404)
				s.send_header("Server", "DiStreamer")
				s.end_headers()
				s.wfile.write("Invalid request")

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
				content_len = int(self.headers.getheader('content-length', 0))
				post_body = self.rfile.read()
				if len(post_body)!=content_len:
					s.send_response(500)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('Incomplete read')
				elif path='icyint':
					s.store.setIcyInt(int(post_body))
					s.send_response(200)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('OK')
				elif path='icytitle':
					s.store.setIcyTitle(post_body)
					s.send_response(200)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('OK')
				elif path='icytitle':
					s.store.setIcyTitle(post_body)
					s.send_response(200)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('OK')
				elif path='icylist':
					icylist={}
					sicylist=post_body.split(',')
					for icyfrag in sicylist:
						aicylist=icyfrag.split(':')
						if aicylist[0]!='':
							icyidx=int(aicylist[0])
							icylist[icyidx]=map(int,aicylist[1].split('-'))
					s.store.setIcyList(icylist)
					s.send_response(200)
					s.send_header("Server","DiStreamer")
					s.end_headers()
					s.wfile.write('OK')
				elif path='icyheaders':
					aicyheaders=post_body.split(',')
					tmplist={}
					for header in aicyheaders:
						seppos=header.find(':')
						key=header[:seppos]
						val=header[seppos+1:]
						if key!='':
							tmplist[key]=val
					s.store.setIcyHeaders(tmplist)
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
						s.send_response(200)
						s.send_header("Server","DiStreamer")
						s.end_headers()
						s.wfile.write('OK')
					else:
						s.send_response(500)
						s.send_header("Server","DiStreamer")
						s.end_headers()
						s.wfile.write('Invalid request')
		
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
			'port': '5080',
			'password': ''
		}
		
	def setConfig(self,config):
		self.config=config
		self.config_set=True
	
	def run(self):
		if not self.config_set:
			raise ValueError('Config not set')
		handler=makeServerHandler(self.store,self.logger,self.config)
		self.httpd = ThreadingSimpleServer((self.config['hostname'], int(self.config['port'])), handler)
		self.logger.log('Started','DiStreamerRevServer',2)
		try:
			self.httpd.serve_forever()
		except:
			pass
		self.logger.log('Server terminated','DiStreamerRevServer',2)

	def close(self):
		self.logger.log('Exiting normally','DiStreamerRevServer',2)
		self.httpd.server_close()
