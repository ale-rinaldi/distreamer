import BaseHTTPServer
from SocketServer import ThreadingMixIn

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

def makeServerHandler(store,logger):
	class distreamerServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		def __init__(s, *args, **kwargs):
			s.store=store
			s.logger=logger
			super(distreamerServerHandler, s).__init__(*args, **kwargs)
		def do_HEAD(s):
			try:
				if(s.path=='/list'):
					s.send_response(200)
					s.send_header("Content-Type", "text/plain")
				else:
					key=int(s.path[1:])
					if s.store.getFragments().has_key(key):
						s.send_response(200)
					else:
						s.send_response(404)
			except:
				s.logger.log('HEAD error','DiStreamerServer',3)
				pass

		def do_GET(s):
			icylist=s.store.getIcyList()
			icyint=s.store.getIcyInt()
			icyheaders=s.store.getIcyHeaders()
			icytitle=s.store.getIcyTitle()
			fragments=s.store.getFragments()
			reconnect=s.store.getSourceGen()
			try:
				if s.path=='/list':
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
					key=int(s.path[1:])
					if fragments.has_key(key):
						s.send_response(200)
						s.send_header("Server", "DiStreamer")
						s.send_header("Content-Length", str(len(fragments[key])))
						s.end_headers()
						s.wfile.write(fragments[key])
					else:
						s.send_response(404)
						s.send_header("Server", "DiStreamer")
						s.end_headers()
						s.wfile.write("Invalid fragment "+str(key))
			except:
				s.logger.log('GET error','DiStreamerServer',3)
				pass
		def log_message(self, format, *args):
			return
	return distreamerServerHandler

class DiStreamerServer:

	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False

	def getDefaultConfig(self):
		return {
			'hostname': '0.0.0.0',
			'port': '7080',
		}
		
	def setConfig(self,config):
		self.config=config
		self.config_set=True
	
	def run(self):
		if not self.config_set:
			raise ValueError('Config not set')
		handler=makeServerHandler(self.store,self.logger)
		self.httpd = ThreadingSimpleServer((self.config['hostname'], int(self.config['port'])), handler)
		self.logger.log('Started','DiStreamerServer',2)
		try:
			self.httpd.serve_forever()
		except:
			pass
		self.logger.log('Server terminated','DiStreamerServer',2)

	def close(self):
		self.logger.log('Exiting normally','DiStreamerServer',2)
		self.httpd.server_close()
