import BaseHTTPServer
import time,json
from SocketServer import ThreadingMixIn

class ShoutcastServerStatsManager():
	def __init__(self):
		self.counter=0
	def add(self):
		self.counter+=1
	def rem(self):
		self.counter-=1
	def get(self):
		return self.counter

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

def makeServerHandler(store,logger,config,lisclosing,statmgr):
	class shoutcastServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
		statpages=['/stats','/favicon.ico']
		def do_HEAD(s):
			s.added=False
			s.send_response(200)
			s.send_header("Server", "DiStreamer")
			icyheaders=store.getIcyHeaders()
			for header in icyheaders:
				s.send_header(header,icyheaders[header])
			if(store.getIcyInt()>0):
				s.send_header("icy-metaint", str(store.getIcyInt()))
				
		def do_GET(s):
			s.added=False
			fragments=store.getFragments()
			if s.path in s.statpages:
				s.send_response(200)
				s.send_header('content-type','application/json')
				s.end_headers()
				s.wfile.write(json.dumps({
					'connectedClients':statmgr.get(),
					'fragmentsList':fragments.keys()
					}))
				return None
			if len(fragments)<config['minfragments']:
				s.send_response(404)
				s.send_header('Server','DiStreamer')
				s.end_headers()
				s.wfile.write('No stream yet')
				return None
			s.send_response(200)
			s.send_header('Server','DiStreamer')
			statmgr.add()
			s.added=True
			icyheaders=store.getIcyHeaders()
			for header in icyheaders:
				s.send_header(header,icyheaders[header])
			if(store.getIcyInt()>0):
				s.send_header("icy-metaint", str(store.getIcyInt()))
			s.end_headers()
			reconnect=store.getSourceGen()
			if reconnect<=0:
				return None
			sentlist=[]
			locreconnect=reconnect
			icytitle=store.getIcyTitle()
			icyint=store.getIcyInt()
			firstsent=False
			if icyint>0:
				if icytitle!='':
					s.wfile.write(''.join(chr(255) for i in xrange(icyint)))
					chridx=len(icytitle)/16
					s.wfile.write(chr(chridx))
					s.wfile.write(icytitle)
				while not firstsent:
					if len(icylist.keys()==0)
						continue
					reconnect=store.getSourceGen()
					if locreconnect!=reconnect or reconnect<=0:
						logger.log('Local source gen: '+str(locreconnect)+', source gen: '+str(reconnect)+'. Closing stream to client.','ShoutcastServer',2)
						return None
					locallist=fragments.keys()
					locallist.sort()
					icylist=store.getIcyList()
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
						time.sleep(0.5)
						if lisclosing[0]:
							break
			else:
				lastsent=min(fragments.keys())-1
			while not lisclosing[0]:
				reconnect=store.getSourceGen()
				if locreconnect!=reconnect or reconnect<=0:
					logger.log('Local source gen: '+str(locreconnect)+', source gen: '+str(reconnect)+'. Closing stream to client.','ShoutcastServer',2)
					return None
				tosend=''
				locallist=fragments.keys()
				locallist.sort()
				for fragn in locallist:
					if fragn not in sentlist:
						if fragn!=lastsent+1:
							logger.log('Expected fragment: '+str(lastsent+1)+', first available: '+str(fragn)+'. Closing stream to client.','ShoutcastServer',2)
							return None
						lastsent=fragn
						tosend=tosend+fragments[fragn]
						sentlist.append(fragn)
				for sentn in sentlist:
					if not sentn in locallist:
						sentlist.remove(sentn)
						logger.log('Removed from sent list: '+str(sentn),'ShoutcastServer',4)
				s.wfile.write(tosend)
				time.sleep(1)
		def log_message(self, format, *args):
			return
		
		def finish(s):
			if s.added:
				statmgr.rem()

	return shoutcastServerHandler

class ShoutcastServer:
	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False

	def getDefaultConfig(self):
		return {
			'hostname': '0.0.0.0',
			'port': 8080,
			'minfragments': 5
		}
		
	def setConfig(self,config):
		self.config=config
		self.config_set=True
	
	def run(self):
		if not self.config_set:
			self.logger.log("Config not set",'ShoutcastServer',1)
			return None
		self.logger.log('Starting','ShoutcastServer',2)
		self.lisclosing=[False]
		statmgr=ShoutcastServerStatsManager()
		handler=makeServerHandler(self.store,self.logger,self.config,self.lisclosing,statmgr)
		self.httpd = ThreadingSimpleServer((self.config['hostname'], self.config['port']), handler)
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
