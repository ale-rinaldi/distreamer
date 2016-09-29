import socket,urlparse

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
		s.send('GET '+path+ ' HTTP/1.1\r\n')
		s.send('Host: '+u.netloc+'\r\n')
		s.send('Accept-Encoding: identity\r\n')
		for key in headers.keys():
			s.send(key+': '+headers[key]+'\r\n')
		s.send('\r\n')
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
		self.logger.log('Started','ShoutcastClient',3)
		if not self.config_set:
			raise ValueError("Configuration not set")

		if self.config['streamurl']=='':
			raise ValueError("Stream URL not defined")

		self.store.incrementSourceGen()
		self.store.reset()
		
		counter=1
		icyread=0
		icynbstart=0
		icyreadfromblock=0
		icyreadingtitle=False
		icytemptitle=""
		
		fragments=self.store.getFragments()
		icylist=self.store.getIcyList()
		icyheaders=self.store.getIcyHeaders()
		
		self.logger.log('Stream URL: '+self.config['streamurl'],'ShoutcastClient',3)
		
		if self.config['getmetadata']:
			self.logger.log("Connecting to stream requesting metadata",'ShoutcastClient',3)
			#stream=urllib2.urlopen(urllib2.Request(self.config['streamurl'],headers={'Icy-MetaData':'1','User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			stream=self._ShoutcastConnect(self.config['streamurl'],{'Icy-MetaData':'1','User-Agent':'DiStreamer'},self.config['httptimeout'])
		else:
			stream=self._ShoutcastConnect(self.config['streamurl'],{'User-Agent':'DiStreamer'},self.config['httptimeout'])
		self.logger.log("Connected to stream",'ShoutcastClient',3)
		self.store.setIcyHeaders(icyheaders)
		
		while not self.isclosing:
			try:
				fragment=stream.read(self.config['fragmentsize'])
			except:
				if self.isclosing:
					return None
			if len(fragment)!=self.config['fragmentsize']:
				raise ValueError("Incomplete read of block")
			idx=counter
			if self.store.getIcyInt()>0:
				if idx==icyreadfromblock:
					icytemptitle=icytemptitle+fragment[:icynbstart-1]
					icyreadingtitle=False
				if not icyreadingtitle and icytemptitle!='':
					self.store.setIcyTitle(icytemptitle)
					icytemptitle=""
				if idx<icyreadfromblock and icyreadingtitle:
					icytemptitle=icytemptitle+fragment
				if idx>=icyreadfromblock:
					if icynbstart>0:
						x=icynbstart
					else:
						x=0
					icynbstart=0
					while x<self.config['fragmentsize']:
						if icyread==self.store.getIcyInt():
							icylen=ord(fragment[x])*16+1
							icystart=x+1
							icytpos=x+icylen
							icytblock=idx
							while icytpos>=self.config['fragmentsize']:
								icytblock=icytblock+1
								icytpos=icytpos-self.config['fragmentsize']
								icynbstart=icytpos+1
							icyblock=icytblock
							icypos=icytpos
							icyreadfromblock=icyblock
							if icylen>1:
								if icyblock==idx:
									icyreadingtitle=False
									icytemptitle=fragment[icystart:icypos]
								else:
									icyreadingtitle=True
									icytemptitle=fragment[icystart:]
							if not icylist.has_key(icyblock):
								icylist[icyblock]=[]
							icylist[icyblock].append(icypos)
							x=x+icylen
							icyread=0
						icyread=icyread+1
						x=x+1
			counter=counter+1
			fragments[idx]=fragment
			self.logger.log("Created fragment "+str(idx),'ShoutcastClient',3)
			while len(fragments)>self.config['fragmentsnumber']:
				todelete=min(fragments.keys())
				del fragments[todelete]
				if icylist.has_key(todelete):
					del icylist[todelete]
				self.logger.log("Deleted fragment "+str(todelete),'ShoutcastClient',3)
			self.store.setFragments(fragments)
			self.store.setIcyList(icylist)
		self.logger.log('ShoutcastClient terminated normally','ShoutcastClient',2)
		
	def close(self):
		self.isclosing=True
		self.logger.log('ShoutcastClient is terminating, this could need some time','ShoutcastClient',3)
		if self.socket:
			self.socket.close()
