import BaseHTTPServer
import time
from SocketServer import ThreadingMixIn

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

def makeServerHandler(store,logger,lisclosing):
	class shoutcastServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		def __init__(s, *args, **kwargs):
			s.store=store
			s.logger=logger
			s.lisclosing=lisclosing
			super(shoutcastServerHandler, s).__init__(*args, **kwargs)
		def do_HEAD(s):
			s.send_response(200)
			s.send_header("Server", "DiStreamer")
			icyheaders=s.store.getIcyHeaders()
			for header in icyheaders:
				s.send_header(header,icyheaders[header])
			if(s.store.getIcyInt()>0):
				s.send_header("icy-metaint", str(s.store.getIcyInt()))
				
		def do_GET(s):
			s.send_response(200)
			s.send_header("Server", "DiStreamer")
			icyheaders=s.store.getIcyHeaders()
			for header in icyheaders:
				s.send_header(header,icyheaders[header])
			if(s.store.getIcyInt()>0):
				s.send_header("icy-metaint", str(s.store.getIcyInt()))
			s.end_headers()
			reconnect=s.store.getSourceGen()
			if reconnect<=0:
				return None
			sentlist=[]
			locreconnect=reconnect
			icytitle=s.store.getIcyTitle()
			icyint=s.store.getIcyInt()
			firstsent=False
			fragments=s.store.getFragments()
			if icyint>0:
				if icytitle!='':
					s.wfile.write(''.join(chr(255) for i in xrange(icyint)))
					chridx=len(icytitle)/16
					s.wfile.write(chr(chridx))
					s.wfile.write(icytitle)
				while not firstsent:
					reconnect=s.store.getSourceGen()
					if locreconnect!=reconnect or reconnect<=0:
						return None
					locallist=fragments.keys()
					locallist.sort()
					icylist=s.store.getIcyList()
					for fragn in locallist:
						if icylist.has_key(fragn):
							icyblkmin=min(icylist[fragn])
							lastsent=fragn
							s.wfile.write(fragments[fragn][icyblkmin:])
							sentlist.append(fragn)
							firstsent=True
							break
						else:
							sentlist.append(fragn)
						time.sleep(1)
						if s.lisclosing[0]:
							break
					fragments=s.store.getFragments()
			else:
				lastsent=min(fragments.keys())-1
			while not s.lisclosing[0]:
				fragments=s.store.getFragments()
				reconnect=s.store.getSourceGen()
				if locreconnect!=reconnect or reconnect<=0:
					return None
				tosend=''
				locallist=fragments.keys()
				locallist.sort()
				for fragn in locallist:
					if fragn not in sentlist:
						if fragn!=lastsent+1:
							return None
						lastsent=fragn
						tosend=tosend+fragments[fragn]
						sentlist.append(fragn)
				for sentn in sentlist:
					if not fragments.has_key(sentn):
						sentlist.remove(sentn)
						s.logger.log('Removed from sent list: '+str(sentn),'ShoutcastServer',3)
				s.wfile.write(tosend)
				time.sleep(1)
		def log_message(self, format, *args):
			return

	return shoutcastServerHandler

class ShoutcastServer:
	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False

	def getDefaultConfig(self):
		return {
			'hostname': '0.0.0.0',
			'port': '8080',
		}
		
	def setConfig(self,config):
		self.config=config
		self.config_set=True
	
	def run(self):
		if not self.config_set:
			raise ValueError('Config not set')
		self.logger.log('Starting','ShoutcastServer',2)
		self.lisclosing=[False]
		handler=makeServerHandler(self.store,self.logger,self.lisclosing)
		self.httpd = ThreadingSimpleServer((self.config['hostname'], int(self.config['port'])), handler)
		self.logger.log('Started','ShoutcastServer',2)
		try:
			self.httpd.serve_forever()
		except:
			pass
		self.logger.log('Server terminated','ShoutcastServer',2)

	def close(self):
		self.logger.log('Exiting normally','ShoutcastServer',2)
		self.httpd.server_close()
		self.lisclosing[0]=True
