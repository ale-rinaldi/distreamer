import socket,urlparse

class ShoutcastClientFragmentsManager:
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
			self.logger.log('Created fragment '+str(self.fragcounter),'ShoutcastClient',3)
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
			self.logger.log("Deleted fragment "+str(todelete),'ShoutcastClient',3)
		self.store.setIcyList(icylist)
	def setIcyPos(self):
		icylist=self.store.getIcyList()
		if not icylist.has_key(self.fragcounter):
			icylist[self.fragcounter]=[]
		icylist[self.fragcounter].append(self.poscounter)
		self.store.setIcyList(icylist)

class ShoutcastClient():

	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False
		self.isclosing=False
		self.socket=None

	def _ShoutcastConnect(self,url,headers,timeout):
		u=urlparse.urlparse(url)
		if u.path=='':
			path='/'
		else:
			path=u.path
		server=u.netloc.split(':')[0]
		port=-1
		if len(u.netloc.split(':'))>1:
			port=int(u.netloc.split(':')[1])
		if port<0:
			port=80
		self.logger.log('Connecting to '+server+' on port '+str(port),'ShoutcastClient',4)
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setblocking(1)
		s.connect((server, port))
		self.logger.log('Connected','ShoutcastClient',4)
		f=s.makefile()
		s.settimeout(timeout)
		s.sendall('GET '+path+ ' HTTP/1.1\r\n')
		s.sendall('Host: '+u.netloc+'\r\n')
		s.sendall('Accept-Encoding: identity\r\n')
		for key in headers.keys():
			s.send(key+': '+headers[key]+'\r\n')
		s.sendall('\r\n')
		lstatus=f.readline()
		if lstatus.split(' ')[1]!='200':
			s.close()
			raise ValueError('Invalid status from server')
		headerscount=0
		headers=self.store.getIcyHeaders()
		while True:
			headerscount+=1
			if headerscount>100:
				s.close()
				raise ValueError('Too many headers received')
			lheader=f.readline(65537)
			if len(lheader)>65536:
				s.close()
				raise ValueError('Header too long')
			header=lheader.strip()
			if header=='':
				break
			self.logger.log("Received header - "+header,'ShoutcastClient',4)
			seppos=header.find(':')
			k=header[:seppos]
			v=header[seppos+1:]
			if k.lower()=='icy-metaint':
				self.store.setIcyInt(int(v))
			elif k.lower()[:4]=='icy-' or k.lower()=='content-type':
				headers[k]=v
		if self.store.getIcyInt()<0:
			self.store.setIcyInt(0)
		self.store.setIcyHeaders(headers)
		self.socket=s
		self.socketfile=f
		return f
		
	def getDefaultConfig(self):
		return {
			'streamurl': '',
			'fragmentsnumber': 5,
			'fragmentsize': 81920,
			'getmetadata': True,
			'httptimeout': 5,
		}
	
	def setConfig(self,config):
		self.config=config
		self.config_set=True

	def run(self):
		if not self.config_set:
			self.logger.log('Config not set','ShoutcastClient',1)
			return None

		if self.config['streamurl']=='':
			self.logger.log('Stream URL not defined','ShoutcastClient',1)
			return None

		self.logger.log('Started','ShoutcastClient',2)
		self.store.incrementSourceGen()
		self.store.reset()
		
		fmanager=ShoutcastClientFragmentsManager(self.store,self.logger,self.config)

		self.logger.log('Stream URL: '+self.config['streamurl'],'ShoutcastClient',3)
		
		if self.config['getmetadata']:
			self.logger.log("Connecting to stream requesting metadata",'ShoutcastClient',3)
			#stream=urllib2.urlopen(urllib2.Request(self.config['streamurl'],headers={'Icy-MetaData':'1','User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			stream=self._ShoutcastConnect(self.config['streamurl'],{'Icy-MetaData':'1','User-Agent':'DiStreamer'},self.config['httptimeout'])
		else:
			stream=self._ShoutcastConnect(self.config['streamurl'],{'User-Agent':'DiStreamer'},self.config['httptimeout'])
		self.logger.log("Connected to stream",'ShoutcastClient',3)
		
		icyint=self.store.getIcyInt()
		if icyint>0:
			toread=icyint
		else:
			toread=self.config['fragmentsize']
		while not self.isclosing:
			try:
				buf=stream.read(toread)
			except:
				if self.isclosing:
					return None
				pass
			if len(buf)!=toread:
				self.logger.log('Incomplete read of block','ShoutcastClient',2)
				return None
			fmanager.push(buf)
			buf=''
			if icyint>0:
				ordicylen=stream.read(1)
				fmanager.push(ordicylen)
				icylen=ord(ordicylen)*16
				if icylen>0:
					try:
						title=stream.read(icylen)
					except:
						if self.isclosing:
							return None
					if len(title)!=icylen:
						self.logger.log('Incomplete read of title','ShoutcastClient',2)
						return None
					self.store.setIcyTitle(title)
					fmanager.push(title)
				fmanager.setIcyPos()
		self.logger.log('ShoutcastClient terminated normally','ShoutcastClient',2)
		
	def close(self):
		self.isclosing=True
		self.logger.log('ShoutcastClient is terminating, this could need some time','ShoutcastClient',2)
		if self.socket:
			self.socket.close()
